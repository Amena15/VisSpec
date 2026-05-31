-- Add version history tracking for requirements (BR-15 compliance)
-- This migration adds support for undo/redo functionality

-- Add version history table
CREATE TABLE IF NOT EXISTS requirement_version_history (
    version_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    req_id VARCHAR(36) NOT NULL,
    doc_id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    old_text TEXT NOT NULL,
    new_text TEXT NOT NULL,
    change_reason VARCHAR(255),
    changed_by VARCHAR(36),
    change_type VARCHAR(50) DEFAULT 'suggestion_applied',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (req_id) REFERENCES requirements(req_id) ON DELETE CASCADE,
    FOREIGN KEY (doc_id) REFERENCES requirement_documents(doc_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_version_history_req_id ON requirement_version_history(req_id);
CREATE INDEX IF NOT EXISTS idx_version_history_doc_id ON requirement_version_history(doc_id);
CREATE INDEX IF NOT EXISTS idx_version_history_created_at ON requirement_version_history(created_at);

-- Add previous_text column to requirements table for quick undo
ALTER TABLE requirements ADD COLUMN IF NOT EXISTS previous_text TEXT;

-- Add change tracking columns
ALTER TABLE requirements ADD COLUMN IF NOT EXISTS last_modified_by VARCHAR(36);
ALTER TABLE requirements ADD COLUMN IF NOT EXISTS last_modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Add foreign key for last_modified_by
ALTER TABLE requirements ADD CONSTRAINT fk_requirements_last_modified_by 
    FOREIGN KEY (last_modified_by) REFERENCES users(user_id) ON DELETE SET NULL;

-- Create index for last_modified_at
CREATE INDEX IF NOT EXISTS idx_requirements_last_modified_at ON requirements(last_modified_at);

COMMENT ON TABLE requirement_version_history IS 'Tracks all text changes to requirements for undo/redo functionality (BR-15)';
COMMENT ON COLUMN requirement_version_history.change_type IS 'Type of change: suggestion_applied, manual_edit, undo, redo';
COMMENT ON COLUMN requirements.previous_text IS 'Previous text for single-level undo (BR-15)';
