import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.guardian_consent import (
    GuardianConsent,
    GuardianConsentDocument,
    GuardianConsentEvent,
    GuardianConsentStatus,
)
from app.models.talent_profile import TalentProfile


def get_consent(db: Session, consent_id: uuid.UUID) -> GuardianConsent | None:
    return db.query(GuardianConsent).filter(GuardianConsent.id == consent_id).first()


def get_latest_for_profile(db: Session, talent_profile_id: uuid.UUID) -> GuardianConsent | None:
    return (
        db.query(GuardianConsent)
        .filter(GuardianConsent.talent_profile_id == talent_profile_id)
        .order_by(GuardianConsent.created_at.desc())
        .first()
    )


def list_by_status(db: Session, status: str) -> list[GuardianConsent]:
    # Oldest first: a guardian waiting on review shouldn't be overtaken by later submissions.
    return (
        db.query(GuardianConsent)
        .filter(GuardianConsent.status == status)
        .order_by(GuardianConsent.submitted_at.asc().nullslast())
        .all()
    )


def get_document(db: Session, document_id: uuid.UUID) -> GuardianConsentDocument | None:
    return db.query(GuardianConsentDocument).filter(GuardianConsentDocument.id == document_id).first()


def _record_event(
    db: Session,
    consent: GuardianConsent,
    *,
    from_status: str | None,
    to_status: str,
    actor_user_id: uuid.UUID | None,
    reason: str | None = None,
) -> None:
    db.add(
        GuardianConsentEvent(
            guardian_consent_id=consent.id,
            from_status=from_status,
            to_status=to_status,
            actor_user_id=actor_user_id,
            reason=reason,
        )
    )


def submit_consent(
    db: Session,
    profile: TalentProfile,
    *,
    guardian_user_id: uuid.UUID,
    guardian_full_name: str,
    guardian_relationship: str,
    guardian_email: str | None,
    guardian_phone: str | None,
    minor_full_name: str,
    consented_scopes: list[str],
    consent_statement: str,
    terms_version: str,
    privacy_version: str,
    ip_address: str | None,
    user_agent: str | None,
    documents: list[tuple[str, str, str, int, str | None, bytes]],
) -> GuardianConsent:
    """Create a submitted consent record with its proof documents.

    `documents` is a list of (doc_type, storage_key, content_type, size_bytes, filename, data);
    `data` is used only to fingerprint the file -- the bytes themselves are already stored
    privately by the caller.
    """
    consent = GuardianConsent(
        talent_profile_id=profile.id,
        guardian_user_id=guardian_user_id,
        guardian_full_name=guardian_full_name,
        guardian_relationship=guardian_relationship,
        guardian_email=guardian_email,
        guardian_phone=guardian_phone,
        minor_full_name=minor_full_name,
        minor_date_of_birth=profile.date_of_birth,
        status=GuardianConsentStatus.SUBMITTED.value,
        consented_scopes=consented_scopes,
        consent_statement=consent_statement,
        terms_version=terms_version,
        privacy_version=privacy_version,
        ip_address=ip_address,
        user_agent=user_agent,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(consent)
    db.flush()

    for doc_type, storage_key, content_type, size_bytes, filename, data in documents:
        db.add(
            GuardianConsentDocument(
                guardian_consent_id=consent.id,
                doc_type=doc_type,
                storage_key=storage_key,
                content_type=content_type,
                size_bytes=size_bytes,
                original_filename=filename,
                sha256=hashlib.sha256(data).hexdigest(),
            )
        )

    _record_event(
        db,
        consent,
        from_status=profile.guardian_consent_status,
        to_status=GuardianConsentStatus.SUBMITTED.value,
        actor_user_id=guardian_user_id,
    )
    profile.guardian_consent_status = GuardianConsentStatus.SUBMITTED.value
    db.commit()
    db.refresh(consent)
    return consent


def decide(
    db: Session,
    consent: GuardianConsent,
    profile: TalentProfile,
    *,
    approved: bool,
    reviewer_user_id: uuid.UUID,
    reason: str | None,
) -> GuardianConsent:
    """Approve or reject, updating the record, the audit trail and the denormalized status on
    the profile in one transaction so they can never disagree.
    """
    new_status = GuardianConsentStatus.APPROVED.value if approved else GuardianConsentStatus.REJECTED.value
    _record_event(
        db,
        consent,
        from_status=consent.status,
        to_status=new_status,
        actor_user_id=reviewer_user_id,
        reason=reason,
    )
    consent.status = new_status
    consent.reviewed_at = datetime.now(timezone.utc)
    consent.reviewed_by_user_id = reviewer_user_id
    consent.decision_reason = reason
    profile.guardian_consent_status = new_status
    db.commit()
    db.refresh(consent)
    return consent


def revoke(db: Session, consent: GuardianConsent, profile: TalentProfile, *, actor_user_id: uuid.UUID, reason: str | None) -> GuardianConsent:
    _record_event(
        db,
        consent,
        from_status=consent.status,
        to_status=GuardianConsentStatus.REVOKED.value,
        actor_user_id=actor_user_id,
        reason=reason,
    )
    consent.status = GuardianConsentStatus.REVOKED.value
    consent.revoked_at = datetime.now(timezone.utc)
    consent.revoked_reason = reason
    profile.guardian_consent_status = GuardianConsentStatus.REVOKED.value
    db.commit()
    db.refresh(consent)
    return consent


def mark_required(db: Session, profile: TalentProfile) -> None:
    """Flag a newly created minor's profile as needing consent before it goes anywhere."""
    profile.guardian_consent_status = GuardianConsentStatus.REQUIRED.value
    db.commit()
