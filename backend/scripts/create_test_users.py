import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from backend.config.database import engine, Base

from models import User, UserRole
from utils.security import get_password_hash

def create_test_users():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create analyst user
        analyst_user = db.query(User).filter(User.username == "analyst").first()
        if not analyst_user:
            analyst_user = User(
                username="analyst",
                email="analyst@vispec.com",
                role=UserRole.ANALYST.value
            )
            analyst_user.set_password("VisSpec123")  # Shorter password to avoid bcrypt issues
            db.add(analyst_user)
            print("Created analyst user")

        # Create supervisor user
        supervisor_user = db.query(User).filter(User.username == "supervisor").first()
        if not supervisor_user:
            supervisor_user = User(
                username="supervisor",
                email="supervisor@vispec.com",
                role=UserRole.SUPERVISOR.value
            )
            supervisor_user.set_password("VisSpec123")  # Shorter password to avoid bcrypt issues
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