#!/usr/bin/env python3
import sys
sys.path.append('.')
from config.database import SessionLocal
from sqlalchemy import text

def run_migration():
    db = SessionLocal()
    try:
        print('Running content column migration...')
        
        # Check current column type
        result = db.execute(text('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = \'requirement_documents\' AND column_name = \'content\''))
        current = result.fetchone()
        print(f'Current content column type: {current[1] if current else "Not found"}')
        
        if current and current[1] == 'text':
            # Add new binary column
            db.execute(text('ALTER TABLE requirement_documents ADD COLUMN content_binary BYTEA'))
            print('✅ Added content_binary column')
            
            # Convert hex data to binary
            result = db.execute(text('UPDATE requirement_documents SET content_binary = decode(content, \'hex\') WHERE content IS NOT NULL AND content ~ \'^[0-9a-fA-F]+$\''))
            print(f'✅ Converted {result.rowcount} records to binary')
            
            # Drop old column
            db.execute(text('ALTER TABLE requirement_documents DROP COLUMN content'))
            print('✅ Dropped old content column')
            
            # Rename new column
            db.execute(text('ALTER TABLE requirement_documents RENAME COLUMN content_binary TO content'))
            print('✅ Renamed content_binary to content')
            
            db.commit()
            
            # Verify
            result = db.execute(text('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = \'requirement_documents\' AND column_name = \'content\''))
            final = result.fetchone()
            print(f'🎉 Migration complete! New type: {final[1] if final else "Not found"}')
            
        else:
            print('⚠️ Already migrated or column not found')
            
    except Exception as e:
        print(f'❌ Error: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    run_migration()
