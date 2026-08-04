import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.media import MediaType
from app.models.talent_profile import TalentCategory
from app.schemas.credit import CreditRead


class TalentProfileCreate(BaseModel):
    display_name: str
    category: TalentCategory
    bio: str | None = None
    city: str | None = None
    date_of_birth: date | None = None
    experience_years: int | None = None
    skills: list[str] | None = None
    instruments: list[str] | None = None
    instagram_url: str | None = None
    facebook_url: str | None = None
    tiktok_url: str | None = None
    twitter_url: str | None = None
    youtube_url: str | None = None
    website_url: str | None = None
    intro_video_url: str | None = None
    attributes: dict[str, str] | None = None
    job_alert_emails: bool = True


class TalentProfileUpdate(BaseModel):
    display_name: str | None = None
    category: TalentCategory | None = None
    bio: str | None = None
    city: str | None = None
    date_of_birth: date | None = None
    experience_years: int | None = None
    skills: list[str] | None = None
    instruments: list[str] | None = None
    instagram_url: str | None = None
    facebook_url: str | None = None
    tiktok_url: str | None = None
    twitter_url: str | None = None
    youtube_url: str | None = None
    website_url: str | None = None
    intro_video_url: str | None = None
    attributes: dict[str, str] | None = None
    job_alert_emails: bool | None = None


class MediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    media_type: MediaType
    title: str | None
    is_cover: bool


class MediaCreate(BaseModel):
    url: str
    media_type: MediaType
    title: str | None = None
    is_cover: bool = False


class MediaUpdate(BaseModel):
    title: str | None = None


class TalentProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str
    category: TalentCategory
    bio: str | None
    city: str | None
    date_of_birth: date | None
    experience_years: int | None
    skills: list[str] | None
    instruments: list[str] | None
    tier: str
    is_verified: bool
    verification_requested_at: datetime | None
    instagram_url: str | None
    facebook_url: str | None
    tiktok_url: str | None
    twitter_url: str | None
    youtube_url: str | None
    website_url: str | None
    intro_video_url: str | None
    attributes: dict[str, str] | None
    job_alert_emails: bool
    created_at: datetime
    media: list[MediaRead] = []
    credits: list[CreditRead] = []
