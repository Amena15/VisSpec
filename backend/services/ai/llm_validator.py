"""
Enhanced LLM Validator for VisSpec (structured IEEE 830 validation with
confidence filtering, BR-10).

Provider selection: backend/core/config.py LLM_PROFILES. Default profile is
groq-gpt-oss-120b (a REASONING model); the ovh-llama33-70b profile runs the
same code against OVHcloud AI Endpoints. Switch with LLM_PROFILE in .env.

Reproducibility notes:
- The exact prompt lives in backend/services/ai/prompts_v2.txt; its SHA-256 is
  computed at import time and exposed as PROMPT_SHA256 (recorded by the
  evaluation for provenance).
- The 0.70 threshold (BR-10) is applied in application code only
  (_filter_by_confidence), never in the prompt.
- Raw (pre-filter) confidences and the LLM's evidence field are preserved in
  the returned payload so evaluations can apply any threshold after the fact.
- PII is redacted (privacy.py) before the request leaves the machine and
  restored locally after the response returns.
- Honesty rules: an EMPTY answer, a CUT-OFF answer (finish_reason=length),
  a malformed payload, or a response whose model id differs from the
  configured one are ALL llm_failed — never counted as "no defects".
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential


def _rate_limit_aware_wait(retry_state) -> float:
    """Retry wait strategy: HTTP 429 (anonymous-tier rolling window) gets a
    long flat 30s cool-down; any other error keeps the short exponential
    backoff. Without this, brief 429 bursts exhaust the 3-attempt budget and
    unnecessarily mark an otherwise-valid evaluation run INCOMPLETE."""
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    if exc is not None and "429" in str(exc):
        return 30.0
    return wait_exponential(multiplier=1, min=4, max=10)(retry_state)

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.services.ai import privacy

logger = get_logger(__name__)

# Exact prompt artifact (single source of truth) + its hash for provenance.
_PROMPT_PATH = Path(__file__).resolve().parent / "prompts_v2.txt"
PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")
PROMPT_SHA256 = hashlib.sha256(PROMPT_TEMPLATE.encode("utf-8")).hexdigest()


class LLMValidator:
    """
    Provider-agnostic LLM validator (profile from config: default
    Groq openai/gpt-oss-120b). Structured validation with IEEE 830 criteria
    and confidence filtering.
    """

    def __init__(self, prompt_path: Optional[str] = None,
                 temperature: Optional[float] = None):
        """
        Args:
            prompt_path: optional alternate prompt artifact (dev-only prompt
                tuning candidates, e.g. prompts_v3.txt). Default is the
                frozen prompts_v2.txt.
            temperature: optional temperature override (dev-only tuning
                compares 0.1 vs 0.0). Default is settings.LLM_TEMPERATURE.
        """
        self.api_key = settings.LLM_API_KEY
        self.model = settings.llm_model_id
        self.base_url = settings.llm_base_url
        self.temperature = settings.LLM_TEMPERATURE if temperature is None else temperature
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.reasoning_effort = settings.LLM_REASONING_EFFORT
        self.profile = settings.LLM_PROFILE
        self.confidence_threshold = settings.MIN_CONFIDENCE_THRESHOLD

        # Prompt artifact: default = frozen candidate; overrides are for
        # dev-only tuning and must be recorded (SHA) in experiments_dev.md.
        self.prompt_path = Path(prompt_path) if prompt_path else _PROMPT_PATH
        self.prompt_template = self.prompt_path.read_text(encoding="utf-8")
        self.prompt_sha256 = hashlib.sha256(
            self.prompt_template.encode("utf-8")
        ).hexdigest()

        # Availability = key present for key-required profiles; the OVH
        # anonymous tier needs only its base URL (no key at all).
        self._available = settings.llm_available

        if not self._available:
            logger.warning(
                f"LLM profile '{self.profile}' unavailable "
                f"(key required: {settings.llm_key_required}, key set: "
                f"{bool(self.api_key)}). LLM validation will be disabled."
            )
        else:
            logger.info(
                f"LLM Validator initialized: profile={self.profile} "
                f"model={self.model} host={settings.llm_host}"
            )

    @property
    def is_available(self) -> bool:
        """Check if LLM validator is available."""
        return self._available

    def validate_requirement(self, requirement_text: str) -> Dict[str, Any]:
        """
        Validate a single requirement using LLaMA 3.3 70B with IEEE 830 standards.

        Args:
            requirement_text: The requirement text to validate

        Returns:
            Dict with:
              - defects: raw defects as returned by the LLM (with evidence),
                         unfiltered — raw confidence preserved on each defect
              - filtered_defects: defects passing BR-10 (confidence >= 0.70)
              - llm_used: True ONLY when the provider answered and JSON parsed
              - json_parse_ok: whether the response parsed as the expected JSON
              - model_used: model id reported by the API response (falls back to
                            the configured id if the API omits it)
              - error: redacted error message, if any
        """
        if not self._available:
            return {"defects": [], "filtered_defects": [], "llm_used": False,
                    "json_parse_ok": False, "error": "LLM not available"}

        try:
            # Local privacy control: redact PII before the text leaves the machine,
            # restore it in the response fields afterwards. (Zero-retention is a
            # provider policy guarantee, not a feature of this code.)
            redacted_text, mapping = privacy.redact(requirement_text)
            logger.info("Sending PII-redacted requirement to LLM provider.")

            # Construct IEEE 830 compliant prompt (threshold NOT in prompt)
            prompt = self._build_validation_prompt(redacted_text)

            # Call LLM with retry logic
            response, api_model, finish_reason = self._call_llm_with_retry(prompt)
            model_returned = api_model or None

            # --- Honesty gate 1: model identity ---
            # The API must report the exact configured model; anything else
            # means we are not evaluating what we claim to evaluate.
            if model_returned and model_returned != self.model:
                return {"defects": [], "filtered_defects": [], "llm_used": False,
                        "json_parse_ok": False, "model_used": model_returned,
                        "model_returned": model_returned,
                        "error": f"model mismatch: returned '{model_returned}' "
                                 f"!= configured '{self.model}'"}

            # --- Honesty gate 2: empty or cut-off answer ---
            # A reasoning model can burn its token budget and return nothing
            # (or be truncated at finish_reason=length). That is a FAILED call,
            # never an implicit "no defects".
            if finish_reason == "length":
                return {"defects": [], "filtered_defects": [], "llm_used": False,
                        "json_parse_ok": False, "model_used": model_returned or self.model,
                        "model_returned": model_returned,
                        "error": "answer cut off (finish_reason=length)"}
            if not (response and response.strip()):
                return {"defects": [], "filtered_defects": [], "llm_used": False,
                        "json_parse_ok": False, "model_used": model_returned or self.model,
                        "model_returned": model_returned,
                        "error": "empty answer from LLM (no content returned)"}

            # Parse JSON response
            parsed_response = self._parse_llm_response(response)
            json_parse_ok = parsed_response is not None and "defects" in parsed_response

            if json_parse_ok:
                raw_defects = parsed_response["defects"]
                # Restore redacted spans locally in the evidence/description fields
                for d in raw_defects:
                    for key in ("evidence", "description", "text"):
                        if isinstance(d.get(key), str):
                            d[key] = privacy.restore(d[key], mapping)

                # BR-10 filter in application code only (raw list kept intact)
                filtered_defects = self._filter_by_confidence(raw_defects)

                logger.info("LLM response received and parsed successfully.")
                return {
                    "defects": raw_defects,
                    "filtered_defects": filtered_defects,
                    "llm_used": True,
                    "json_parse_ok": True,
                    "model_used": model_returned or self.model,
                    "model_returned": model_returned,
                }

            # Provider answered but payload was malformed -> NOT an LLM verdict
            return {"defects": [], "filtered_defects": [], "llm_used": False,
                    "json_parse_ok": False,
                    "model_used": model_returned or self.model,
                    "model_returned": model_returned,
                    "error": "LLM response did not parse as valid JSON"}

        except Exception as e:
            # Redact any PII that a provider error message might echo back.
            safe_error = privacy.redact(str(e))[0]
            logger.error(f"LLM validation failed: {safe_error}")
            return {"defects": [], "filtered_defects": [], "llm_used": False,
                    "json_parse_ok": False, "model_used": self.model,
                    "model_returned": None,
                    "error": safe_error}

    def validate_batch(self, requirements: List[str]) -> Dict[str, Any]:
        """
        Validate multiple requirements in batch for efficiency.
        
        Args:
            requirements: List of requirement texts to validate
            
        Returns:
            Dict with defects mapped to requirement indices
        """
        if not self._available:
            return {"defects_by_index": {}, "llm_used": False, "error": "LLM not available"}

        try:
            logger.info(f"Validating batch of {len(requirements)} requirements with LLM")
            
            all_defects = {}
            for i, req_text in enumerate(requirements):
                result = self.validate_requirement(req_text)
                if result.get("defects"):
                    all_defects[i] = result["defects"]
            
            return {
                "defects_by_index": all_defects,
                "llm_used": True,
                "model_used": self.model,
                "total_requirements": len(requirements),
                "requirements_with_defects": len(all_defects)
            }

        except Exception as e:
            logger.error(f"Batch LLM validation failed: {e}")
            return {"defects_by_index": {}, "llm_used": False, "error": str(e)}

    def _build_validation_prompt(self, requirement_text: str) -> str:
        """
        Build the validation prompt from the saved artifact (prompts_v2.txt).

        The exact template and its SHA-256 (PROMPT_SHA256) are recorded by the
        evaluation for reproducibility. The BR-10 threshold is intentionally
        NOT part of the prompt — it is applied in application code only.

        Args:
            requirement_text: The requirement to validate

        Returns:
            Structured prompt for LLM
        """
        return self.prompt_template.replace("{requirement_text}", requirement_text)

    @retry(
        stop=stop_after_attempt(5),
        wait=_rate_limit_aware_wait,
        reraise=True
    )
    def _call_llm_with_retry(self, prompt: str) -> tuple:
        """
        Call LLM with retry logic for reliability.

        Args:
            prompt: The prompt to send to LLM

        Returns:
            (content, api_model, finish_reason):
              content      — LLM response text (may be empty; caller must treat
                             empty as llm_failed, never as "no defects")
              api_model    — model id reported by the API response, if any
              finish_reason — provider finish_reason (e.g. "stop", "length";
                             "length" means the answer was CUT OFF)
        """
        import requests

        headers = {
         "Content-Type": "application/json",
        }
        if self.api_key:
         headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"}
        }
        # Reasoning models accept reasoning_effort on Groq (probe-verified);
        # if the provider rejects the parameter, drop it for this call and
        # record it once — see README "reasoning_effort" note.
        if self.reasoning_effort and self.profile.startswith("groq-"):
            payload["reasoning_effort"] = self.reasoning_effort

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            if response.status_code == 400 and "reasoning_effort" in response.text:
                logger.warning(
                    "Provider rejected reasoning_effort; retrying without it. "
                    "Remove LLM_REASONING_EFFORT from config if this persists."
                )
                payload.pop("reasoning_effort", None)
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=120
                )
            response.raise_for_status()

            data = response.json()
            api_model = data.get("model")  # model actually used, as reported by API
            choice = data["choices"][0]
            content = choice.get("message", {}).get("content")
            finish_reason = choice.get("finish_reason")
            # None content (reasoning model burned tokens) -> empty string so
            # the caller's empty-answer rule fires deterministically.
            return (content or ""), api_model, finish_reason

        except requests.RequestException as e:
            # Redact: provider errors can echo request fragments.
            logger.error(f"LLM API request failed: {privacy.redact(str(e))[0]}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in LLM call: {privacy.redact(str(e))[0]}")
            raise

    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse LLM JSON response safely.
        
        Args:
            response: Raw LLM response text
            
        Returns:
            Parsed JSON dict or None if invalid
        """
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Invalid JSON response: {response}")
            return None

    def _filter_by_confidence(self, defects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter defects by confidence threshold (BR-10).
        
        Args:
            defects: List of defect dictionaries
            
        Returns:
            Filtered list with confidence >= 0.70
        """
        filtered = []
        for defect in defects:
            confidence = defect.get("confidence", 0.0)
            if confidence >= self.confidence_threshold:
                filtered.append(defect)
            else:
                logger.debug(f"Filtered defect with confidence {confidence}: {defect.get('type', 'unknown')}")
        
        logger.info(f"Filtered defects: {len(filtered)}/{len(defects)} meet confidence >= {self.confidence_threshold}")
        return filtered

    def get_validation_stats(self) -> Dict[str, Any]:
        """
        Get validation statistics and status.
        
        Returns:
            Dict with validator status and configuration
        """
        return {
            "available": self._available,
            "model": self.model,
            "temperature": self.temperature,
            "confidence_threshold": self.confidence_threshold,
            "api_key_configured": bool(self.api_key)
        }
