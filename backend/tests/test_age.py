"""Age arithmetic and date-of-birth validation.

Age is not cosmetic here: it decides whether a guardian's consent is required and whether a
talent may be offered paid work, so the boundaries are pinned rather than assumed.
"""
from datetime import date, timedelta

import pytest

from app.core.age import calculate_age, today_lk, years_ago
from tests.conftest import ADULT_DOB


# --- calculate_age -------------------------------------------------------------------------


def test_age_on_the_exact_birthday():
    assert calculate_age(date(2008, 6, 15), on=date(2026, 6, 15)) == 18


def test_age_the_day_before_the_birthday_is_still_a_year_less():
    # The case that decides whether someone is a minor for one more day.
    assert calculate_age(date(2008, 6, 15), on=date(2026, 6, 14)) == 17


def test_age_the_day_after_the_birthday():
    assert calculate_age(date(2008, 6, 15), on=date(2026, 6, 16)) == 18


def test_born_today_is_zero():
    assert calculate_age(date(2026, 6, 15), on=date(2026, 6, 15)) == 0


def test_a_leap_day_birthday_in_a_non_leap_year():
    # Someone born 29 Feb 2008 turns 18 in 2026, a non-leap year. Before 1 March they are 17.
    assert calculate_age(date(2008, 2, 29), on=date(2026, 2, 28)) == 17
    assert calculate_age(date(2008, 2, 29), on=date(2026, 3, 1)) == 18


def test_a_future_date_of_birth_gives_a_negative_age():
    # Nothing should ever store one, but the gates must not read a future date as "old enough".
    assert calculate_age(date(2030, 1, 1), on=date(2026, 1, 1)) < 0


def test_calculate_age_defaults_to_sri_lankan_today():
    # The server runs UTC; Colombo is 5h30m ahead. A date of birth of "today in Colombo" must
    # read as age 0, which it wouldn't if this used date.today() during the overlap window.
    assert calculate_age(today_lk()) == 0


# --- years_ago, and its agreement with calculate_age ---------------------------------------


def test_years_ago_is_the_plain_calendar_answer():
    assert years_ago(18, on=date(2026, 6, 15)) == date(2008, 6, 15)


def test_years_ago_handles_a_leap_day_reference():
    assert years_ago(1, on=date(2024, 2, 29)) == date(2023, 2, 28)


@pytest.mark.parametrize("threshold", [16, 18])
@pytest.mark.parametrize("offset_days", [-2, -1, 0, 1, 2])
def test_the_sql_filter_and_the_python_gate_agree_at_the_boundary(threshold, offset_days):
    """`date_of_birth <= years_ago(n)` is how search filters ask "at least n years old", while
    the gates ask `calculate_age(dob) >= n`. If those two ever disagreed, a talent could be
    filtered out of search but still be bookable (or the reverse).
    """
    reference = date(2026, 6, 15)
    dob = years_ago(threshold, on=reference) + timedelta(days=offset_days)

    sql_says_old_enough = dob <= years_ago(threshold, on=reference)
    python_says_old_enough = calculate_age(dob, on=reference) >= threshold

    assert sql_says_old_enough == python_says_old_enough


# --- Date-of-birth validation over the API -------------------------------------------------


def _create(client, headers, **overrides):
    payload = {"display_name": "DOB Test", "category": "acting", "date_of_birth": ADULT_DOB}
    payload.update(overrides)
    return client.post("/api/v1/talents/me", json=payload, headers=headers)


def test_date_of_birth_is_required(client, talent_headers):
    resp = client.post(
        "/api/v1/talents/me",
        json={"display_name": "No DOB", "category": "acting"},
        headers=talent_headers,
    )
    assert resp.status_code == 422


def test_a_future_date_of_birth_is_rejected(client, talent_headers):
    tomorrow = (today_lk() + timedelta(days=1)).isoformat()
    resp = _create(client, talent_headers, date_of_birth=tomorrow)
    assert resp.status_code == 422
    assert "future" in resp.text.lower()


def test_an_implausibly_old_date_of_birth_is_rejected(client, talent_headers):
    resp = _create(client, talent_headers, date_of_birth="1850-01-01")
    assert resp.status_code == 422


def test_todays_date_is_accepted(client, talent_headers):
    # A newborn is a legitimate profile on a casting platform (Spotlight starts at 6 months),
    # and more importantly "today" must not trip the future-date check across timezones.
    resp = _create(client, talent_headers, date_of_birth=today_lk().isoformat())
    assert resp.status_code == 201, resp.text


def test_date_of_birth_can_be_corrected(client, talent_headers, talent_profile):
    resp = client.patch(
        "/api/v1/talents/me", json={"date_of_birth": "1990-01-01"}, headers=talent_headers
    )
    assert resp.status_code == 200
    assert resp.json()["date_of_birth"] == "1990-01-01"


def test_date_of_birth_cannot_be_cleared(client, talent_headers, talent_profile):
    # Clearing it would drop the profile out of every age check, so an explicit null is refused
    # even though every other field on this schema treats null as "leave alone".
    resp = client.patch("/api/v1/talents/me", json={"date_of_birth": None}, headers=talent_headers)
    assert resp.status_code == 422


def test_omitting_date_of_birth_on_a_partial_update_leaves_it_alone(client, talent_headers, talent_profile):
    resp = client.patch("/api/v1/talents/me", json={"city": "Galle"}, headers=talent_headers)
    assert resp.status_code == 200
    assert resp.json()["city"] == "Galle"
    assert resp.json()["date_of_birth"] == ADULT_DOB
