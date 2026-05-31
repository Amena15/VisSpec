"""Seed/Upsert the dev login users required by the frontend login flow.

Run (from repo root):
  python backend/scripts/seed_required_login_users.py

Expected credentials (must match backend/utils/security.py dev_passwords):
- analyst@vispec.com / VisSpec123
- supervisor@vispec.com / VisSpec123
- yousef@vispec.com / Yousef@2026

Notes:
- This backend uses SQLAlchemy async engine (MissingGreenlet can occur if we try to call sync create_all).
- We therefore use the async session path for upserting.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # /VisSpec
BACKEND_ROOT = os.path.join(REPO_ROOT, "backend")  # /VisSpec/backend

# Support both import styles used across the codebase.
# Put both /VisSpec (so `backend.*` imports work) and /VisSpec/backend (so `config.*`/`models.*` work).
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from backend.core.config import settings  # noqa: F401, E402
from backend.config.database import AsyncSessionLocal, Base  # noqa: E402
from backend.config.database import engine  # noqa: E402
from backend.models.user import User, UserRole  # noqa: E402

from sqlalchemy import select  # noqa: E402


REQUIRED_USERS = [
    {
        "username": "analyst",
        "email": "analyst@vispec.com",
        "role": UserRole.ANALYST.value,
        "password": "VisSpec123",
    },
    {
        "username": "supervisor",
        "email": "supervisor@vispec.com",
        "role": UserRole.SUPERVISOR.value,
        "password": "VisSpec123",
    },
    {
        "username": "yousef",
        "email": "yousef@vispec.com",
        "role": UserRole.ANALYST.value,
        "password": "Yousef@2026",
    },
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


async def _async_main() -> None:
    # Best-effort: if tables already exist (typical in your setup), this is a no-op.
    # If not, migrations should create them; create_all can be dialect/driver dependent.
    # We intentionally do NOT call create_all here to avoid sync/async mismatches.

    async with AsyncSessionLocal() as db:
        now_str = _now_iso()

        for u in REQUIRED_USERS:
            result = await db.execute(select(User).where(User.email == u["email"]))
            existing = result.scalar_one_or_none()

            if existing is None:
                existing = User(
                    username=u["username"],
                    email=u["email"],
                    role=u["role"],
                    is_active=1,
                    created_at=now_str,
                    updated_at=now_str,
                )
                db.add(existing)

            existing.username = u["username"]
            existing.role = u["role"]
            existing.is_active = 1
            existing.updated_at = now_str

            # Force password hash to match backend/utils/security.py dev_passwords.
            existing.set_password(u["password"])

            print(f"Upserted {existing.email} ({existing.role})")

        await db.commit()
        print("Required login users seeded successfully.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(_async_main())

