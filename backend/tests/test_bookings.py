from datetime import datetime, timedelta, timezone

from tests.conftest import auth_headers, register_and_verify


def next_weekday_at(day_of_week: int, hour: int, minute: int = 0) -> datetime:
    """Return the next occurrence of `day_of_week` (0=Monday) at the given UTC time."""
    now = datetime.now(timezone.utc)
    days_ahead = (day_of_week - now.weekday()) % 7
    days_ahead = days_ahead if days_ahead > 0 else 7
    target = now + timedelta(days=days_ahead)
    return target.replace(hour=hour, minute=minute, second=0, microsecond=0)


def set_monday_9_to_5(client, talent_headers):
    resp = client.post(
        "/api/v1/talents/me/availability",
        json={"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00"},
        headers=talent_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_talent_sets_and_lists_availability(client, talent_headers, talent_profile):
    window = set_monday_9_to_5(client, talent_headers)
    assert window["day_of_week"] == 0
    assert window["start_time"] == "09:00:00"

    resp = client.get("/api/v1/talents/me/availability", headers=talent_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_availability_rejects_end_before_start(client, talent_headers, talent_profile):
    resp = client.post(
        "/api/v1/talents/me/availability",
        json={"day_of_week": 0, "start_time": "17:00:00", "end_time": "09:00:00"},
        headers=talent_headers,
    )
    assert resp.status_code == 422


def test_talent_deletes_availability(client, talent_headers, talent_profile):
    window = set_monday_9_to_5(client, talent_headers)
    resp = client.delete(f"/api/v1/talents/me/availability/{window['id']}", headers=talent_headers)
    assert resp.status_code == 204

    resp = client.get("/api/v1/talents/me/availability", headers=talent_headers)
    assert resp.json() == []


def test_public_can_view_talent_availability(client, talent_headers, talent_profile):
    set_monday_9_to_5(client, talent_headers)
    resp = client.get(f"/api/v1/talents/{talent_profile['id']}/availability")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_recruiter_requests_booking_within_availability(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    resp = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat(), "message": "Let's meet"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "pending"
    assert body["agreement_status"] == "not_required"
    assert body["talent_display_name"] == talent_profile["display_name"]
    assert body["recruiter_company_name"] == recruiter_profile["company_name"]


def test_booking_outside_availability_rejected(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 20)  # 8pm, outside the 9-5 window
    resp = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    )
    assert resp.status_code == 400


def test_booking_overlap_rejected(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    payload = {"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()}
    resp1 = client.post(f"/api/v1/talents/{talent_profile['id']}/bookings", json=payload, headers=recruiter_headers)
    assert resp1.status_code == 201

    overlapping_start = start + timedelta(minutes=30)
    resp2 = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": overlapping_start.isoformat(), "end_at": (overlapping_start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    )
    assert resp2.status_code == 400


def test_talent_accepts_booking_and_agreement_becomes_pending(
    client, talent_headers, talent_profile, recruiter_headers, recruiter_profile
):
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    booking = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    ).json()

    resp = client.patch(f"/api/v1/bookings/{booking['id']}/respond", json={"status": "accepted"}, headers=talent_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "accepted"
    assert body["agreement_status"] == "pending"


def test_talent_declines_booking(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    booking = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    ).json()

    resp = client.patch(f"/api/v1/bookings/{booking['id']}/respond", json={"status": "declined"}, headers=talent_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "declined"
    assert resp.json()["agreement_status"] == "not_required"


def test_cannot_respond_twice(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    booking = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    ).json()

    client.patch(f"/api/v1/bookings/{booking['id']}/respond", json={"status": "accepted"}, headers=talent_headers)
    resp = client.patch(f"/api/v1/bookings/{booking['id']}/respond", json={"status": "declined"}, headers=talent_headers)
    assert resp.status_code == 400


def test_non_owner_talent_cannot_respond(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile, db_session):
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    booking = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    ).json()

    other_token = register_and_verify(client, db_session, "otherbooking@example.com", role="talent")
    other_headers = auth_headers(other_token)
    client.post("/api/v1/talents/me", json={"display_name": "Other", "category": "acting"}, headers=other_headers)

    resp = client.patch(f"/api/v1/bookings/{booking['id']}/respond", json={"status": "accepted"}, headers=other_headers)
    assert resp.status_code == 404


def test_recruiter_cancels_pending_booking(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    booking = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    ).json()

    resp = client.patch(f"/api/v1/bookings/{booking['id']}/cancel", headers=recruiter_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_recruiter_cannot_cancel_after_accepted(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    booking = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    ).json()
    client.patch(f"/api/v1/bookings/{booking['id']}/respond", json={"status": "accepted"}, headers=talent_headers)

    resp = client.patch(f"/api/v1/bookings/{booking['id']}/cancel", headers=recruiter_headers)
    assert resp.status_code == 400


def test_agreement_cannot_be_signed_before_accepted(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    booking = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    ).json()

    resp = client.patch(f"/api/v1/bookings/{booking['id']}/agreement/sign", json={"signature_name": "Amila"}, headers=talent_headers)
    assert resp.status_code == 400


def test_first_signer_leaves_agreement_pending(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    booking = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    ).json()
    client.patch(f"/api/v1/bookings/{booking['id']}/respond", json={"status": "accepted"}, headers=talent_headers)

    resp = client.patch(
        f"/api/v1/bookings/{booking['id']}/agreement/sign",
        json={"signature_name": "Fixture Recruiter"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["agreement_status"] == "pending"
    assert body["recruiter_signature_name"] == "Fixture Recruiter"
    assert body["recruiter_signed_at"] is not None
    assert body["talent_signed_at"] is None


def test_both_parties_signing_marks_agreement_signed(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    booking = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    ).json()
    client.patch(f"/api/v1/bookings/{booking['id']}/respond", json={"status": "accepted"}, headers=talent_headers)

    client.patch(
        f"/api/v1/bookings/{booking['id']}/agreement/sign",
        json={"signature_name": "Fixture Recruiter"},
        headers=recruiter_headers,
    )
    resp = client.patch(
        f"/api/v1/bookings/{booking['id']}/agreement/sign",
        json={"signature_name": "Fixture Talent"},
        headers=talent_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["agreement_status"] == "signed"
    assert body["talent_signature_name"] == "Fixture Talent"
    assert body["recruiter_signature_name"] == "Fixture Recruiter"


def test_same_party_cannot_sign_twice(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    booking = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    ).json()
    client.patch(f"/api/v1/bookings/{booking['id']}/respond", json={"status": "accepted"}, headers=talent_headers)

    client.patch(
        f"/api/v1/bookings/{booking['id']}/agreement/sign",
        json={"signature_name": "Fixture Recruiter"},
        headers=recruiter_headers,
    )
    resp = client.patch(
        f"/api/v1/bookings/{booking['id']}/agreement/sign",
        json={"signature_name": "Fixture Recruiter Again"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 400


def test_cannot_sign_after_both_parties_signed(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    booking = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    ).json()
    client.patch(f"/api/v1/bookings/{booking['id']}/respond", json={"status": "accepted"}, headers=talent_headers)
    client.patch(
        f"/api/v1/bookings/{booking['id']}/agreement/sign",
        json={"signature_name": "Fixture Recruiter"},
        headers=recruiter_headers,
    )
    client.patch(
        f"/api/v1/bookings/{booking['id']}/agreement/sign",
        json={"signature_name": "Fixture Talent"},
        headers=talent_headers,
    )

    resp = client.patch(
        f"/api/v1/bookings/{booking['id']}/agreement/sign",
        json={"signature_name": "Fixture Talent"},
        headers=talent_headers,
    )
    assert resp.status_code == 400


def test_talent_and_recruiter_list_own_bookings(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    )

    talent_list = client.get("/api/v1/talents/me/bookings", headers=talent_headers)
    assert talent_list.status_code == 200
    assert len(talent_list.json()) == 1

    recruiter_list = client.get("/api/v1/recruiters/me/bookings", headers=recruiter_headers)
    assert recruiter_list.status_code == 200
    assert len(recruiter_list.json()) == 1


def _apply_to_casting_call(client, talent_headers, casting_call):
    role_id = casting_call["roles"][0]["id"]
    resp = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications", json={"role_id": role_id}, headers=talent_headers
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_send_offer_creates_booking_linked_to_application(
    client, talent_headers, talent_profile, recruiter_headers, recruiter_profile, casting_call
):
    application = _apply_to_casting_call(client, talent_headers, casting_call)
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    resp = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={
            "start_at": start.isoformat(),
            "end_at": (start + timedelta(hours=1)).isoformat(),
            "application_id": application["id"],
        },
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["application_id"] == application["id"]
    assert body["application_role_title"] == casting_call["roles"][0]["title"]


def test_send_offer_for_someone_elses_casting_call_rejected(
    client, db_session, talent_headers, talent_profile, recruiter_headers, recruiter_profile, casting_call
):
    application = _apply_to_casting_call(client, talent_headers, casting_call)
    set_monday_9_to_5(client, talent_headers)

    other_token = register_and_verify(client, db_session, "other_recruiter_offer@example.com", role="recruiter")
    other_headers = auth_headers(other_token)
    client.post("/api/v1/recruiters/me", json={"company_name": "Other Co"}, headers=other_headers)

    start = next_weekday_at(0, 10)
    resp = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={
            "start_at": start.isoformat(),
            "end_at": (start + timedelta(hours=1)).isoformat(),
            "application_id": application["id"],
        },
        headers=other_headers,
    )
    assert resp.status_code == 403


def test_duplicate_pending_offer_rejected(
    client, talent_headers, talent_profile, recruiter_headers, recruiter_profile, casting_call
):
    application = _apply_to_casting_call(client, talent_headers, casting_call)
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    payload = {
        "start_at": start.isoformat(),
        "end_at": (start + timedelta(hours=1)).isoformat(),
        "application_id": application["id"],
    }
    first = client.post(f"/api/v1/talents/{talent_profile['id']}/bookings", json=payload, headers=recruiter_headers)
    assert first.status_code == 201

    # A different (non-overlapping) proposed time, same application — still rejected because
    # the first offer is still pending, not because the time slot conflicts.
    second_start = start + timedelta(hours=3)
    resp = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={
            "start_at": second_start.isoformat(),
            "end_at": (second_start + timedelta(hours=1)).isoformat(),
            "application_id": application["id"],
        },
        headers=recruiter_headers,
    )
    assert resp.status_code == 400
    assert "already pending" in resp.json()["detail"]


def test_declined_offer_frees_application_for_a_new_offer(
    client, talent_headers, talent_profile, recruiter_headers, recruiter_profile, casting_call
):
    application = _apply_to_casting_call(client, talent_headers, casting_call)
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    first = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={
            "start_at": start.isoformat(),
            "end_at": (start + timedelta(hours=1)).isoformat(),
            "application_id": application["id"],
        },
        headers=recruiter_headers,
    ).json()
    client.patch(f"/api/v1/bookings/{first['id']}/respond", json={"status": "declined"}, headers=talent_headers)

    second_start = start + timedelta(hours=3)
    resp = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={
            "start_at": second_start.isoformat(),
            "end_at": (second_start + timedelta(hours=1)).isoformat(),
            "application_id": application["id"],
        },
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text


def test_both_parties_signing_offer_auto_accepts_the_application(
    client, db_session, talent_headers, talent_profile, recruiter_headers, recruiter_profile, casting_call
):
    application = _apply_to_casting_call(client, talent_headers, casting_call)
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    booking = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={
            "start_at": start.isoformat(),
            "end_at": (start + timedelta(hours=1)).isoformat(),
            "application_id": application["id"],
        },
        headers=recruiter_headers,
    ).json()

    client.patch(f"/api/v1/bookings/{booking['id']}/respond", json={"status": "accepted"}, headers=talent_headers)
    client.patch(
        f"/api/v1/bookings/{booking['id']}/agreement/sign",
        json={"signature_name": "Fixture Recruiter"},
        headers=recruiter_headers,
    )
    resp = client.patch(
        f"/api/v1/bookings/{booking['id']}/agreement/sign",
        json={"signature_name": "Fixture Talent"},
        headers=talent_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["agreement_status"] == "signed"

    from app.models.application import Application, ApplicationStatus

    updated_application = db_session.query(Application).filter(Application.id == application["id"]).first()
    assert updated_application.status == ApplicationStatus.ACCEPTED


def test_standalone_booking_has_no_application_link(
    client, talent_headers, talent_profile, recruiter_headers, recruiter_profile
):
    set_monday_9_to_5(client, talent_headers)
    start = next_weekday_at(0, 10)
    resp = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["application_id"] is None
    assert body["application_role_title"] is None


def test_booking_unknown_talent_404(client, recruiter_headers, recruiter_profile):
    start = next_weekday_at(0, 10)
    resp = client.post(
        "/api/v1/talents/00000000-0000-0000-0000-000000000000/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    )
    assert resp.status_code == 404
