import uuid
from datetime import date, datetime, timedelta, timezone
from functools import reduce

from sqlalchemy import String, case, cast, func, or_
from sqlalchemy.orm import Session

from app.models.media import Media, MediaType
from app.models.talent_profile import TalentCategory, TalentProfile
from app.schemas.talent_profile import MediaCreate, MediaUpdate, TalentProfileCreate, TalentProfileUpdate


def get_talent_profile(db: Session, talent_id: uuid.UUID) -> TalentProfile | None:
    return db.query(TalentProfile).filter(TalentProfile.id == talent_id).first()


def get_talent_profile_by_user(db: Session, user_id: uuid.UUID) -> TalentProfile | None:
    return db.query(TalentProfile).filter(TalentProfile.user_id == user_id).first()


def list_talent_profiles_by_user(db: Session, user_id: uuid.UUID) -> list[TalentProfile]:
    """Every profile this account manages -- one for ordinary talent, one per child for a guardian."""
    return (
        db.query(TalentProfile)
        .filter(TalentProfile.user_id == user_id)
        .order_by(TalentProfile.created_at.asc())
        .all()
    )


def _years_ago(n: int) -> date:
    today = date.today()
    try:
        return today.replace(year=today.year - n)
    except ValueError:
        # Feb 29 on a target non-leap year -- fall back to Feb 28.
        return today.replace(year=today.year - n, day=28)


def list_talent_profiles(
    db: Session,
    categories: list[TalentCategory] | None,
    city: str | None,
    q: str | None,
    skip: int,
    limit: int,
    experience_min: int | None = None,
    experience_max: int | None = None,
    verified_only: bool = False,
    instruments: list[str] | None = None,
    gender: str | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    min_tiktok_followers: int | None = None,
) -> list[TalentProfile]:
    query = db.query(TalentProfile)
    if categories:
        # "Any of the selected categories" — same array-overlap pattern used for instruments
        # below, so a talent who does both acting and singing is found by filtering on either.
        query = query.filter(TalentProfile.categories.op("&&")(categories))
    if city:
        query = query.filter(TalentProfile.city.ilike(f"%{city}%"))
    if verified_only:
        query = query.filter(TalentProfile.is_verified.is_(True))
    if experience_min is not None:
        query = query.filter(TalentProfile.experience_years >= experience_min)
    if experience_max is not None:
        query = query.filter(TalentProfile.experience_years <= experience_max)
    if gender:
        query = query.filter(TalentProfile.gender.ilike(gender))
    if age_min is not None:
        # At least age_min years old -> born on or before N years ago.
        query = query.filter(TalentProfile.date_of_birth <= _years_ago(age_min))
    if age_max is not None:
        # At most age_max years old -> born after (age_max + 1) years ago.
        query = query.filter(TalentProfile.date_of_birth > _years_ago(age_max + 1))
    if min_tiktok_followers is not None:
        query = query.filter(TalentProfile.tiktok_followers >= min_tiktok_followers)
    if instruments:
        # Postgres array overlap ("any of the selected instruments") — the "multi-layered"
        # search requested: pick several instrument families and match talent with ANY of them.
        # `.op("&&")` rather than `.overlap()` since the column uses the generic sa.ARRAY type
        # (matching `skills`/`tags` elsewhere), not the postgresql-dialect-specific ARRAY class
        # whose comparator adds `.overlap()`.
        query = query.filter(TalentProfile.instruments.op("&&")(instruments))

    # Premium talent get priority placement in results, ahead of relevance/recency.
    tier_boost = case((TalentProfile.tier == "premium", 1), else_=0)

    if q:
        tokens = [t for t in q.strip().split() if t]
        if tokens:
            skills_as_text = func.array_to_string(TalentProfile.skills, ",")
            categories_as_text = func.array_to_string(TalentProfile.categories, ",")
            instruments_as_text = func.array_to_string(TalentProfile.instruments, ",")
            # Cast the freeform per-category attributes JSONB (height/look/vocal range/etc) to
            # text so leftover "characteristic" keywords from a smart-search query (e.g.
            # "traditional", "athletic") can match it too, not just name/skills/bio.
            attributes_as_text = cast(TalentProfile.attributes, String)
            match_conditions = []
            score_terms = []
            for token in tokens:
                pattern = f"%{token}%"
                name_match = TalentProfile.display_name.ilike(pattern)
                skills_match = skills_as_text.ilike(pattern)
                category_match = TalentProfile.category.ilike(pattern) | categories_as_text.ilike(pattern)
                bio_match = TalentProfile.bio.ilike(pattern)
                instruments_match = instruments_as_text.ilike(pattern)
                attributes_match = attributes_as_text.ilike(pattern)
                match_conditions.extend(
                    [name_match, skills_match, category_match, bio_match, instruments_match, attributes_match]
                )
                # Weight matches by field relevance: name and skills matter most for finding the right talent.
                score_terms.append(case((name_match, 3), else_=0))
                score_terms.append(case((skills_match, 3), else_=0))
                score_terms.append(case((category_match, 2), else_=0))
                score_terms.append(case((instruments_match, 2), else_=0))
                score_terms.append(case((attributes_match, 1), else_=0))
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
        .filter(TalentProfile.categories.op("&&")(list(categories)), TalentProfile.job_alert_emails.is_(True))
        .all()
    )


def list_featured_talent(db: Session, limit: int) -> list[TalentProfile]:
    """A capped, rotating "Featured talent" carousel — premium + verified talent only, ordered
    by a hash of (talent id, ISO week number). This gives a stable-for-the-week, changes-next-
    week rotation with zero cron/scheduler needed (the app has none), unlike the uncapped
    `tier_boost` sort in list_talent_profiles() which just puts every premium talent first.
    """
    rotation_key = func.md5(func.concat(cast(TalentProfile.id, String), func.to_char(func.now(), "IYYY-IW")))
    return (
        db.query(TalentProfile)
        .filter(TalentProfile.tier == "premium", TalentProfile.is_verified.is_(True))
        .order_by(rotation_key)
        .limit(limit)
        .all()
    )


def list_new_arrivals(db: Session, categories: set[str], hours: int = 48) -> list[TalentProfile]:
    """A curated early-look feed for premium recruiters — deliberately additive, not
    exclusionary: new talent are still fully visible everywhere else (normal browse/search)
    from the moment they sign up, this just surfaces them here too before the window elapses.
    """
    if not categories:
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return (
        db.query(TalentProfile)
        .filter(TalentProfile.categories.op("&&")(list(categories)), TalentProfile.created_at >= cutoff)
        .order_by(TalentProfile.created_at.desc())
        .all()
    )


def create_talent_profile(db: Session, user_id: uuid.UUID, profile_in: TalentProfileCreate) -> TalentProfile:
    data = profile_in.model_dump()
    categories = data.pop("categories")
    data.pop("category", None)
    profile = TalentProfile(user_id=user_id, category=categories[0], categories=categories, **data)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_talent_profile(db: Session, profile: TalentProfile, profile_in: TalentProfileUpdate) -> TalentProfile:
    data = profile_in.model_dump(exclude_unset=True)
    # `category` (the primary category) is derived from categories[0] so every other place
    # that filters/matches on a single scalar category stays correct. `category` (singular)
    # is still accepted as a legacy update path — mirrored into `categories` when it's the
    # only one given.
    legacy_category = data.pop("category", None)
    categories = data.get("categories")
    if categories:
        profile.category = categories[0]
    elif legacy_category is not None:
        profile.category = legacy_category
        profile.categories = [legacy_category]

    for field, value in data.items():
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
