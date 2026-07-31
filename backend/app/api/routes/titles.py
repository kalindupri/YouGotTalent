import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud import title as title_crud
from app.db.session import get_db
from app.models.title import WorkType
from app.models.user import User
from app.schemas.title import TitleCreate, TitleRead, TitleReviewCreate, TitleReviewRead

router = APIRouter(prefix="/titles", tags=["titles"])


@router.get("", response_model=list[TitleRead])
def read_titles(work_type: WorkType | None = None, q: str | None = None, db: Session = Depends(get_db)):
    return title_crud.list_titles(db, work_type, q)


@router.post("", response_model=TitleRead, status_code=status.HTTP_201_CREATED)
def create_title(payload: TitleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return title_crud.create_title(db, user.id, payload)


@router.get("/{title_id}", response_model=TitleRead)
def read_title(title_id: uuid.UUID, db: Session = Depends(get_db)):
    title = title_crud.get_title(db, title_id)
    if title is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Title not found")
    return title


@router.get("/{title_id}/reviews", response_model=list[TitleReviewRead])
def read_title_reviews(title_id: uuid.UUID, db: Session = Depends(get_db)):
    if title_crud.get_title(db, title_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Title not found")
    return title_crud.list_reviews_for_title(db, title_id)


@router.get("/{title_id}/reviews/mine", response_model=TitleReviewRead | None)
def read_my_review(title_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    review = title_crud.get_review_for_user(db, title_id, user.id)
    return title_crud.review_to_dict(db, review) if review else None


@router.post("/{title_id}/reviews", response_model=TitleReviewRead, status_code=status.HTTP_201_CREATED)
def submit_review(
    title_id: uuid.UUID,
    payload: TitleReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if title_crud.get_title(db, title_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Title not found")
    review = title_crud.upsert_review(db, title_id, user.id, payload)
    return title_crud.review_to_dict(db, review)


@router.delete("/{title_id}/reviews/mine", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_review(title_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    review = title_crud.get_review_for_user(db, title_id, user.id)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You haven't reviewed this title")
    title_crud.delete_review(db, review)
