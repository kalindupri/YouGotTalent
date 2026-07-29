import uuid

from sqlalchemy.orm import Session

from app.models.follow import Follow
from app.models.talent_profile import TalentProfile


def _attach_summary_fields(follow: Follow) -> Follow:
    follow.recruiter_company_name = follow.recruiter.company_name
    return follow


def is_following(db: Session, talent_id: uuid.UUID, recruiter_id: uuid.UUID) -> bool:
    return (
        db.query(Follow).filter(Follow.talent_id == talent_id, Follow.recruiter_id == recruiter_id).first()
        is not None
    )


def follow_recruiter(db: Session, talent_id: uuid.UUID, recruiter_id: uuid.UUID) -> Follow:
    follow = Follow(talent_id=talent_id, recruiter_id=recruiter_id)
    db.add(follow)
    db.commit()
    db.refresh(follow)
    return _attach_summary_fields(follow)


def unfollow_recruiter(db: Session, talent_id: uuid.UUID, recruiter_id: uuid.UUID) -> None:
    follow = db.query(Follow).filter(Follow.talent_id == talent_id, Follow.recruiter_id == recruiter_id).first()
    if follow is not None:
        db.delete(follow)
        db.commit()


def list_followed_recruiters(db: Session, talent_id: uuid.UUID) -> list[Follow]:
    follows = db.query(Follow).filter(Follow.talent_id == talent_id).order_by(Follow.created_at.desc()).all()
    return [_attach_summary_fields(f) for f in follows]


def list_follower_talents(db: Session, recruiter_id: uuid.UUID) -> list[TalentProfile]:
    return (
        db.query(TalentProfile)
        .join(Follow, Follow.talent_id == TalentProfile.id)
        .filter(Follow.recruiter_id == recruiter_id)
        .all()
    )
