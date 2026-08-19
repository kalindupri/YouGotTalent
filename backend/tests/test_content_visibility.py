from tests.conftest import auth_headers, register_and_verify


def add_media(client, headers, *, visibility="public", url="https://example.com/a.jpg"):
    payload = {"url": url, "media_type": "photo", "title": "T"}
    if visibility is not None:
        payload["visibility"] = visibility
    resp = client.post("/api/v1/talents/me/media", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def add_reel(client, headers, *, visibility="public", url="https://www.tiktok.com/@user/video/1"):
    payload = {"url": url, "visibility": visibility}
    resp = client.post("/api/v1/talents/me/reels", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def add_library_item(client, headers, *, visibility="public", url="https://soundcloud.com/example/1"):
    resp = client.post(
        "/api/v1/talents/me/library",
        json={"title": "Item", "media_type": "audio", "url": url, "visibility": visibility},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def get_public_media_ids(client, talent_id, headers=None):
    resp = client.get(f"/api/v1/talents/{talent_id}", headers=headers or {})
    assert resp.status_code == 200
    return {m["id"] for m in resp.json()["media"]}, {r["id"] for r in resp.json()["reels"]}


def test_default_visibility_is_public(client, talent_headers, talent_profile):
    media = add_media(client, talent_headers, visibility=None)
    assert media["visibility"] == "public"

    media_ids, _ = get_public_media_ids(client, talent_profile["id"])
    assert media["id"] in media_ids


def test_members_only_media_hidden_from_guest_visible_to_logged_in_talent(client, db_session, talent_headers, talent_profile):
    media = add_media(client, talent_headers, visibility="members")

    guest_ids, _ = get_public_media_ids(client, talent_profile["id"])
    assert media["id"] not in guest_ids

    other_token = register_and_verify(client, db_session, "viewer_member@example.com", full_name="Viewer Member")
    other_headers = auth_headers(other_token)
    member_ids, _ = get_public_media_ids(client, talent_profile["id"], other_headers)
    assert media["id"] in member_ids


def test_recruiters_only_reel_hidden_from_talent_visible_to_recruiter(
    client, db_session, talent_headers, talent_profile, recruiter_headers, recruiter_profile
):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200
    reel = add_reel(client, talent_headers, visibility="recruiters")

    guest_ids, guest_reel_ids = get_public_media_ids(client, talent_profile["id"])
    assert reel["id"] not in guest_reel_ids

    other_token = register_and_verify(client, db_session, "viewer_talent@example.com", full_name="Viewer Talent")
    other_headers = auth_headers(other_token)
    _, talent_reel_ids = get_public_media_ids(client, talent_profile["id"], other_headers)
    assert reel["id"] not in talent_reel_ids

    _, recruiter_reel_ids = get_public_media_ids(client, talent_profile["id"], recruiter_headers)
    assert reel["id"] in recruiter_reel_ids


def test_library_item_visibility_filtered_on_public_route(client, db_session, talent_headers, talent_profile):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200
    public_item = add_library_item(client, talent_headers, visibility="public", url="https://example.com/pub")
    recruiters_item = add_library_item(client, talent_headers, visibility="recruiters", url="https://example.com/rec")

    resp = client.get(f"/api/v1/talents/{talent_profile['id']}/library")
    assert resp.status_code == 200
    ids = {item["id"] for item in resp.json()}
    assert public_item["id"] in ids
    assert recruiters_item["id"] not in ids


def test_owner_sees_all_their_own_content_regardless_of_tier(client, talent_headers, talent_profile):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200
    add_media(client, talent_headers, visibility="recruiters", url="https://example.com/mine.jpg")

    resp = client.get("/api/v1/talents/me", headers=talent_headers)
    assert resp.status_code == 200
    assert len(resp.json()["media"]) == 1


# --- "Only me" visibility -------------------------------------------------------------------


def test_private_media_is_visible_only_to_its_owner(client, db_session, talent_headers, talent_profile, recruiter_headers, recruiter_profile, admin_headers):
    """"Only me" is checked before the admin short-circuit. Labelling something "Only me" and
    then showing it to staff would be a false promise, and there is nothing to moderate in
    content nobody else can reach.
    """
    resp = client.post(
        "/api/v1/talents/me/media",
        json={"url": "https://example.com/secret.jpg", "media_type": "photo", "title": "WIP", "visibility": "private"},
        headers=talent_headers,
    )
    assert resp.status_code == 201, resp.text

    def titles_for(headers=None):
        body = client.get(f"/api/v1/talents/{talent_profile['id']}", headers=headers or {}).json()
        return {m["title"] for m in body["media"]}

    assert "WIP" in titles_for(talent_headers)   # the owner
    assert "WIP" not in titles_for()             # a guest
    assert "WIP" not in titles_for(recruiter_headers)
    assert "WIP" not in titles_for(admin_headers)


def test_private_is_a_valid_visibility_on_every_content_type(client, talent_headers, talent_profile):
    media = client.post(
        "/api/v1/talents/me/media",
        json={"url": "https://example.com/a.jpg", "media_type": "photo", "visibility": "private"},
        headers=talent_headers,
    )
    assert media.status_code == 201
    assert media.json()["visibility"] == "private"

    sample = client.post(
        "/api/v1/talents/me/writing-samples",
        json={
            "title": "Private draft",
            "writing_type": "poem",
            "language": "english",
            "body": "one\ntwo",
            "visibility": "private",
            "is_published": True,
        },
        headers=talent_headers,
    )
    assert sample.status_code == 201
    assert sample.json()["visibility"] == "private"


def test_a_published_but_private_writing_sample_stays_hidden(client, talent_headers, talent_profile):
    client.post(
        "/api/v1/talents/me/writing-samples",
        json={
            "title": "Not for anyone",
            "writing_type": "poem",
            "language": "english",
            "body": "one\ntwo",
            "visibility": "private",
            "is_published": True,
        },
        headers=talent_headers,
    )
    body = client.get(f"/api/v1/talents/{talent_profile['id']}").json()
    assert [s["title"] for s in body["writing_samples"]] == []
