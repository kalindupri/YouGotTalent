from tests.conftest import ADULT_DOB, auth_headers, register_and_verify


def add_sample(client, headers, *, title="Chapter One", writing_type="novel", language="english", body=None, **kwargs):
    payload = {
        "title": title,
        "writing_type": writing_type,
        "language": language,
        "body": body or "\n".join(f"Line {i}" for i in range(1, 21)),
        **kwargs,
    }
    return client.post("/api/v1/talents/me/writing-samples", json=payload, headers=headers)


def test_draft_sample_not_visible_to_public(client, talent_headers, writer_profile):
    resp = add_sample(client, talent_headers, is_published=False)
    assert resp.status_code == 201, resp.text

    profile_resp = client.get(f"/api/v1/talents/{writer_profile['id']}")
    assert profile_resp.json()["writing_samples"] == []


def test_owner_sees_own_draft_via_public_profile_when_authenticated(client, talent_headers, writer_profile):
    add_sample(client, talent_headers, is_published=False)

    profile_resp = client.get(f"/api/v1/talents/{writer_profile['id']}", headers=talent_headers)
    samples = profile_resp.json()["writing_samples"]
    assert len(samples) == 1
    assert samples[0]["is_excerpt"] is False


def test_published_sample_truncated_to_visible_lines_for_non_owner(client, db_session, talent_headers, writer_profile):
    body = "\n".join(f"Line {i}" for i in range(1, 21))  # 20 lines
    resp = add_sample(client, talent_headers, body=body, visible_lines=5, is_published=True)
    assert resp.status_code == 201, resp.text
    assert resp.json()["body"] == body  # owner (creator) gets the full text back

    other_token = register_and_verify(client, db_session, "reader1@example.com", full_name="Reader One")
    other_headers = auth_headers(other_token)
    resp = client.post(
        "/api/v1/talents/me",
        json={"date_of_birth": ADULT_DOB, "display_name": "Reader One", "category": "acting", "city": "Kandy"},
        headers=other_headers,
    )
    assert resp.status_code == 201, resp.text

    profile_resp = client.get(f"/api/v1/talents/{writer_profile['id']}", headers=other_headers)
    samples = profile_resp.json()["writing_samples"]
    assert len(samples) == 1
    assert samples[0]["body"] == "\n".join(f"Line {i}" for i in range(1, 6))
    assert samples[0]["is_excerpt"] is True


def test_guest_gets_truncated_body_too(client, talent_headers, writer_profile):
    body = "\n".join(f"Line {i}" for i in range(1, 21))
    add_sample(client, talent_headers, body=body, visible_lines=3, is_published=True)

    profile_resp = client.get(f"/api/v1/talents/{writer_profile['id']}")
    samples = profile_resp.json()["writing_samples"]
    assert samples[0]["body"] == "\n".join(f"Line {i}" for i in range(1, 4))
    assert samples[0]["is_excerpt"] is True


def test_short_piece_under_visible_lines_is_not_marked_excerpt(client, talent_headers, writer_profile):
    add_sample(client, talent_headers, body="Only two\nlines here", visible_lines=8, is_published=True)

    profile_resp = client.get(f"/api/v1/talents/{writer_profile['id']}")
    samples = profile_resp.json()["writing_samples"]
    assert samples[0]["body"] == "Only two\nlines here"
    assert samples[0]["is_excerpt"] is False


def test_invalid_writing_type_rejected(client, talent_headers, writer_profile):
    resp = add_sample(client, talent_headers, writing_type="screenplay-of-doom")
    assert resp.status_code == 400


def test_invalid_language_rejected(client, talent_headers, writer_profile):
    resp = add_sample(client, talent_headers, language="klingon")
    assert resp.status_code == 400


def test_all_supported_languages_accepted(client, talent_headers, writer_profile):
    for language in ["sinhala", "tamil", "english", "other"]:
        resp = add_sample(client, talent_headers, title=f"Piece in {language}", language=language)
        assert resp.status_code == 201, resp.text


def test_all_supported_writing_types_accepted(client, talent_headers, writer_profile):
    for writing_type in ["novel", "script", "song", "poem", "other"]:
        resp = add_sample(client, talent_headers, title=f"A {writing_type}", writing_type=writing_type)
        assert resp.status_code == 201, resp.text


def test_free_tier_publish_limit_enforced(client, talent_headers, writer_profile):
    for i in range(3):
        resp = add_sample(client, talent_headers, title=f"Piece {i}", is_published=True)
        assert resp.status_code == 201, resp.text

    resp = add_sample(client, talent_headers, title="Piece overflow", is_published=True)
    assert resp.status_code == 403
    assert "limit" in resp.json()["detail"].lower() or "3" in resp.json()["detail"]


def test_free_tier_drafts_dont_count_toward_publish_limit(client, talent_headers, writer_profile):
    for i in range(5):
        resp = add_sample(client, talent_headers, title=f"Draft {i}", is_published=False)
        assert resp.status_code == 201, resp.text

    resp = add_sample(client, talent_headers, title="First publish", is_published=True)
    assert resp.status_code == 201, resp.text


def test_premium_talent_not_limited(client, talent_headers, writer_profile):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200
    for i in range(5):
        resp = add_sample(client, talent_headers, title=f"Piece {i}", is_published=True)
        assert resp.status_code == 201, resp.text


def test_talent_edits_own_draft_then_publishes(client, talent_headers, writer_profile):
    sample = add_sample(client, talent_headers, title="Draft title", is_published=False).json()

    resp = client.patch(
        f"/api/v1/talents/me/writing-samples/{sample['id']}",
        json={"title": "Final title", "is_published": True, "visible_lines": 4},
        headers=talent_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["title"] == "Final title"
    assert body["is_published"] is True
    assert body["visible_lines"] == 4


def test_talent_lists_own_samples_including_drafts(client, talent_headers, writer_profile):
    add_sample(client, talent_headers, title="Published one", is_published=True)
    add_sample(client, talent_headers, title="Draft one", is_published=False)

    resp = client.get("/api/v1/talents/me/writing-samples", headers=talent_headers)
    assert resp.status_code == 200
    titles = {s["title"] for s in resp.json()}
    assert titles == {"Published one", "Draft one"}


def test_talent_deletes_own_sample(client, talent_headers, writer_profile):
    sample = add_sample(client, talent_headers, is_published=True).json()

    resp = client.delete(f"/api/v1/talents/me/writing-samples/{sample['id']}", headers=talent_headers)
    assert resp.status_code == 204

    profile_resp = client.get(f"/api/v1/talents/{writer_profile['id']}")
    assert profile_resp.json()["writing_samples"] == []


def test_talent_cannot_edit_or_delete_another_talents_sample(client, db_session, talent_headers, writer_profile):
    sample = add_sample(client, talent_headers, is_published=True).json()

    other_token = register_and_verify(client, db_session, "other_writer@example.com", full_name="Other Writer")
    other_headers = auth_headers(other_token)
    resp = client.post(
        "/api/v1/talents/me",
        json={"date_of_birth": ADULT_DOB, "display_name": "Other Writer", "category": "script_writing", "city": "Galle"},
        headers=other_headers,
    )
    assert resp.status_code == 201, resp.text

    resp = client.patch(
        f"/api/v1/talents/me/writing-samples/{sample['id']}", json={"title": "Hijacked"}, headers=other_headers
    )
    assert resp.status_code == 404

    resp = client.delete(f"/api/v1/talents/me/writing-samples/{sample['id']}", headers=other_headers)
    assert resp.status_code == 404


def test_writing_samples_are_refused_for_non_writing_categories(client, talent_headers, talent_profile):
    """An acting-only profile has no business publishing scripts or lyrics -- and the check is
    server-side, so hiding the card in the UI isn't the only thing stopping it.
    """
    resp = add_sample(client, talent_headers)
    assert resp.status_code == 403
    assert "script writers and songwriters" in resp.json()["detail"]


def test_a_songwriter_under_the_music_category_can_add_them(client, talent_headers):
    resp = client.post(
        "/api/v1/talents/me",
        json={
            "display_name": "Songwriter",
            "categories": ["music"],
            "date_of_birth": ADULT_DOB,
        },
        headers=talent_headers,
    )
    assert resp.status_code == 201, resp.text
    assert add_sample(client, talent_headers, writing_type="song").status_code == 201
