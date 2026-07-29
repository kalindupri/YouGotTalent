import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.availability_window import AvailabilityWindow
from app.models.booking import Booking
from app.schemas.booking import BookingCreate


def _attach_summary_fields(booking: Booking) -> Booking:
    booking.talent_display_name = booking.talent.display_name
    booking.recruiter_company_name = booking.recruiter.company_name
    booking.casting_call_title = booking.casting_call.title if booking.casting_call else None
    return booking


def get_booking(db: Session, booking_id: uuid.UUID) -> Booking | None:
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    return _attach_summary_fields(booking) if booking else None


def list_bookings_for_talent(db: Session, talent_id: uuid.UUID) -> list[Booking]:
    bookings = db.query(Booking).filter(Booking.talent_id == talent_id).order_by(Booking.start_at.asc()).all()
    return [_attach_summary_fields(b) for b in bookings]


def list_bookings_for_recruiter(db: Session, recruiter_id: uuid.UUID) -> list[Booking]:
    bookings = db.query(Booking).filter(Booking.recruiter_id == recruiter_id).order_by(Booking.start_at.asc()).all()
    return [_attach_summary_fields(b) for b in bookings]


def slot_within_availability(db: Session, talent_id: uuid.UUID, booking_in: BookingCreate) -> bool:
    if booking_in.start_at.date() != booking_in.end_at.date():
        return False
    day_of_week = booking_in.start_at.weekday()
    windows = (
        db.query(AvailabilityWindow)
        .filter(AvailabilityWindow.talent_id == talent_id, AvailabilityWindow.day_of_week == day_of_week)
        .all()
    )
    start_time, end_time = booking_in.start_at.time(), booking_in.end_at.time()
    return any(w.start_time <= start_time and end_time <= w.end_time for w in windows)


def has_overlapping_booking(db: Session, talent_id: uuid.UUID, booking_in: BookingCreate) -> bool:
    conflicting = (
        db.query(Booking)
        .filter(
            Booking.talent_id == talent_id,
            Booking.status.in_(["pending", "accepted"]),
            Booking.start_at < booking_in.end_at,
            Booking.end_at > booking_in.start_at,
        )
        .first()
    )
    return conflicting is not None


def create_booking(db: Session, talent_id: uuid.UUID, recruiter_id: uuid.UUID, booking_in: BookingCreate) -> Booking:
    booking = Booking(
        talent_id=talent_id,
        recruiter_id=recruiter_id,
        casting_call_id=booking_in.casting_call_id,
        start_at=booking_in.start_at,
        end_at=booking_in.end_at,
        message=booking_in.message,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return _attach_summary_fields(booking)


def update_booking_status(db: Session, booking: Booking, status: str) -> Booking:
    booking.status = status
    if status == "accepted":
        booking.agreement_status = "pending"
    db.commit()
    db.refresh(booking)
    return _attach_summary_fields(booking)


def mark_agreement_signed(db: Session, booking: Booking, document_url: str | None) -> Booking:
    booking.agreement_status = "signed"
    booking.agreement_document_url = document_url
    db.commit()
    db.refresh(booking)
    return _attach_summary_fields(booking)
