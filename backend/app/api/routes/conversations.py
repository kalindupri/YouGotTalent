import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_recruiter_profile, get_current_user
from app.core.config import settings
from app.core.email import send_email
from app.crud.conversation import (
    create_conversation,
    create_message,
    get_conversation,
    get_conversation_by_participants,
    last_message_for_conversation,
    list_conversations_for_recruiter,
    list_conversations_for_talent,
    list_messages,
    mark_messages_read,
    unread_count,
)
from app.crud.notification import create_notification
from app.crud.talent_profile import get_talent_profile
from app.db.session import get_db
from app.models.conversation import Conversation
from app.models.recruiter_profile import RecruiterProfile
from app.models.user import User, UserRole
from app.schemas.conversation import ConversationCreate, ConversationSummary, MessageCreate, MessageRead

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _assert_participant(conversation: Conversation, user: User) -> None:
    is_talent_side = user.role == UserRole.TALENT and conversation.talent.user_id == user.id
    is_recruiter_side = user.role == UserRole.RECRUITER and conversation.recruiter.user_id == user.id
    if not (is_talent_side or is_recruiter_side):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant in this conversation")


def _summarize(db: Session, conversation: Conversation, reader_user_id: uuid.UUID) -> ConversationSummary:
    other_party_name = (
        conversation.recruiter.company_name
        if reader_user_id == conversation.talent.user_id
        else conversation.talent.display_name
    )
    last_message = last_message_for_conversation(db, conversation.id)
    return ConversationSummary(
        id=conversation.id,
        talent_id=conversation.talent_id,
        recruiter_id=conversation.recruiter_id,
        casting_call_id=conversation.casting_call_id,
        created_at=conversation.created_at,
        other_party_name=other_party_name,
        last_message=last_message.body if last_message else None,
        last_message_at=last_message.created_at if last_message else None,
        unread_count=unread_count(db, conversation.id, reader_user_id),
    )


@router.post("", response_model=ConversationSummary, status_code=status.HTTP_201_CREATED)
def start_conversation(
    conversation_in: ConversationCreate,
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    if get_talent_profile(db, conversation_in.talent_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent profile not found")

    conversation = get_conversation_by_participants(db, recruiter.id, conversation_in.talent_id) or create_conversation(
        db, recruiter.id, conversation_in.talent_id, conversation_in.casting_call_id
    )
    return _summarize(db, conversation, reader_user_id=recruiter.user_id)


@router.get("", response_model=list[ConversationSummary])
def read_my_conversations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role == UserRole.TALENT:
        # One inbox across every profile this account manages, so a guardian with more than
        # one child doesn't have to switch profiles to notice a new message.
        conversations = [c for p in user.talent_profiles for c in list_conversations_for_talent(db, p.id)]
        if not conversations:
            return []
    elif user.role == UserRole.RECRUITER:
        if user.recruiter_profile is None:
            return []
        conversations = list_conversations_for_recruiter(db, user.recruiter_profile.id)
    else:
        return []
    return [_summarize(db, c, reader_user_id=user.id) for c in conversations]


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
def read_messages(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversation = get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    _assert_participant(conversation, user)
    mark_messages_read(db, conversation_id, user.id)
    return list_messages(db, conversation_id)


@router.post("/{conversation_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
def send_message(
    conversation_id: uuid.UUID,
    message_in: MessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversation = get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    _assert_participant(conversation, user)
    message = create_message(db, conversation_id, user.id, message_in.body)

    is_from_talent = user.id == conversation.talent.user_id
    recipient_email = conversation.recruiter.user.email if is_from_talent else conversation.talent.user.email
    recipient_user_id = conversation.recruiter.user_id if is_from_talent else conversation.talent.user_id
    sender_name = conversation.talent.display_name if is_from_talent else conversation.recruiter.company_name
    background_tasks.add_task(
        send_email,
        recipient_email,
        f"New message from {sender_name}",
        f"{sender_name} sent you a message on YouGotTalent:\n\n\"{message_in.body}\"\n\n"
        f"Reply here: {settings.FRONTEND_URL}/messages/{conversation_id}",
    )
    create_notification(
        db,
        recipient_user_id,
        "new_message",
        f"New message from {sender_name}",
        message_in.body,
        f"/messages/{conversation_id}",
    )
    return message
