-- Fix data inconsistency: validation sessions with defects but no requirements
-- This resets validation sessions for documents that have 0 requirements but > 0 defects

UPDATE validation_sessions
SET defect_count = 0, overall_score = 100
WHERE doc_id IN (
    SELECT d.doc_id FROM requirement_documents d
    LEFT JOIN requirements r ON r.doc_id = d.doc_id
    GROUP BY d.doc_id
    HAVING COUNT(r.req_id) = 0
)
AND defect_count > 0;
