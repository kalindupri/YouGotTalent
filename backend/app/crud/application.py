import uuid

from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.schemas.application import ApplicationCreate


def get_application(db: Session, application_id: uuid.UUID) -> Application | None:
    return db.query(Application).filter(Application.id == application_id).first()


def list_applications_for_casting_call(db: Session, casting_call_id: uuid.UUID) -> list[Application]:
    return db.query(Application).filter(Application.casting_call_id == casting_call_id).all()


def list_applications_for_talent(db: Session, talent_id: uuid.UUID) -> list[Application]:
    return db.query(Application).filter(Application.talent_id == talent_id).all()


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
    return application


def update_application_status(db: Session, application: Application, status: ApplicationStatus) -> Application:
    application.status = status
    db.commit()
    db.refresh(application)
    return application
