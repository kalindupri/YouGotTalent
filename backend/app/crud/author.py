import uuid

from sqlalchemy.orm import Session

from app.models.recruiter_profile import RecruiterProfile
from app.models.talent_profile import TalentProfile
from app.models.user import User


def get_author_info(db: Session, user_id: uuid.UUID) -> dict:
    """Resolves a community post's author to a display name + role badge, since a User can be
    either a talent or a recruiter — used across titles, reviews, and discussions.
    """
    talent = db.query(TalentProfile).filter(TalentProfile.user_id == user_id).first()
    if talent:
        return {"name": talent.display_name, "role": "talent", "profile_id": str(talent.id)}
    recruiter = db.query(RecruiterProfile).filter(RecruiterProfile.user_id == user_id).first()
    if recruiter:
        return {"name": recruiter.company_name, "role": "recruiter", "profile_id": str(recruiter.id)}
    user = db.query(User).filter(User.id == user_id).first()
    return {"name": user.full_name if user else "Unknown", "role": "admin", "profile_id": None}
