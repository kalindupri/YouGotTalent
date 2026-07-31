def create_title(client, headers, *, name="Superhitha", work_type="film", **extra):
    return client.post(
        "/api/v1/titles",
        json={"name": name, "work_type": work_type, **extra},
        headers=headers,
    )


def test_create_and_list_titles(client, talent_headers, talent_profile):
    resp = create_title(client, talent_headers, name="Aloko Udapadi", work_type="film", release_year=2017, genre="Historical Drama")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "Aloko Udapadi"
    assert body["average_rating"] is None
    assert body["review_count"] == 0

    resp = client.get("/api/v1/titles")
    assert resp.status_code == 200
    assert any(t["name"] == "Aloko Udapadi" for t in resp.json())


def test_search_and_filter_titles(client, talent_headers, talent_profile):
    create_title(client, talent_headers, name="Sanda Diyaniya", work_type="song", genre="Sinhala Pop")
    create_title(client, talent_headers, name="Kolamba Sanniya", work_type="tv_series", genre="Comedy")

    resp = client.get("/api/v1/titles", params={"q": "Sanda"})
    names = [t["name"] for t in resp.json()]
    assert "Sanda Diyaniya" in names
    assert "Kolamba Sanniya" not in names

    resp = client.get("/api/v1/titles", params={"work_type": "tv_series"})
    names = [t["name"] for t in resp.json()]
    assert "Kolamba Sanniya" in names
    assert "Sanda Diyaniya" not in names


def test_get_title_detail_404_for_missing(client):
    resp = client.get("/api/v1/titles/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_public_can_browse_titles_without_login(client, talent_headers, talent_profile):
    create_title(client, talent_headers, name="Public Browse Test")
    resp = client.get("/api/v1/titles")
    assert resp.status_code == 200


def test_creating_title_requires_login(client):
    resp = client.post("/api/v1/titles", json={"name": "No Auth", "work_type": "film"})
    assert resp.status_code == 401


def test_review_upsert_and_average_rating(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    created = create_title(client, talent_headers, name="Rating Test Film").json()
    title_id = created["id"]

    resp = client.post(f"/api/v1/titles/{title_id}/reviews", json={"rating": 4, "body": "Pretty good"}, headers=talent_headers)
    assert resp.status_code == 201, resp.text
    assert resp.json()["author_role"] == "talent"
    assert resp.json()["author_name"] == talent_profile["display_name"]

    resp = client.post(f"/api/v1/titles/{title_id}/reviews", json={"rating": 2}, headers=recruiter_headers)
    assert resp.status_code == 201, resp.text
    assert resp.json()["author_role"] == "recruiter"
    assert resp.json()["author_name"] == recruiter_profile["company_name"]

    resp = client.get(f"/api/v1/titles/{title_id}")
    body = resp.json()
    assert body["average_rating"] == 3.0
    assert body["review_count"] == 2

    # Re-submitting updates the same review rather than creating a second one.
    client.post(f"/api/v1/titles/{title_id}/reviews", json={"rating": 5}, headers=talent_headers)
    resp = client.get(f"/api/v1/titles/{title_id}")
    assert resp.json()["review_count"] == 2


def test_review_rating_must_be_1_to_5(client, talent_headers, talent_profile):
    created = create_title(client, talent_headers).json()
    resp = client.post(f"/api/v1/titles/{created['id']}/reviews", json={"rating": 6}, headers=talent_headers)
    assert resp.status_code == 422


def test_get_and_delete_my_review(client, talent_headers, talent_profile):
    created = create_title(client, talent_headers).json()
    title_id = created["id"]

    assert client.get(f"/api/v1/titles/{title_id}/reviews/mine", headers=talent_headers).json() is None

    client.post(f"/api/v1/titles/{title_id}/reviews", json={"rating": 3}, headers=talent_headers)
    resp = client.get(f"/api/v1/titles/{title_id}/reviews/mine", headers=talent_headers)
    assert resp.json()["rating"] == 3

    resp = client.delete(f"/api/v1/titles/{title_id}/reviews/mine", headers=talent_headers)
    assert resp.status_code == 204
    assert client.get(f"/api/v1/titles/{title_id}/reviews/mine", headers=talent_headers).json() is None


def test_list_reviews_for_title(client, talent_headers, talent_profile):
    created = create_title(client, talent_headers).json()
    client.post(f"/api/v1/titles/{created['id']}/reviews", json={"rating": 5, "body": "Loved it"}, headers=talent_headers)

    resp = client.get(f"/api/v1/titles/{created['id']}/reviews")
    assert resp.status_code == 200
    reviews = resp.json()
    assert len(reviews) == 1
    assert reviews[0]["body"] == "Loved it"


def create_thread(client, headers, *, category="films", subject="Best teledrama of the year?", body="Discuss.", **extra):
    return client.post(
        "/api/v1/discussions",
        json={"category": category, "subject": subject, "body": body, **extra},
        headers=headers,
    )


def test_create_and_list_discussion_threads(client, talent_headers, talent_profile):
    resp = create_thread(client, talent_headers, subject="New Sinhala films worth watching")
    assert resp.status_code == 201, resp.text
    assert resp.json()["author_role"] == "talent"
    assert resp.json()["reply_count"] == 0

    resp = client.get("/api/v1/discussions")
    assert resp.status_code == 200
    assert any(t["subject"] == "New Sinhala films worth watching" for t in resp.json())


def test_filter_discussions_by_category(client, talent_headers, talent_profile):
    create_thread(client, talent_headers, category="music", subject="New album drop")
    create_thread(client, talent_headers, category="industry_news", subject="Studio announcement")

    resp = client.get("/api/v1/discussions", params={"category": "music"})
    subjects = [t["subject"] for t in resp.json()]
    assert "New album drop" in subjects
    assert "Studio announcement" not in subjects


def test_thread_linked_to_title(client, talent_headers, talent_profile):
    title = create_title(client, talent_headers, name="Linked Title").json()
    resp = create_thread(client, talent_headers, subject="About Linked Title", title_id=title["id"])
    assert resp.status_code == 201
    assert resp.json()["title_id"] == title["id"]

    resp = client.get("/api/v1/discussions", params={"title_id": title["id"]})
    assert len(resp.json()) == 1


def test_creating_thread_requires_login(client):
    resp = client.post("/api/v1/discussions", json={"category": "general", "subject": "x", "body": "y"})
    assert resp.status_code == 401


def test_thread_detail_and_replies(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    thread = create_thread(client, talent_headers).json()

    resp = client.get(f"/api/v1/discussions/{thread['id']}")
    assert resp.status_code == 200
    assert resp.json()["subject"] == thread["subject"]

    resp = client.post(f"/api/v1/discussions/{thread['id']}/replies", json={"body": "Great question!"}, headers=recruiter_headers)
    assert resp.status_code == 201, resp.text
    assert resp.json()["author_role"] == "recruiter"

    resp = client.get(f"/api/v1/discussions/{thread['id']}/replies")
    assert len(resp.json()) == 1

    resp = client.get(f"/api/v1/discussions/{thread['id']}")
    assert resp.json()["reply_count"] == 1


def test_replying_requires_login(client, talent_headers, talent_profile):
    thread = create_thread(client, talent_headers).json()
    resp = client.post(f"/api/v1/discussions/{thread['id']}/replies", json={"body": "no auth"})
    assert resp.status_code == 401


def test_reply_to_missing_thread_404s(client, talent_headers, talent_profile):
    resp = client.post(
        "/api/v1/discussions/00000000-0000-0000-0000-000000000000/replies",
        json={"body": "x"},
        headers=talent_headers,
    )
    assert resp.status_code == 404


def test_admin_can_delete_community_content(client, admin_headers, talent_headers, talent_profile):
    title = create_title(client, talent_headers).json()
    client.post(f"/api/v1/titles/{title['id']}/reviews", json={"rating": 4}, headers=talent_headers)
    review_id = client.get(f"/api/v1/titles/{title['id']}/reviews/mine", headers=talent_headers).json()["id"]
    thread = create_thread(client, talent_headers).json()
    reply_id = client.post(f"/api/v1/discussions/{thread['id']}/replies", json={"body": "reply"}, headers=talent_headers).json()["id"]

    assert client.delete(f"/api/v1/admin/community/replies/{reply_id}", headers=admin_headers).status_code == 204
    assert client.delete(f"/api/v1/admin/community/threads/{thread['id']}", headers=admin_headers).status_code == 204
    assert client.delete(f"/api/v1/admin/community/reviews/{review_id}", headers=admin_headers).status_code == 204
    assert client.delete(f"/api/v1/admin/community/titles/{title['id']}", headers=admin_headers).status_code == 204

    assert client.get(f"/api/v1/titles/{title['id']}").status_code == 404


def test_non_admin_cannot_delete_community_content(client, talent_headers, talent_profile):
    title = create_title(client, talent_headers).json()
    assert client.delete(f"/api/v1/admin/community/titles/{title['id']}", headers=talent_headers).status_code == 403


def test_report_accepts_new_community_target_types(client, talent_headers, talent_profile):
    title = create_title(client, talent_headers).json()
    resp = client.post(
        "/api/v1/reports",
        json={
            "category": "inappropriate_content",
            "target_type": "title",
            "target_id": title["id"],
            "subject": "Inappropriate poster",
            "description": "This title's synopsis is inappropriate.",
        },
        headers=talent_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["target_type"] == "title"
