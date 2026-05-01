"""
Migration script: Migrate all data from SQLite (vispec.db) to PostgreSQL.

Usage:
    cd backend
    python scripts/migrate_sqlite_to_postgres.py

Prerequisites:
    - PostgreSQL is running and database 'vispec' exists
    - DATABASE_URL env var or .env points to PostgreSQL
    - Original SQLite vispec.db is present (never modified)

Safety:
    - Original vispec.db is NEVER modified or deleted
    - Each table is committed independently
    - Duplicate PKs are skipped with a warning
    - FK-safe insertion order is enforced
"""
import os
import sys

# Ensure backend is on path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

from core.config import settings
from models import (
    User, PasswordResetToken, SystemLog,
    Project, RequirementDocument, Requirement,
    ValidationSession, Defect, AIPromptLog,
    Diagram, DiagramElement, ProjectMetrics,
    TraceabilityMatrix, TraceabilityNote,
    ReviewAudit, ExportReport,
)
from config.database import Base

SQLITE_PATH = os.path.join(os.path.dirname(__file__), "..", "vispec.db")
SQLITE_PATH = os.path.abspath(SQLITE_PATH)

PG_URL = settings.DATABASE_URL

if not PG_URL.startswith("postgresql"):
    print(f"ERROR: DATABASE_URL does not point to PostgreSQL: {PG_URL}")
    print("Set DATABASE_URL in .env to your PostgreSQL connection string.")
    sys.exit(1)

if not os.path.exists(SQLITE_PATH):
    print(f"ERROR: SQLite database not found at {SQLITE_PATH}")
    sys.exit(1)

print(f"Source:      {SQLITE_PATH}")
print(f"Destination: {PG_URL}")
print("-" * 50)

# Connect to SQLite (read-only source)
sqlite_engine = create_engine(f"sqlite:///{SQLITE_PATH}")
SQLiteSession = sessionmaker(bind=sqlite_engine)
src = SQLiteSession()

# Connect to PostgreSQL (write destination)
pg_engine = create_engine(PG_URL)
PGSession = sessionmaker(bind=pg_engine)
dst = PGSession()

# Ensure PostgreSQL schema exists
Base.metadata.create_all(bind=pg_engine)
print("PostgreSQL schema created/verified.")


def migrate_table(session_src, session_dst, model_cls, filter_deleted=True):
    """Migrate all rows from SQLite table to PostgreSQL table."""
    table_name = model_cls.__tablename__
    rows = session_src.query(model_cls).all()
    total = len(rows)
    inserted = 0
    skipped = 0

    for row in rows:
        # Convert to dict (bypass SQLAlchemy identity map)
        row_dict = {col.name: getattr(row, col.name) for col in model_cls.__table__.columns}

        # Check if already exists in PG
        pk_col = list(model_cls.__table__.primary_key.columns)[0]
        pk_val = row_dict.get(pk_col.name)
        existing = session_dst.query(model_cls).filter(pk_col == pk_val).first()
        if existing:
            skipped += 1
            continue

        new_obj = model_cls(**row_dict)
        session_dst.add(new_obj)
        inserted += 1

    session_dst.commit()
    print(f"  {table_name:30s}  total={total:4d}  inserted={inserted:4d}  skipped={skipped:4d}")


# =============================================================================
# MIGRATION ORDER: parent tables first to respect foreign keys
# =============================================================================
MIGRATION_ORDER = [
    User,
    PasswordResetToken,
    SystemLog,
    Project,
    RequirementDocument,
    Requirement,
    ValidationSession,
    Defect,
    AIPromptLog,
    Diagram,
    DiagramElement,
    ProjectMetrics,
    TraceabilityMatrix,
    TraceabilityNote,
    ReviewAudit,
    ExportReport,
]

print("\nMigrating tables (FK-safe order)...")
for model in MIGRATION_ORDER:
    migrate_table(src, dst, model)

print("\nAll tables migrated successfully.")

# =============================================================================
# SEQUENCE RESET (for any future serial/auto-increment columns)
# =============================================================================
print("\nResetting sequences...")
try:
    inspector = inspect(pg_engine)
    tables = inspector.get_table_names()
    for table in tables:
        columns = inspector.get_columns(table)
        for col in columns:
            # Check if column has a default sequence
            result = dst.execute(text(f"""
                SELECT pg_get_serial_sequence('{table}', '{col['name']}') AS seq
            """)).fetchone()
            seq = result[0] if result else None
            if seq:
                dst.execute(text(f"""
                    SELECT setval('{seq}', COALESCE((SELECT MAX("{col['name']}") FROM "{table}"), 1), true)
                """))
                print(f"  Reset sequence {seq} for {table}.{col['name']}")
    dst.commit()
    print("Sequence reset complete.")
except Exception as e:
    print(f"  Sequence reset skipped (not critical): {e}")
    dst.rollback()

src.close()
dst.close()

print("\n" + "=" * 50)
print("MIGRATION COMPLETE")
print("=" * 50)
print("You can now start the app with PostgreSQL.")
print("To rollback to SQLite, set DATABASE_URL=sqlite:///./vispec.db in .env")

