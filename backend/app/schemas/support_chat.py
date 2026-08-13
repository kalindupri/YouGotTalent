import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SupportMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sender: str
    content: str
    created_at: datetime


class SupportConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    messages: list[SupportMessageRead]


class StartSupportChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class SendSupportMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
