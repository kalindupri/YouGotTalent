import uuid

from sqlalchemy.orm import Session

from app.models.invitation import Invitation
from app.schemas.invitation import InvitationCreate


def get_invitation(db: Session, invitation_id: uuid.UUID) -> Invitation | None:
    return db.query(Invitation).filter(Invitation.id == invitation_id).first()


def list_invitations_for_talent(db: Session, talent_id: uuid.UUID) -> list[Invitation]:
    return db.query(Invitation).filter(Invitation.talent_id == talent_id).order_by(Invitation.created_at.desc()).all()


def list_invitations_for_casting_call(db: Session, casting_call_id: uuid.UUID) -> list[Invitation]:
    return db.query(Invitation).filter(Invitation.casting_call_id == casting_call_id).all()


def create_invitation(db: Session, casting_call_id: uuid.UUID, recruiter_id: uuid.UUID, invitation_in: InvitationCreate) -> Invitation:
    invitation = Invitation(
        casting_call_id=casting_call_id,
        recruiter_id=recruiter_id,
        talent_id=invitation_in.talent_id,
        message=invitation_in.message,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


def update_invitation_status(db: Session, invitation: Invitation, status: str) -> Invitation:
    invitation.status = status
    db.commit()
    db.refresh(invitation)
    return invitation
