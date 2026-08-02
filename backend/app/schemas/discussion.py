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
    author_user_id: uuid.UUID
    author_name: str
    author_role: str
    author_profile_id: str | None
    reply_count: int


class ThreadUpdate(BaseModel):
    category: DiscussionCategory | None = None
    subject: str | None = None
    body: str | None = None
    title_id: uuid.UUID | None = None


class ReplyCreate(BaseModel):
    body: str


class ReplyUpdate(BaseModel):
    body: str


class ReplyRead(BaseModel):
    id: uuid.UUID
    thread_id: uuid.UUID
    body: str
    created_at: datetime
    author_user_id: uuid.UUID
    author_name: str
    author_role: str
    author_profile_id: str | None
