import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from app.core.age import today_lk, years_ago
from app.models.content_visibility import ContentVisibility
from app.models.media import MediaType
from app.models.talent_profile import TalentCategory
from app.schemas.credit import CreditRead
from app.schemas.reel import ReelRead
from app.schemas.writing_sample import WritingSampleRead

# Oldest plausible date of birth. Not a real limit on anyone, just a guard against a typo
# ("1902" for "1992") silently making someone look old enough to work.
_MAX_PLAUSIBLE_AGE = 120


def _validate_date_of_birth(value: date) -> date:
    if value > today_lk():
        raise ValueError("That date of birth is in the future.")
    if value < years_ago(_MAX_PLAUSIBLE_AGE):
        raise ValueError("Please enter a real date of birth.")
    return value


# Date of birth decides whether guardian consent is required and whether paid work is allowed,
# so it's validated everywhere it's accepted rather than trusted from the client.
DateOfBirth = Annotated[date, AfterValidator(_validate_date_of_birth)]


class TalentProfileCreate(BaseModel):
    display_name: str
    # `category` (singular) is still accepted for backward compatibility with existing
    # callers — it's folded into `categories` below if that's not given directly.
    category: TalentCategory | None = None
    categories: list[TalentCategory] | None = None
    bio: str | None = None
    city: str | None = None
    # Required: the platform cannot tell a 13-year-old from a 30-year-old without it, and both
    # the guardian-consent rule and the minimum-working-age rule depend on knowing.
    date_of_birth: DateOfBirth
    gender: str | None = None
    tiktok_followers: int | None = None
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

    @model_validator(mode="after")
    def _require_at_least_one_category(self) -> "TalentProfileCreate":
        if not self.categories:
            if self.category is None:
                raise ValueError("category or categories is required")
            self.categories = [self.category]
        return self


class TalentProfileUpdate(BaseModel):
    display_name: str | None = None
    category: TalentCategory | None = None
    categories: list[TalentCategory] | None = Field(default=None, min_length=1)
    bio: str | None = None
    city: str | None = None
    # Correctable, but not erasable: an explicit null is rejected below, because clearing it
    # would drop the profile out of every age check.
    date_of_birth: DateOfBirth | None = None
    gender: str | None = None
    tiktok_followers: int | None = None
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

    @model_validator(mode="after")
    def _date_of_birth_cannot_be_cleared(self) -> "TalentProfileUpdate":
        # Every other field here treats None as "not supplied", so the two cases are only
        # distinguishable via model_fields_set.
        if "date_of_birth" in self.model_fields_set and self.date_of_birth is None:
            raise ValueError("Date of birth can be corrected but not removed.")
        return self


class ParsedTalentSearchQuery(BaseModel):
    categories: list[str] | None = None
    gender: str | None = None
    age_min: int | None = None
    age_max: int | None = None
    experience_min: int | None = None
    experience_max: int | None = None
    min_tiktok_followers: int | None = None
    instruments: list[str] | None = None
    keywords: str | None = None


class MediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    media_type: MediaType
    title: str | None
    is_cover: bool
    visibility: ContentVisibility


class MediaCreate(BaseModel):
    url: str
    media_type: MediaType
    title: str | None = None
    is_cover: bool = False
    visibility: ContentVisibility = ContentVisibility.PUBLIC


class MediaUpdate(BaseModel):
    title: str | None = None


class TalentProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str
    category: TalentCategory
    categories: list[str]
    bio: str | None
    city: str | None
    # Age, never the birth date. Recruiters cast by age; nobody outside the account needs a
    # minor's exact date of birth, which the PDPA treats as special-category data.
    # TalentProfileOwnerRead below re-adds the real date for the account that owns the profile.
    age: int | None
    gender: str | None
    tiktok_followers: int | None
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
    reels: list[ReelRead] = []
    writing_samples: list[WritingSampleRead] = []


class TalentProfileOwnerRead(TalentProfileRead):
    """What the account managing this profile sees -- and the only schema exposing the real
    date of birth. Every other schema that nests a talent profile (applications, invitations,
    saved talents, list members, new arrivals) inherits the plain read above, so opting in
    here is the entire surface on which a birth date can leak.
    """

    date_of_birth: date | None
    guardian_consent_status: str
