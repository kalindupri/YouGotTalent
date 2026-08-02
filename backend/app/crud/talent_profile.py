import uuid
from functools import reduce

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.models.media import Media, MediaType
from app.models.talent_profile import TalentCategory, TalentProfile
from app.schemas.talent_profile import MediaCreate, MediaUpdate, TalentProfileCreate, TalentProfileUpdate


def get_talent_profile(db: Session, talent_id: uuid.UUID) -> TalentProfile | None:
    return db.query(TalentProfile).filter(TalentProfile.id == talent_id).first()


def get_talent_profile_by_user(db: Session, user_id: uuid.UUID) -> TalentProfile | None:
    return db.query(TalentProfile).filter(TalentProfile.user_id == user_id).first()


def list_talent_profiles(
    db: Session,
    category: TalentCategory | None,
    city: str | None,
    q: str | None,
    skip: int,
    limit: int,
    experience_min: int | None = None,
    experience_max: int | None = None,
    verified_only: bool = False,
) -> list[TalentProfile]:
    query = db.query(TalentProfile)
    if category:
        query = query.filter(TalentProfile.category == category)
    if city:
        query = query.filter(TalentProfile.city.ilike(f"%{city}%"))
    if verified_only:
        query = query.filter(TalentProfile.is_verified.is_(True))
    if experience_min is not None:
        query = query.filter(TalentProfile.experience_years >= experience_min)
    if experience_max is not None:
        query = query.filter(TalentProfile.experience_years <= experience_max)

    # Premium talent get priority placement in results, ahead of relevance/recency.
    tier_boost = case((TalentProfile.tier == "premium", 1), else_=0)

    if q:
        tokens = [t for t in q.strip().split() if t]
        if tokens:
            skills_as_text = func.array_to_string(TalentProfile.skills, ",")
            match_conditions = []
            score_terms = []
            for token in tokens:
                pattern = f"%{token}%"
                name_match = TalentProfile.display_name.ilike(pattern)
                skills_match = skills_as_text.ilike(pattern)
                category_match = TalentProfile.category.ilike(pattern)
                bio_match = TalentProfile.bio.ilike(pattern)
                match_conditions.extend([name_match, skills_match, category_match, bio_match])
                # Weight matches by field relevance: name and skills matter most for finding the right talent.
                score_terms.append(case((name_match, 3), else_=0))
                score_terms.append(case((skills_match, 3), else_=0))
                score_terms.append(case((category_match, 2), else_=0))
                score_terms.append(case((bio_match, 1), else_=0))
            relevance = reduce(lambda a, b: a + b, score_terms)
            query = query.filter(or_(*match_conditions)).order_by(tier_boost.desc(), relevance.desc(), TalentProfile.created_at.desc())
            return query.offset(skip).limit(limit).all()

    query = query.order_by(tier_boost.desc(), TalentProfile.created_at.desc())
    return query.offset(skip).limit(limit).all()


def list_talent_profiles_for_job_alert(db: Session, categories: set[str]) -> list[TalentProfile]:
    if not categories:
        return []
    return (
        db.query(TalentProfile)
        .filter(TalentProfile.category.in_(categories), TalentProfile.job_alert_emails.is_(True))
        .all()
    )


def create_talent_profile(db: Session, user_id: uuid.UUID, profile_in: TalentProfileCreate) -> TalentProfile:
    profile = TalentProfile(user_id=user_id, **profile_in.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_talent_profile(db: Session, profile: TalentProfile, profile_in: TalentProfileUpdate) -> TalentProfile:
    for field, value in profile_in.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


def add_media(db: Session, talent_profile_id: uuid.UUID, media_in: MediaCreate) -> Media:
    media = Media(talent_profile_id=talent_profile_id, **media_in.model_dump())
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


def count_media(db: Session, talent_profile_id: uuid.UUID) -> int:
    return db.query(Media).filter(Media.talent_profile_id == talent_profile_id).count()


def count_media_by_type(db: Session, talent_profile_id: uuid.UUID, media_type: MediaType) -> int:
    return (
        db.query(Media)
        .filter(Media.talent_profile_id == talent_profile_id, Media.media_type == media_type)
        .count()
    )


def get_cover_media(db: Session, talent_profile_id: uuid.UUID) -> Media | None:
    return db.query(Media).filter(Media.talent_profile_id == talent_profile_id, Media.is_cover.is_(True)).first()


def update_media(db: Session, media: Media, media_in: MediaUpdate) -> Media:
    for field, value in media_in.model_dump(exclude_unset=True).items():
        setattr(media, field, value)
    db.commit()
    db.refresh(media)
    return media


def get_media(db: Session, media_id: uuid.UUID) -> Media | None:
    return db.query(Media).filter(Media.id == media_id).first()


def delete_media(db: Session, media: Media) -> None:
    db.delete(media)
    db.commit()


def request_verification(db: Session, profile: TalentProfile) -> TalentProfile:
    profile.verification_requested_at = func.now()
    db.commit()
    db.refresh(profile)
    return profile


def set_tier(db: Session, profile: TalentProfile, tier: str) -> TalentProfile:
    profile.tier = tier
    db.commit()
    db.refresh(profile)
    return profile
