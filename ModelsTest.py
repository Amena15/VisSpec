#!/usr/bin/env python3
"""
Comprehensive model test for VisSpec.
Tests all models and their relationships.
Idempotent: uses unique IDs per run, never conflicts with existing data.
Run with: python ModelsTest.py
"""

import asyncio
import sys
from pathlib import Path
import uuid
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.config.database import AsyncSessionLocal, engine, Base as DBBase
from backend.core.config import settings
from backend.models.user import User
from backend.models.project import Project
from backend.models.document import RequirementDocument
from backend.models.requirement import Requirement
from backend.models.requirement_history import RequirementVersionHistory  # corrected import
from backend.models.validation import ValidationSession, Defect
from backend.models.diagram import Diagram, DiagramElement
from backend.models.traceability import TraceabilityMatrix, TraceabilityNote
from backend.models.metrics import ProjectMetrics
from backend.models.review import ReviewAudit
from backend.models.auxiliary import ExportReport, AIPromptLog
from backend.models.notification import Notification

# For sync table creation and async queries
from sqlalchemy import create_engine, select
from sqlalchemy.orm import selectinload

# Generate a unique suffix for this run (makes all IDs unique)
RUN_SUFFIX = uuid.uuid4().hex[:8]
TEST_EMAIL = f"test-{RUN_SUFFIX}@example.com"
TEST_USER_ID = f"test-user-{RUN_SUFFIX}"
TEST_PROJECT_ID = f"test-proj-{RUN_SUFFIX}"
TEST_DOC_ID = f"test-doc-{RUN_SUFFIX}"
TEST_REQ_ID = f"test-req-{RUN_SUFFIX}"
TEST_VAL_ID = f"test-val-{RUN_SUFFIX}"
TEST_DEFECT_ID = f"test-defect-{RUN_SUFFIX}"
TEST_DIAGRAM_ID = f"test-diag-{RUN_SUFFIX}"
TEST_ELEMENT_ID = f"test-elem-{RUN_SUFFIX}"
TEST_TM_ID = f"test-tm-{RUN_SUFFIX}"
TEST_NOTE_ID = f"test-note-{RUN_SUFFIX}"
TEST_METRICS_ID = f"test-metrics-{RUN_SUFFIX}"
TEST_REVIEW_ID = f"test-review-{RUN_SUFFIX}"
TEST_REPORT_ID = f"test-report-{RUN_SUFFIX}"
TEST_PROMPT_ID = f"test-prompt-{RUN_SUFFIX}"
TEST_NOTIF_ID = f"test-notif-{RUN_SUFFIX}"
TEST_VERSION_ID = f"test-ver-{RUN_SUFFIX}"


async def create_tables():
    """Create all tables if they don't exist (idempotent)."""
    sync_db_url = settings.DATABASE_URL
    if sync_db_url.startswith("postgresql+asyncpg://"):
        sync_db_url = sync_db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    sync_engine = create_engine(sync_db_url)
    DBBase.metadata.create_all(bind=sync_engine)
    sync_engine.dispose()
    print("✅ Tables ensured.")


async def test_all_models():
    """Create sample records for every model and verify relationships."""
    async with AsyncSessionLocal() as db:
        print(f"\n🔹 Running test with suffix: {RUN_SUFFIX}")
        print(f"   User email: {TEST_EMAIL}")

        # ----- 1. User -----
        user = User(
            user_id=TEST_USER_ID,
            email=TEST_EMAIL,
            username=f"tester-{RUN_SUFFIX}",
            password_hash="fakehash",
            role="analyst"
        )
        db.add(user)
        await db.flush()
        print(f"✓ Created User: {user.user_id}")

        # ----- 2. Project -----
        project = Project(
            project_id=TEST_PROJECT_ID,
            owner_id=user.user_id,
            name=f"Test Project {RUN_SUFFIX}",
            description="Sample project"
        )
        db.add(project)
        await db.flush()
        print(f"✓ Created Project: {project.project_id}")

        # ----- 3. RequirementDocument -----
        doc = RequirementDocument(
            doc_id=TEST_DOC_ID,
            project_id=project.project_id,
            uploaded_by=user.user_id,
            filename=f"sample_{RUN_SUFFIX}.txt",
            file_extension="txt",
            file_size_bytes=1024,
            status="Uploaded"
        )
        db.add(doc)
        await db.flush()
        print(f"✓ Created Document: {doc.doc_id}")

        # ----- 4. Requirement -----
        req = Requirement(
            req_id=TEST_REQ_ID,
            doc_id=doc.doc_id,
            project_id=project.project_id,
            original_text="The system shall allow users to log in.",
            current_text="The system shall allow users to log in.",
            word_count=8
        )
        db.add(req)
        await db.flush()
        print(f"✓ Created Requirement: {req.req_id}")

        # ----- 5. RequirementVersionHistory -----
        version = RequirementVersionHistory(
            version_id=TEST_VERSION_ID,
            req_id=req.req_id,
            doc_id=doc.doc_id,
            project_id=project.project_id,
            old_text="Old text",
            new_text="New text",
            change_type="suggestion_applied"
        )
        db.add(version)
        await db.flush()
        print(f"✓ Created RequirementVersionHistory: {version.version_id}")

        # ----- 6. ValidationSession -----
        val = ValidationSession(
            validation_id=TEST_VAL_ID,
            project_id=project.project_id,
            doc_id=doc.doc_id,
            triggered_by=user.user_id,
            status="completed",
            overall_score=85.5,
            total_requirements=1,
            defect_count=1
        )
        db.add(val)
        await db.flush()
        print(f"✓ Created ValidationSession: {val.validation_id}")

        # ----- 7. Defect -----
        defect = Defect(
            defect_id=TEST_DEFECT_ID,
            validation_id=val.validation_id,
            req_id=req.req_id,
            defect_type="ambiguity",
            severity="medium",
            confidence_score=0.9,
            description="Ambiguous wording"
        )
        db.add(defect)
        await db.flush()
        print(f"✓ Created Defect: {defect.defect_id}")

        # ----- 8. Diagram -----
        diag = Diagram(
            diagram_id=TEST_DIAGRAM_ID,
            project_id=project.project_id,
            validation_id=val.validation_id,
            diagram_type="usecase",
            mermaid_syntax="graph TD; A-->B;",
            syntax_valid=1
        )
        db.add(diag)
        await db.flush()
        print(f"✓ Created Diagram: {diag.diagram_id}")

        # ----- 9. DiagramElement -----
        elem = DiagramElement(
            element_id=TEST_ELEMENT_ID,
            diagram_id=diag.diagram_id,
            source_req_id=req.req_id,
            element_type="actor",
            element_name="User"
        )
        db.add(elem)
        await db.flush()
        print(f"✓ Created DiagramElement: {elem.element_id}")

        # ----- 10. TraceabilityMatrix -----
        tm = TraceabilityMatrix(
            matrix_id=TEST_TM_ID,
            project_id=project.project_id,
            req_id=req.req_id,
            validation_id=val.validation_id,
            diagram_id=diag.diagram_id,
            validation_status="passed"
        )
        db.add(tm)
        await db.flush()
        print(f"✓ Created TraceabilityMatrix: {tm.matrix_id}")

        # ----- 11. TraceabilityNote -----
        tn = TraceabilityNote(
            note_id=TEST_NOTE_ID,
            req_id=req.req_id,
            created_by=user.user_id,
            project_id=project.project_id,
            content="This is a test note"
        )
        db.add(tn)
        await db.flush()
        print(f"✓ Created TraceabilityNote: {tn.note_id}")

        # ----- 12. ProjectMetrics -----
        metrics = ProjectMetrics(
            metrics_id=TEST_METRICS_ID,
            project_id=project.project_id,
            validation_id=val.validation_id,
            total_requirements=1,
            complexity_score=50.0
        )
        db.add(metrics)
        await db.flush()
        print(f"✓ Created ProjectMetrics: {metrics.metrics_id}")

        # ----- 13. ReviewAudit -----
        review = ReviewAudit(
            review_id=TEST_REVIEW_ID,
            project_id=project.project_id,
            supervisor_id=user.user_id,
            validation_id=val.validation_id,
            decision="approved"
        )
        db.add(review)
        await db.flush()
        print(f"✓ Created ReviewAudit: {review.review_id}")

        # ----- 14. ExportReport -----
        report = ExportReport(
            report_id=TEST_REPORT_ID,
            project_id=project.project_id,
            validation_id=val.validation_id,
            generated_by=user.user_id,
            report_type="full"
        )
        db.add(report)
        await db.flush()
        print(f"✓ Created ExportReport: {report.report_id}")

        # ----- 15. AIPromptLog -----
        prompt_log = AIPromptLog(
            prompt_log_id=TEST_PROMPT_ID,
            validation_id=val.validation_id,
            req_batch_index=0,
            model="llama3-70b-8192",
            temperature=0.1,
            parse_succeeded=1
        )
        db.add(prompt_log)
        await db.flush()
        print(f"✓ Created AIPromptLog: {prompt_log.prompt_log_id}")

        # ----- 16. Notification -----
        notif = Notification(
            id=TEST_NOTIF_ID,
            user_id=user.user_id,
            project_id=project.project_id,
            type="review_approved",
            content="Your project was approved"
        )
        db.add(notif)
        await db.flush()
        print(f"✓ Created Notification: {notif.id}")

        # Commit everything
        await db.commit()
        print("\n🎉 All models created successfully!")

        # ----- Verify relationships (eager load after commit) -----
        print("\n🔍 Verifying relationships...")

        # Re‑fetch user with projects
        stmt = select(User).where(User.user_id == TEST_USER_ID).options(selectinload(User.projects))
        result = await db.execute(stmt)
        user = result.scalar_one()

        # Re‑fetch project with its relationships
        stmt = select(Project).where(Project.project_id == TEST_PROJECT_ID).options(
            selectinload(Project.documents),
            selectinload(Project.metrics),
            selectinload(Project.traceability_matrix),
            selectinload(Project.traceability_notes),
            selectinload(Project.review_audits),
            selectinload(Project.export_reports),
        )
        result = await db.execute(stmt)
        project = result.scalar_one()

        # Re‑fetch document with requirements
        stmt = select(RequirementDocument).where(RequirementDocument.doc_id == TEST_DOC_ID).options(
            selectinload(RequirementDocument.requirements)
        )
        result = await db.execute(stmt)
        doc = result.scalar_one()

        # Re‑fetch requirement with defects and version history
        stmt = select(Requirement).where(Requirement.req_id == TEST_REQ_ID).options(
            selectinload(Requirement.defects),
            selectinload(Requirement.version_history),
        )
        result = await db.execute(stmt)
        req = result.scalar_one()

        # Re‑fetch validation session with its children
        stmt = select(ValidationSession).where(ValidationSession.validation_id == TEST_VAL_ID).options(
            selectinload(ValidationSession.defects),
            selectinload(ValidationSession.diagrams),
            selectinload(ValidationSession.ai_prompt_logs),
        )
        result = await db.execute(stmt)
        val = result.scalar_one()

        # Re‑fetch diagram with elements
        stmt = select(Diagram).where(Diagram.diagram_id == TEST_DIAGRAM_ID).options(
            selectinload(Diagram.elements)
        )
        result = await db.execute(stmt)
        diag = result.scalar_one()

        # Assertions
        assert user.projects[0].project_id == project.project_id
        assert project.documents[0].doc_id == doc.doc_id
        assert doc.requirements[0].req_id == req.req_id
        assert req.defects[0].defect_id == TEST_DEFECT_ID
        assert req.version_history[0].version_id == TEST_VERSION_ID
        assert val.defects[0].defect_id == TEST_DEFECT_ID
        assert val.diagrams[0].diagram_id == TEST_DIAGRAM_ID
        assert diag.elements[0].element_id == TEST_ELEMENT_ID
        assert project.metrics.metrics_id == TEST_METRICS_ID
        assert project.traceability_matrix[0].matrix_id == TEST_TM_ID
        assert project.traceability_notes[0].note_id == TEST_NOTE_ID
        assert project.review_audits[0].review_id == TEST_REVIEW_ID
        assert project.export_reports[0].report_id == TEST_REPORT_ID
        assert val.ai_prompt_logs[0].prompt_log_id == TEST_PROMPT_ID

        print("✅ All relationship checks passed!")

        
        print("\n🎉 All tests completed successfully!")


async def main():
    print("=" * 60)
    print("VisSpec - Full Model Test Suite")
    print("=" * 60)
    await create_tables()
    await test_all_models()
    await engine.dispose()
    print("\n✨ Done.")


if __name__ == "__main__":
    asyncio.run(main())