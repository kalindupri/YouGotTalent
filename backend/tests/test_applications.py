import pytest

from tests.conftest import register_and_verify, auth_headers


def create_talent_profile(client, headers, **overrides):
    payload = {"display_name": "Applicant", "category": "acting"}
    payload.update(overrides)
    resp = client.post("/api/v1/talents/me", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_apply_to_a_role(client, talent_headers, casting_call):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    resp = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications",
        json={"role_id": role_id, "message": "I'd love this role"},
        headers=talent_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["role_id"] == role_id
    assert body["status"] == "pending"


def test_apply_requires_talent_role(client, recruiter_headers, casting_call):
    role_id = casting_call["roles"][0]["id"]
    resp = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications",
        json={"role_id": role_id},
        headers=recruiter_headers,
    )
    assert resp.status_code == 403


def test_apply_to_unknown_casting_call_404(client, talent_headers):
    create_talent_profile(client, talent_headers)
    resp = client.post(
        "/api/v1/casting-calls/00000000-0000-0000-0000-000000000000/applications",
        json={"role_id": "00000000-0000-0000-0000-000000000000"},
        headers=talent_headers,
    )
    assert resp.status_code == 404


def test_apply_with_role_from_a_different_casting_call_rejected(client, talent_headers, recruiter_headers, casting_call):
    create_talent_profile(client, talent_headers)
    other_call = client.post(
        "/api/v1/casting-calls",
        json={"title": "Other call", "description": "x", "category": "acting", "roles": [{"title": "x"}]},
        headers=recruiter_headers,
    ).json()

    resp = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications",
        json={"role_id": other_call["roles"][0]["id"]},
        headers=talent_headers,
    )
    assert resp.status_code == 400


def test_duplicate_application_to_same_role_rejected(client, talent_headers, casting_call):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    payload = {"role_id": role_id}
    resp1 = client.post(f"/api/v1/casting-calls/{casting_call['id']}/applications", json=payload, headers=talent_headers)
    assert resp1.status_code == 201
    resp2 = client.post(f"/api/v1/casting-calls/{casting_call['id']}/applications", json=payload, headers=talent_headers)
    assert resp2.status_code == 400


def test_apply_to_two_different_roles_on_same_call(client, talent_headers, recruiter_headers, recruiter_profile):
    create_talent_profile(client, talent_headers, category="modeling")
    assert client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers).status_code == 200
    call = client.post(
        "/api/v1/casting-calls",
        json={
            "title": "Multi-role shoot",
            "description": "x",
            "category": "modeling",
            "roles": [{"title": "Models"}, {"title": "Actors"}],
        },
        headers=recruiter_headers,
    ).json()

    for role in call["roles"]:
        resp = client.post(
            f"/api/v1/casting-calls/{call['id']}/applications",
            json={"role_id": role["id"]},
            headers=talent_headers,
        )
        assert resp.status_code == 201, resp.text


def test_recruiter_can_list_applications_for_own_call(client, talent_headers, recruiter_headers, casting_call):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    client.post(f"/api/v1/casting-calls/{casting_call['id']}/applications", json={"role_id": role_id}, headers=talent_headers)

    resp = client.get(f"/api/v1/casting-calls/{casting_call['id']}/applications", headers=recruiter_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_other_recruiter_cannot_list_applications(client, talent_headers, casting_call, db_session):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    client.post(f"/api/v1/casting-calls/{casting_call['id']}/applications", json={"role_id": role_id}, headers=talent_headers)

    other_token = register_and_verify(client, db_session, "otherrecruiter@example.com", role="recruiter")
    other_headers = auth_headers(other_token)
    client.post("/api/v1/recruiters/me", json={"company_name": "Other Co"}, headers=other_headers)

    resp = client.get(f"/api/v1/casting-calls/{casting_call['id']}/applications", headers=other_headers)
    assert resp.status_code == 404


def test_talent_can_list_own_applications(client, talent_headers, casting_call):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    client.post(f"/api/v1/casting-calls/{casting_call['id']}/applications", json={"role_id": role_id}, headers=talent_headers)

    resp = client.get("/api/v1/talents/me/applications", headers=talent_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_recruiter_updates_application_status(client, talent_headers, recruiter_headers, casting_call):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    application = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications", json={"role_id": role_id}, headers=talent_headers
    ).json()

    resp = client.patch(
        f"/api/v1/applications/{application['id']}", json={"status": "shortlisted"}, headers=recruiter_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "shortlisted"


def test_direct_patch_to_accepted_rejected(client, talent_headers, recruiter_headers, casting_call):
    # "Accepted" is only reachable through the offer + both-parties-sign flow now — see
    # test_bookings.py::test_both_parties_signing_offer_auto_accepts_the_application.
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    application = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications", json={"role_id": role_id}, headers=talent_headers
    ).json()

    resp = client.patch(
        f"/api/v1/applications/{application['id']}", json={"status": "accepted"}, headers=recruiter_headers
    )
    assert resp.status_code == 400
    assert "offer" in resp.json()["detail"].lower()

    unchanged = client.get(f"/api/v1/talents/me/applications", headers=talent_headers).json()
    assert unchanged[0]["status"] == "pending"


def test_non_owning_recruiter_cannot_update_status(client, talent_headers, casting_call, db_session):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    application = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications", json={"role_id": role_id}, headers=talent_headers
    ).json()

    other_token = register_and_verify(client, db_session, "notowner@example.com", role="recruiter")
    other_headers = auth_headers(other_token)
    client.post("/api/v1/recruiters/me", json={"company_name": "Not Owner Co"}, headers=other_headers)

    resp = client.patch(
        f"/api/v1/applications/{application['id']}", json={"status": "accepted"}, headers=other_headers
    )
    assert resp.status_code == 403


@pytest.mark.parametrize("bad_status", ["not-a-status", "", "PENDING"])
def test_update_status_rejects_invalid_values(client, talent_headers, recruiter_headers, casting_call, bad_status):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    application = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications", json={"role_id": role_id}, headers=talent_headers
    ).json()

    resp = client.patch(
        f"/api/v1/applications/{application['id']}", json={"status": bad_status}, headers=recruiter_headers
    )
    assert resp.status_code == 422


def apply_with_upload(client, headers, casting_call, role_id, file_bytes, filename, content_type, media_type, *, message=None):
    data = {"role_id": role_id, "media_type": media_type}
    if message:
        data["message"] = message
    return client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications/upload",
        data=data,
        files={"file": (filename, file_bytes, content_type)},
        headers=headers,
    )


def test_apply_with_video_upload(client, talent_headers, casting_call, sample_video_bytes):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    resp = apply_with_upload(
        client, talent_headers, casting_call, role_id, sample_video_bytes, "take.mp4", "video/mp4", "video",
        message="Here's my take",
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["role_id"] == role_id
    assert body["submission_url"]
    assert body["message"] == "Here's my take"


def test_apply_with_audio_upload(client, talent_headers, casting_call, sample_audio_bytes):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    resp = apply_with_upload(
        client, talent_headers, casting_call, role_id, sample_audio_bytes, "take.mp3", "audio/mpeg", "audio",
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["submission_url"]


def test_apply_with_upload_rejects_video_over_30_seconds(client, talent_headers, casting_call, long_sample_video_bytes):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    resp = apply_with_upload(
        client, talent_headers, casting_call, role_id, long_sample_video_bytes, "take.mp4", "video/mp4", "video",
    )
    assert resp.status_code == 400
    assert "30 seconds" in resp.json()["detail"]


def test_apply_with_upload_rejects_unsupported_media_type(client, talent_headers, casting_call, sample_video_bytes):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    resp = apply_with_upload(
        client, talent_headers, casting_call, role_id, sample_video_bytes, "take.jpg", "image/jpeg", "photo",
    )
    assert resp.status_code == 400


def test_apply_with_upload_rejects_corrupt_file(client, talent_headers, casting_call):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    resp = apply_with_upload(
        client, talent_headers, casting_call, role_id, b"not a real video file", "take.mp4", "video/mp4", "video",
    )
    assert resp.status_code == 400


def test_apply_with_upload_still_rejects_duplicate_role(client, talent_headers, casting_call, sample_video_bytes):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    first = apply_with_upload(
        client, talent_headers, casting_call, role_id, sample_video_bytes, "take.mp4", "video/mp4", "video",
    )
    assert first.status_code == 201

    second = apply_with_upload(
        client, talent_headers, casting_call, role_id, sample_video_bytes, "take.mp4", "video/mp4", "video",
    )
    assert second.status_code == 400


def test_application_viewed_at_null_before_recruiter_lists(client, talent_headers, casting_call):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    application = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications", json={"role_id": role_id}, headers=talent_headers
    ).json()
    assert application["viewed_at"] is None


def test_recruiter_listing_applications_stamps_viewed_at(client, talent_headers, recruiter_headers, casting_call):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    client.post(f"/api/v1/casting-calls/{casting_call['id']}/applications", json={"role_id": role_id}, headers=talent_headers)

    resp = client.get(f"/api/v1/casting-calls/{casting_call['id']}/applications", headers=recruiter_headers)
    assert resp.status_code == 200
    assert resp.json()[0]["viewed_at"] is not None


def test_free_talent_cannot_apply_to_premium_talent_only_call(client, talent_headers, recruiter_headers, recruiter_profile):
    create_talent_profile(client, talent_headers)
    client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers)
    call = client.post(
        "/api/v1/casting-calls",
        json={
            "title": "Exclusive role",
            "description": "x",
            "category": "acting",
            "roles": [{"title": "Exclusive role"}],
            "premium_talent_only": True,
        },
        headers=recruiter_headers,
    ).json()

    resp = client.post(
        f"/api/v1/casting-calls/{call['id']}/applications",
        json={"role_id": call["roles"][0]["id"]},
        headers=talent_headers,
    )
    assert resp.status_code == 403


def test_premium_talent_can_apply_to_premium_talent_only_call(client, talent_headers, recruiter_headers, recruiter_profile):
    create_talent_profile(client, talent_headers)
    client.post("/api/v1/talents/me/upgrade", headers=talent_headers)
    client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers)
    call = client.post(
        "/api/v1/casting-calls",
        json={
            "title": "Exclusive role",
            "description": "x",
            "category": "acting",
            "roles": [{"title": "Exclusive role"}],
            "premium_talent_only": True,
        },
        headers=recruiter_headers,
    ).json()

    resp = client.post(
        f"/api/v1/casting-calls/{call['id']}/applications",
        json={"role_id": call["roles"][0]["id"]},
        headers=talent_headers,
    )
    assert resp.status_code == 201, resp.text


def test_free_recruiter_sees_no_match_score(client, talent_headers, recruiter_headers, casting_call):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    client.post(f"/api/v1/casting-calls/{casting_call['id']}/applications", json={"role_id": role_id}, headers=talent_headers)

    resp = client.get(f"/api/v1/casting-calls/{casting_call['id']}/applications", headers=recruiter_headers)
    assert resp.status_code == 200
    assert resp.json()[0]["match_score"] is None


def test_premium_recruiter_sees_match_score_sorted_best_first(client, recruiter_headers, recruiter_profile, casting_call, db_session):
    from tests.conftest import auth_headers, register_and_verify

    client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers)
    role_id = casting_call["roles"][0]["id"]

    strong_token = register_and_verify(client, db_session, "strong-fit@example.com", role="talent")
    strong_headers = auth_headers(strong_token)
    create_talent_profile(
        client, strong_headers, display_name="Strong Fit", category="acting", experience_years=10,
        skills=["lead role in short film"],
    )
    client.post(f"/api/v1/casting-calls/{casting_call['id']}/applications", json={"role_id": role_id}, headers=strong_headers)

    weak_token = register_and_verify(client, db_session, "weak-fit@example.com", role="talent")
    weak_headers = auth_headers(weak_token)
    create_talent_profile(client, weak_headers, display_name="Weak Fit", category="painting")
    client.post(f"/api/v1/casting-calls/{casting_call['id']}/applications", json={"role_id": role_id}, headers=weak_headers)

    resp = client.get(f"/api/v1/casting-calls/{casting_call['id']}/applications", headers=recruiter_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert all(a["match_score"] is not None for a in body)
    assert body[0]["match_score"] >= body[1]["match_score"]
    assert body[0]["talent_id"] != body[1]["talent_id"]


def test_talent_sees_viewed_at_after_recruiter_lists(client, talent_headers, recruiter_headers, casting_call):
    create_talent_profile(client, talent_headers)
    role_id = casting_call["roles"][0]["id"]
    client.post(f"/api/v1/casting-calls/{casting_call['id']}/applications", json={"role_id": role_id}, headers=talent_headers)

    # Talent's own view of the application still shows unseen until the recruiter lists it.
    before = client.get("/api/v1/talents/me/applications", headers=talent_headers).json()
    assert before[0]["viewed_at"] is None

    client.get(f"/api/v1/casting-calls/{casting_call['id']}/applications", headers=recruiter_headers)

    after = client.get("/api/v1/talents/me/applications", headers=talent_headers).json()
    assert after[0]["viewed_at"] is not None
