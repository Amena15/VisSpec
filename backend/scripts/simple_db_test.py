#!/usr/bin/env python3

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import SessionLocal
    print("✅ Database import successful")
except ImportError as e:
    print(f"❌ Database import failed: {e}")
    print("Available files in current directory:")
    for file in os.listdir('.'):
        if file.endswith('.py'):
            print(f"  {file}")
    sys.exit(1)

try:
    from models.project import Project
    from models.user import User
    print("✅ Model imports successful")
except ImportError as e:
    print(f"❌ Model imports failed: {e}")
    sys.exit(1)

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
    test_simple_query()
