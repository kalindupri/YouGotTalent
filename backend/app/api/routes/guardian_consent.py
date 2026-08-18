"""Guardian-facing consent submission, and the admin review queue."""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_talent_profile, require_admin
from app.core.age import calculate_age
from app.core.config import settings
from app.core.private_storage import upload_private_file
from app.core.security import create_document_token
from app.core.talent_eligibility import is_adult
from app.core.upload_validation import enforce_document_size, sniff_document
from app.crud import guardian_consent as consent_crud
from app.crud.notification import create_notification
from app.crud.talent_profile import get_talent_profile
from app.db.session import get_db
from app.core.email import send_email
from app.models.guardian_consent import CONSENT_SCOPES, DOCUMENT_TYPES, GUARDIAN_RELATIONSHIPS, GuardianConsentStatus
from app.models.talent_profile import TalentProfile
from app.models.user import User
from app.schemas.guardian_consent import (
    AdminGuardianConsentRead,
    DocumentLink,
    GuardianConsentDecision,
    GuardianConsentRead,
    GuardianConsentRejection,
    GuardianConsentRevocation,
)

router = APIRouter(tags=["guardian-consent"])

# Shown to the guardian and stored verbatim on the record, so we can always evidence not just
# that consent was given but exactly what was agreed to.
CONSENT_STATEMENT = (
    "I confirm I am the parent or legal guardian of the young person named above, that the "
    "documents I have uploaded prove that relationship, and that I consent to YouGotTalent "
    "processing their personal data — including their photographs and audition media — for "
    "the purposes I have selected, in line with the Personal Data Protection Act No. 9 of 2022. "
    "I understand I can withdraw this consent at any time."
)


# --- Guardian-facing --------------------------------------------------------------------


@router.get("/talents/me/guardian-consent", response_model=GuardianConsentRead | None)
def read_my_guardian_consent(
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    return consent_crud.get_latest_for_profile(db, profile.id)


@router.post("/talents/me/guardian-consent", response_model=GuardianConsentRead, status_code=status.HTTP_201_CREATED)
def submit_my_guardian_consent(
    request: Request,
    background_tasks: BackgroundTasks,
    guardian_full_name: str = Form(...),
    guardian_relationship: str = Form(...),
    minor_full_name: str = Form(...),
    guardian_email: str | None = Form(default=None),
    guardian_phone: str | None = Form(default=None),
    consented_scopes: list[str] = Form(...),
    agreed: bool = Form(...),
    birth_certificate: UploadFile = File(...),
    guardian_id: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    if is_adult(profile):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This profile belongs to an adult, so guardian consent isn't needed.",
        )
    if not agreed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You must agree to the consent statement.")
    if guardian_relationship not in GUARDIAN_RELATIONSHIPS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select how you're related to the young person.")
    unknown_scopes = set(consented_scopes) - set(CONSENT_SCOPES)
    if unknown_scopes or not consented_scopes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose what you're consenting to.")

    existing = consent_crud.get_latest_for_profile(db, profile.id)
    if existing is not None and existing.status == GuardianConsentStatus.SUBMITTED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A consent request is already under review.")

    stored: list[tuple[str, str, str, int, str | None, bytes]] = []
    for doc_type, upload in (("birth_certificate", birth_certificate), ("guardian_id", guardian_id)):
        if upload is None:
            continue
        data = upload.file.read()
        enforce_document_size(len(data))
        # Type comes from the bytes, never from the filename or the declared content type.
        content_type, extension = sniff_document(data)
        key = upload_private_file(data, extension, content_type)
        stored.append((doc_type, key, content_type, len(data), upload.filename, data))

    consent = consent_crud.submit_consent(
        db,
        profile,
        guardian_user_id=profile.user_id,
        guardian_full_name=guardian_full_name,
        guardian_relationship=guardian_relationship,
        guardian_email=guardian_email,
        guardian_phone=guardian_phone,
        minor_full_name=minor_full_name,
        consented_scopes=consented_scopes,
        consent_statement=CONSENT_STATEMENT,
        terms_version=settings.CONSENT_TERMS_VERSION,
        privacy_version=settings.CONSENT_PRIVACY_VERSION,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        documents=stored,
    )
    return consent


@router.post("/talents/me/guardian-consent/revoke", response_model=GuardianConsentRead)
def revoke_my_guardian_consent(
    body: GuardianConsentRevocation,
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    consent = consent_crud.get_latest_for_profile(db, profile.id)
    if consent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No guardian consent on file.")
    return consent_crud.revoke(db, consent, profile, actor_user_id=profile.user_id, reason=body.reason)


# --- Admin review -----------------------------------------------------------------------


def _to_admin_read(db: Session, consent) -> AdminGuardianConsentRead:
    data = AdminGuardianConsentRead.model_validate(consent)
    data.minor_age = calculate_age(consent.minor_date_of_birth)
    talent = get_talent_profile(db, consent.talent_profile_id)
    data.talent_display_name = talent.display_name if talent else None
    return data


@router.get("/admin/guardian-consents", response_model=list[AdminGuardianConsentRead])
def list_guardian_consents(
    status_filter: str = GuardianConsentStatus.SUBMITTED.value,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return [_to_admin_read(db, c) for c in consent_crud.list_by_status(db, status_filter)]


def _load_for_review(db: Session, consent_id: uuid.UUID):
    consent = consent_crud.get_consent(db, consent_id)
    if consent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent request not found")
    profile = get_talent_profile(db, consent.talent_profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent profile not found")
    return consent, profile


def _notify_guardian(background_tasks: BackgroundTasks, db: Session, profile: TalentProfile, *, approved: bool, reason: str | None) -> None:
    subject = "Guardian consent approved" if approved else "Guardian consent needs attention"
    body = (
        f"The guardian consent for {profile.display_name} has been approved. Their profile is now "
        "visible to talent hunts."
        if approved
        else f"We couldn't approve the guardian consent for {profile.display_name}.\n\nReason: {reason}\n\n"
        "You can submit again with corrected details or documents."
    )
    user = profile.user
    if user is not None:
        background_tasks.add_task(send_email, user.email, subject, body)
    create_notification(db, profile.user_id, "guardian_consent", subject, body, "/dashboard")


@router.post("/admin/guardian-consents/{consent_id}/approve", response_model=AdminGuardianConsentRead)
def approve_guardian_consent(
    consent_id: uuid.UUID,
    body: GuardianConsentDecision,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    consent, profile = _load_for_review(db, consent_id)
    consent_crud.decide(db, consent, profile, approved=True, reviewer_user_id=admin.id, reason=body.note)
    _notify_guardian(background_tasks, db, profile, approved=True, reason=None)
    return _to_admin_read(db, consent)


@router.post("/admin/guardian-consents/{consent_id}/reject", response_model=AdminGuardianConsentRead)
def reject_guardian_consent(
    consent_id: uuid.UUID,
    body: GuardianConsentRejection,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    consent, profile = _load_for_review(db, consent_id)
    consent_crud.decide(db, consent, profile, approved=False, reviewer_user_id=admin.id, reason=body.reason)
    _notify_guardian(background_tasks, db, profile, approved=False, reason=body.reason)
    return _to_admin_read(db, consent)


@router.post("/admin/guardian-consents/{consent_id}/documents/{document_id}/link", response_model=DocumentLink)
def mint_document_link(
    consent_id: uuid.UUID,
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """POST, not GET, so a document link is never created by a prefetch or left in a history
    entry just from navigating the queue.
    """
    document = consent_crud.get_document(db, document_id)
    if document is None or document.guardian_consent_id != consent_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    ttl = settings.DOCUMENT_LINK_TTL_SECONDS
    token = create_document_token(str(document.id), ttl_seconds=ttl)
    return DocumentLink(
        url=f"{settings.BACKEND_PUBLIC_URL}{settings.API_V1_PREFIX}/documents/{document.id}?t={token}",
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl),
    )
