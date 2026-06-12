#!/usr/bin/env python3\n\n"""Legacy manual test file.\n\nThis file is NOT executed by pytest (no test_ functions).\nIt is kept for developer convenience but must be import-safe.\n\nIMPORTANT:\nThe original repo used sys.path manipulation which breaks SQLAlchemy model registry.\nThis file intentionally uses only backend.* imports.\n"""\n\nfrom backend.config.database import SessionLocal\nfrom backend.models.document import RequirementDocument\n


def run_manual_validation_status_update() -> None:
    """Manually update a document status (developer utility)."""
    db = SessionLocal()
    try:
        doc_id = '13730565-f82a-422b-976f-fd2189021438'
        doc = (
            db.query(RequirementDocument)
            .filter(RequirementDocument.doc_id == doc_id)
            .first()
        )
        if not doc:
            print('Document not found')
            return

        print(f'Before update: {doc.status}')
        doc.status = "Validated - Test"
        db.commit()

        updated_doc = (
            db.query(RequirementDocument)
            .filter(RequirementDocument.doc_id == doc_id)
            .first()
        )
        print(f'After update: {updated_doc.status}')

        doc.status = "Ready for Analysis"
        db.commit()
        print(f'Reset to: {doc.status}')
    finally:
        db.close()


if __name__ == '__main__':
    run_manual_validation_status_update()

