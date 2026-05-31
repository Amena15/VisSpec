"""Notification API routes.

Used to display supervisor review feedback (BR-19) on student dashboard.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from models.user import User
from models.notification import Notification
from utils.security import get_current_active_user
from config.database import get_db

router = APIRouter(tags=["notifications"])


class MarkReadRequest(BaseModel):
    notification_ids: List[str]


class NotificationItem(BaseModel):
    id: str
    project_id: str
    type: str
    content: str
    is_read: bool
    created_at: str


@router.get("/unread")
async def get_unread_notifications(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    result = await db.execute(
        select(Notification)
        .filter(
            Notification.user_id == current_user.user_id, 
            Notification.is_read == False
        )
        .order_by(Notification.created_at.desc())
    )
    rows = result.scalars().all()

    return [
        {
            "id": r.id,
            "project_id": r.project_id,
            "type": r.type,
            "content": r.content,
            "is_read": r.is_read,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.post("/mark-read")
async def mark_notifications_read(
    body: MarkReadRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not body.notification_ids:
        raise HTTPException(status_code=400, detail="No notification ids provided")

    result = await db.execute(
        select(Notification)
        .filter(
            Notification.id.in_(body.notification_ids),  # type: ignore[attr-defined]
            Notification.user_id == current_user.user_id,
        )
    )
    updated = result.scalars().all()

    for n in updated:
        n.is_read = True

    await db.commit()
    return {"success": True, "updated_count": len(updated)}

