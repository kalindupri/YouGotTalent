import uuid

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.crud.author import get_author_info
from app.models.discussion import DiscussionCategory, DiscussionReply, DiscussionThread
from app.schemas.discussion import ThreadCreate, ReplyCreate


def _to_thread_dict(db: Session, thread: DiscussionThread, reply_count: int | None = None) -> dict:
    author = get_author_info(db, thread.author_user_id)
    if reply_count is None:
        reply_count = db.query(func.count(DiscussionReply.id)).filter(DiscussionReply.thread_id == thread.id).scalar() or 0
    return {
        "id": thread.id,
        "category": thread.category,
        "subject": thread.subject,
        "body": thread.body,
        "title_id": thread.title_id,
        "created_at": thread.created_at,
        "author_name": author["name"],
        "author_role": author["role"],
        "author_profile_id": author["profile_id"],
        "reply_count": reply_count,
    }


def create_thread(db: Session, user_id: uuid.UUID, thread_in: ThreadCreate) -> dict:
    thread = DiscussionThread(**thread_in.model_dump(), author_user_id=user_id)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return _to_thread_dict(db, thread, reply_count=0)


def get_thread(db: Session, thread_id: uuid.UUID) -> DiscussionThread | None:
    return db.query(DiscussionThread).filter(DiscussionThread.id == thread_id).first()


def get_thread_dict(db: Session, thread_id: uuid.UUID) -> dict | None:
    thread = get_thread(db, thread_id)
    return _to_thread_dict(db, thread) if thread else None


def list_threads(db: Session, category: DiscussionCategory | None = None, title_id: uuid.UUID | None = None, q: str | None = None) -> list[dict]:
    query = db.query(DiscussionThread)
    if category:
        query = query.filter(DiscussionThread.category == category)
    if title_id:
        query = query.filter(DiscussionThread.title_id == title_id)
    if q:
        pattern = f"%{q}%"
        query = query.filter(or_(DiscussionThread.subject.ilike(pattern), DiscussionThread.body.ilike(pattern)))
    threads = query.order_by(DiscussionThread.created_at.desc()).all()
    return [_to_thread_dict(db, t) for t in threads]


def delete_thread(db: Session, thread: DiscussionThread) -> None:
    db.delete(thread)
    db.commit()


def create_reply(db: Session, thread_id: uuid.UUID, user_id: uuid.UUID, reply_in: ReplyCreate) -> dict:
    reply = DiscussionReply(thread_id=thread_id, author_user_id=user_id, body=reply_in.body)
    db.add(reply)
    db.commit()
    db.refresh(reply)
    author = get_author_info(db, user_id)
    return {
        "id": reply.id,
        "thread_id": reply.thread_id,
        "body": reply.body,
        "created_at": reply.created_at,
        "author_name": author["name"],
        "author_role": author["role"],
        "author_profile_id": author["profile_id"],
    }


def list_replies(db: Session, thread_id: uuid.UUID) -> list[dict]:
    replies = db.query(DiscussionReply).filter(DiscussionReply.thread_id == thread_id).order_by(DiscussionReply.created_at.asc()).all()
    out = []
    for r in replies:
        author = get_author_info(db, r.author_user_id)
        out.append(
            {
                "id": r.id,
                "thread_id": r.thread_id,
                "body": r.body,
                "created_at": r.created_at,
                "author_name": author["name"],
                "author_role": author["role"],
                "author_profile_id": author["profile_id"],
            }
        )
    return out


def get_reply(db: Session, reply_id: uuid.UUID) -> DiscussionReply | None:
    return db.query(DiscussionReply).filter(DiscussionReply.id == reply_id).first()


def delete_reply(db: Session, reply: DiscussionReply) -> None:
    db.delete(reply)
    db.commit()
