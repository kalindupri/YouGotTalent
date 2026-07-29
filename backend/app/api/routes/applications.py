import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_recruiter_profile, get_current_talent_profile
from app.core.config import settings
from app.core.email import send_email
from app.crud.application import (
    create_application,
    get_application,
    list_applications_for_casting_call,
    list_applications_for_talent,
    update_application_status,
)
from app.crud.casting_call import get_casting_call
from app.db.session import get_db
from app.models.recruiter_profile import RecruiterProfile
from app.models.talent_profile import TalentProfile
from app.schemas.application import ApplicationCreate, ApplicationRead, ApplicationStatusUpdate

router = APIRouter(tags=["applications"])


@router.post("/casting-calls/{casting_call_id}/applications", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def apply_to_casting_call(
    casting_call_id: uuid.UUID,
    application_in: ApplicationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    talent: TalentProfile = Depends(get_current_talent_profile),
):
    call = get_casting_call(db, casting_call_id)
    if call is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Casting call not found")
    if not any(r.id == application_in.role_id for r in call.roles):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That role doesn't belong to this casting call")

    try:
        application = create_application(db, casting_call_id, talent.id, application_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You've already applied to this role")

    background_tasks.add_task(
        send_email,
        call.recruiter.user.email,
        f"New application for {call.title}",
        f"{talent.display_name} just applied to your talent hunt \"{call.title}\".\n\n"
        f"Review it here: {settings.FRONTEND_URL}/dashboard/casting-calls/{call.id}",
    )
    return application


@router.get("/casting-calls/{casting_call_id}/applications", response_model=list[ApplicationRead])
def list_casting_call_applications(
    casting_call_id: uuid.UUID,
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    call = get_casting_call(db, casting_call_id)
    if call is None or call.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Casting call not found")
    return list_applications_for_casting_call(db, casting_call_id)


@router.get("/talents/me/applications", response_model=list[ApplicationRead])
def list_my_applications(
    db: Session = Depends(get_db),
    talent: TalentProfile = Depends(get_current_talent_profile),
):
    return list_applications_for_talent(db, talent.id)


@router.patch("/applications/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: uuid.UUID,
    status_in: ApplicationStatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    application = get_application(db, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    call = get_casting_call(db, application.casting_call_id)
    if call is None or call.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your casting call")
    updated = update_application_status(db, application, status_in.status)

    background_tasks.add_task(
        send_email,
        application.talent.user.email,
        f"Your application for {call.title} was updated",
        f"Your application for \"{call.title}\" is now: {status_in.status.value}.\n\n"
        f"View it here: {settings.FRONTEND_URL}/casting-calls/{call.id}",
    )
    return updated