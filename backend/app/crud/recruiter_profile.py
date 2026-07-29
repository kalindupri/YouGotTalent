import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.casting_call import CastingCall, CastingCallStatus
from app.models.recruiter_profile import RecruiterProfile
from app.schemas.recruiter_profile import RecruiterProfileCreate


def get_recruiter_profile_by_user(db: Session, user_id: uuid.UUID) -> RecruiterProfile | None:
    return db.query(RecruiterProfile).filter(RecruiterProfile.user_id == user_id).first()


def get_recruiter_profile(db: Session, recruiter_id: uuid.UUID) -> RecruiterProfile | None:
    return db.query(RecruiterProfile).filter(RecruiterProfile.id == recruiter_id).first()


def create_recruiter_profile(db: Session, user_id: uuid.UUID, profile_in: RecruiterProfileCreate) -> RecruiterProfile:
    profile = RecruiterProfile(user_id=user_id, **profile_in.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def count_open_casting_calls(db: Session, recruiter_id: uuid.UUID) -> int:
    return (
        db.query(CastingCall)
        .filter(CastingCall.recruiter_id == recruiter_id, CastingCall.status == CastingCallStatus.OPEN)
        .count()
    )


def request_verification(db: Session, profile: RecruiterProfile) -> RecruiterProfile:
    profile.verification_requested_at = func.now()
    db.commit()
    db.refresh(profile)
    return profile


def set_tier(db: Session, profile: RecruiterProfile, tier: str) -> RecruiterProfile:
    profile.tier = tier
    db.commit()
    db.refresh(profile)
    return profile
