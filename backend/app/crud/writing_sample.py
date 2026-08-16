import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.writing_sample import WritingSample
from app.schemas.writing_sample import WritingSampleCreate, WritingSampleRead, WritingSampleUpdate


def count_published_writing_samples(db: Session, talent_profile_id: uuid.UUID) -> int:
    return (
        db.query(func.count(WritingSample.id))
        .filter(WritingSample.talent_profile_id == talent_profile_id, WritingSample.is_published.is_(True))
        .scalar()
        or 0
    )


def get_writing_sample(db: Session, sample_id: uuid.UUID) -> WritingSample | None:
    return db.query(WritingSample).filter(WritingSample.id == sample_id).first()


def list_writing_samples_for_profile(db: Session, talent_profile_id: uuid.UUID, *, owner_view: bool) -> list[WritingSample]:
    query = db.query(WritingSample).filter(WritingSample.talent_profile_id == talent_profile_id)
    if not owner_view:
        # Drafts are never visible outside the owner's own dashboard, regardless of the
        # `visibility` field (which only governs published pieces).
        query = query.filter(WritingSample.is_published.is_(True))
    return query.order_by(WritingSample.created_at.desc()).all()


def create_writing_sample(db: Session, talent_profile_id: uuid.UUID, sample_in: WritingSampleCreate) -> WritingSample:
    sample = WritingSample(talent_profile_id=talent_profile_id, **sample_in.model_dump())
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return sample


def update_writing_sample(db: Session, sample: WritingSample, sample_in: WritingSampleUpdate) -> WritingSample:
    for field, value in sample_in.model_dump(exclude_unset=True).items():
        setattr(sample, field, value)
    db.commit()
    db.refresh(sample)
    return sample


def delete_writing_sample(db: Session, sample: WritingSample) -> None:
    db.delete(sample)
    db.commit()


def to_read_schema(sample: WritingSample, *, is_owner: bool) -> WritingSampleRead:
    """The owner always gets the full `body` (they're the one editing it). Anyone else gets at
    most `visible_lines` lines -- enforced here, not left to the frontend, so the full text is
    never actually sent over the wire to a non-owner viewer.
    """
    data = WritingSampleRead.model_validate(sample)
    if is_owner:
        return data

    lines = sample.body.splitlines()
    if len(lines) > sample.visible_lines:
        data.body = "\n".join(lines[: sample.visible_lines])
        data.is_excerpt = True
    return data
