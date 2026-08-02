import uuid

from sqlalchemy.orm import Session

from app.models.credit import Credit
from app.schemas.credit import CreditCreate, CreditUpdate


def get_credit(db: Session, credit_id: uuid.UUID) -> Credit | None:
    return db.query(Credit).filter(Credit.id == credit_id).first()


def create_credit(db: Session, talent_profile_id: uuid.UUID, credit_in: CreditCreate) -> Credit:
    credit = Credit(talent_profile_id=talent_profile_id, **credit_in.model_dump())
    db.add(credit)
    db.commit()
    db.refresh(credit)
    return credit


def update_credit(db: Session, credit: Credit, credit_in: CreditUpdate) -> Credit:
    for field, value in credit_in.model_dump(exclude_unset=True).items():
        setattr(credit, field, value)
    db.commit()
    db.refresh(credit)
    return credit


def delete_credit(db: Session, credit: Credit) -> None:
    db.delete(credit)
    db.commit()
