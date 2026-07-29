import uuid

from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.models.casting_call import CastingCall
from app.models.casting_call_role import CastingCallRole
from app.models.talent_profile import TalentCategory
from app.schemas.casting_call import CastingCallCreate


def get_casting_call(db: Session, casting_call_id: uuid.UUID) -> CastingCall | None:
    return db.query(CastingCall).filter(CastingCall.id == casting_call_id).first()


def increment_view_count(db: Session, call: CastingCall) -> CastingCall:
    call.view_count += 1
    db.commit()
    db.refresh(call)
    return call


def list_casting_calls(db: Session, category: TalentCategory | None, skip: int, limit: int) -> list[CastingCall]:
    query = db.query(CastingCall)
    if category:
        query = query.filter(CastingCall.category == category)
    return query.order_by(CastingCall.created_at.desc()).offset(skip).limit(limit).all()


def create_casting_call(db: Session, recruiter_id: uuid.UUID, call_in: CastingCallCreate) -> CastingCall:
    data = call_in.model_dump()
    roles_in = data.pop("roles")
    call = CastingCall(recruiter_id=recruiter_id, **data)
    call.roles = [CastingCallRole(**role) for role in roles_in]
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


def get_recruiter_analytics(db: Session, recruiter_id: uuid.UUID) -> dict:
    calls = db.query(CastingCall).filter(CastingCall.recruiter_id == recruiter_id).order_by(CastingCall.created_at.desc()).all()

    call_analytics = []
    total_applications = 0
    total_non_pending = 0
    for call in calls:
        applications = db.query(Application).filter(Application.casting_call_id == call.id).all()
        pending = sum(1 for a in applications if a.status == ApplicationStatus.PENDING)
        shortlisted = sum(1 for a in applications if a.status == ApplicationStatus.SHORTLISTED)
        accepted = sum(1 for a in applications if a.status == ApplicationStatus.ACCEPTED)
        rejected = sum(1 for a in applications if a.status == ApplicationStatus.REJECTED)
        total_applications += len(applications)
        total_non_pending += len(applications) - pending
        call_analytics.append(
            {
                "id": call.id,
                "title": call.title,
                "status": call.status,
                "view_count": call.view_count,
                "application_count": len(applications),
                "pending_count": pending,
                "shortlisted_count": shortlisted,
                "accepted_count": accepted,
                "rejected_count": rejected,
            }
        )

    return {
        "total_views": sum(c.view_count for c in calls),
        "total_applications": total_applications,
        "response_rate": round((total_non_pending / total_applications) * 100, 1) if total_applications else 0.0,
        "casting_calls": call_analytics,
    }
