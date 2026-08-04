import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.profile_view import ProfileView
from app.models.recruiter_profile import RecruiterProfile


def record_profile_view(db: Session, talent_id: uuid.UUID, recruiter_id: uuid.UUID) -> None:
    db.add(ProfileView(talent_id=talent_id, recruiter_id=recruiter_id))
    db.commit()


def count_profile_views(db: Session, talent_id: uuid.UUID) -> int:
    return db.query(func.count(ProfileView.id)).filter(ProfileView.talent_id == talent_id).scalar() or 0


def list_distinct_viewers(db: Session, talent_id: uuid.UUID) -> list[dict]:
    """Most-recent visit per distinct recruiter, newest first."""
    latest_per_recruiter = (
        db.query(ProfileView.recruiter_id, func.max(ProfileView.viewed_at).label("viewed_at"))
        .filter(ProfileView.talent_id == talent_id)
        .group_by(ProfileView.recruiter_id)
        .subquery()
    )
    rows = (
        db.query(RecruiterProfile, latest_per_recruiter.c.viewed_at)
        .join(latest_per_recruiter, RecruiterProfile.id == latest_per_recruiter.c.recruiter_id)
        .order_by(latest_per_recruiter.c.viewed_at.desc())
        .all()
    )
    return [{"recruiter_id": r.id, "company_name": r.company_name, "viewed_at": viewed_at} for r, viewed_at in rows]
