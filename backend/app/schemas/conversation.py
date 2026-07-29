import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    talent_id: uuid.UUID
    casting_call_id: uuid.UUID | None = None


class MessageCreate(BaseModel):
    body: str


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_user_id: uuid.UUID
    body: str
    read_at: datetime | None
    created_at: datetime


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    talent_id: uuid.UUID
    recruiter_id: uuid.UUID
    casting_call_id: uuid.UUID | None
    created_at: datetime


class ConversationSummary(ConversationRead):
    other_party_name: str
    last_message: str | None
    last_message_at: datetime | None
    unread_count: int
