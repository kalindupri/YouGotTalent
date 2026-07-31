import uuid

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.crud.author import get_author_info
from app.models.title import Title, TitleReview, WorkType
from app.schemas.title import TitleCreate, TitleReviewCreate


def _attach_rating_summary(db: Session, title: Title) -> Title:
    average, count = (
        db.query(func.avg(TitleReview.rating), func.count(TitleReview.id)).filter(TitleReview.title_id == title.id).first()
    )
    title.average_rating = round(float(average), 1) if average is not None else None
    title.review_count = count or 0
    return title


def create_title(db: Session, user_id: uuid.UUID, title_in: TitleCreate) -> Title:
    title = Title(**title_in.model_dump(), added_by_user_id=user_id)
    db.add(title)
    db.commit()
    db.refresh(title)
    return _attach_rating_summary(db, title)


def get_title(db: Session, title_id: uuid.UUID) -> Title | None:
    title = db.query(Title).filter(Title.id == title_id).first()
    return _attach_rating_summary(db, title) if title else None


def list_titles(db: Session, work_type: WorkType | None = None, q: str | None = None) -> list[Title]:
    query = db.query(Title)
    if work_type:
        query = query.filter(Title.work_type == work_type)
    if q:
        pattern = f"%{q}%"
        query = query.filter(or_(Title.name.ilike(pattern), Title.genre.ilike(pattern)))
    titles = query.order_by(Title.created_at.desc()).all()
    return [_attach_rating_summary(db, t) for t in titles]


def delete_title(db: Session, title: Title) -> None:
    db.delete(title)
    db.commit()


def get_review_for_user(db: Session, title_id: uuid.UUID, user_id: uuid.UUID) -> TitleReview | None:
    return db.query(TitleReview).filter(TitleReview.title_id == title_id, TitleReview.user_id == user_id).first()


def upsert_review(db: Session, title_id: uuid.UUID, user_id: uuid.UUID, review_in: TitleReviewCreate) -> TitleReview:
    review = get_review_for_user(db, title_id, user_id)
    if review is None:
        review = TitleReview(title_id=title_id, user_id=user_id, rating=review_in.rating, body=review_in.body)
        db.add(review)
    else:
        review.rating = review_in.rating
        review.body = review_in.body
    db.commit()
    db.refresh(review)
    return review


def review_to_dict(db: Session, review: TitleReview) -> dict:
    author = get_author_info(db, review.user_id)
    return {
        "id": review.id,
        "rating": review.rating,
        "body": review.body,
        "created_at": review.created_at,
        "updated_at": review.updated_at,
        "author_name": author["name"],
        "author_role": author["role"],
        "author_profile_id": author["profile_id"],
    }


def list_reviews_for_title(db: Session, title_id: uuid.UUID) -> list[dict]:
    reviews = db.query(TitleReview).filter(TitleReview.title_id == title_id).order_by(TitleReview.created_at.desc()).all()
    return [review_to_dict(db, r) for r in reviews]


def get_review(db: Session, review_id: uuid.UUID) -> TitleReview | None:
    return db.query(TitleReview).filter(TitleReview.id == review_id).first()


def delete_review(db: Session, review: TitleReview) -> None:
    db.delete(review)
    db.commit()
