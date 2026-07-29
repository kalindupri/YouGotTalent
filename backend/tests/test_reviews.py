from datetime import datetime, timedelta, timezone


def next_weekday_at(day_of_week: int, hour: int) -> datetime:
    now = datetime.now(timezone.utc)
    days_ahead = (day_of_week - now.weekday()) % 7
    days_ahead = days_ahead if days_ahead > 0 else 7
    return (now + timedelta(days=days_ahead)).replace(hour=hour, minute=0, second=0, microsecond=0)


def create_accepted_booking(client, talent_headers, talent_profile, recruiter_headers, day_of_week=0):
    client.post(
        "/api/v1/talents/me/availability",
        json={"day_of_week": day_of_week, "start_time": "09:00:00", "end_time": "17:00:00"},
        headers=talent_headers,
    )
    start = next_weekday_at(day_of_week, 10)
    booking = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    ).json()
    client.patch(f"/api/v1/bookings/{booking['id']}/respond", json={"status": "accepted"}, headers=talent_headers)
    return booking


def test_recruiter_reviews_talent(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    booking = create_accepted_booking(client, talent_headers, talent_profile, recruiter_headers)

    resp = client.post(
        f"/api/v1/bookings/{booking['id']}/reviews",
        json={"rating": 5, "comment": "Great to work with"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["reviewer_role"] == "recruiter"
    assert body["rating"] == 5
    assert body["reviewer_name"] == recruiter_profile["company_name"]

    resp = client.get(f"/api/v1/talents/{talent_profile['id']}/reviews")
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["review_count"] == 1
    assert summary["average_rating"] == 5.0


def test_talent_reviews_recruiter(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    booking = create_accepted_booking(client, talent_headers, talent_profile, recruiter_headers)

    resp = client.post(
        f"/api/v1/bookings/{booking['id']}/reviews",
        json={"rating": 4},
        headers=talent_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["reviewer_role"] == "talent"
    assert resp.json()["reviewer_name"] == talent_profile["display_name"]

    resp = client.get("/api/v1/recruiters/me/reviews", headers=recruiter_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["rating"] == 4


def test_average_rating_across_multiple_reviews(client, db_session, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    from tests.conftest import auth_headers, register_and_verify

    booking1 = create_accepted_booking(client, talent_headers, talent_profile, recruiter_headers)
    client.post(f"/api/v1/bookings/{booking1['id']}/reviews", json={"rating": 5}, headers=recruiter_headers)

    other_recruiter_token = register_and_verify(client, db_session, "otherreviewer@example.com", role="recruiter")
    other_recruiter_headers = auth_headers(other_recruiter_token)
    client.post("/api/v1/recruiters/me", json={"company_name": "Other Studios"}, headers=other_recruiter_headers)

    booking2 = create_accepted_booking(client, talent_headers, talent_profile, other_recruiter_headers, day_of_week=1)
    client.post(f"/api/v1/bookings/{booking2['id']}/reviews", json={"rating": 3}, headers=other_recruiter_headers)

    resp = client.get(f"/api/v1/talents/{talent_profile['id']}/reviews")
    body = resp.json()
    assert body["review_count"] == 2
    assert body["average_rating"] == 4.0


def test_duplicate_review_from_same_role_rejected(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    booking = create_accepted_booking(client, talent_headers, talent_profile, recruiter_headers)
    client.post(f"/api/v1/bookings/{booking['id']}/reviews", json={"rating": 5}, headers=recruiter_headers)
    resp = client.post(f"/api/v1/bookings/{booking['id']}/reviews", json={"rating": 2}, headers=recruiter_headers)
    assert resp.status_code == 400


def test_review_rejected_before_booking_accepted(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    client.post(
        "/api/v1/talents/me/availability",
        json={"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00"},
        headers=talent_headers,
    )
    start = next_weekday_at(0, 10)
    booking = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=recruiter_headers,
    ).json()

    resp = client.post(f"/api/v1/bookings/{booking['id']}/reviews", json={"rating": 5}, headers=recruiter_headers)
    assert resp.status_code == 400


def test_review_rating_out_of_range_rejected(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    booking = create_accepted_booking(client, talent_headers, talent_profile, recruiter_headers)
    resp = client.post(f"/api/v1/bookings/{booking['id']}/reviews", json={"rating": 6}, headers=recruiter_headers)
    assert resp.status_code == 422


def test_non_party_cannot_review_booking(client, db_session, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    from tests.conftest import auth_headers, register_and_verify

    booking = create_accepted_booking(client, talent_headers, talent_profile, recruiter_headers)

    other_token = register_and_verify(client, db_session, "notparty@example.com", role="talent")
    other_headers = auth_headers(other_token)
    client.post("/api/v1/talents/me", json={"display_name": "Not Party", "category": "acting"}, headers=other_headers)

    resp = client.post(f"/api/v1/bookings/{booking['id']}/reviews", json={"rating": 5}, headers=other_headers)
    assert resp.status_code == 404
