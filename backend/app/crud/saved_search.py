import uuid

from sqlalchemy.orm import Session

from app.models.saved_search import SavedSearch
from app.schemas.saved_search import SavedSearchCreate


def list_saved_searches(db: Session, recruiter_id: uuid.UUID) -> list[SavedSearch]:
    return db.query(SavedSearch).filter(SavedSearch.recruiter_id == recruiter_id).order_by(SavedSearch.created_at.desc()).all()


def get_saved_search(db: Session, saved_search_id: uuid.UUID) -> SavedSearch | None:
    return db.query(SavedSearch).filter(SavedSearch.id == saved_search_id).first()


def create_saved_search(db: Session, recruiter_id: uuid.UUID, search_in: SavedSearchCreate) -> SavedSearch:
    saved_search = SavedSearch(recruiter_id=recruiter_id, **search_in.model_dump())
    db.add(saved_search)
    db.commit()
    db.refresh(saved_search)
    return saved_search


def delete_saved_search(db: Session, saved_search: SavedSearch) -> None:
    db.delete(saved_search)
    db.commit()
