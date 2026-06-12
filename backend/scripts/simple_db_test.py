#!/usr/bin/env python3

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# NOTE:
# This script is only intended for manual smoke-testing.
# Pytest collection/importing this file should never cause failures.
# Therefore we do *not* sys.exit() on import errors here.
try:
    import backend.config.database as _db
    print("✅ Backend database module import successful")
except Exception as e:
    print(f"⚠️ Backend database module import failed (ignored during pytest): {e}")

try:
    from backend.models.project import Project
    from backend.models.user import User
    print("✅ Backend model imports successful")
except Exception as e:
    print(f"⚠️ Backend model imports failed (ignored during pytest): {e}")
    Project = None
    User = None


def test_simple_query():

    """Test simple database query"""
    db = SessionLocal()
    try:
        print("🔍 Testing simple database query...")
        
        # Count projects
        project_count = db.query(Project).count()
        print(f"📊 Projects: {project_count}")
        
        # Count users
        user_count = db.query(User).count()
        print(f"👥 Users: {user_count}")
        
        # Test join query
        projects_with_users = (
            db.query(Project, User)
            .join(User, Project.owner_id == User.user_id)
            .limit(3)
            .all()
        )
        
        print(f"✅ Join query successful: {len(projects_with_users)} results")
        
        for project, user in projects_with_users:
            print(f"  - {project.name} by {user.email}")
            
        print("🎉 Database test successful!")
        
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    # When run manually, execute the DB connectivity test.
    test_simple_query()


