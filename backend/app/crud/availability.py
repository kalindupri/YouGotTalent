import uuid

from sqlalchemy.orm import Session

from app.models.availability_window import AvailabilityWindow
from app.schemas.availability import AvailabilityWindowCreate


def list_availability_for_talent(db: Session, talent_id: uuid.UUID) -> list[AvailabilityWindow]:
    return (
        db.query(AvailabilityWindow)
        .filter(AvailabilityWindow.talent_id == talent_id)
        .order_by(AvailabilityWindow.day_of_week.asc(), AvailabilityWindow.start_time.asc())
        .all()
    )


def get_availability_window(db: Session, window_id: uuid.UUID) -> AvailabilityWindow | None:
    return db.query(AvailabilityWindow).filter(AvailabilityWindow.id == window_id).first()


def create_availability_window(db: Session, talent_id: uuid.UUID, window_in: AvailabilityWindowCreate) -> AvailabilityWindow:
    window = AvailabilityWindow(
        talent_id=talent_id,
        day_of_week=window_in.day_of_week,
        start_time=window_in.start_time,
        end_time=window_in.end_time,
    )
    db.add(window)
    db.commit()
    db.refresh(window)
    return window


def delete_availability_window(db: Session, window: AvailabilityWindow) -> None:
    db.delete(window)
    db.commit()
