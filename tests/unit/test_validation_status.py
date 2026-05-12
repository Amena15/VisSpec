#!/usr/bin/env python3
import sys
sys.path.append('backend')

from config.database import SessionLocal
from models.document import RequirementDocument

# Test document status update
db = SessionLocal()
try:
    doc = db.query(RequirementDocument).filter(RequirementDocument.doc_id == '13730565-f82a-422b-976f-fd2189021438').first()
    if doc:
        print(f'Before update: {doc.status}')
        # Test status update
        doc.status = "Validated - Test"
        db.commit()
        
        # Verify update
        updated_doc = db.query(RequirementDocument).filter(RequirementDocument.doc_id == '13730565-f82a-422b-976f-fd2189021438').first()
        print(f'After update: {updated_doc.status}')
        
        # Reset to original status
        doc.status = "Ready for Analysis"
        db.commit()
        print(f'Reset to: {doc.status}')
    else:
        print('Document not found')
finally:
    db.close()
