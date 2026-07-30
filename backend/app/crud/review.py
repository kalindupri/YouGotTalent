import uuid

from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.review import Review
from app.schemas.review import ReviewCreate


def _attach_reviewer_name(review: Review) -> Review:
    review.reviewer_name = review.talent.display_name if review.reviewer_role == "talent" else review.recruiter.company_name
    return review


def create_review(db: Session, booking: Booking, reviewer_role: str, review_in: ReviewCreate) -> Review:
    review = Review(
        booking_id=booking.id,
        talent_id=booking.talent_id,
        recruiter_id=booking.recruiter_id,
        reviewer_role=reviewer_role,
        rating=review_in.rating,
        comment=review_in.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return _attach_reviewer_name(review)


def list_reviews_for_talent(db: Session, talent_id: uuid.UUID) -> list[Review]:
    reviews = (
        db.query(Review)
        .filter(Review.talent_id == talent_id, Review.reviewer_role == "recruiter")
        .order_by(Review.created_at.desc())
        .all()
    )
    return [_attach_reviewer_name(r) for r in reviews]


def list_reviews_for_recruiter(db: Session, recruiter_id: uuid.UUID) -> list[Review]:
    reviews = (
        db.query(Review)
        .filter(Review.recruiter_id == recruiter_id, Review.reviewer_role == "talent")
        .order_by(Review.created_at.desc())
        .all()
    )
    return [_attach_reviewer_name(r) for r in reviews]


def get_talent_review_summary(db: Session, talent_id: uuid.UUID) -> dict:
    reviews = list_reviews_for_talent(db, talent_id)
    average = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else None
    return {"average_rating": average, "review_count": len(reviews), "reviews": reviews}


def get_recruiter_review_summary(db: Session, recruiter_id: uuid.UUID) -> dict:
    reviews = list_reviews_for_recruiter(db, recruiter_id)
    average = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else None
    return {"average_rating": average, "review_count": len(reviews), "reviews": reviews}
