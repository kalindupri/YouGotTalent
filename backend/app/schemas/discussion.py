import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.discussion import DiscussionCategory


class ThreadCreate(BaseModel):
    category: DiscussionCategory
    subject: str
    body: str
    title_id: uuid.UUID | None = None


class ThreadRead(BaseModel):
    id: uuid.UUID
    category: DiscussionCategory
    subject: str
    body: str
    title_id: uuid.UUID | None
    created_at: datetime
    author_name: str
    author_role: str
    author_profile_id: str | None
    reply_count: int


class ReplyCreate(BaseModel):
    body: str


class ReplyRead(BaseModel):
    id: uuid.UUID
    thread_id: uuid.UUID
    body: str
    created_at: datetime
    author_name: str
    author_role: str
    author_profile_id: str | None
