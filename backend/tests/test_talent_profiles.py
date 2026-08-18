from tests.conftest import ADULT_DOB, register_and_verify, auth_headers


def create_profile(client, headers, **overrides):
    payload = {"date_of_birth": ADULT_DOB, "display_name": "Test Talent", "category": "acting", "city": "Colombo"}
    payload.update(overrides)
    resp = client.post("/api/v1/talents/me", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_profile(client, talent_headers):
    body = create_profile(client, talent_headers, display_name="Ishara", category="singing")
    assert body["display_name"] == "Ishara"
    assert body["category"] == "singing"
    assert body["tier"] == "free"
    assert body["is_verified"] is False
    assert body["job_alert_emails"] is True
    assert body["media"] == []
    assert body["credits"] == []


def test_create_profile_twice_rejected(client, talent_headers):
    create_profile(client, talent_headers)
    resp = client.post(
        "/api/v1/talents/me",
        json={"date_of_birth": ADULT_DOB, "display_name": "Again", "category": "acting"},
        headers=talent_headers,
    )
    assert resp.status_code == 400


def test_create_profile_requires_talent_role(client, recruiter_headers):
    resp = client.post(
        "/api/v1/talents/me",
        json={"date_of_birth": ADULT_DOB, "display_name": "Recruiter as talent", "category": "acting"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 403


def test_read_my_profile_requires_profile_to_exist(client, talent_headers):
    resp = client.get("/api/v1/talents/me", headers=talent_headers)
    assert resp.status_code == 404


def test_get_talent_by_id(client, talent_headers):
    created = create_profile(client, talent_headers)
    resp = client.get(f"/api/v1/talents/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_talent_unknown_id_404(client):
    resp = client.get("/api/v1/talents/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_update_profile_bio_city_and_attributes(client, talent_headers):
    create_profile(client, talent_headers, category="singing")
    resp = client.patch(
        "/api/v1/talents/me",
        json={
            "bio": "Playback vocalist",
            "city": "Kandy",
            "attributes": {"vocal_range": "Mezzo-soprano"},
            "intro_video_url": "https://www.youtube.com/watch?v=abc123",
        },
        headers=talent_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["bio"] == "Playback vocalist"
    assert body["city"] == "Kandy"
    assert body["attributes"] == {"vocal_range": "Mezzo-soprano"}
    assert body["intro_video_url"] == "https://www.youtube.com/watch?v=abc123"


def test_update_job_alert_emails_preference(client, talent_headers):
    create_profile(client, talent_headers)
    resp = client.patch("/api/v1/talents/me", json={"job_alert_emails": False}, headers=talent_headers)
    assert resp.status_code == 200
    assert resp.json()["job_alert_emails"] is False


def test_request_verification_sets_timestamp(client, talent_headers):
    create_profile(client, talent_headers)
    resp = client.post("/api/v1/talents/me/request-verification", headers=talent_headers)
    assert resp.status_code == 200
    assert resp.json()["verification_requested_at"] is not None


def test_upgrade_tier_sets_premium(client, talent_headers):
    create_profile(client, talent_headers)
    resp = client.post("/api/v1/talents/me/upgrade", headers=talent_headers)
    assert resp.status_code == 200
    assert resp.json()["tier"] == "premium"


def test_add_media_within_free_tier_limit(client, talent_headers):
    create_profile(client, talent_headers)
    for i in range(3):
        resp = client.post(
            "/api/v1/talents/me/media",
            json={"url": f"https://example.com/{i}.jpg", "media_type": "photo", "title": f"Photo {i}"},
            headers=talent_headers,
        )
        assert resp.status_code == 201, resp.text


def test_add_media_beyond_free_tier_limit_rejected(client, talent_headers):
    create_profile(client, talent_headers)
    for i in range(3):
        resp = client.post(
            "/api/v1/talents/me/media",
            json={"url": f"https://example.com/{i}.jpg", "media_type": "photo"},
            headers=talent_headers,
        )
        assert resp.status_code == 201

    resp = client.post(
        "/api/v1/talents/me/media",
        json={"url": "https://example.com/4th.jpg", "media_type": "photo"},
        headers=talent_headers,
    )
    assert resp.status_code == 403
    assert "premium" in resp.json()["detail"].lower()


def test_premium_tier_bypasses_media_limit(client, talent_headers):
    create_profile(client, talent_headers)
    client.post("/api/v1/talents/me/upgrade", headers=talent_headers)
    for i in range(5):
        resp = client.post(
            "/api/v1/talents/me/media",
            json={"url": f"https://example.com/{i}.jpg", "media_type": "photo"},
            headers=talent_headers,
        )
        assert resp.status_code == 201, resp.text


def test_add_and_delete_credit(client, talent_headers):
    create_profile(client, talent_headers)
    resp = client.post(
        "/api/v1/talents/me/credits",
        json={"project_type": "film", "title": "Short film lead", "role": "Lead actor"},
        headers=talent_headers,
    )
    assert resp.status_code == 201, resp.text
    credit_id = resp.json()["id"]

    resp = client.delete(f"/api/v1/talents/me/credits/{credit_id}", headers=talent_headers)
    assert resp.status_code == 204

    resp = client.delete(f"/api/v1/talents/me/credits/{credit_id}", headers=talent_headers)
    assert resp.status_code == 404


def test_cannot_delete_another_talents_credit(client, db_session):
    from tests.conftest import DEFAULT_PASSWORD

    token_a = register_and_verify(client, db_session, "talent-a@example.com", role="talent")
    token_b = register_and_verify(client, db_session, "talent-b@example.com", role="talent")
    headers_a = auth_headers(token_a)
    headers_b = auth_headers(token_b)

    create_profile(client, headers_a, display_name="Talent A")
    create_profile(client, headers_b, display_name="Talent B")

    resp = client.post(
        "/api/v1/talents/me/credits",
        json={"project_type": "film", "title": "A's credit"},
        headers=headers_a,
    )
    credit_id = resp.json()["id"]

    resp = client.delete(f"/api/v1/talents/me/credits/{credit_id}", headers=headers_b)
    assert resp.status_code == 404


def test_update_own_credit(client, talent_headers):
    create_profile(client, talent_headers)
    resp = client.post(
        "/api/v1/talents/me/credits",
        json={"project_type": "film", "title": "Short film lead", "role": "Lead actor"},
        headers=talent_headers,
    )
    credit_id = resp.json()["id"]

    resp = client.patch(
        f"/api/v1/talents/me/credits/{credit_id}",
        json={"title": "Feature film lead", "role": "Supporting actor"},
        headers=talent_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["title"] == "Feature film lead"
    assert resp.json()["role"] == "Supporting actor"
    assert resp.json()["project_type"] == "film"


def test_cannot_update_another_talents_credit(client, db_session):
    token_a = register_and_verify(client, db_session, "credit-a@example.com", role="talent")
    token_b = register_and_verify(client, db_session, "credit-b@example.com", role="talent")
    headers_a = auth_headers(token_a)
    headers_b = auth_headers(token_b)

    create_profile(client, headers_a, display_name="Credit A")
    create_profile(client, headers_b, display_name="Credit B")

    credit_id = client.post(
        "/api/v1/talents/me/credits",
        json={"project_type": "film", "title": "A's credit"},
        headers=headers_a,
    ).json()["id"]

    resp = client.patch(f"/api/v1/talents/me/credits/{credit_id}", json={"title": "Hijacked"}, headers=headers_b)
    assert resp.status_code == 404


def test_update_and_delete_own_media(client, talent_headers):
    create_profile(client, talent_headers)
    resp = client.post(
        "/api/v1/talents/me/media",
        json={"url": "https://example.com/photo.jpg", "media_type": "photo", "title": "Headshot"},
        headers=talent_headers,
    )
    media_id = resp.json()["id"]

    resp = client.patch(f"/api/v1/talents/me/media/{media_id}", json={"title": "Updated headshot"}, headers=talent_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["title"] == "Updated headshot"

    resp = client.delete(f"/api/v1/talents/me/media/{media_id}", headers=talent_headers)
    assert resp.status_code == 204

    resp = client.delete(f"/api/v1/talents/me/media/{media_id}", headers=talent_headers)
    assert resp.status_code == 404


def test_cannot_edit_or_delete_another_talents_media(client, db_session):
    token_a = register_and_verify(client, db_session, "media-a@example.com", role="talent")
    token_b = register_and_verify(client, db_session, "media-b@example.com", role="talent")
    headers_a = auth_headers(token_a)
    headers_b = auth_headers(token_b)

    create_profile(client, headers_a, display_name="Media A")
    create_profile(client, headers_b, display_name="Media B")

    media_id = client.post(
        "/api/v1/talents/me/media",
        json={"url": "https://example.com/photo.jpg", "media_type": "photo"},
        headers=headers_a,
    ).json()["id"]

    assert client.patch(f"/api/v1/talents/me/media/{media_id}", json={"title": "Hijacked"}, headers=headers_b).status_code == 404
    assert client.delete(f"/api/v1/talents/me/media/{media_id}", headers=headers_b).status_code == 404

    # Confirm B's failed attempts didn't touch A's copy — still deletable by the real owner.
    assert client.delete(f"/api/v1/talents/me/media/{media_id}", headers=headers_a).status_code == 204


def test_browse_filters_by_category(client, talent_headers, db_session):
    create_profile(client, talent_headers, category="singing")
    token_b = register_and_verify(client, db_session, "actor@example.com", role="talent")
    create_profile(client, auth_headers(token_b), category="acting")

    resp = client.get("/api/v1/talents", params={"categories": ["singing"]})
    assert resp.status_code == 200
    categories = {t["category"] for t in resp.json()}
    assert categories == {"singing"}


def test_create_profile_with_multiple_categories(client, talent_headers):
    body = create_profile(client, talent_headers, categories=["singing", "acting", "script_writing"])
    assert body["categories"] == ["singing", "acting", "script_writing"]
    # The primary category (used everywhere a single scalar is still needed) is the first one.
    assert body["category"] == "singing"


def test_update_profile_categories_updates_primary_category(client, talent_headers):
    create_profile(client, talent_headers, categories=["acting"])
    resp = client.patch("/api/v1/talents/me", json={"categories": ["dancing", "choreography"]}, headers=talent_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["categories"] == ["dancing", "choreography"]
    assert body["category"] == "dancing"


def test_browse_filters_by_categories_returns_union(client, talent_headers, db_session):
    create_profile(client, talent_headers, categories=["singing"])
    token_b = register_and_verify(client, db_session, "actor2@example.com", role="talent")
    create_profile(client, auth_headers(token_b), display_name="Actor", categories=["acting"])
    token_c = register_and_verify(client, db_session, "dancer2@example.com", role="talent")
    create_profile(client, auth_headers(token_c), display_name="Dancer", categories=["dancing"])

    resp = client.get("/api/v1/talents", params={"categories": ["singing", "acting"]})
    assert resp.status_code == 200
    names = {t["display_name"] for t in resp.json()}
    assert names == {"Test Talent", "Actor"}


def test_browse_filters_by_city(client, talent_headers, db_session):
    create_profile(client, talent_headers, city="Colombo")
    token_b = register_and_verify(client, db_session, "galletown@example.com", role="talent")
    create_profile(client, auth_headers(token_b), display_name="Galle Talent", city="Galle")

    resp = client.get("/api/v1/talents", params={"city": "Galle"})
    assert resp.status_code == 200
    cities = {t["city"] for t in resp.json()}
    assert cities == {"Galle"}


def test_browse_search_matches_skills(client, talent_headers):
    create_profile(client, talent_headers, skills=["carnatic classical", "playback singing"])
    resp = client.get("/api/v1/talents", params={"q": "carnatic"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_browse_filters_by_experience_range(client, talent_headers, db_session):
    create_profile(client, talent_headers, experience_years=2)
    token_b = register_and_verify(client, db_session, "veteran@example.com", role="talent")
    create_profile(client, auth_headers(token_b), display_name="Veteran", experience_years=10)

    resp = client.get("/api/v1/talents", params={"experience_min": 5})
    assert resp.status_code == 200
    names = {t["display_name"] for t in resp.json()}
    assert names == {"Veteran"}


def test_browse_filters_by_instruments(client, talent_headers, db_session):
    create_profile(client, talent_headers, category="music", instruments=["drums", "cajon"])
    token_b = register_and_verify(client, db_session, "violinist@example.com", role="talent")
    create_profile(client, auth_headers(token_b), display_name="Violinist", category="music", instruments=["violin"])

    resp = client.get("/api/v1/talents", params={"instruments": ["drums"]})
    assert resp.status_code == 200
    names = {t["display_name"] for t in resp.json()}
    assert names == {"Test Talent"}

    resp = client.get("/api/v1/talents", params={"instruments": ["drums", "violin"]})
    assert resp.status_code == 200
    names = {t["display_name"] for t in resp.json()}
    assert names == {"Test Talent", "Violinist"}


def test_browse_verified_only_filter(client, talent_headers, db_session):
    from app.models.talent_profile import TalentProfile

    create_profile(client, talent_headers, display_name="Unverified")

    token_b = register_and_verify(client, db_session, "verified@example.com", role="talent")
    verified = create_profile(client, auth_headers(token_b), display_name="Verified")

    # Approving verification isn't exposed over the API (manual review only) — flip it directly.
    profile = db_session.query(TalentProfile).filter(TalentProfile.id == verified["id"]).first()
    profile.is_verified = True
    db_session.commit()

    resp = client.get("/api/v1/talents", params={"verified_only": True})
    assert resp.status_code == 200
    names = {t["display_name"] for t in resp.json()}
    assert names == {"Verified"}


# --- Multiple profiles per account (a guardian managing several children) -------------------
#
# The API still refuses to create a second profile (nothing yet distinguishes a guardian), so
# these insert the second one directly, the same way test_browse_verified_only_filter flips a
# flag the API doesn't expose.


def _add_second_profile(db_session, owner_user_id, *, display_name: str):
    from app.models.talent_profile import TalentProfile

    profile = TalentProfile(user_id=owner_user_id, display_name=display_name, category="singing", categories=["singing"])
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


def test_second_profile_for_same_account_is_allowed_by_the_database(client, talent_headers, talent_profile, db_session):
    from app.models.user import User

    user = db_session.query(User).filter(User.email == "talent_fixture@example.com").first()
    second = _add_second_profile(db_session, user.id, display_name="Second Child")

    assert second.id != talent_profile["id"]
    assert len(user.talent_profiles) == 2


def test_me_requires_choosing_when_the_account_manages_several_profiles(client, talent_headers, talent_profile, db_session):
    from app.models.user import User

    user = db_session.query(User).filter(User.email == "talent_fixture@example.com").first()
    _add_second_profile(db_session, user.id, display_name="Second Child")

    resp = client.get("/api/v1/talents/me", headers=talent_headers)
    assert resp.status_code == 409
    assert "more than one profile" in resp.json()["detail"]


def test_profile_header_selects_which_profile_me_acts_as(client, talent_headers, talent_profile, db_session):
    from app.models.user import User

    user = db_session.query(User).filter(User.email == "talent_fixture@example.com").first()
    second = _add_second_profile(db_session, user.id, display_name="Second Child")

    resp = client.get("/api/v1/talents/me", headers={**talent_headers, "X-Talent-Profile-Id": str(second.id)})
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Second Child"

    resp = client.get("/api/v1/talents/me", headers={**talent_headers, "X-Talent-Profile-Id": talent_profile["id"]})
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Fixture Talent"


def test_cannot_act_as_a_profile_belonging_to_someone_else(client, talent_headers, talent_profile, db_session):
    other_token = register_and_verify(client, db_session, "other_talent@example.com", role="talent")
    other = create_profile(client, auth_headers(other_token), display_name="Not Yours")

    resp = client.get("/api/v1/talents/me", headers={**talent_headers, "X-Talent-Profile-Id": other["id"]})
    assert resp.status_code == 403
    assert "isn't yours" in resp.json()["detail"]


def test_single_profile_accounts_never_need_the_header(client, talent_headers, talent_profile):
    resp = client.get("/api/v1/talents/me", headers=talent_headers)
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Fixture Talent"
