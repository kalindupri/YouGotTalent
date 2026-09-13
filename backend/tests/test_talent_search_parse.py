"""The natural-language search parser.

Untested until now, which was tolerable while it fed an optional "Smart search" button and a
row of read-only "Detected:" chips. It is not tolerable once the chips become the filter UI and
the parse runs on every search: a wrong parse then silently narrows results with no box for the
recruiter to look at and correct.
"""
from app.core.talent_search_parse import parse_talent_search_query as parse


# --- City ------------------------------------------------------------------------------------
# The important one. Keyword search covers name, skills, category, bio, instruments and
# attributes -- NOT city. So a city left in `keywords` matched only talent who happened to name
# it in their bio, and missed everyone who simply lives there.

def test_city_is_parsed_out_of_the_query_not_left_as_a_keyword():
    r = parse("singer in Kandy under 25")
    assert r["city"] == "Kandy"
    assert r["categories"] == ["singing"]
    assert r["age_max"] == 24
    assert not r["keywords"], "the city must not also survive as a keyword"


def test_multi_word_city_wins_over_its_fragments():
    r = parse("actor nuwara eliya")
    assert r["city"] == "Nuwara Eliya"
    assert not r["keywords"]


def test_city_matching_is_case_insensitive():
    assert parse("dancer colombo")["city"] == "Colombo"
    assert parse("dancer COLOMBO")["city"] == "Colombo"


def test_an_unknown_place_still_falls_through_to_keywords():
    # The list is deliberately not exhaustive; an unrecognised town must degrade to the old
    # behaviour rather than being dropped from the query altogether.
    r = parse("singer in Ambalangoda")
    assert r["city"] is None
    assert "ambalangoda" in (r["keywords"] or "").lower()


# --- Ranges and flags -------------------------------------------------------------------------

def test_bare_numeric_age_range_is_parsed():
    r = parse("female dancer colombo 18-24")
    assert (r["age_min"], r["age_max"]) == (18, 24)
    assert r["gender"] == "female"
    assert r["city"] == "Colombo"


def test_an_implausible_bare_range_is_not_read_as_an_age():
    # Guards against a fragment of a phone number or a year being read as ages.
    r = parse("singer 1990-2024")
    assert r["age_min"] is None and r["age_max"] is None


def test_verified_is_a_filter_not_a_keyword():
    r = parse("verified photographer galle over 30")
    assert r["verified_only"] is True
    assert r["city"] == "Galle"
    assert r["age_min"] == 31
    assert "verified" not in (r["keywords"] or "").lower()


def test_verified_defaults_to_false():
    assert parse("photographer")["verified_only"] is False


# --- Behaviour the UI now leans on ------------------------------------------------------------

def test_craft_gender_and_age_together():
    r = parse("actor wanted under 35 male with some experience")
    assert r["categories"] == ["acting"]
    assert r["gender"] == "male"
    assert r["age_max"] == 34
    assert r["experience_min"] == 1


def test_a_plain_craft_word_parses_to_a_category_and_nothing_else():
    r = parse("singer")
    assert r["categories"] == ["singing"]
    assert not r["keywords"]
    assert r["city"] is None and r["gender"] is None


def test_unrecognised_terms_survive_as_keywords():
    r = parse("carnatic vocalist")
    assert r["categories"] == ["singing"]
    assert "carnatic" in (r["keywords"] or "")


def test_empty_query_parses_to_nothing():
    r = parse("")
    # Empty collections come back as None rather than [] -- the schema treats both as absent.
    assert not r["categories"]
    assert r["city"] is None
    assert not r["keywords"]
    assert r["verified_only"] is False
