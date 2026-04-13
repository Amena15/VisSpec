"""
Migration script: Upgrade from 3-table schema to full 16-table + views schema.
Backs up existing data, drops old tables, creates new schema.
"""
import sqlite3
import shutil
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "vispec.db")
DB_PATH = os.path.abspath(DB_PATH)
BACKUP_PATH = f"{DB_PATH}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ============================================================
-- TABLE 1: users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    user_id               TEXT PRIMARY KEY NOT NULL,
    email                 TEXT NOT NULL UNIQUE,
    username              TEXT NOT NULL,
    password_hash         TEXT NOT NULL,
    role                  TEXT NOT NULL CHECK (role IN ('student','developer','supervisor')),
    is_pre_provisioned    INTEGER NOT NULL DEFAULT 0,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until          TEXT,
    last_login_at         TEXT,
    is_active             INTEGER NOT NULL DEFAULT 1,
    storage_quota_mb      REAL NOT NULL DEFAULT 100,
    created_at            TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at            TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ============================================================
-- TABLE 2: password_reset_tokens
-- ============================================================
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    token_id              TEXT PRIMARY KEY NOT NULL,
    user_id               TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash            TEXT NOT NULL UNIQUE,
    expires_at            TEXT NOT NULL,
    is_used               INTEGER NOT NULL DEFAULT 0,
    previous_hash_check   TEXT,
    created_at            TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- ============================================================
-- TABLE 3: system_logs
-- ============================================================
CREATE TABLE IF NOT EXISTS system_logs (
    log_id     TEXT PRIMARY KEY NOT NULL,
    user_id    TEXT REFERENCES users(user_id) ON DELETE SET NULL,
    level      TEXT NOT NULL CHECK (level IN ('info','warning','error','critical')),
    event      TEXT NOT NULL,
    details    TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON system_logs(created_at);

-- ============================================================
-- TABLE 4: projects
-- ============================================================
CREATE TABLE IF NOT EXISTS projects (
    project_id     TEXT PRIMARY KEY NOT NULL,
    owner_id       TEXT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    name           TEXT NOT NULL,
    description    TEXT,
    status         TEXT NOT NULL DEFAULT 'pending'
                       CHECK (status IN ('pending','uploading','parsing','validating',
                                         'validated','reviewed','archived')),
    review_status  TEXT NOT NULL DEFAULT 'not_reviewed'
                       CHECK (review_status IN ('not_reviewed','approved','changes_requested')),
    is_deleted     INTEGER NOT NULL DEFAULT 0,
    deleted_at     TEXT,
    created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

-- ============================================================
-- TABLE 5: requirement_documents
-- ============================================================
CREATE TABLE IF NOT EXISTS requirement_documents (
    doc_id              TEXT PRIMARY KEY NOT NULL,
    project_id          TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    uploaded_by         TEXT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    filename            TEXT NOT NULL,
    file_extension      TEXT NOT NULL CHECK (file_extension IN ('pdf','docx','txt')),
    file_size_bytes     INTEGER NOT NULL CHECK (file_size_bytes <= 10485760),
    word_count          INTEGER,
    page_count          INTEGER,
    status              TEXT NOT NULL DEFAULT 'uploading'
                            CHECK (status IN ('uploading','parsing','ready','failed','deleted')),
    parse_error         TEXT,
    is_scanned_pdf      INTEGER NOT NULL DEFAULT 0,
    extracted_author    TEXT,
    extracted_version   TEXT,
    malware_scan_passed INTEGER NOT NULL DEFAULT 0,
    upload_date         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_docs_project ON requirement_documents(project_id);
CREATE INDEX IF NOT EXISTS idx_docs_status ON requirement_documents(status);

-- ============================================================
-- TABLE 6: requirements
-- ============================================================
CREATE TABLE IF NOT EXISTS requirements (
    req_id              TEXT PRIMARY KEY NOT NULL,
    doc_id              TEXT NOT NULL REFERENCES requirement_documents(doc_id) ON DELETE CASCADE,
    project_id          TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    req_identifier      TEXT,
    section_header      TEXT,
    original_text       TEXT NOT NULL,
    current_text        TEXT NOT NULL,
    word_count          INTEGER NOT NULL DEFAULT 0,
    actors_json         TEXT,
    modal_verbs_json    TEXT,
    vague_terms_json    TEXT,
    validation_status   TEXT NOT NULL DEFAULT 'pending'
                            CHECK (validation_status IN ('pending','valid','defective','skipped')),
    sequence_order      INTEGER NOT NULL DEFAULT 0,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_reqs_doc ON requirements(doc_id);
CREATE INDEX IF NOT EXISTS idx_reqs_project ON requirements(project_id);
CREATE INDEX IF NOT EXISTS idx_reqs_status ON requirements(validation_status);

-- ============================================================
-- TABLE 7: validation_sessions
-- ============================================================
CREATE TABLE IF NOT EXISTS validation_sessions (
    validation_id             TEXT PRIMARY KEY NOT NULL,
    project_id                TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    doc_id                    TEXT NOT NULL REFERENCES requirement_documents(doc_id) ON DELETE CASCADE,
    triggered_by              TEXT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    status                    TEXT NOT NULL DEFAULT 'running'
                                  CHECK (status IN ('running','completed','failed','retrying')),
    overall_score             REAL CHECK (overall_score >= 0.0 AND overall_score <= 100.0),
    total_requirements        INTEGER NOT NULL DEFAULT 0,
    defect_count              INTEGER NOT NULL DEFAULT 0,
    ambiguity_count           INTEGER NOT NULL DEFAULT 0,
    incompleteness_count      INTEGER NOT NULL DEFAULT 0,
    inconsistency_count       INTEGER NOT NULL DEFAULT 0,
    unverifiable_count        INTEGER NOT NULL DEFAULT 0,
    llm_model_used            TEXT NOT NULL DEFAULT 'llama3-70b-8192',
    api_retries               INTEGER NOT NULL DEFAULT 0,
    processing_time_ms        INTEGER,
    zero_retention_confirmed  INTEGER NOT NULL DEFAULT 1,
    validation_date           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    error_message             TEXT
);
CREATE INDEX IF NOT EXISTS idx_val_project ON validation_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_val_date ON validation_sessions(validation_date);

-- ============================================================
-- TABLE 8: defects
-- ============================================================
CREATE TABLE IF NOT EXISTS defects (
    defect_id          TEXT PRIMARY KEY NOT NULL,
    validation_id      TEXT NOT NULL REFERENCES validation_sessions(validation_id) ON DELETE CASCADE,
    req_id             TEXT NOT NULL REFERENCES requirements(req_id) ON DELETE CASCADE,
    defect_type        TEXT NOT NULL
                           CHECK (defect_type IN ('ambiguity','incompleteness','inconsistency','unverifiable')),
    severity           TEXT NOT NULL CHECK (severity IN ('high','medium','low')),
    confidence_score   REAL NOT NULL CHECK (confidence_score > 0.70 AND confidence_score <= 1.0),
    description        TEXT NOT NULL,
    ai_suggestion      TEXT,
    suggestion_applied INTEGER NOT NULL DEFAULT 0,
    applied_at         TEXT,
    is_false_positive  INTEGER NOT NULL DEFAULT 0,
    user_note          TEXT,
    detected_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_defects_val ON defects(validation_id);
CREATE INDEX IF NOT EXISTS idx_defects_req ON defects(req_id);
CREATE INDEX IF NOT EXISTS idx_defects_type ON defects(defect_type);
CREATE INDEX IF NOT EXISTS idx_defects_severity ON defects(severity);

-- ============================================================
-- TABLE 9: ai_prompt_logs
-- ============================================================
CREATE TABLE IF NOT EXISTS ai_prompt_logs (
    prompt_log_id     TEXT PRIMARY KEY NOT NULL,
    validation_id     TEXT NOT NULL REFERENCES validation_sessions(validation_id) ON DELETE CASCADE,
    req_batch_index   INTEGER NOT NULL,
    model             TEXT NOT NULL,
    temperature       REAL NOT NULL DEFAULT 0.1,
    response_time_ms  INTEGER,
    was_retry         INTEGER NOT NULL DEFAULT 0,
    parse_succeeded   INTEGER NOT NULL,
    created_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- ============================================================
-- TABLE 10: diagrams
-- ============================================================
CREATE TABLE IF NOT EXISTS diagrams (
    diagram_id                    TEXT PRIMARY KEY NOT NULL,
    project_id                    TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    validation_id                 TEXT NOT NULL REFERENCES validation_sessions(validation_id) ON DELETE CASCADE,
    diagram_type                  TEXT NOT NULL CHECK (diagram_type IN ('usecase','sequence','activity')),
    scenario_name                 TEXT,
    mermaid_syntax                TEXT NOT NULL,
    syntax_valid                  INTEGER NOT NULL DEFAULT 0,
    total_elements                INTEGER NOT NULL DEFAULT 0,
    hallucination_rejected_count  INTEGER NOT NULL DEFAULT 0,
    generation_time_ms            INTEGER,
    created_at                    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_diagrams_project ON diagrams(project_id);
CREATE INDEX IF NOT EXISTS idx_diagrams_type ON diagrams(diagram_type);

-- ============================================================
-- TABLE 11: diagram_elements
-- ============================================================
CREATE TABLE IF NOT EXISTS diagram_elements (
    element_id         TEXT PRIMARY KEY NOT NULL,
    diagram_id         TEXT NOT NULL REFERENCES diagrams(diagram_id) ON DELETE CASCADE,
    source_req_id      TEXT NOT NULL REFERENCES requirements(req_id) ON DELETE CASCADE,
    element_type       TEXT NOT NULL CHECK (element_type IN ('actor','usecase','interaction','node')),
    element_name       TEXT NOT NULL,
    was_hallucination  INTEGER NOT NULL DEFAULT 0,
    created_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_elements_diagram ON diagram_elements(diagram_id);
CREATE INDEX IF NOT EXISTS idx_elements_req ON diagram_elements(source_req_id);

-- ============================================================
-- TABLE 12: project_metrics
-- ============================================================
CREATE TABLE IF NOT EXISTS project_metrics (
    metrics_id           TEXT PRIMARY KEY NOT NULL,
    project_id           TEXT NOT NULL UNIQUE REFERENCES projects(project_id) ON DELETE CASCADE,
    validation_id        TEXT NOT NULL REFERENCES validation_sessions(validation_id) ON DELETE CASCADE,
    complexity_score     REAL CHECK (complexity_score >= 0.0 AND complexity_score <= 100.0),
    actor_count          INTEGER NOT NULL DEFAULT 0,
    total_requirements   INTEGER NOT NULL DEFAULT 0,
    avg_requirement_words REAL,
    workflow_depth       INTEGER NOT NULL DEFAULT 0,
    estimated_weeks      REAL,
    relative_cost_index  TEXT CHECK (relative_cost_index IN ('low','medium','high')),
    quality_score        REAL CHECK (quality_score >= 0.0 AND quality_score <= 100.0),
    validation_rate      REAL CHECK (validation_rate >= 0.0 AND validation_rate <= 100.0),
    modal_density        REAL,
    vague_density        REAL,
    calculated_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- ============================================================
-- TABLE 13: traceability_matrix
-- ============================================================
CREATE TABLE IF NOT EXISTS traceability_matrix (
    matrix_id                     TEXT PRIMARY KEY NOT NULL,
    project_id                    TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    req_id                        TEXT NOT NULL REFERENCES requirements(req_id) ON DELETE CASCADE,
    validation_id                 TEXT REFERENCES validation_sessions(validation_id) ON DELETE SET NULL,
    diagram_id                    TEXT REFERENCES diagrams(diagram_id) ON DELETE SET NULL,
    validation_status             TEXT NOT NULL DEFAULT 'pending'
                                      CHECK (validation_status IN ('valid','defective','pending','skipped')),
    defect_types_json             TEXT,
    linked_diagram_elements_json  TEXT,
    updated_at                    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE (project_id, req_id)
);
CREATE INDEX IF NOT EXISTS idx_matrix_project ON traceability_matrix(project_id);
CREATE INDEX IF NOT EXISTS idx_matrix_req ON traceability_matrix(req_id);

-- ============================================================
-- TABLE 14: traceability_notes
-- ============================================================
CREATE TABLE IF NOT EXISTS traceability_notes (
    note_id     TEXT PRIMARY KEY NOT NULL,
    req_id      TEXT NOT NULL REFERENCES requirements(req_id) ON DELETE CASCADE,
    created_by  TEXT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    project_id  TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    note_type   TEXT NOT NULL DEFAULT 'user_annotation'
                    CHECK (note_type IN ('user_annotation','supervisor_feedback','system_note')),
    is_resolved INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_notes_req ON traceability_notes(req_id);
CREATE INDEX IF NOT EXISTS idx_notes_project ON traceability_notes(project_id);

-- ============================================================
-- TABLE 15: review_audits
-- ============================================================
CREATE TABLE IF NOT EXISTS review_audits (
    review_id                TEXT PRIMARY KEY NOT NULL,
    project_id               TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    supervisor_id            TEXT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    validation_id            TEXT REFERENCES validation_sessions(validation_id) ON DELETE SET NULL,
    decision                 TEXT NOT NULL DEFAULT 'pending'
                                 CHECK (decision IN ('approved','changes_requested','pending')),
    comments                 TEXT,
    quality_score_at_review  REAL,
    defect_count_at_review   INTEGER,
    review_in_progress       INTEGER NOT NULL DEFAULT 0,
    review_started_at        TEXT,
    review_completed_at      TEXT,
    created_at               TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_reviews_project ON review_audits(project_id);
CREATE INDEX IF NOT EXISTS idx_reviews_supervisor ON review_audits(supervisor_id);

-- ============================================================
-- TABLE 16: export_reports
-- ============================================================
CREATE TABLE IF NOT EXISTS export_reports (
    report_id               TEXT PRIMARY KEY NOT NULL,
    project_id              TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    validation_id           TEXT NOT NULL REFERENCES validation_sessions(validation_id) ON DELETE CASCADE,
    generated_by            TEXT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    report_type             TEXT NOT NULL DEFAULT 'full'
                                CHECK (report_type IN ('full','summary','supervisor')),
    includes_diagrams       INTEGER NOT NULL DEFAULT 1,
    includes_metrics        INTEGER NOT NULL DEFAULT 1,
    includes_traceability   INTEGER NOT NULL DEFAULT 1,
    watermark_text          TEXT NOT NULL DEFAULT 'VisSpec',
    file_size_bytes         INTEGER,
    generation_time_ms      INTEGER,
    generated_at            TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_reports_project ON export_reports(project_id);

-- ============================================================
-- VIEWS
-- ============================================================
DROP VIEW IF EXISTS vw_project_dashboard;
CREATE VIEW vw_project_dashboard AS
SELECT
    p.project_id,
    p.name,
    p.status,
    p.review_status,
    u.email AS owner_email,
    pm.quality_score,
    pm.complexity_score,
    pm.estimated_weeks,
    pm.relative_cost_index,
    vs.defect_count,
    vs.ambiguity_count,
    vs.incompleteness_count,
    vs.inconsistency_count,
    vs.validation_date,
    (SELECT COUNT(*) FROM requirements r WHERE r.project_id = p.project_id) AS total_requirements,
    (SELECT COUNT(*) FROM diagrams d WHERE d.project_id = p.project_id) AS diagram_count
FROM projects p
JOIN users u ON u.user_id = p.owner_id
LEFT JOIN project_metrics pm ON pm.project_id = p.project_id
LEFT JOIN validation_sessions vs ON vs.validation_id = pm.validation_id
WHERE p.is_deleted = 0;

DROP VIEW IF EXISTS vw_supervisor_dashboard;
CREATE VIEW vw_supervisor_dashboard AS
SELECT
    p.project_id,
    p.name AS project_name,
    u.email AS student_email,
    p.status,
    p.review_status,
    ra.decision AS latest_review_decision,
    ra.review_completed_at,
    pm.quality_score,
    vs.defect_count
FROM projects p
JOIN users u ON u.user_id = p.owner_id
LEFT JOIN review_audits ra ON ra.project_id = p.project_id
LEFT JOIN project_metrics pm ON pm.project_id = p.project_id
LEFT JOIN validation_sessions vs ON vs.validation_id = pm.validation_id
WHERE p.is_deleted = 0
ORDER BY p.created_at DESC;
"""


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Creating new database with full schema.")
        conn = sqlite3.connect(DB_PATH)
        conn.executescript(SCHEMA_SQL)
        conn.close()
        print("New database created successfully.")
        return

    # Backup existing database
    print(f"Backing up existing database to {BACKUP_PATH}...")
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"Backup saved to {BACKUP_PATH}")

    # Read existing data
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get existing tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    print(f"Existing tables: {existing_tables}")

    # Backup existing users if table exists
    old_users = []
    if 'users' in existing_tables:
        cursor.execute("SELECT * FROM users")
        old_users = [dict(row) for row in cursor.fetchall()]
        print(f"  Found {len(old_users)} existing users to migrate")

    # Backup existing documents if table exists
    old_documents = []
    if 'documents' in existing_tables:
        cursor.execute("SELECT * FROM documents")
        old_documents = [dict(row) for row in cursor.fetchall()]
        print(f"  Found {len(old_documents)} existing documents to migrate")

    # Backup existing analysis_results if table exists
    old_analysis = []
    if 'analysis_results' in existing_tables:
        cursor.execute("SELECT * FROM analysis_results")
        old_analysis = [dict(row) for row in cursor.fetchall()]
        print(f"  Found {len(old_analysis)} existing analysis results to migrate")

    conn.close()

    # Drop old database and create new one
    os.remove(DB_PATH)
    print("Dropped old database.")

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL)
    cursor = conn.cursor()
    print("Created new schema with 16 tables + 2 views.")

    # Migrate old users to new schema
    role_map = {
        'analyst': 'student',
        'supervisor': 'supervisor',
    }
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    migrated_users = 0
    for old_user in old_users:
        user_id = f"migrated_{old_user.get('id', old_user.get('user_id', ''))}"
        old_role = old_user.get('role', 'analyst')
        new_role = role_map.get(old_role, 'student')
        password_hash = old_user.get('hashed_password', old_user.get('password_hash', ''))

        created_at = old_user.get('created_at') or now_str
        updated_at = old_user.get('updated_at') or now_str

        try:
            cursor.execute("""
                INSERT INTO users (user_id, email, username, password_hash, role, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                old_user.get('email', ''),
                old_user.get('username', ''),
                password_hash,
                new_role,
                1 if old_user.get('is_active', True) else 0,
                created_at,
                updated_at,
            ))
            migrated_users += 1
        except sqlite3.IntegrityError as e:
            print(f"  Skipping user {old_user.get('username')}: {e}")

    print(f"  Migrated {migrated_users} users.")

    conn.commit()
    conn.close()
    print("Migration complete!")


if __name__ == "__main__":
    migrate()
