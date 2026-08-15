"""Turns a free-text recruiter query ("Actor wanted under 35 male with some industry
experience") into the same structured filters `list_talent_profiles` already accepts.
Deliberately rule-based (regex + synonym lookups), not an LLM call -- matches this
codebase's existing "AI shortlisting" precedent (see `_compute_match_score` in
crud/application.py), and keeps this feature free and instant with no new API dependency.

Anything not recognized as a structured filter is left in `keywords` and passed straight
through to the existing `q` keyword search (which now also checks `instruments` and the
per-category `attributes` JSONB, not just name/skills/bio) -- so unmatched phrases like
"television ad" still contribute to relevance instead of being silently dropped.
"""
import re

CATEGORY_SYNONYMS: dict[str, str] = {
    "actor": "acting", "actress": "acting", "actors": "acting", "actresses": "acting", "acting": "acting",
    "singer": "singing", "singers": "singing", "vocalist": "singing", "vocalists": "singing", "singing": "singing",
    "dancer": "dancing", "dancers": "dancing", "dancing": "dancing",
    "painter": "painting", "painters": "painting", "painting": "painting",
    "writer": "script_writing", "writers": "script_writing", "scriptwriter": "script_writing",
    "screenwriter": "script_writing", "script_writing": "script_writing",
    "photographer": "photography", "photographers": "photography", "photography": "photography",
    "musician": "music", "musicians": "music", "music": "music",
    "choreographer": "choreography", "choreographers": "choreography", "choreography": "choreography",
    "comedian": "comedy", "comedians": "comedy", "comedy": "comedy",
    "voiceover": "voice_over", "narrator": "voice_over", "narrators": "voice_over", "voice_over": "voice_over",
    "director": "direction", "directors": "direction", "direction": "direction",
    "model": "modeling", "models": "modeling", "modeling": "modeling", "modelling": "modeling",
    "designer": "design", "designers": "design", "design": "design",
    "influencer": "content_creator", "influencers": "content_creator", "creator": "content_creator",
    "youtuber": "content_creator", "tiktoker": "content_creator", "content_creator": "content_creator",
}

# Not exhaustive -- covers common cases and is easy to extend. An instrument hit implies
# category=music (unless another category was already found) and adds to the `instruments`
# array filter, on top of whatever leftover keyword matching also catches.
INSTRUMENT_SYNONYMS: dict[str, list[str]] = {
    "percussion": ["percussion", "drums", "tabla", "congas", "cajon", "bongo", "djembe"],
    "drum": ["drums", "percussion"],
    "drummer": ["drums", "percussion"],
    "drums": ["drums", "percussion"],
    "guitar": ["guitar"],
    "guitarist": ["guitar"],
    "piano": ["piano", "keyboard"],
    "pianist": ["piano", "keyboard"],
    "violin": ["violin"],
    "violinist": ["violin"],
    "flute": ["flute"],
    "sitar": ["sitar"],
    "tabla": ["tabla"],
}

GENDER_SYNONYMS: dict[str, str] = {
    "male": "male", "man": "male", "men": "male", "boy": "male", "boys": "male", "guy": "male", "guys": "male",
    "female": "female", "woman": "female", "women": "female", "girl": "female", "girls": "female",
    "lady": "female", "ladies": "female",
}

# Words consumed by structured matching, plus generic filler -- whatever's left forms the
# residual keyword search.
STOPWORDS = {
    "wanted", "needed", "looking", "want", "need", "find", "search", "searching", "for", "with", "who",
    "is", "are", "has", "have", "some", "a", "an", "the", "of", "to", "in", "on", "and", "or", "i", "we",
    "years", "year", "yrs", "yr", "old", "yo", "industry", "more", "than", "less", "under", "over",
    "above", "below", "around", "about", "audience", "followers", "follower", "subscribers", "fans",
    "tiktok", "instagram", "youtube", "k",
}


def _extract_first(text: str, pattern: str, flags: int = re.IGNORECASE) -> tuple[str, re.Match | None]:
    match = re.search(pattern, text, flags)
    if match:
        text = text[: match.start()] + " " + text[match.end() :]
    return text, match


def parse_talent_search_query(raw_query: str) -> dict:
    text = f" {raw_query.strip()} "
    result: dict = {
        "categories": [],
        "gender": None,
        "age_min": None,
        "age_max": None,
        "experience_min": None,
        "experience_max": None,
        "min_tiktok_followers": None,
        "instruments": [],
        "keywords": "",
    }

    # --- Follower/audience count (TikTok is the only platform we store a number for today) ---
    mentions_tiktok = bool(re.search(r"\btiktok\b", raw_query, re.IGNORECASE))
    text, m = _extract_first(text, r"\b(\d[\d,]*)\s*k\+?\s*(?:followers|audience|subscribers|fans)\b")
    if m:
        if mentions_tiktok:
            result["min_tiktok_followers"] = int(m.group(1).replace(",", "")) * 1000
    else:
        text, m = _extract_first(text, r"\b(\d[\d,]{2,})\s*(?:followers|audience|subscribers|fans)\b")
        if m and mentions_tiktok:
            result["min_tiktok_followers"] = int(m.group(1).replace(",", ""))

    # --- Numeric age ranges (checked before fuzzy words so "older than 40" isn't double-counted) ---
    text, m = _extract_first(text, r"\bbetween\s+(\d{1,2})\s+and\s+(\d{1,2})\b")
    if m:
        result["age_min"], result["age_max"] = int(m.group(1)), int(m.group(2))
    else:
        text, m = _extract_first(text, r"\b(\d{1,2})\s*(?:-|to)\s*(\d{1,2})\s*years?\b")
        if m:
            result["age_min"], result["age_max"] = int(m.group(1)), int(m.group(2))
    text, m = _extract_first(text, r"\b(?:under|below|younger than)\s+(\d{1,2})\b")
    if m:
        result["age_max"] = int(m.group(1)) - 1
    text, m = _extract_first(text, r"\b(?:over|above|older than)\s+(\d{1,2})\b")
    if m:
        result["age_min"] = int(m.group(1)) + 1
    text, m = _extract_first(text, r"\b(\d{1,2})\s*(?:years?\s*old|yo)\b")
    if m:
        age = int(m.group(1))
        result["age_min"], result["age_max"] = age, age

    # --- Fuzzy age words (approximate cutoffs, only applied if no numeric age was already found) ---
    if result["age_min"] is None and result["age_max"] is None:
        text, m = _extract_first(text, r"\bmiddle[- ]aged\b")
        if m:
            result["age_min"], result["age_max"] = 35, 55
        else:
            text, m = _extract_first(text, r"\bteen(?:ager)?s?\b")
            if m:
                result["age_min"], result["age_max"] = 13, 19
            else:
                text, m = _extract_first(text, r"\byoung(?:er)?\b")
                if m:
                    result["age_max"] = 30
                else:
                    text, m = _extract_first(text, r"\bsenior\b")
                    if m:
                        result["age_min"] = 50
                    else:
                        text, m = _extract_first(text, r"\bold(?:er)?\b")
                        if m:
                            result["age_min"] = 45

    # --- Experience ---
    text, m = _extract_first(text, r"\b(\d{1,2})\+?\s*years?\s*(?:of\s*)?experience\b")
    if m:
        result["experience_min"] = int(m.group(1))
    else:
        text, m = _extract_first(text, r"\b(?:no|zero|without any)\s+experience\b")
        if m:
            result["experience_max"] = 0
        else:
            text, m = _extract_first(text, r"\b(?:beginner|novice|newcomer|fresh(?:er)?|entry[- ]level)\b")
            if m:
                result["experience_max"] = 0
            else:
                text, m = _extract_first(
                    text, r"\b(?:experienced|seasoned|veteran|extensive experience|lots of experience)\b"
                )
                if m:
                    result["experience_min"] = 3
                else:
                    text, m = _extract_first(
                        text, r"\b(?:some|a bit of|a little)\s+(?:industry\s+)?experience\b"
                    )
                    if m:
                        result["experience_min"] = 1

    # --- Gender ---
    words = re.findall(r"[a-zA-Z']+", text)
    remaining_words = []
    for word in words:
        lower = word.lower()
        if lower in GENDER_SYNONYMS and result["gender"] is None:
            result["gender"] = GENDER_SYNONYMS[lower]
            continue
        remaining_words.append(word)

    # --- Category + instrument synonyms ---
    final_words = []
    for word in remaining_words:
        lower = word.lower()
        if lower in INSTRUMENT_SYNONYMS:
            result["instruments"].extend(INSTRUMENT_SYNONYMS[lower])
            if "music" not in result["categories"]:
                result["categories"].append("music")
            continue
        if lower in CATEGORY_SYNONYMS:
            mapped = CATEGORY_SYNONYMS[lower]
            if mapped not in result["categories"]:
                result["categories"].append(mapped)
            continue
        final_words.append(word)

    # De-dupe instruments while preserving order.
    result["instruments"] = list(dict.fromkeys(result["instruments"])) or None
    result["categories"] = result["categories"] or None

    leftover = [w for w in final_words if w.lower() not in STOPWORDS]
    result["keywords"] = " ".join(leftover).strip() or None

    return result
