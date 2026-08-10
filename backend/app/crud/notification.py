import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session, user_id: uuid.UUID, type: str, title: str, body: str | None = None, link_url: str | None = None
) -> Notification:
    notification = Notification(user_id=user_id, type=type, title=title, body=body, link_url=link_url)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def list_notifications_for_user(db: Session, user_id: uuid.UUID, limit: int = 50) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )


def get_notification(db: Session, notification_id: uuid.UUID) -> Notification | None:
    return db.query(Notification).filter(Notification.id == notification_id).first()


def unread_count_for_user(db: Session, user_id: uuid.UUID) -> int:
    return (
        db.query(func.count(Notification.id))
        .filter(Notification.user_id == user_id, Notification.read_at.is_(None))
        .scalar()
        or 0
    )


def mark_notification_read(db: Session, notification: Notification) -> Notification:
    if notification.read_at is None:
        notification.read_at = func.now()
        db.commit()
        db.refresh(notification)
    return notification


def mark_all_read(db: Session, user_id: uuid.UUID) -> None:
    db.query(Notification).filter(Notification.user_id == user_id, Notification.read_at.is_(None)).update(
        {"read_at": func.now()}
    )
    db.commit()
