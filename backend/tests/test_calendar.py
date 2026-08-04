from datetime import date, timedelta

from tests.conftest import auth_headers, register_and_verify
from tests.test_bookings import next_weekday_at


def create_entry(client, talent_headers, *, title="Wedding gig", days_from_today=5, span=1, is_public=True, notes=None):
    start = date.today() + timedelta(days=days_from_today)
    end = start + timedelta(days=span)
    resp = client.post(
        "/api/v1/talents/me/calendar-entries",
        json={
            "title": title,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "notes": notes,
            "is_public": is_public,
        },
        headers=talent_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_talent_creates_and_lists_calendar_entry(client, talent_headers, talent_profile):
    entry = create_entry(client, talent_headers)
    assert entry["title"] == "Wedding gig"

    resp = client.get("/api/v1/talents/me/calendar-entries", headers=talent_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_calendar_entry_rejects_end_before_start(client, talent_headers, talent_profile):
    start = date.today() + timedelta(days=5)
    resp = client.post(
        "/api/v1/talents/me/calendar-entries",
        json={"title": "Bad entry", "start_date": start.isoformat(), "end_date": (start - timedelta(days=1)).isoformat()},
        headers=talent_headers,
    )
    assert resp.status_code == 422


def test_talent_deletes_own_calendar_entry(client, talent_headers, talent_profile):
    entry = create_entry(client, talent_headers)
    resp = client.delete(f"/api/v1/talents/me/calendar-entries/{entry['id']}", headers=talent_headers)
    assert resp.status_code == 204

    resp = client.get("/api/v1/talents/me/calendar-entries", headers=talent_headers)
    assert resp.json() == []


def test_talent_cannot_delete_another_talents_calendar_entry(client, db_session, talent_headers, talent_profile):
    entry = create_entry(client, talent_headers)

    other_token = register_and_verify(client, db_session, "other_talent_calendar@example.com", full_name="Other Talent")
    other_headers = auth_headers(other_token)
    resp = client.post(
        "/api/v1/talents/me",
        json={"display_name": "Other Talent", "category": "acting", "city": "Kandy"},
        headers=other_headers,
    )
    assert resp.status_code == 201, resp.text

    resp = client.delete(f"/api/v1/talents/me/calendar-entries/{entry['id']}", headers=other_headers)
    assert resp.status_code == 404


def test_monthly_calendar_includes_entry_in_matching_month(client, talent_headers, talent_profile):
    today = date.today()
    entry = create_entry(client, talent_headers, days_from_today=3)
    month = today.strftime("%Y-%m")

    resp = client.get(f"/api/v1/talents/me/calendar?month={month}", headers=talent_headers)
    assert resp.status_code == 200
    events = resp.json()
    assert any(e["kind"] == "entry" and e["id"] == entry["id"] for e in events)


def test_monthly_calendar_rejects_bad_month_format(client, talent_headers, talent_profile):
    resp = client.get("/api/v1/talents/me/calendar?month=2026-13", headers=talent_headers)
    assert resp.status_code == 400


def test_monthly_calendar_includes_accepted_booking(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    resp = client.post(
        "/api/v1/talents/me/availability",
        json={"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00"},
        headers=talent_headers,
    )
    assert resp.status_code == 201, resp.text

    start = next_weekday_at(0, 10)
    resp = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat(), "message": "Let's meet"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text
    booking_id = resp.json()["id"]

    month = start.strftime("%Y-%m")
    resp = client.get(f"/api/v1/talents/me/calendar?month={month}", headers=talent_headers)
    assert resp.status_code == 200
    events = resp.json()
    assert any(e["kind"] == "booking" and e["id"] == booking_id for e in events)


def test_monthly_calendar_sorts_mixed_bookings_and_entries(
    client, talent_headers, talent_profile, recruiter_headers, recruiter_profile
):
    resp = client.post(
        "/api/v1/talents/me/availability",
        json={"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00"},
        headers=talent_headers,
    )
    assert resp.status_code == 201, resp.text

    start = next_weekday_at(0, 10)
    resp = client.post(
        f"/api/v1/talents/{talent_profile['id']}/bookings",
        json={"start_at": start.isoformat(), "end_at": (start + timedelta(hours=1)).isoformat(), "message": "Let's meet"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text
    booking_id = resp.json()["id"]

    entry_start = start.date()
    entry = create_entry(client, talent_headers, days_from_today=(entry_start - date.today()).days)

    month = start.strftime("%Y-%m")
    resp = client.get(f"/api/v1/talents/me/calendar?month={month}", headers=talent_headers)
    assert resp.status_code == 200
    events = resp.json()
    kinds_and_ids = {(e["kind"], e["id"]) for e in events}
    assert ("booking", booking_id) in kinds_and_ids
    assert ("entry", entry["id"]) in kinds_and_ids


def test_public_busy_dates_shows_title_only_when_public(client, talent_headers, talent_profile):
    create_entry(client, talent_headers, title="Private thing", is_public=False, days_from_today=10)
    create_entry(client, talent_headers, title="Public gig", is_public=True, days_from_today=20)

    resp = client.get(f"/api/v1/talents/{talent_profile['id']}/calendar/busy-dates")
    assert resp.status_code == 200
    ranges = resp.json()
    assert len(ranges) == 2
    titles = {r["title"] for r in ranges}
    assert "Public gig" in titles
    assert "Private thing" not in titles
    assert None in titles


def test_busy_dates_for_unknown_talent_returns_404(client):
    resp = client.get("/api/v1/talents/00000000-0000-0000-0000-000000000000/calendar/busy-dates")
    assert resp.status_code == 404
