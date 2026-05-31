#!/usr/bin/env python3
"""
Database migration runner for VisSpec.
Applies all pending migrations to bring database schema up to date.
"""

import sys
import os
sys.path.append('.')

from config.database import SessionLocal, engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_version_history_migration():
    """Run the version history migration (004_add_version_history.sql)."""
    db = SessionLocal()
    try:
        logger.info("Running version history migration...")
        
        # Read migration SQL
        migration_file = "migrations/004_add_version_history.sql"
        if not os.path.exists(migration_file):
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        db.execute(text(migration_sql))
        db.commit()
        
        logger.info("✅ Version history migration completed successfully")
        
        # Verify tables exist
        result = db.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('requirement_version_history')
        """))
        tables = [row[0] for row in result.fetchall()]
        
        logger.info(f"✅ Tables created: {tables}")
        
        # Check columns in requirements table
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'requirements' 
            AND column_name IN ('previous_text', 'last_modified_by', 'last_modified_at')
        """))
        columns = [row[0] for row in result.fetchall()]
        
        logger.info(f"✅ Columns added to requirements: {columns}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def check_migration_status():
    """Check current migration status."""
    db = SessionLocal()
    try:
        logger.info("Checking migration status...")
        
        # Check if version history table exists
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'requirement_version_history'
            )
        """))
        version_history_exists = result.fetchone()[0]
        
        # Check if requirements table has new columns
        result = db.execute(text("""
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_name = 'requirements' 
            AND column_name IN ('previous_text', 'last_modified_by', 'last_modified_at')
        """))
        new_columns_count = result.fetchone()[0]
        
        logger.info(f"Version history table exists: {version_history_exists}")
        logger.info(f"New columns in requirements: {new_columns_count}/3")
        
        if version_history_exists and new_columns_count == 3:
            logger.info("✅ All migrations applied successfully")
            return True
        else:
            logger.warning("⚠️ Some migrations are pending")
            return False
            
    except Exception as e:
        logger.error(f"❌ Status check failed: {e}")
        return False
    finally:
        db.close()

def main():
    """Main migration runner."""
    logger.info("🚀 Starting VisSpec database migration...")
    
    # Check current status
    if check_migration_status():
        logger.info("✅ Database is already up to date")
        return True
    
    # Run pending migrations
    success = run_version_history_migration()
    
    if success:
        # Verify final status
        if check_migration_status():
            logger.info("🎉 All migrations completed successfully!")
            return True
        else:
            logger.error("❌ Migration verification failed")
            return False
    else:
        logger.error("❌ Migration failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
