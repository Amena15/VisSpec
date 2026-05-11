#!/usr/bin/env python3
import sys
sys.path.append('.')

from services.ai.requirement_organizer import requirement_organizer

# Test the enrichment service directly
test_reqs = [{'req_id': 'test-001', 'req_identifier': 'REQ-001', 'original_text': 'The system shall allow users to register accounts with email verification.', 'current_text': 'The system shall allow users to register accounts with email verification.', 'word_count': 11, 'sequence_order': 0}]

full_text = 'The system shall allow users to register accounts with email verification. Patients must be able to login using secure credentials.'

try:
    enriched = requirement_organizer.organize_and_enrich(test_reqs, full_text, use_llm=False)
    print('Enrichment test successful')
    for req in enriched:
        print('Req:', req.get('req_identifier'))
        print('Category:', req.get('category'))
        print('Module:', req.get('module_name'))
        print('Semantic ID:', req.get('semantic_id'))
        print('Actors:', req.get('actors'))
except Exception as e:
    print('Enrichment test failed:', e)
    import traceback
    traceback.print_exc()
