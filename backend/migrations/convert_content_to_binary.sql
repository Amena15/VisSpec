-- Migration: Convert content column from TEXT to LargeBinary
-- Purpose: Fix REQ_05 compliance - content should store binary file, extracted_text should store text

-- Step 1: Add new binary column
ALTER TABLE requirement_documents 
ADD COLUMN content_binary BYTEA;

-- Step 2: For existing records with NULL content_binary, copy from content if it contains binary data
-- Note: This is a best-effort migration - records with text in content will have NULL content_binary
UPDATE requirement_documents 
SET content_binary = decode(content, 'hex') 
WHERE content_binary IS NULL 
AND content IS NOT NULL 
AND content ~ '^[0-9a-fA-F]+$';

-- Step 3: Drop old content column
ALTER TABLE requirement_documents DROP COLUMN content;

-- Step 4: Rename content_binary to content
ALTER TABLE requirement_documents RENAME COLUMN content_binary TO content;

-- Step 5: Ensure extracted_text is populated for all records
UPDATE requirement_documents 
SET extracted_text = content 
WHERE extracted_text IS NULL 
AND content IS NOT NULL 
AND content NOT LIKE '^[0-9a-fA-F]+$';

-- Step 6: Add comment to document the purpose
COMMENT ON COLUMN requirement_documents.content IS 'Original uploaded file (binary data)';
COMMENT ON COLUMN requirement_documents.extracted_text IS 'Extracted and sanitized text for analysis';
