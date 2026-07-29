import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message


def get_conversation(db: Session, conversation_id: uuid.UUID) -> Conversation | None:
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()


def get_conversation_by_participants(db: Session, recruiter_id: uuid.UUID, talent_id: uuid.UUID) -> Conversation | None:
    return (
        db.query(Conversation)
        .filter(Conversation.recruiter_id == recruiter_id, Conversation.talent_id == talent_id)
        .first()
    )


def create_conversation(
    db: Session, recruiter_id: uuid.UUID, talent_id: uuid.UUID, casting_call_id: uuid.UUID | None
) -> Conversation:
    conversation = Conversation(recruiter_id=recruiter_id, talent_id=talent_id, casting_call_id=casting_call_id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def list_conversations_for_talent(db: Session, talent_id: uuid.UUID) -> list[Conversation]:
    return db.query(Conversation).filter(Conversation.talent_id == talent_id).all()


def list_conversations_for_recruiter(db: Session, recruiter_id: uuid.UUID) -> list[Conversation]:
    return db.query(Conversation).filter(Conversation.recruiter_id == recruiter_id).all()


def list_messages(db: Session, conversation_id: uuid.UUID) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )


def create_message(db: Session, conversation_id: uuid.UUID, sender_user_id: uuid.UUID, body: str) -> Message:
    message = Message(conversation_id=conversation_id, sender_user_id=sender_user_id, body=body)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def last_message_for_conversation(db: Session, conversation_id: uuid.UUID) -> Message | None:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .first()
    )


def unread_count(db: Session, conversation_id: uuid.UUID, reader_user_id: uuid.UUID) -> int:
    return (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation_id,
            Message.sender_user_id != reader_user_id,
            Message.read_at.is_(None),
        )
        .count()
    )


def mark_messages_read(db: Session, conversation_id: uuid.UUID, reader_user_id: uuid.UUID) -> None:
    db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.sender_user_id != reader_user_id,
        Message.read_at.is_(None),
    ).update({"read_at": func.now()}, synchronize_session=False)
    db.commit()
