import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_recruiter_profile, get_current_talent_profile
from app.core.config import settings
from app.core.email import send_email
from app.crud.casting_call import get_casting_call
from app.crud.invitation import (
    create_invitation,
    get_invitation,
    list_invitations_for_casting_call,
    list_invitations_for_talent,
    update_invitation_status,
)
from app.crud.talent_profile import get_talent_profile
from app.db.session import get_db
from app.models.invitation import INVITATION_STATUSES
from app.models.recruiter_profile import RecruiterProfile
from app.models.talent_profile import TalentProfile
from app.schemas.invitation import InvitationCreate, InvitationRead, InvitationStatusUpdate

router = APIRouter(tags=["invitations"])


@router.post("/casting-calls/{casting_call_id}/invitations", response_model=InvitationRead, status_code=status.HTTP_201_CREATED)
def invite_talent_to_casting_call(
    casting_call_id: uuid.UUID,
    invitation_in: InvitationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    call = get_casting_call(db, casting_call_id)
    if call is None or call.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Casting call not found")
    talent = get_talent_profile(db, invitation_in.talent_id)
    if talent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent profile not found")

    try:
        invitation = create_invitation(db, casting_call_id, recruiter.id, invitation_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You've already invited this talent to this role")

    background_tasks.add_task(
        send_email,
        talent.user.email,
        f"You've been invited to audition for {call.title}",
        f"{recruiter.company_name} invited you to audition for \"{call.title}\".\n\n"
        f"View the invitation here: {settings.FRONTEND_URL}/dashboard",
    )
    return invitation


@router.get("/casting-calls/{casting_call_id}/invitations", response_model=list[InvitationRead])
def list_casting_call_invitations(
    casting_call_id: uuid.UUID,
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    call = get_casting_call(db, casting_call_id)
    if call is None or call.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Casting call not found")
    return list_invitations_for_casting_call(db, casting_call_id)


@router.get("/talents/me/invitations", response_model=list[InvitationRead])
def list_my_invitations(
    db: Session = Depends(get_db),
    talent: TalentProfile = Depends(get_current_talent_profile),
):
    return list_invitations_for_talent(db, talent.id)


@router.patch("/invitations/{invitation_id}", response_model=InvitationRead)
def respond_to_invitation(
    invitation_id: uuid.UUID,
    status_in: InvitationStatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    talent: TalentProfile = Depends(get_current_talent_profile),
):
    invitation = get_invitation(db, invitation_id)
    if invitation is None or invitation.talent_id != talent.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    if status_in.status not in (s for s in INVITATION_STATUSES if s != "pending"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be 'accepted' or 'declined'")
    updated = update_invitation_status(db, invitation, status_in.status)

    background_tasks.add_task(
        send_email,
        invitation.recruiter.user.email,
        f"{talent.display_name} {status_in.status} your invitation",
        f"{talent.display_name} {status_in.status} your invitation to audition for \"{invitation.casting_call.title}\".\n\n"
        f"View it here: {settings.FRONTEND_URL}/dashboard/casting-calls/{invitation.casting_call_id}",
    )
    return updated
