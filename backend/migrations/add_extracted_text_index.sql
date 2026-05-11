-- Migration: Add extracted_text column and GIN index for full-text search
-- This migration adds the extracted_text column and creates a GIN index for PostgreSQL full-text search

-- Add extracted_text column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='requirement_documents' 
        AND column_name='extracted_text'
    ) THEN
        ALTER TABLE requirement_documents ADD COLUMN extracted_text TEXT;
    END IF;
END $$;

-- Create GIN index for full-text search
CREATE INDEX IF NOT EXISTS idx_doc_extracted_text 
ON requirement_documents 
USING GIN(to_tsvector('english', extracted_text));

-- Update existing documents to populate extracted_text (optional)
UPDATE requirement_documents 
SET extracted_text = content 
WHERE extracted_text IS NULL AND content IS NOT NULL;

-- Comment on the new column
COMMENT ON COLUMN requirement_documents.extracted_text IS 'Sanitized text for full-text search indexing';
