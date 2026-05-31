#!/usr/bin/env python
"""One-time cleanup script for existing requirement texts in PostgreSQL.

Fixes historical data issues after the parser/sanitizer improvements:
- Merged modal verbs (e.g., shallwill -> shall will)
- Duplicate words (e.g., willwill -> will)
- OCR/truncation artefacts in stored text (best-effort via current cleaning logic)

IMPORTANT:
- Run this script ONCE after deploying cleaning improvements.
- After running it, you MUST re-enrich and re-validate affected documents
  (UI: "Organize Requirements" then "Run Validation").

Idempotent: re-running should not further change already-clean text.
"""

import os
import sys
from typing import Tuple

# Ensure we can import backend modules when running as: python backend/scripts/clean_requirements.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session

from config.database import SessionLocal
from models.requirement import Requirement
from models.document import RequirementDocument
from services.document.parser import DocumentParser
from services.ai.text_cleaner import TextCleaner


def _best_effort_fix_truncated_thousands(text: str) -> str:
    """Fix historical truncation like '25,00' -> '25,000' and '25,0' -> '25,000'.

    This is intentionally narrow to avoid corrupting arbitrary numbers.
    """
    # Case: 1-3 digits, comma, then 1 or 2 digits, then not immediately another digit.
    # 25,0  -> 25,000
    # 25,00 -> 25,000
    import re

    # 25,0 -> 25,000
    text = re.sub(r"\b(\d{1,3}),(\d)\b", lambda m: f"{m.group(1)},{m.group(2)}00", text)

    # 25,00 -> 25,000
    text = re.sub(r"\b(\d{1,3}),(\d{2})\b", lambda m: f"{m.group(1)},{m.group(2)}0", text)

    return text


def _clean_requirement_text(parser: DocumentParser, cleaner: TextCleaner, text: str) -> str:
    """Apply cleaning logic used during enrichment.

    Runs:
    - TextCleaner (handles concatenated modals + repeated words)
    - parser.sanitize_text (conservative whitespace/page noise cleanup)
    - best-effort truncated-thousands fix (25,0 / 25,00 -> 25,000)
    """
    cleaned = cleaner.clean_requirement_text(text)
    cleaned = _best_effort_fix_truncated_thousands(cleaned)
    cleaned = parser.sanitize_text(cleaned)
    return cleaned



def _count_and_clean_requirements(db: Session, parser: DocumentParser, cleaner: TextCleaner) -> Tuple[int, int]:
    """Returns (updated_requirements, scanned_missing_original_text)."""
    requirements = db.query(Requirement).all()
    updated = 0
    skipped_missing = 0

    for req in requirements:
        original = req.original_text
        if not original:
            skipped_missing += 1
            continue

        cleaned = _clean_requirement_text(parser, cleaner, original)
        if cleaned != original:
            req.original_text = cleaned
            # In this codebase, current_text is typically the working/enriched version.
            # Resetting both ensures downstream steps see consistent cleaned text.
            req.current_text = cleaned
            req.word_count = len(cleaned.split())
            updated += 1

    return updated, skipped_missing


def _count_and_clean_documents_text(db: Session, parser: DocumentParser) -> int:
    documents = db.query(RequirementDocument).all()
    updated = 0

    for doc in documents:
        if not doc.extracted_text:
            continue
        cleaned = parser.sanitize_text(doc.extracted_text)
        if cleaned != doc.extracted_text:
            doc.extracted_text = cleaned
            updated += 1

    return updated


def main() -> None:
    print("Starting one-time requirement cleanup...")

    db: Session = SessionLocal()
    parser = DocumentParser()
    cleaner = TextCleaner()

    try:
        updated_reqs, skipped_missing = _count_and_clean_requirements(db, parser, cleaner)
        updated_docs = _count_and_clean_documents_text(db, parser)

        db.commit()

        print("\n✅ Cleanup complete")
        print(f"- Updated requirements: {updated_reqs}")
        print(f"- Skipped requirements w/ missing original_text: {skipped_missing}")
        print(f"- Updated documents extracted_text: {updated_docs}")

        print("\nNext steps (required):")
        print("1) Re-enrich affected documents (UI: click 'Organize Requirements')")
        print("2) Re-validate affected documents (UI: click 'Run Validation')")

    except Exception as e:
        db.rollback()
        print(f"❌ Cleanup failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

