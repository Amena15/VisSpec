"""
Text cleaning service for requirement preprocessing.
Cleans common OCR and formatting errors in requirements text.
"""

import re
from typing import Dict, List, Any
from backend.core.logging import get_logger

logger = get_logger(__name__)

# Modal verbs that often get concatenated by PDF extraction (no space between words)
_MODAL_ALT = r"shall|must|should|will|may|might|could|would|can"
CONCATENATED_MODAL_PAIR = re.compile(
    rf"(?i)({_MODAL_ALT})({_MODAL_ALT})(?!\w)",
)

# ---------------------------------------------------------------------------
# PII redaction patterns (privacy-by-default before any text reaches the LLM).
#
# NOTE: Zero-retention is a policy guarantee of the Groq API provider, not a
# locally enforced code feature. Local PII redaction IS applied here, in
# text_cleaner.py, so that obvious personally-identifiable information is
# stripped before the text is ever sent to an external LLM.
# ---------------------------------------------------------------------------
PII_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PII_PHONE = re.compile(
    r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}(?!\d)"
)
# Long digit runs that are not years in a plausible range (e.g. account/ID numbers)
PII_LONG_NUMBER = re.compile(r"(?<!\d)\d{7,}(?!\d)")
# National ID / IC / NRIC style tokens: letter + digits + letter (e.g. 990101-14-5555)
PII_NRIC = re.compile(r"\b\d{6}\s?-?\s?\d{2}\s?-?\s?\d{4}\b")
# IPv4 addresses
PII_IP = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")

PII_PLACEHOLDER_EMAIL = "[EMAIL_REDACTED]"
PII_PLACEHOLDER_PHONE = "[PHONE_REDACTED]"
PII_PLACEHOLDER_NRIC = "[ID_REDACTED]"
PII_PLACEHOLDER_NUMBER = "[NUMBER_REDACTED]"
PII_PLACEHOLDER_IP = "[IP_REDACTED]"



class TextCleaner:
    """Cleans and standardizes requirement text."""

    # Common repeated words and their corrections (both with and without space)
    WORD_CORRECTIONS = {
        'willwill': 'will',
        'will will': 'will',
        'shallshall': 'shall',
        'shall shall': 'shall',
        'mustmust': 'must',
        'must must': 'must',
        'shouldshould': 'should',
        'should should': 'should',
        'cancan': 'can',
        'can can': 'can',
        'maymay': 'may',
        'may may': 'may',
        'couldcould': 'could',
        'could could': 'could',
        'wouldwould': 'would',
        'would would': 'would',
        'mighmight': 'might',
        'might might': 'might',
        'needneed': 'need',
        'need need': 'need',
        'havehave': 'have',
        'have have': 'have',
        'bebe': 'be',
        'be be': 'be',
        'dodo': 'do',
        'do do': 'do',
        'is is': 'is',
        'are are': 'are',
        'was was': 'was',
        'were were': 'were',
        'the the': 'the',
        'and and': 'and',
        'or or': 'or',
        'to to': 'to',
        'of of': 'of',
        'in in': 'in',
        'on on': 'on',
        'at at': 'at',
        'for for': 'for',
        'with with': 'with',
        'by by': 'by',
        'from from': 'from',
        'as as': 'as',
    }

    # Pattern to find repeated words (case insensitive)
    REPEATED_WORDS_PATTERN = re.compile(r'\b(\w+)(\s+\1)+\b', re.IGNORECASE)

    # Pattern to clean up extra whitespace
    WHITESPACE_PATTERN = re.compile(r'\s+')

    # Pattern to fix sentence spacing
    SENTENCE_SPACING_PATTERN = re.compile(r'\.([a-zA-Z])')

    # Pattern to fix "shall shall" and similar patterns (both with and without space)
    DOUBLE_MODAL_PATTERN = re.compile(r'\b(shall|will|must|should|can|may|could|would|might|need|have|be|do|is|are|was|were|the|and|or|to|of|in|on|at|for|with|by|from|as)(\s+\1|\1)\b', re.IGNORECASE)

    @classmethod
    def fix_concatenated_modals(cls, text: str) -> str:
        """
        Split modal verbs jammed together without a space (e.g. PDF extraction: 'shallwill').
        A trailing \\b between modals does not match, so the old merged-modal regex missed these.
        """
        if not text or not isinstance(text, str):
            return text

        def _repl(m: re.Match) -> str:
            a, b = m.group(1), m.group(2)
            if a.lower() == b.lower():
                return a
            return f"{a} {b}"

        return CONCATENATED_MODAL_PAIR.sub(_repl, text)

    @classmethod
    def redact_pii(cls, text: str) -> str:
        """
        Strip obvious personally-identifiable information from requirement text
        BEFORE it is sent to an external LLM provider (Groq / LLaMA 3).

        This is a local privacy control. It is deliberately conservative: it only
        targets unambiguous PII patterns (emails, phone numbers, national-ID /
        NRIC-style numbers, and long account/ID digit runs) and replaces them with
        clear placeholders. It is applied first in clean_requirement_text().

        Args:
            text: Raw requirement text (may contain PII)

        Returns:
            Text with obvious PII replaced by redaction placeholders.
        """
        if not text or not isinstance(text, str):
            return text

        original_text = text

        # Order matters: redact more specific patterns before the generic ones.
        # NRIC/ID and long account numbers are handled before the generic phone
        # pattern so a 10-digit account number is labelled as a number, not a phone.
        text = PII_EMAIL.sub(PII_PLACEHOLDER_EMAIL, text)
        text = PII_NRIC.sub(PII_PLACEHOLDER_NRIC, text)
        text = PII_LONG_NUMBER.sub(PII_PLACEHOLDER_NUMBER, text)
        text = PII_IP.sub(PII_PLACEHOLDER_IP, text)
        text = PII_PHONE.sub(PII_PLACEHOLDER_PHONE, text)

        if text != original_text:
            logger.info("Redacted PII from requirement text before LLM transmission.")

        return text

    @classmethod
    def clean_requirement_text(cls, text: str) -> str:
        """
        Clean and standardize requirement text.
        
        Args:
            text: Raw requirement text
            
        Returns:
            Cleaned requirement text
        """
        if not text or not isinstance(text, str):
            return text

        original_text = text

        # Step -1: Redact obvious PII (emails, phone numbers, national IDs, IPs,
        # long account numbers) BEFORE the text ever reaches the LLM provider.
        text = cls.redact_pii(text)

        # Add this new step to strip markdown (**) and stray slashes
        text = text.replace('**', '').replace('__', '').replace('`', '')
        text = text.replace('\\', '')
        
        # Step 0: Modal + modal with no space (shallwill -> shall will)
        text = cls.fix_concatenated_modals(text)
        
        # Step 1: Fix repeated words (willwill -> will)
        for repeated, correction in cls.WORD_CORRECTIONS.items():
            text = text.replace(repeated, correction)
        
        # Step 2: Fix pattern-based repetitions (shall shall -> shall)
        text = cls.DOUBLE_MODAL_PATTERN.sub(lambda m: m.group(1).lower(), text)
        
        # Step 3: Fix any remaining repeated words using regex
        text = cls.REPEATED_WORDS_PATTERN.sub(lambda m: m.group(1), text)
        
        # Step 4: Clean up extra whitespace
        text = cls.WHITESPACE_PATTERN.sub(' ', text)
        
        # Step 5: Fix sentence spacing (.word -> . word)
        text = cls.SENTENCE_SPACING_PATTERN.sub(r'. \1', text)
        
        # Step 6: Strip leading/trailing whitespace
        text = text.strip()
        
        # Step 7: Ensure proper sentence capitalization
        if text and len(text) > 0:
            text = text[0].upper() + text[1:]
        
        # Log if changes were made
        if text != original_text:
            logger.info(f"Cleaned requirement text: '{original_text[:50]}...' -> '{text[:50]}...'")
        
        return text

    @classmethod
    def clean_and_redact(cls, text: str) -> str:
        """
        Convenience pipeline: redact PII first (privacy-by-default), then apply the
        normal text cleaning/standardisation. Use this wherever text is about to be
        sent to an external LLM.
        """
        return cls.clean_requirement_text(cls.redact_pii(text))



    @classmethod
    def clean_requirements_batch(cls, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean a batch of requirements.
        
        Args:
            requirements: List of requirement dictionaries
            
        Returns:
            List of cleaned requirement dictionaries
        """
        cleaned_requirements = []
        
        for req in requirements:
            cleaned_req = req.copy()
            
            # Clean both original_text and current_text if they exist
            if 'original_text' in cleaned_req:
                cleaned_req['original_text'] = cls.clean_requirement_text(cleaned_req['original_text'])
            
            if 'current_text' in cleaned_req:
                cleaned_req['current_text'] = cls.clean_requirement_text(cleaned_req['current_text'])
            
            # Also clean section headers if present
            if 'section_header' in cleaned_req:
                cleaned_req['section_header'] = cls.clean_requirement_text(cleaned_req['section_header'])
            
            cleaned_requirements.append(cleaned_req)
        
        logger.info(f"Cleaned {len(cleaned_requirements)} requirements")
        return cleaned_requirements

    @classmethod
    def validate_cleaning(cls, original: str, cleaned: str) -> Dict[str, Any]:
        """
        Validate the cleaning process and report changes.
        
        Args:
            original: Original text
            cleaned: Cleaned text
            
        Returns:
            Dictionary with validation results
        """
        changes = []
        
        # Check for repeated words removal
        original_repeated = cls.REPEATED_WORDS_PATTERN.findall(original)
        cleaned_repeated = cls.REPEATED_WORDS_PATTERN.findall(cleaned)
        
        if len(original_repeated) > len(cleaned_repeated):
            changes.append(f"Removed {len(original_repeated) - len(cleaned_repeated)} repeated word instances")
        
        # Check for specific corrections
        for repeated, correction in cls.WORD_CORRECTIONS.items():
            if repeated in original and correction in cleaned:
                changes.append(f"Fixed '{repeated}' -> '{correction}'")
        
        # Check length reduction
        if len(cleaned) < len(original):
            changes.append(f"Reduced length by {len(original) - len(cleaned)} characters")
        
        return {
            'original_length': len(original),
            'cleaned_length': len(cleaned),
            'changes_made': changes,
            'improvement_ratio': (len(original) - len(cleaned)) / len(original) if original else 0
        }
