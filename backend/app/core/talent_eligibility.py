"""Whether a talent can be shown to recruiters, and whether they can be engaged for paid work.

Two independent rules, from two different laws:

  * Under 18 (PDPA)  -- a guardian must have consented before the profile is discoverable or
    contactable at all. Their data is a special category.
  * Under 16 (EWYPCA) -- Sri Lanka's minimum age of employment. They may hold a profile, but
    cannot be offered or booked for paid work.

Plain functions rather than FastAPI dependencies, because the subject is *the talent being
engaged*, which the handler has already loaded -- and because bulk invite needs a per-talent
decision inside a loop, which a request-level dependency cannot express.
"""
from fastapi import HTTPException, status

from app.core.age import calculate_age
from app.core.config import settings
from app.models.guardian_consent import GuardianConsentStatus
from app.models.talent_profile import TalentProfile

CONSENT_PENDING_DETAIL = (
    "This talent is under 18 and their guardian hasn't completed consent yet. "
    "They'll become contactable once that's approved."
)
UNDER_WORKING_AGE_DETAIL = (
    "Sri Lankan law sets the minimum working age at {age}. This talent can't be booked or "
    "offered paid work yet, but you can still follow their profile."
)
OWN_CONSENT_PENDING_DETAIL = (
    "Your guardian consent is still being reviewed. You'll be able to apply once it's "
    "approved — we'll email you as soon as it is."
)
OWN_UNDER_WORKING_AGE_DETAIL = (
    "You need to be at least {age} to apply for paid work in Sri Lanka. Keep building your "
    "profile — we'll let you know the moment you're eligible."
)
GUARDIAN_MUST_SIGN_DETAIL = "A contract for a talent under 18 must be signed by their registered guardian."


def is_adult(profile: TalentProfile) -> bool:
    """False when the date of birth is unknown -- an unknown age is never treated as an adult."""
    if profile.date_of_birth is None:
        return False
    return calculate_age(profile.date_of_birth) >= settings.GUARDIAN_CONSENT_AGE


def is_engageable(profile: TalentProfile) -> bool:
    """Discoverable and contactable: an adult, or a minor whose guardian consent is approved.

    Age is tested *before* the stored status, so a talent becomes engageable the moment they
    turn 18 with no scheduler and no reconciliation pass -- which matters, because a recruiter
    browsing never triggers anything that would update the denormalized column.
    """
    if is_adult(profile):
        return True
    if profile.date_of_birth is None:
        return False  # unknown age -- fail closed
    return profile.guardian_consent_status == GuardianConsentStatus.APPROVED.value


def is_working_age(profile: TalentProfile) -> bool:
    if profile.date_of_birth is None:
        return False  # unknown age -- fail closed
    return calculate_age(profile.date_of_birth) >= settings.MINIMUM_WORKING_AGE


def require_engageable(profile: TalentProfile, *, own: bool = False) -> None:
    if not is_engageable(profile):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=OWN_CONSENT_PENDING_DETAIL if own else CONSENT_PENDING_DETAIL,
        )


def require_working_age(profile: TalentProfile, *, own: bool = False) -> None:
    template = OWN_UNDER_WORKING_AGE_DETAIL if own else UNDER_WORKING_AGE_DETAIL
    if not is_working_age(profile):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=template.format(age=settings.MINIMUM_WORKING_AGE),
        )


def needs_guardian_consent(profile: TalentProfile) -> bool:
    """A minor whose consent isn't approved -- used to decide what to show the guardian."""
    return not is_adult(profile) and profile.guardian_consent_status != GuardianConsentStatus.APPROVED.value
