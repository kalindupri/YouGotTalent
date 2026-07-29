import uuid

from sqlalchemy.orm import Session

from app.models.saved_talent import SavedTalent
from app.models.talent_profile import TalentProfile


def get_saved_talent(db: Session, recruiter_id: uuid.UUID, talent_id: uuid.UUID) -> SavedTalent | None:
    return (
        db.query(SavedTalent)
        .filter(SavedTalent.recruiter_id == recruiter_id, SavedTalent.talent_id == talent_id)
        .first()
    )


def save_talent(db: Session, recruiter_id: uuid.UUID, talent_id: uuid.UUID) -> SavedTalent:
    saved = SavedTalent(recruiter_id=recruiter_id, talent_id=talent_id)
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved


def unsave_talent(db: Session, saved: SavedTalent) -> None:
    db.delete(saved)
    db.commit()


def list_saved_talents(db: Session, recruiter_id: uuid.UUID) -> list[TalentProfile]:
    return (
        db.query(TalentProfile)
        .join(SavedTalent, SavedTalent.talent_id == TalentProfile.id)
        .filter(SavedTalent.recruiter_id == recruiter_id)
        .all()
    )
