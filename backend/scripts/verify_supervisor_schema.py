#!/usr/bin/env python3

from sqlalchemy import inspect
from config.database import engine

def verify_database_schema():
    """Verify all required database schema for supervisor implementation"""
    inspector = inspect(engine)

    print('=== DATABASE SCHEMA VERIFICATION ===')
    print()

    # Check projects table
    print('1. Projects Table Schema:')
    projects_columns = inspector.get_columns('projects')
    review_status_exists = any(col['name'] == 'review_status' for col in projects_columns)
    print(f'   ✅ review_status column exists: {review_status_exists}')
    if review_status_exists:
        review_status_col = next(col for col in projects_columns if col['name'] == 'review_status')
        print(f'   ✅ Type: {review_status_col["type"]}, Default: {review_status_col.get("default", "N/A")}')
    print()

    # Check review_audits table
    print('2. ReviewAudits Table Schema:')
    try:
        review_columns = inspector.get_columns('review_audits')
        required_columns = ['review_id', 'project_id', 'supervisor_id', 'decision', 'comments', 'quality_score_at_review', 'defect_count_at_review']
        for col in required_columns:
            exists = any(c['name'] == col for c in review_columns)
            print(f'   ✅ {col}: {exists}')
        print()
    except Exception as e:
        print(f'   ❌ Error: {e}')
        print()

    # Check notifications table
    print('3. Notifications Table Schema:')
    try:
        notif_columns = inspector.get_columns('notifications')
        required_columns = ['id', 'user_id', 'project_id', 'type', 'content', 'is_read', 'created_at']
        for col in required_columns:
            exists = any(c['name'] == col for c in notif_columns)
            print(f'   ✅ {col}: {exists}')
        print()
    except Exception as e:
        print(f'   ❌ Error: {e}')
        print()

    # Check foreign keys
    print('4. Foreign Key Constraints:')
    try:
        foreign_keys = inspector.get_foreign_keys('review_audits')
        print(f'   ✅ ReviewAudits FKs: {len(foreign_keys)}')
        for fk in foreign_keys:
            print(f'      {fk["constrained_columns"]} -> {fk["referred_table"]}.{fk["referred_columns"]}')
        
        foreign_keys = inspector.get_foreign_keys('notifications')
        print(f'   ✅ Notifications FKs: {len(foreign_keys)}')
        for fk in foreign_keys:
            print(f'      {fk["constrained_columns"]} -> {fk["referred_table"]}.{fk["referred_columns"]}')
    except Exception as e:
        print(f'   ❌ Error: {e}')

if __name__ == "__main__":
    verify_database_schema()
