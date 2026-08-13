import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_optional_current_user
from app.core.config import settings
from app.crud import support_chat as crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.support_chat import SendSupportMessageRequest, StartSupportChatRequest, SupportConversationRead

router = APIRouter(prefix="/support", tags=["support"])


@router.get("/available")
def is_available() -> dict:
    return {"available": bool(settings.DISCORD_SUPPORT_CHANNEL_ID)}


@router.post("/start", response_model=SupportConversationRead)
def start_chat(
    body: StartSupportChatRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> object:
    if not settings.DISCORD_SUPPORT_CHANNEL_ID:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Live chat isn't available right now.")
    try:
        return crud.start_conversation(db, body.question, user)
    except httpx.HTTPError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Couldn't start live chat. Please try again.")


@router.get("/{conversation_id}", response_model=SupportConversationRead)
def poll_conversation(conversation_id: uuid.UUID, db: Session = Depends(get_db)) -> object:
    conversation = crud.get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    crud.sync_agent_replies(db, conversation)
    db.refresh(conversation)
    return conversation


@router.post("/{conversation_id}/messages", response_model=SupportConversationRead)
def send_message(conversation_id: uuid.UUID, body: SendSupportMessageRequest, db: Session = Depends(get_db)) -> object:
    conversation = crud.get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    crud.add_customer_message(db, conversation, body.content)
    crud.sync_agent_replies(db, conversation)
    db.refresh(conversation)
    return conversation
