import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_recruiter_profile, get_current_talent_profile, get_current_user
from app.core.config import settings
from app.core.email import send_email
from app.core.sanitize import sanitize_contract_html
from app.crud.availability import (
    create_availability_window,
    delete_availability_window,
    get_availability_window,
    list_availability_for_talent,
)
from app.crud.application import get_application
from app.crud.booking import (
    create_booking,
    get_booking,
    has_overlapping_booking,
    has_pending_offer_for_application,
    list_bookings_for_recruiter,
    list_bookings_for_talent,
    sign_agreement,
    slot_within_availability,
    update_booking_status,
)
from app.crud.casting_call import get_casting_call
from app.crud.notification import create_notification
from app.crud.review import create_review
from app.crud.talent_profile import get_talent_profile
from app.db.session import get_db
from app.models.recruiter_profile import RecruiterProfile
from app.core.talent_eligibility import (
    GUARDIAN_MUST_SIGN_DETAIL,
    is_adult,
    require_engageable,
    require_working_age,
)
from app.crud.guardian_consent import get_latest_for_profile
from app.models.guardian_consent import GuardianConsentStatus
from app.models.talent_profile import TalentProfile
from app.models.user import User
from app.schemas.availability import AvailabilityWindowCreate, AvailabilityWindowRead
from app.schemas.booking import BookingAgreementSign, BookingCreate, BookingRead, BookingStatusUpdate
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

    # An unconsented minor's calendar is a discovery surface like any other.
    require_engageable(talent)
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
    # Before any of the offer/availability branching below, so it covers both shapes this
    # endpoint serves: a paid offer against an application, and a standalone session booking.
    require_engageable(talent)
    require_working_age(talent)

    is_offer = booking_in.application_id is not None
    if is_offer:
        application = get_application(db, booking_in.application_id)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        call = get_casting_call(db, application.casting_call_id)
        if call is None or call.recruiter_id != recruiter.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your casting call")
        if application.talent_id != talent_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This application doesn't belong to this talent")
        if has_pending_offer_for_application(db, booking_in.application_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An offer is already pending for this application")
        if booking_in.contract_content:
            booking_in.contract_content = sanitize_contract_html(booking_in.contract_content)
    else:
        # An offer is a hire/contract agreement, not a calendar slot — only a standalone
        # booking request needs to fit the talent's declared availability.
        if not slot_within_availability(db, talent_id, booking_in):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That time is outside this talent's availability")
        if has_overlapping_booking(db, talent_id, booking_in):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That time overlaps an existing booking")

    booking = create_booking(db, talent_id, recruiter.id, booking_in)

    if is_offer:
        subject = f"{recruiter.company_name} sent you a contract offer for {call.title}"
        email_body = (
            f"{recruiter.company_name} sent you a contract offer for \"{call.title}\".\n\n"
            f"Review and sign it here: {settings.FRONTEND_URL}/dashboard"
        )
        notification_body = f"Review the contract for \"{call.title}\" and sign to accept."
        notification_type = "offer_sent"
    else:
        subject = f"{recruiter.company_name} requested to book a session with you"
        email_body = (
            f"{recruiter.company_name} requested a booking from {booking.start_at} to {booking.end_at}.\n\n"
            f"Respond here: {settings.FRONTEND_URL}/dashboard"
        )
        notification_body = f"Requested from {booking.start_at} to {booking.end_at}."
        notification_type = "booking_requested"

    background_tasks.add_task(send_email, talent.user.email, subject, email_body)
    create_notification(db, talent.user_id, notification_type, subject, notification_body, "/dashboard")
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

    is_offer = updated.application_id is not None
    thing = "contract offer" if is_offer else "booking request"
    detail = "" if is_offer else f" for {updated.start_at}"
    background_tasks.add_task(
        send_email,
        updated.recruiter.user.email,
        f"{talent.display_name} {status_in.status} your {thing}",
        f"{talent.display_name} {status_in.status} your {thing}{detail}.\n\n"
        f"View it here: {settings.FRONTEND_URL}/dashboard",
    )
    create_notification(
        db,
        updated.recruiter.user_id,
        "booking_responded",
        f"{talent.display_name} {status_in.status} your {thing}",
        f"For your {thing}{detail}.",
        "/dashboard",
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


def _names_match(signature: str, guardian_name: str) -> bool:
    """Compare a typed signature to the registered guardian's name, ignoring case and stray
    whitespace -- someone typing their own name shouldn't be defeated by a double space.
    """
    return " ".join(signature.split()).casefold() == " ".join(guardian_name.split()).casefold()


@router.patch("/bookings/{booking_id}/agreement/sign", response_model=BookingRead)
def sign_booking_agreement(
    booking_id: uuid.UUID,
    agreement_in: BookingAgreementSign,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    booking = get_booking(db, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.talent.user_id == user.id:
        party = "talent"
    elif booking.recruiter.user_id == user.id:
        party = "recruiter"
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.status != "accepted" or booking.agreement_status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No pending agreement to sign for this booking")
    if (party == "talent" and booking.talent_signed_at) or (party == "recruiter" and booking.recruiter_signed_at):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You've already signed this agreement")

    if party == "talent":
        # Re-checked at signing, not just when the offer was sent: the date of birth may have
        # been corrected in between, and this is the moment the engagement becomes binding.
        require_working_age(booking.talent, own=True)
        if not is_adult(booking.talent):
            consent = get_latest_for_profile(db, booking.talent_id)
            approved = consent is not None and consent.status == GuardianConsentStatus.APPROVED.value
            signed_by_guardian = (
                agreement_in.signed_as_guardian
                and approved
                and _names_match(agreement_in.signature_name, consent.guardian_full_name)
            )
            if not signed_by_guardian:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=GUARDIAN_MUST_SIGN_DETAIL)

    updated = sign_agreement(db, booking, party, agreement_in.signature_name)

    # Fully signed AND this booking is an offer against a specific application — sign_agreement
    # already flipped that Application to ACCEPTED; this is the acceptance notice for it,
    # reusing the same copy pattern applications.py uses for its own status-change emails.
    if updated.agreement_status == "signed" and updated.application_id is not None:
        application = updated.application
        call = application.casting_call if application else None
        if application is not None and call is not None:
            background_tasks.add_task(
                send_email,
                application.talent.user.email,
                f"Your application for {call.title} was accepted",
                f"Both parties have signed the contract for \"{call.title}\" — your application is now accepted.\n\n"
                f"View it here: {settings.FRONTEND_URL}/casting-calls/{call.id}",
            )
            create_notification(
                db,
                application.talent.user_id,
                "application_status_changed",
                f"Your application for {call.title} was accepted",
                "Both parties have signed the contract.",
                f"/casting-calls/{call.id}",
            )
    return updated


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
