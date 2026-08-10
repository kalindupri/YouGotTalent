import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.notification import (
    get_notification,
    list_notifications_for_user,
    mark_all_read,
    mark_notification_read,
    unread_count_for_user,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.notification import NotificationRead, UnreadCountRead

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_my_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list_notifications_for_user(db, user.id)


@router.get("/unread-count", response_model=UnreadCountRead)
def read_unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return UnreadCountRead(count=unread_count_for_user(db, user.id))


@router.patch("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_notifications_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    mark_all_read(db, user.id)


@router.patch("/{notification_id}/read", response_model=NotificationRead)
def mark_one_notification_read(
    notification_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    notification = get_notification(db, notification_id)
    # 404, not 403, for a notification owned by someone else — matches this app's existing
    # hide-existence pattern rather than confirming another user's notification exists.
    if notification is None or notification.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return mark_notification_read(db, notification)
