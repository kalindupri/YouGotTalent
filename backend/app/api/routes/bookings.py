import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_recruiter_profile, get_current_talent_profile, get_current_user
from app.core.config import settings
from app.core.email import send_email
from app.crud.availability import (
    create_availability_window,
    delete_availability_window,
    get_availability_window,
    list_availability_for_talent,
)
from app.crud.booking import (
    create_booking,
    get_booking,
    has_overlapping_booking,
    list_bookings_for_recruiter,
    list_bookings_for_talent,
    mark_agreement_signed,
    slot_within_availability,
    update_booking_status,
)
from app.crud.review import create_review
from app.crud.talent_profile import get_talent_profile
from app.db.session import get_db
from app.models.recruiter_profile import RecruiterProfile
from app.models.talent_profile import TalentProfile
from app.models.user import User
from app.schemas.availability import AvailabilityWindowCreate, AvailabilityWindowRead
from app.schemas.booking import BookingAgreementUpdate, BookingCreate, BookingRead, BookingStatusUpdate
from app.schemas.review import ReviewCreate, ReviewRead

router = APIRouter(tags=["bookings"])


@router.get("/talents/me/availability", response_model=list[AvailabilityWindowRead])
def read_my_availability(db: Session = Depends(get_db), talent: TalentProfile = Depends(get_current_talent_profile)):
    return list_availability_for_talent(db, talent.id)


@router.post("/talents/me/availability", response_model=AvailabilityWindowRead, status_code=status.HTTP_201_CREATED)
def add_my_availability(
    window_in: AvailabilityWindowCreate,
    db: Session = Depends(get_db),
    talent: TalentProfile = Depends(get_current_talent_profile),
):
    return create_availability_window(db, talent.id, window_in)


@router.delete("/talents/me/availability/{window_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_my_availability(
    window_id: uuid.UUID,
    db: Session = Depends(get_db),
    talent: TalentProfile = Depends(get_current_talent_profile),
):
    window = get_availability_window(db, window_id)
    if window is None or window.talent_id != talent.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability window not found")
    delete_availability_window(db, window)


@router.get("/talents/{talent_id}/availability", response_model=list[AvailabilityWindowRead])
def read_talent_availability(talent_id: uuid.UUID, db: Session = Depends(get_db)):
    talent = get_talent_profile(db, talent_id)
    if talent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent profile not found")
    return list_availability_for_talent(db, talent_id)


@router.post("/talents/{talent_id}/bookings", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def request_booking(
    talent_id: uuid.UUID,
    booking_in: BookingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    talent = get_talent_profile(db, talent_id)
    if talent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent profile not found")
    if not slot_within_availability(db, talent_id, booking_in):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That time is outside this talent's availability")
    if has_overlapping_booking(db, talent_id, booking_in):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That time overlaps an existing booking")

    booking = create_booking(db, talent_id, recruiter.id, booking_in)

    background_tasks.add_task(
        send_email,
        talent.user.email,
        f"{recruiter.company_name} requested to book a session with you",
        f"{recruiter.company_name} requested a booking from {booking.start_at} to {booking.end_at}.\n\n"
        f"Respond here: {settings.FRONTEND_URL}/dashboard",
    )
    return booking


@router.get("/talents/me/bookings", response_model=list[BookingRead])
def read_my_bookings_as_talent(db: Session = Depends(get_db), talent: TalentProfile = Depends(get_current_talent_profile)):
    return list_bookings_for_talent(db, talent.id)


@router.get("/recruiters/me/bookings", response_model=list[BookingRead])
def read_my_bookings_as_recruiter(
    db: Session = Depends(get_db), recruiter: RecruiterProfile = Depends(get_current_recruiter_profile)
):
    return list_bookings_for_recruiter(db, recruiter.id)


@router.patch("/bookings/{booking_id}/respond", response_model=BookingRead)
def respond_to_booking(
    booking_id: uuid.UUID,
    status_in: BookingStatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    talent: TalentProfile = Depends(get_current_talent_profile),
):
    booking = get_booking(db, booking_id)
    if booking is None or booking.talent_id != talent.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This booking has already been responded to")
    if status_in.status not in ("accepted", "declined"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be 'accepted' or 'declined'")

    updated = update_booking_status(db, booking, status_in.status)

    background_tasks.add_task(
        send_email,
        updated.recruiter.user.email,
        f"{talent.display_name} {status_in.status} your booking request",
        f"{talent.display_name} {status_in.status} your booking request for {updated.start_at}.\n\n"
        f"View it here: {settings.FRONTEND_URL}/dashboard",
    )
    return updated


@router.patch("/bookings/{booking_id}/cancel", response_model=BookingRead)
def cancel_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    booking = get_booking(db, booking_id)
    if booking is None or booking.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only a pending request can be cancelled")
    return update_booking_status(db, booking, "cancelled")


@router.patch("/bookings/{booking_id}/agreement", response_model=BookingRead)
def sign_booking_agreement(
    booking_id: uuid.UUID,
    agreement_in: BookingAgreementUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    booking = get_booking(db, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    is_party = booking.talent.user_id == user.id or booking.recruiter.user_id == user.id
    if not is_party:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.status != "accepted" or booking.agreement_status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No pending agreement to sign for this booking")
    return mark_agreement_signed(db, booking, agreement_in.agreement_document_url)


@router.post("/bookings/{booking_id}/reviews", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def leave_review(
    booking_id: uuid.UUID,
    review_in: ReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    booking = get_booking(db, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if user.id == booking.talent.user_id:
        reviewer_role = "talent"
    elif user.id == booking.recruiter.user_id:
        reviewer_role = "recruiter"
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.status != "accepted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You can only review a completed booking")

    try:
        return create_review(db, booking, reviewer_role, review_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You've already reviewed this booking")
