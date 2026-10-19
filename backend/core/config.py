"""
Environment configuration management.
Loads settings from .env file with sensible defaults using Pydantic Settings.
"""
from pathlib import Path
from urllib.parse import urlparse

from pydantic_settings import BaseSettings

# ---------------------------------------------------------------------------
# Named LLM provider profiles. Select with LLM_PROFILE in .env; individual
# LLM_BASE_URL / LLM_MODEL / LLM_API_KEY values in .env override the profile.
# Adding a profile = adding an entry here; no code changes elsewhere.
# ---------------------------------------------------------------------------
LLM_PROFILES = {
    # Groq (key required). openai/gpt-oss-120b is a reasoning model: use
    # max_tokens 4096 and (if the API accepts it) reasoning_effort="low".
    "groq-gpt-oss-120b": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "openai/gpt-oss-120b",
        "key_required": True,
    },
    # OVHcloud AI Endpoints, anonymous tier (no key required).
    "ovh-llama33-70b": {
        "base_url": "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1",
        "model": "Meta-Llama-3_3-70B-Instruct",
        "key_required": False,
    },
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # Application
    APP_NAME: str = "VisSpec"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Override via .env for real credentials.
    # NOTE: keep defaults only for local dev; real values should come from backend/.env
    DATABASE_URL: str = "postgresql+asyncpg://vispec:vispec123@localhost:5432/vispec"

    # Security
    SECRET_KEY: str = "vispec_secret_key_for_development_purpose_only"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- LLM provider (see LLM_PROFILES above) ---
    # NOTE (accuracy audit): single source of truth = this configuration,
    # overridden by backend/.env (gitignored) or the process environment. The
    # model id must match what the evaluation actually calls — verified by
    # backend/_smoke_test.py before any evaluation run, and re-checked per
    # response (model_returned must equal the configured id or the case is
    # llm_failed). Never silently fall back to rules — never mislabel a
    # rule-based verdict as an LLM verdict.
    LLM_PROFILE: str = "groq-gpt-oss-120b"
    LLM_API_KEY: str = ""           # from .env; never printed/logged/committed
    LLM_BASE_URL: str = ""          # empty = use profile default
    LLM_MODEL: str = ""             # empty = use profile default
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096
    LLM_MAX_RETRIES: int = 3
    # Reasoning models (gpt-oss) may accept reasoning_effort; probe-verified.
    # Set empty in .env if the provider rejects the parameter.
    LLM_REASONING_EFFORT: str = "low"

    # Rate Limiting
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15

    # Document Limits
    MAX_FILE_SIZE_BYTES: int = 10485760  # 10MB
    MAX_PAGES: int = 50
    MAX_PROCESSING_TIME_MS: int = 180000  # 180 sec

    # Validation
    MIN_CONFIDENCE_THRESHOLD: float = 0.70

    # Report
    REPORT_WATERMARK: str = "VisSpec"

    # --- Resolved LLM accessors (profile + env overrides) ---
    @property
    def llm_profile_config(self) -> dict:
        return LLM_PROFILES.get(self.LLM_PROFILE, {})

    @property
    def llm_base_url(self) -> str:
        """Effective base URL: env override > profile default."""
        if self.LLM_BASE_URL:
            return self.LLM_BASE_URL.rstrip("/")
        return self.llm_profile_config.get("base_url", "").rstrip("/")

    @property
    def llm_model_id(self) -> str:
        """Effective model id: env override > profile default."""
        if self.LLM_MODEL:
            return self.LLM_MODEL
        return self.llm_profile_config.get("model", "")

    @property
    def llm_key_required(self) -> bool:
        return bool(self.llm_profile_config.get("key_required", True))

    @property
    def llm_anonymous_tier(self) -> bool:
        """True when the active endpoint needs no API key (e.g. OVH anonymous)."""
        return not self.llm_key_required

    @property
    def llm_available(self) -> bool:
        if self.llm_key_required:
            return bool(self.LLM_API_KEY)
        return bool(self.llm_base_url)

    @property
    def llm_host(self) -> str:
        """Endpoint host only (no path) — safe to log/publish in FREEZE.md."""
        return urlparse(self.llm_base_url).netloc

    class Config:
        # Load the backend-local .env reliably (so DATABASE_URL overrides defaults)
        env_file = str(Path(__file__).resolve().parent.parent / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance shared across the application
settings = Settings()
