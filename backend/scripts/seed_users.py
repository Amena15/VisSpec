"""Seed default users into the fresh database."""
import sys
import os
# Add backend directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sqlalchemy.orm import Session
from config.database import SessionLocal, engine, Base
from models.user import User, UserRole
from datetime import datetime, timezone

def _now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def seed():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        defaults = [
            {
                "username": "analyst",
                "email": "analyst@vispec.com",
                "password": "VisSpec123",
                "role": UserRole.ANALYST.value,
            },
            {
                "username": "supervisor",
                "email": "supervisor@vispec.com",
                "password": "VisSpec123",
                "role": UserRole.SUPERVISOR.value,
            },
        ]

        for d in defaults:
            existing = db.query(User).filter(User.email == d["email"]).first()
            if existing:
                print(f"  User {d['username']} already exists, skipping.")
                continue

            now_str = _now_iso()
            user = User(
                username=d["username"],
                email=d["email"],
                role=d["role"],
                is_active=1,
                created_at=now_str,
                updated_at=now_str,
            )
            user.set_password(d["password"])
            db.add(user)
            print(f"  Created user: {d['username']} ({d['email']}) [{d['role']}]")

        db.commit()
        print("Seeding complete.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding users: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
