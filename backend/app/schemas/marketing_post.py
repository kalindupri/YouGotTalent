import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.marketing_post import MarketingPostStatus


class MarketingPostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic: str | None
    content: str | None
    status: MarketingPostStatus
    discord_channel_id: str | None
    discord_message_id: str | None
    facebook_post_id: str | None
    error_message: str | None
    created_at: datetime
    decided_at: datetime | None
    posted_at: datetime | None


class GenerateDraftResult(BaseModel):
    created: bool
    reason: str | None = None
    post: MarketingPostRead | None = None


class CheckApprovalsResult(BaseModel):
    checked: int
    posted: int
    rejected: int
    expired: int
    failed: int
