import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.application import Application
from app.models.casting_call import CastingCall, CastingCallStatus
from app.models.invitation import Invitation
from app.models.recruiter_profile import RecruiterProfile
from app.models.talent_profile import TalentProfile
from app.models.user import User, UserRole


def get_stats(db: Session) -> dict:
    return {
        "total_users": db.query(User).count(),
        "total_talents": db.query(TalentProfile).count(),
        "total_recruiters": db.query(RecruiterProfile).count(),
        "verified_talents": db.query(TalentProfile).filter(TalentProfile.is_verified.is_(True)).count(),
        "verified_recruiters": db.query(RecruiterProfile).filter(RecruiterProfile.is_verified.is_(True)).count(),
        "open_casting_calls": db.query(CastingCall).filter(CastingCall.status == CastingCallStatus.OPEN).count(),
        "closed_casting_calls": db.query(CastingCall).filter(CastingCall.status == CastingCallStatus.CLOSED).count(),
        "total_applications": db.query(Application).count(),
        "total_invitations": db.query(Invitation).count(),
    }


def list_users(db: Session, role: UserRole | None, q: str | None) -> list[User]:
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if q:
        pattern = f"%{q}%"
        query = query.filter(or_(User.email.ilike(pattern), User.full_name.ilike(pattern)))
    return query.order_by(User.created_at.desc()).all()


def get_user(db: Session, user_id: uuid.UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def set_user_active(db: Session, user: User, is_active: bool) -> User:
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def list_pending_talent_verifications(db: Session) -> list[TalentProfile]:
    return (
        db.query(TalentProfile)
        .filter(TalentProfile.verification_requested_at.isnot(None), TalentProfile.is_verified.is_(False))
        .order_by(TalentProfile.verification_requested_at.asc())
        .all()
    )


def approve_talent_verification(db: Session, profile: TalentProfile) -> TalentProfile:
    profile.is_verified = True
    profile.verification_requested_at = None
    db.commit()
    db.refresh(profile)
    return profile


def reject_talent_verification(db: Session, profile: TalentProfile) -> TalentProfile:
    profile.verification_requested_at = None
    db.commit()
    db.refresh(profile)
    return profile


def list_pending_recruiter_verifications(db: Session) -> list[RecruiterProfile]:
    return (
        db.query(RecruiterProfile)
        .filter(RecruiterProfile.verification_requested_at.isnot(None), RecruiterProfile.is_verified.is_(False))
        .order_by(RecruiterProfile.verification_requested_at.asc())
        .all()
    )


def approve_recruiter_verification(db: Session, profile: RecruiterProfile) -> RecruiterProfile:
    profile.is_verified = True
    profile.verification_requested_at = None
    db.commit()
    db.refresh(profile)
    return profile


def reject_recruiter_verification(db: Session, profile: RecruiterProfile) -> RecruiterProfile:
    profile.verification_requested_at = None
    db.commit()
    db.refresh(profile)
    return profile


def _attach_admin_fields(db: Session, call: CastingCall) -> CastingCall:
    # Ad-hoc attributes (not mapped columns) — AdminCastingCallRead's from_attributes=True
    # picks these up the same way it reads any other attribute off the ORM instance.
    call.recruiter_company_name = call.recruiter.company_name
    call.application_count = db.query(Application).filter(Application.casting_call_id == call.id).count()
    call.invitation_count = db.query(Invitation).filter(Invitation.casting_call_id == call.id).count()
    return call


def list_all_casting_calls(db: Session, status: CastingCallStatus | None) -> list[CastingCall]:
    query = db.query(CastingCall)
    if status:
        query = query.filter(CastingCall.status == status)
    calls = query.order_by(CastingCall.created_at.desc()).all()
    return [_attach_admin_fields(db, call) for call in calls]


def set_casting_call_status(db: Session, call: CastingCall, status: CastingCallStatus) -> CastingCall:
    call.status = status
    db.commit()
    db.refresh(call)
    return _attach_admin_fields(db, call)


def get_financial_overview(db: Session) -> dict:
    premium_talents = db.query(TalentProfile).filter(TalentProfile.tier == "premium").count()
    free_talents = db.query(TalentProfile).filter(TalentProfile.tier == "free").count()
    premium_recruiters = db.query(RecruiterProfile).filter(RecruiterProfile.tier == "premium").count()
    free_recruiters = db.query(RecruiterProfile).filter(RecruiterProfile.tier == "free").count()
    return {
        "currency": "LKR",
        "free_talents": free_talents,
        "premium_talents": premium_talents,
        "free_recruiters": free_recruiters,
        "premium_recruiters": premium_recruiters,
        "price_per_premium_talent": settings.PREMIUM_TALENT_PRICE_LKR,
        "price_per_premium_recruiter": settings.PREMIUM_RECRUITER_PRICE_LKR,
        "estimated_monthly_revenue": (
            premium_talents * settings.PREMIUM_TALENT_PRICE_LKR
            + premium_recruiters * settings.PREMIUM_RECRUITER_PRICE_LKR
        ),
    }
