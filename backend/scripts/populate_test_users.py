"""
Script to populate the database with test users for VisSpec
"""
import os
import sys
from datetime import datetime

# Add the backend directory to the path so we can import modules
sys.path.append('/Users/amena/Documents/FYPCode/VisSpec/backend')

from sqlalchemy.orm import Session
from config.database import engine, Base
from models.user import User, UserRole
from utils.security import get_password_hash

def create_test_users():
    """Create test users in the database"""
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    from config.database import SessionLocal
    db = SessionLocal()
    
    try:
        # Create analyst user
        analyst_user = db.query(User).filter(User.email == "analyst@vispec.com").first()
        if not analyst_user:
            analyst_user = User(
                username="analyst",
                email="analyst@vispec.com",
                role=UserRole.ANALYST,
                is_active=True
            )
            analyst_user.set_password("VisSpec123")
            db.add(analyst_user)
            print("Created analyst user")
        
        # Create supervisor user
        supervisor_user = db.query(User).filter(User.email == "supervisor@vispec.com").first()
        if not supervisor_user:
            supervisor_user = User(
                username="supervisor",
                email="supervisor@vispec.com",
                role=UserRole.SUPERVISOR,
                is_active=True
            )
            supervisor_user.set_password("VisSpec123")
            db.add(supervisor_user)
            print("Created supervisor user")
        
        # Commit changes
        db.commit()
        print("Test users created successfully!")
        
    except Exception as e:
        print(f"Error creating test users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()