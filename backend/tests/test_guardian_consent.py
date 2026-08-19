"""Guardian consent for under-18 talent, and the two age gates.

Two independent rules being enforced here:
  * under 18 -> a guardian must have consented before the profile is discoverable (PDPA)
  * under 16 -> no paid work at all (Sri Lanka's minimum employment age)
"""
from datetime import timedelta

import pytest

from app.core.age import years_ago
from tests.conftest import ADULT_DOB, auth_headers, register_and_verify

PDF = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\ntest document\n"


def dob_for_age(age: int) -> str:
    """A date of birth making someone comfortably `age` years old (not on the boundary)."""
    return (years_ago(age) - timedelta(days=30)).isoformat()


def create_profile(client, headers, *, age: int, display_name: str = "Young Talent"):
    resp = client.post(
        "/api/v1/talents/me",
        json={"display_name": display_name, "category": "acting", "date_of_birth": dob_for_age(age)},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def submit_consent(client, headers, *, guardian_name="Nimal Perera", minor_name="Sanduni Perera"):
    return client.post(
        "/api/v1/talents/me/guardian-consent",
        data={
            "guardian_full_name": guardian_name,
            "guardian_relationship": "father",
            "minor_full_name": minor_name,
            "consented_scopes": ["profile_public", "recruiter_contact"],
            "agreed": "true",
        },
        files={"birth_certificate": ("cert.pdf", PDF, "application/pdf")},
        headers=headers,
    )


def approve(client, admin_headers, consent_id):
    return client.post(f"/api/v1/admin/guardian-consents/{consent_id}/approve", json={}, headers=admin_headers)


# --- A minor's profile is hidden until consent is approved ---------------------------------


def test_a_new_minor_profile_starts_needing_consent(client, talent_headers):
    profile = create_profile(client, talent_headers, age=13)
    assert profile["guardian_consent_status"] == "required"


def test_an_adult_profile_needs_no_consent(client, talent_headers):
    profile = create_profile(client, talent_headers, age=30)
    assert profile["guardian_consent_status"] == "not_required"


def test_an_unconsented_minor_is_absent_from_browse(client, talent_headers):
    create_profile(client, talent_headers, age=13, display_name="Hidden Child")
    names = {t["display_name"] for t in client.get("/api/v1/talents").json()}
    assert "Hidden Child" not in names


def test_an_unconsented_minors_public_profile_404s_for_a_guest(client, talent_headers):
    profile = create_profile(client, talent_headers, age=13)
    # 404 rather than 403 -- a 403 would confirm the profile exists to anyone guessing ids.
    assert client.get(f"/api/v1/talents/{profile['id']}").status_code == 404


def test_the_owner_can_still_see_their_own_unconsented_minor_profile(client, talent_headers):
    profile = create_profile(client, talent_headers, age=13)
    assert client.get(f"/api/v1/talents/{profile['id']}", headers=talent_headers).status_code == 200


def test_an_admin_can_still_see_an_unconsented_minor_profile(client, talent_headers, admin_headers):
    profile = create_profile(client, talent_headers, age=13)
    assert client.get(f"/api/v1/talents/{profile['id']}", headers=admin_headers).status_code == 200


# --- The consent lifecycle -----------------------------------------------------------------


def test_submitting_consent_does_not_by_itself_unhide_the_profile(client, talent_headers):
    profile = create_profile(client, talent_headers, age=13, display_name="Pending Child")
    resp = submit_consent(client, talent_headers)
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == "submitted"

    names = {t["display_name"] for t in client.get("/api/v1/talents").json()}
    assert "Pending Child" not in names


def test_approval_makes_the_profile_visible_and_leaves_an_audit_trail(client, db_session, talent_headers, admin_headers):
    from app.models.guardian_consent import GuardianConsentEvent
    from app.models.notification import Notification

    profile = create_profile(client, talent_headers, age=13, display_name="Approved Child")
    consent = submit_consent(client, talent_headers).json()

    resp = approve(client, admin_headers, consent["id"])
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "approved"

    names = {t["display_name"] for t in client.get("/api/v1/talents").json()}
    assert "Approved Child" in names
    assert client.get(f"/api/v1/talents/{profile['id']}").status_code == 200

    events = db_session.query(GuardianConsentEvent).filter(
        GuardianConsentEvent.guardian_consent_id == consent["id"]
    ).all()
    # submitted, then approved -- with an actor on each, unlike the older verification queue.
    assert [e.to_status for e in events] == ["submitted", "approved"]
    assert all(e.actor_user_id is not None for e in events)

    assert db_session.query(Notification).count() >= 1


def test_rejecting_requires_a_reason(client, talent_headers, admin_headers):
    create_profile(client, talent_headers, age=13)
    consent = submit_consent(client, talent_headers).json()

    resp = client.post(f"/api/v1/admin/guardian-consents/{consent['id']}/reject", json={}, headers=admin_headers)
    assert resp.status_code == 422
    resp = client.post(
        f"/api/v1/admin/guardian-consents/{consent['id']}/reject", json={"reason": "short"}, headers=admin_headers
    )
    assert resp.status_code == 422


def test_rejection_records_the_reason_and_keeps_the_profile_hidden(client, talent_headers, admin_headers):
    profile = create_profile(client, talent_headers, age=13, display_name="Rejected Child")
    consent = submit_consent(client, talent_headers).json()

    resp = client.post(
        f"/api/v1/admin/guardian-consents/{consent['id']}/reject",
        json={"reason": "The birth certificate was unreadable."},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
    assert resp.json()["decision_reason"] == "The birth certificate was unreadable."
    assert client.get(f"/api/v1/talents/{profile['id']}").status_code == 404


def test_consent_records_what_was_agreed_to_and_which_wording(client, talent_headers):
    create_profile(client, talent_headers, age=13)
    body = submit_consent(client, talent_headers).json()
    assert body["consented_scopes"] == ["profile_public", "recruiter_contact"]
    assert body["minor_full_name"] == "Sanduni Perera"


def test_an_adult_cannot_submit_guardian_consent(client, talent_headers):
    create_profile(client, talent_headers, age=30)
    assert submit_consent(client, talent_headers).status_code == 400


def test_a_second_submission_while_one_is_under_review_is_refused(client, talent_headers):
    create_profile(client, talent_headers, age=13)
    assert submit_consent(client, talent_headers).status_code == 201
    assert submit_consent(client, talent_headers).status_code == 400


def test_consent_documents_are_never_exposed_as_urls(client, talent_headers, admin_headers):
    create_profile(client, talent_headers, age=13)
    consent = submit_consent(client, talent_headers).json()
    body = client.get("/api/v1/admin/guardian-consents", headers=admin_headers).text
    assert "storage_key" not in body
    assert consent["documents"][0]["content_type"] == "application/pdf"


# --- Turning 18 --------------------------------------------------------------------------


def test_turning_eighteen_takes_effect_immediately_without_any_reconciliation(client, talent_headers):
    """Age is checked before the stored status, so no scheduler is needed -- which matters
    because a recruiter browsing never triggers anything that would update the column.
    """
    resp = client.post(
        "/api/v1/talents/me",
        json={"display_name": "Just Eighteen", "category": "acting", "date_of_birth": years_ago(18).isoformat()},
        headers=talent_headers,
    )
    assert resp.status_code == 201
    # Adult on creation, so consent was never required.
    assert resp.json()["guardian_consent_status"] == "not_required"

    names = {t["display_name"] for t in client.get("/api/v1/talents").json()}
    assert "Just Eighteen" in names


def test_a_minor_who_has_since_turned_eighteen_is_visible_despite_a_stale_status(
    client, db_session, talent_headers
):
    from app.models.talent_profile import TalentProfile

    profile = create_profile(client, talent_headers, age=13, display_name="Now Grown")
    row = db_session.query(TalentProfile).filter(TalentProfile.id == profile["id"]).first()
    # Simulate the passage of time: they are now 18, but nothing ever updated the column.
    row.date_of_birth = years_ago(18)
    db_session.commit()
    assert row.guardian_consent_status == "required"

    names = {t["display_name"] for t in client.get("/api/v1/talents").json()}
    assert "Now Grown" in names


# --- Gate B: the minimum working age ------------------------------------------------------


def test_a_fifteen_year_old_cannot_apply_for_work(client, db_session, talent_headers, admin_headers, casting_call):
    create_profile(client, talent_headers, age=15)
    consent = submit_consent(client, talent_headers).json()
    approve(client, admin_headers, consent["id"])  # consent approved, but still under 16

    role_id = casting_call["roles"][0]["id"]
    resp = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications",
        json={"role_id": role_id, "message": "please"},
        headers=talent_headers,
    )
    assert resp.status_code == 403
    assert "16" in resp.json()["detail"]


def test_a_sixteen_year_old_with_approved_consent_can_apply(client, talent_headers, admin_headers, casting_call):
    create_profile(client, talent_headers, age=16)
    consent = submit_consent(client, talent_headers).json()
    approve(client, admin_headers, consent["id"])

    role_id = casting_call["roles"][0]["id"]
    resp = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications",
        json={"role_id": role_id, "message": "please"},
        headers=talent_headers,
    )
    assert resp.status_code == 201, resp.text


def test_a_fifteen_year_old_cannot_be_booked(client, talent_headers, admin_headers, recruiter_headers, recruiter_profile):
    profile = create_profile(client, talent_headers, age=15)
    consent = submit_consent(client, talent_headers).json()
    approve(client, admin_headers, consent["id"])

    resp = client.post(
        f"/api/v1/talents/{profile['id']}/bookings",
        json={"start_at": "2030-01-01T10:00:00Z", "end_at": "2030-01-01T12:00:00Z", "notes": "shoot"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 403
    assert "16" in resp.json()["detail"]


# --- Gate A applied to contact surfaces ----------------------------------------------------


def test_a_recruiter_cannot_message_an_unconsented_minor(client, talent_headers, recruiter_headers, recruiter_profile):
    profile = create_profile(client, talent_headers, age=13)
    resp = client.post("/api/v1/conversations", json={"talent_id": profile["id"]}, headers=recruiter_headers)
    assert resp.status_code == 403
    assert "guardian" in resp.json()["detail"].lower()


def test_a_recruiter_cannot_invite_an_unconsented_minor(client, talent_headers, recruiter_headers, casting_call):
    profile = create_profile(client, talent_headers, age=13)
    resp = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/invitations",
        json={"talent_id": profile["id"]},
        headers=recruiter_headers,
    )
    assert resp.status_code == 403


# --- Signing a contract on behalf of a minor ----------------------------------------------


def _accepted_offer_for(client, db_session, talent_headers, recruiter_headers, casting_call, *, age: int):
    """Drive a 16-17 year old all the way to a pending agreement."""
    profile = create_profile(client, talent_headers, age=age)
    consent_resp = submit_consent(client, talent_headers)
    consent = consent_resp.json()

    from app.models.guardian_consent import GuardianConsent
    from app.models.talent_profile import TalentProfile

    row = db_session.query(GuardianConsent).filter(GuardianConsent.id == consent["id"]).first()
    row.status = "approved"
    db_session.query(TalentProfile).filter(TalentProfile.id == profile["id"]).first().guardian_consent_status = "approved"
    db_session.commit()

    role_id = casting_call["roles"][0]["id"]
    application = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications",
        json={"role_id": role_id, "message": "please"},
        headers=talent_headers,
    ).json()
    booking = client.post(
        f"/api/v1/talents/{profile['id']}/bookings",
        json={"application_id": application["id"], "contract_content": "<p>Terms</p>"},
        headers=recruiter_headers,
    ).json()
    client.patch(f"/api/v1/bookings/{booking['id']}/respond", json={"status": "accepted"}, headers=talent_headers)
    return booking


def test_a_seventeen_year_old_cannot_sign_their_own_contract(
    client, db_session, talent_headers, recruiter_headers, recruiter_profile, casting_call
):
    booking = _accepted_offer_for(client, db_session, talent_headers, recruiter_headers, casting_call, age=17)
    resp = client.patch(
        f"/api/v1/bookings/{booking['id']}/agreement/sign",
        json={"signature_name": "Sanduni Perera"},
        headers=talent_headers,
    )
    assert resp.status_code == 403
    assert "guardian" in resp.json()["detail"].lower()


def test_the_registered_guardian_can_sign_for_a_seventeen_year_old(
    client, db_session, talent_headers, recruiter_headers, recruiter_profile, casting_call
):
    booking = _accepted_offer_for(client, db_session, talent_headers, recruiter_headers, casting_call, age=17)
    resp = client.patch(
        f"/api/v1/bookings/{booking['id']}/agreement/sign",
        # Deliberately sloppy spacing/case -- a real person typing their own name.
        json={"signature_name": "  nimal   perera ", "signed_as_guardian": True},
        headers=talent_headers,
    )
    assert resp.status_code == 200, resp.text


def test_someone_elses_name_does_not_count_as_the_guardians_signature(
    client, db_session, talent_headers, recruiter_headers, recruiter_profile, casting_call
):
    booking = _accepted_offer_for(client, db_session, talent_headers, recruiter_headers, casting_call, age=17)
    resp = client.patch(
        f"/api/v1/bookings/{booking['id']}/agreement/sign",
        json={"signature_name": "Someone Else", "signed_as_guardian": True},
        headers=talent_headers,
    )
    assert resp.status_code == 403


# --- Nobody outside the account ever receives a date of birth ------------------------------


def test_the_public_api_never_returns_a_date_of_birth(client, talent_headers, talent_profile):
    for path in ["/api/v1/talents", f"/api/v1/talents/{talent_profile['id']}", "/api/v1/talents/featured"]:
        assert "date_of_birth" not in client.get(path).text, path


def test_the_public_profile_exposes_an_age_instead(client, talent_headers, talent_profile):
    body = client.get(f"/api/v1/talents/{talent_profile['id']}").json()
    assert "date_of_birth" not in body
    from app.core.age import calculate_age
    from datetime import date

    assert body["age"] == calculate_age(date.fromisoformat(ADULT_DOB))


def test_the_owner_still_gets_their_real_date_of_birth(client, talent_headers, talent_profile):
    body = client.get("/api/v1/talents/me", headers=talent_headers).json()
    assert body["date_of_birth"] == ADULT_DOB


def test_a_recruiter_browsing_never_sees_a_date_of_birth(client, talent_headers, talent_profile, recruiter_headers):
    assert "date_of_birth" not in client.get("/api/v1/talents", headers=recruiter_headers).text


# --- Abuse resistance on the consent endpoint ----------------------------------------------


def test_an_oversized_document_is_rejected_without_being_read_into_memory(client, talent_headers):
    """The size check seeks rather than reading. Without that, an attacker could force the
    server to buffer an arbitrarily large upload before the limit was ever consulted.
    """
    from app.core.config import settings

    create_profile(client, talent_headers, age=13)
    oversized = b"%PDF-1.7\n" + b"\x00" * (settings.MAX_DOCUMENT_SIZE_BYTES + 1024)
    resp = client.post(
        "/api/v1/talents/me/guardian-consent",
        data={
            "guardian_full_name": "Nimal Perera",
            "guardian_relationship": "father",
            "minor_full_name": "Sanduni Perera",
            "consented_scopes": ["profile_public"],
            "agreed": "true",
        },
        files={"birth_certificate": ("big.pdf", oversized, "application/pdf")},
        headers=talent_headers,
    )
    assert resp.status_code == 413


def test_an_executable_disguised_as_a_birth_certificate_is_rejected(client, talent_headers):
    create_profile(client, talent_headers, age=13)
    resp = client.post(
        "/api/v1/talents/me/guardian-consent",
        data={
            "guardian_full_name": "Nimal Perera",
            "guardian_relationship": "father",
            "minor_full_name": "Sanduni Perera",
            "consented_scopes": ["profile_public"],
            "agreed": "true",
        },
        # Claims to be a PDF by both filename and content type. Only the bytes are trusted.
        files={"birth_certificate": ("cert.pdf", b"MZ\x90\x00\x03payload", "application/pdf")},
        headers=talent_headers,
    )
    assert resp.status_code == 400


def test_absurdly_long_names_are_rejected_as_validation_not_a_server_error(client, talent_headers):
    create_profile(client, talent_headers, age=13)
    resp = client.post(
        "/api/v1/talents/me/guardian-consent",
        data={
            "guardian_full_name": "A" * 5000,
            "guardian_relationship": "father",
            "minor_full_name": "Sanduni Perera",
            "consented_scopes": ["profile_public"],
            "agreed": "true",
        },
        files={"birth_certificate": ("cert.pdf", PDF, "application/pdf")},
        headers=talent_headers,
    )
    assert resp.status_code == 422


def test_an_unknown_consent_scope_is_rejected(client, talent_headers):
    create_profile(client, talent_headers, age=13)
    resp = client.post(
        "/api/v1/talents/me/guardian-consent",
        data={
            "guardian_full_name": "Nimal Perera",
            "guardian_relationship": "father",
            "minor_full_name": "Sanduni Perera",
            "consented_scopes": ["profile_public", "become_admin"],
            "agreed": "true",
        },
        files={"birth_certificate": ("cert.pdf", PDF, "application/pdf")},
        headers=talent_headers,
    )
    assert resp.status_code == 400


def test_a_talent_cannot_mint_a_document_link(client, talent_headers, admin_headers):
    create_profile(client, talent_headers, age=13)
    consent = submit_consent(client, talent_headers).json()
    doc_id = consent["documents"][0]["id"]
    resp = client.post(
        f"/api/v1/admin/guardian-consents/{consent['id']}/documents/{doc_id}/link", headers=talent_headers
    )
    assert resp.status_code == 403


def test_a_document_link_cannot_be_repointed_at_another_document(client, talent_headers, admin_headers):
    from app.core.security import create_document_token

    create_profile(client, talent_headers, age=13)
    consent = submit_consent(client, talent_headers).json()
    doc_id = consent["documents"][0]["id"]

    # A validly-signed token for a *different* document must not open this one.
    other = create_document_token("00000000-0000-0000-0000-000000000000", ttl_seconds=60)
    assert client.get(f"/api/v1/documents/{doc_id}?t={other}").status_code == 401


def test_a_document_cannot_be_fetched_with_a_login_token(client, talent_headers, admin_headers, talent_token):
    create_profile(client, talent_headers, age=13)
    consent = submit_consent(client, talent_headers).json()
    doc_id = consent["documents"][0]["id"]
    assert client.get(f"/api/v1/documents/{doc_id}?t={talent_token}").status_code == 401


# --- A minor's media stays out of the public container until consent -----------------------


def _upload_photo(client, headers, *, title="Headshot"):
    """Cover-photo upload goes through ffmpeg, so use a real (tiny) JPEG."""
    jpeg = bytes.fromhex(
        "ffd8ffe000104a46494600010100000100010000ffdb004300"
        + "08" * 64
        + "ffc0000b080001000101011100ffc40014000100000000000000000000000000000009"
        + "ffc40014100100000000000000000000000000000000ffda0008010100003f00d2cf20ffd9"
    )
    return client.post(
        "/api/v1/talents/me/cover-photo",
        files={"file": ("headshot.jpg", jpeg, "image/jpeg")},
        headers=headers,
    )


def test_a_minors_media_is_not_written_to_the_public_container(client, db_session, talent_headers):
    from app.core.private_storage import is_private_ref
    from app.models.media import Media

    profile = create_profile(client, talent_headers, age=13)
    resp = _upload_photo(client, talent_headers)
    assert resp.status_code == 201, resp.text

    row = db_session.query(Media).filter(Media.talent_profile_id == profile["id"]).first()
    # The public media container is provisioned with public blob access -- a child's photo
    # must not land there before a guardian has agreed to it being shown.
    assert is_private_ref(row.url), row.url


def test_an_adults_media_still_goes_to_the_public_container(client, db_session, talent_headers):
    from app.core.private_storage import is_private_ref
    from app.models.media import Media

    profile = create_profile(client, talent_headers, age=30)
    assert _upload_photo(client, talent_headers).status_code == 201

    row = db_session.query(Media).filter(Media.talent_profile_id == profile["id"]).first()
    assert not is_private_ref(row.url)


def test_the_owner_gets_a_working_signed_link_not_a_raw_private_ref(client, talent_headers):
    create_profile(client, talent_headers, age=13)
    _upload_photo(client, talent_headers)

    body = client.get("/api/v1/talents/me", headers=talent_headers).json()
    url = body["media"][0]["url"]
    assert not url.startswith("private:")
    assert "/documents/media/" in url and "t=" in url


def test_approval_migrates_the_media_into_the_public_container(client, db_session, talent_headers, admin_headers):
    from app.core.private_storage import is_private_ref
    from app.models.media import Media

    profile = create_profile(client, talent_headers, age=13)
    _upload_photo(client, talent_headers)
    consent = submit_consent(client, talent_headers).json()

    row = db_session.query(Media).filter(Media.talent_profile_id == profile["id"]).first()
    assert is_private_ref(row.url)

    assert approve(client, admin_headers, consent["id"]).status_code == 200

    db_session.refresh(row)
    # Consent given, so it can now be served the ordinary way.
    assert not is_private_ref(row.url)


def test_private_media_cannot_be_fetched_without_a_valid_token(client, db_session, talent_headers):
    from app.models.media import Media

    profile = create_profile(client, talent_headers, age=13)
    _upload_photo(client, talent_headers)
    media_id = db_session.query(Media).filter(Media.talent_profile_id == profile["id"]).first().id

    assert client.get(f"/api/v1/documents/media/{media_id}?t=garbage").status_code == 401
    assert client.get(f"/api/v1/documents/media/{media_id}").status_code == 422
