"""Run SQL migration to fix validation session inconsistencies."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from config.database import engine

def run_migration():
    """Execute the SQL migration to fix validation inconsistencies."""
    try:
        with engine.connect() as conn:
            # Read the SQL file
            with open('migrations/fix_validation_inconsistency.sql', 'r') as f:
                sql = f.read()
            
            # Execute the SQL
            result = conn.execute(text(sql))
            conn.commit()
            
            print(f"✅ Migration executed successfully")
            print(f"   Updated {result.rowcount} validation sessions")
            return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
