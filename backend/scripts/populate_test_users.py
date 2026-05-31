"""Populate DB with known VisSpec test users.

Run from repo root:
  python backend/scripts/populate_test_users.py
"""

import os
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../VisSpec
BACKEND_ROOT = os.path.join(REPO_ROOT, "backend")

# Ensure imports work when executed as a script
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

# Use scripts-friendly imports (no "backend." prefix) since we added BACKEND_ROOT to sys.path.
# repo-root runnable: import config/database via package
from backend.config.database import engine, Base, SessionLocal
from models.user import User, UserRole



def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def populate():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        now_str = _now_iso()
        defaults = [
            {
                "username": "analyst",
                "email": "analyst@vispec.com",
                "role": UserRole.ANALYST.value,
                "password": "VisSpec123",
            },
            {
                "username": "yousef",
                "email": "yousef@vispec.com",
                "role": UserRole.ANALYST.value,
                "password": "Yousef@2026",
            },
            {
                "username": "supervisor",
                "email": "supervisor@vispec.com",
                "role": UserRole.SUPERVISOR.value,
                "password": "VisSpec123",
            },
        ]

        for d in defaults:
            user = db.query(User).filter(User.email == d["email"]).first()
            if not user:
                user = User(
                    username=d["username"],
                    email=d["email"],
                    role=d["role"],
                    is_active=1,
                    created_at=now_str,
                    updated_at=now_str,
                )
                db.add(user)

            # Deterministic dev creds
            user.set_password(d["password"])

        db.commit()
        print("Test users populated/updated successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error populating test users: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    populate()

