"""Notification API routes.

Used to display supervisor review feedback (BR-19) on student dashboard.
"""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.models.user import User
from backend.models.notification import Notification
from backend.utils.security import get_current_active_user
from backend.config.database import get_db
from backend.core.logging import get_logger

logger = get_logger(__name__)

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


@router.get("/unread", response_model=List[NotificationItem])
async def get_unread_notifications(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all unread notifications for the current user."""
    try:
        stmt = (
            select(Notification)
            .where(
                Notification.user_id == current_user.user_id,
                Notification.is_read == False
            )
            .order_by(Notification.created_at.desc())
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()

        return [
            NotificationItem(
                id=r.id,
                project_id=r.project_id,
                type=r.type,
                content=r.content,
                is_read=r.is_read,
                created_at=r.created_at,
            )
            for r in rows
        ]
    except Exception as e:
        logger.error(f"Error fetching unread notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notifications"
        )


@router.post("/mark-read")
async def mark_notifications_read(
    body: MarkReadRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark one or more notifications as read."""
    if not body.notification_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No notification ids provided"
        )

    try:
        stmt = (
            select(Notification)
            .where(
                Notification.id.in_(body.notification_ids),
                Notification.user_id == current_user.user_id,
            )
        )
        result = await db.execute(stmt)
        notifications = result.scalars().all()

        if not notifications:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No matching notifications found"
            )

        for n in notifications:
            n.is_read = True

        await db.commit()
        return {"success": True, "updated_count": len(notifications)}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error marking notifications as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read"
        )