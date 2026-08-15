"""Backfills gender/date_of_birth/experience_years/instruments/tiktok_followers on
EXISTING talent profiles that don't have them set -- for demoing/testing the smart
talent search (see app/core/talent_search_parse.py). Only ever touches rows where the
field is currently NULL, so it never overwrites anything a real talent has set
themselves; safe to re-run.

Usage:
    python scripts/backfill_test_characteristics.py
"""
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal  # noqa: E402
from app.models.talent_profile import TalentProfile  # noqa: E402

MUSIC_INSTRUMENT_POOL = [
    ["drums", "tabla"],
    ["percussion", "cajon"],
    ["guitar"],
    ["piano", "keyboard"],
    ["violin"],
    ["flute"],
    ["sitar"],
    ["bass", "guitar"],
]


def random_birthdate(min_age: int, max_age: int) -> date:
    age_days = random.randint(min_age * 365, max_age * 365)
    return date.today() - timedelta(days=age_days)


def main() -> None:
    db = SessionLocal()
    updated = 0
    try:
        profiles = db.query(TalentProfile).all()
        random.seed(42)  # deterministic, so re-runs produce the same test data
        for i, profile in enumerate(profiles):
            changed = False
            if profile.gender is None:
                profile.gender = "male" if i % 2 == 0 else "female"
                changed = True
            if profile.date_of_birth is None:
                # Spread across a realistic casting-relevant range, skewed so plenty
                # land both under and over 35 for age-filter testing.
                profile.date_of_birth = random_birthdate(18, 60)
                changed = True
            if profile.experience_years is None:
                profile.experience_years = random.choice([0, 0, 1, 2, 3, 5, 7, 10, 15])
                changed = True
            if profile.category == "music" and not profile.instruments:
                profile.instruments = random.choice(MUSIC_INSTRUMENT_POOL)
                changed = True
            if profile.category == "content_creator" and profile.tiktok_followers is None:
                profile.tiktok_followers = random.choice([5000, 25000, 80000, 120000, 250000, 500000])
                changed = True
            if changed:
                updated += 1
        db.commit()
        print(f"Backfilled characteristics on {updated} of {len(profiles)} talent profiles.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
