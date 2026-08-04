import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.schemas.application import ApplicationCreate


def get_application(db: Session, application_id: uuid.UUID) -> Application | None:
    return db.query(Application).filter(Application.id == application_id).first()


def _compute_match_score(application: Application) -> int:
    """Rule-based fit score (0-100) against the role's category, free-text criteria, and the
    talent's declared experience — no external AI call, just a weighted heuristic recruiters
    can use to sort applicants by relevance instead of application order.
    """
    talent = application.talent
    role = application.role
    call = application.casting_call

    score = 0

    role_category = role.category or call.category
    if role_category and talent.category == role_category:
        score += 40

    criteria_text = f"{role.title} {role.criteria or ''}".lower()
    matched_skills = [s for s in (talent.skills or []) if s and s.lower() in criteria_text]
    score += min(len(matched_skills) * 10, 40)

    if talent.experience_years:
        score += min(talent.experience_years * 2, 20)

    return min(score, 100)


def list_applications_for_casting_call(db: Session, casting_call_id: uuid.UUID, *, score: bool = False) -> list[Application]:
    applications = db.query(Application).filter(Application.casting_call_id == casting_call_id).all()
    unseen = [a for a in applications if a.viewed_at is None]
    if unseen:
        now = datetime.now(timezone.utc)
        for application in unseen:
            application.viewed_at = now
        db.commit()

    for application in applications:
        application.match_score = _compute_match_score(application) if score else None
    if score:
        applications.sort(key=lambda a: a.match_score, reverse=True)
    return applications


def list_applications_for_talent(db: Session, talent_id: uuid.UUID) -> list[Application]:
    applications = db.query(Application).filter(Application.talent_id == talent_id).all()
    for application in applications:
        application.match_score = None
    return applications


def create_application(db: Session, casting_call_id: uuid.UUID, talent_id: uuid.UUID, application_in: ApplicationCreate) -> Application:
    application = Application(
        casting_call_id=casting_call_id,
        role_id=application_in.role_id,
        talent_id=talent_id,
        message=application_in.message,
        submission_url=application_in.submission_url,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    application.match_score = None
    return application


def update_application_status(db: Session, application: Application, status: ApplicationStatus) -> Application:
    application.status = status
    db.commit()
    db.refresh(application)
    application.match_score = None
    return application
