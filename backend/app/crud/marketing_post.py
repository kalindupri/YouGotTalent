import random
from datetime import datetime, timedelta, timezone
from typing import Callable

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core import discord_bot, facebook, marketing_image
from app.core.config import settings
from app.models.booking import Booking
from app.models.casting_call import CastingCall, CastingCallStatus
from app.models.marketing_post import MarketingPost, MarketingPostStatus
from app.models.talent_profile import TalentCategory, TalentProfile

SITE_LINE = "Discover more at yougottalent.lk"
TOPIC_PROMPT = "🗓️ What should today's marketing post be about? Reply in this channel with the post text and I'll draft it."


def _category_label(category: TalentCategory) -> str:
    return category.value.replace("_", " ").title()


def _template_total_talent(db: Session) -> tuple[str, str] | None:
    count = db.query(func.count(TalentProfile.id)).scalar() or 0
    if count == 0:
        return None
    return (
        "Platform growth",
        f"🎭 We've now got {count} creative talent profiles on YouGotTalent — actors, singers, "
        f"dancers, painters, voice-over artists, and more, all in one place. {SITE_LINE}",
    )


def _template_category_spotlight_for(db: Session, category: TalentCategory) -> tuple[str, str] | None:
    count = db.query(func.count(TalentProfile.id)).filter(TalentProfile.category == category).scalar() or 0
    if count == 0:
        return None
    label = _category_label(category)
    return (
        f"Category spotlight: {label}",
        f"🎬 Spotlight on {label}: {count} talented {label.lower()} professionals are ready to be "
        f"discovered on YouGotTalent right now. Casting? Start here. {SITE_LINE}",
    )


def _template_category_spotlight(db: Session) -> tuple[str, str] | None:
    categories = list(TalentCategory)
    random.shuffle(categories)
    for category in categories:
        result = _template_category_spotlight_for(db, category)
        if result is not None:
            return result
    return None


def _template_open_castings(db: Session) -> tuple[str, str] | None:
    count = db.query(func.count(CastingCall.id)).filter(CastingCall.status == CastingCallStatus.OPEN).scalar() or 0
    if count == 0:
        return None
    return (
        "Open talent hunts",
        f"📢 {count} talent hunt{'s' if count != 1 else ''} open for applications on YouGotTalent right "
        f"now. Your next role could be one application away. {SITE_LINE}",
    )


def _template_new_this_week(db: Session) -> tuple[str, str] | None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    count = db.query(func.count(TalentProfile.id)).filter(TalentProfile.created_at >= cutoff).scalar() or 0
    if count == 0:
        return None
    return (
        "New talent this week",
        f"✨ {count} new creative{'s' if count != 1 else ''} joined YouGotTalent this week. The community "
        f"keeps growing — welcome aboard! {SITE_LINE}",
    )


def _template_bookings_confirmed(db: Session) -> tuple[str, str] | None:
    # Booking.status is a plain string column ("pending" | "accepted" | "declined" |
    # "cancelled") — there's no "completed" state in this app's booking lifecycle, so
    # "accepted" is the honest signal for "a real booking got confirmed here."
    count = db.query(func.count(Booking.id)).filter(Booking.status == "accepted").scalar() or 0
    if count == 0:
        return None
    return (
        "Real bookings, real work",
        f"🤝 {count} booking{'s' if count != 1 else ''} confirmed through YouGotTalent so far — real "
        f"creative work, real opportunities, matched on our platform. {SITE_LINE}",
    )


def _template_recruiter_cta(db: Session) -> tuple[str, str] | None:
    return (
        "Call to action — recruiters",
        "🔎 Casting for a project? Post a talent hunt on YouGotTalent and reach actors, singers, "
        f"dancers, models, and more across Sri Lanka's creative scene in minutes. {SITE_LINE}",
    )


def _template_talent_cta(db: Session) -> tuple[str, str] | None:
    return (
        "Call to action — talent",
        "🌟 Actors, singers, dancers, painters, photographers, voice artists — build your profile on "
        f"YouGotTalent and get discovered by recruiters actively casting right now. {SITE_LINE}",
    )


TEMPLATES = [
    _template_total_talent,
    _template_category_spotlight,
    _template_open_castings,
    _template_new_this_week,
    _template_bookings_confirmed,
    _template_recruiter_cta,
    _template_talent_cta,
]


_CATEGORY_KEYWORDS: dict[TalentCategory, list[str]] = {
    TalentCategory.ACTING: ["actor", "actors", "actress", "acting"],
    TalentCategory.SINGING: ["singer", "singers", "singing", "vocalist"],
    TalentCategory.DANCING: ["dancer", "dancers", "dancing", "dance"],
    TalentCategory.PAINTING: ["painter", "painters", "painting"],
    TalentCategory.SCRIPT_WRITING: ["screenwriter", "screenwriters", "script writing", "scriptwriting"],
    TalentCategory.PHOTOGRAPHY: ["photographer", "photographers", "photography"],
    TalentCategory.MUSIC: ["musician", "musicians", "music", "band"],
    TalentCategory.CHOREOGRAPHY: ["choreographer", "choreographers", "choreography"],
    TalentCategory.COMEDY: ["comedian", "comedians", "comedy"],
    TalentCategory.VOICE_OVER: ["voice over", "voice-over", "voiceover", "narrator"],
    TalentCategory.DIRECTION: ["director", "directors", "direction"],
    TalentCategory.MODELING: ["model", "models", "modeling", "modelling"],
    TalentCategory.DESIGN: ["designer", "designers"],
}

_TOPIC_KEYWORDS: list[tuple[list[str], Callable[[Session], tuple[str, str] | None]]] = [
    (["recruiter", "recruiters", "casting director", "hire", "post a job", "post a casting"], _template_recruiter_cta),
    (["booking", "bookings", "confirmed booking", "real work"], _template_bookings_confirmed),
    (["casting", "castings", "talent hunt", "talent hunts", "open role", "apply now"], _template_open_castings),
    (["new talent", "this week", "new signup", "new signups", "new member", "newcomer"], _template_new_this_week),
    (["growth", "platform growth", "total talent", "how many talent", "milestone"], _template_total_talent),
    (["join", "build your profile", "build a profile", "sign up", "get discovered"], _template_talent_cta),
]


def match_topic_from_reply(db: Session, reply: str) -> tuple[str, str]:
    """Matches a human's Discord reply to one of the pre-written templates by keyword, rather
    than using their text as literal post copy — there's no LLM in this pipeline to turn a
    short topic into polished marketing copy (a deliberate no-AI-cost choice). Falls back to a
    random topic if nothing matches or the matched template's live stat is currently zero.
    """
    lowered = reply.lower()

    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            result = _template_category_spotlight_for(db, category)
            if result is not None:
                return result
            break

    for keywords, template_fn in _TOPIC_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            result = template_fn(db)
            if result is not None:
                return result

    return generate_topic_and_content(db)


def generate_topic_and_content(db: Session) -> tuple[str, str]:
    """Picks a random template, backed by a real live platform stat where the template needs
    one, falling back to the next template if that stat is currently zero (e.g. don't brag
    about "0 bookings completed" on a quiet week) or if the same topic was used last time.
    """
    last = db.query(MarketingPost).order_by(MarketingPost.created_at.desc()).first()
    candidates = list(TEMPLATES)
    random.shuffle(candidates)
    for template_fn in candidates:
        result = template_fn(db)
        if result is None:
            continue
        topic, content = result
        if last is not None and last.topic == topic:
            continue
        return topic, content
    # Every template returned None (e.g. a brand-new, empty platform) or all matched the last
    # topic — fall back to whatever the first template produces even if repeated.
    for template_fn in candidates:
        result = template_fn(db)
        if result is not None:
            return result
    return ("Welcome", f"🎭 YouGotTalent — Sri Lanka's creative talent marketplace. {SITE_LINE}")


def get_pending(db: Session) -> MarketingPost | None:
    return (
        db.query(MarketingPost)
        .filter(MarketingPost.status == MarketingPostStatus.PENDING_APPROVAL)
        .order_by(MarketingPost.created_at.desc())
        .first()
    )


def get_awaiting_topic(db: Session) -> MarketingPost | None:
    return (
        db.query(MarketingPost)
        .filter(MarketingPost.status == MarketingPostStatus.AWAITING_TOPIC)
        .order_by(MarketingPost.created_at.desc())
        .first()
    )


def _post_draft(db: Session, post: MarketingPost, topic: str, content: str) -> tuple[bool, str, MarketingPost]:
    """Shared by the human-topic and auto-fallback paths: renders the branded image, posts the
    draft with ✅/❌ reactions, and moves the row from AWAITING_TOPIC to PENDING_APPROVAL.
    """
    image_bytes = marketing_image.generate_post_image(topic, marketing_image.content_to_subtext(content))
    try:
        message_id = discord_bot.post_draft_for_approval(content, image_bytes)
    except Exception as exc:
        post.status = MarketingPostStatus.FAILED
        post.error_message = f"Could not post draft to Discord: {exc}"
        db.commit()
        return False, post.error_message, post

    post.topic = topic
    post.content = content
    post.status = MarketingPostStatus.PENDING_APPROVAL
    post.discord_message_id = message_id
    db.commit()
    db.refresh(post)
    return True, "Draft posted to Discord for approval", post


def request_topic(db: Session) -> tuple[bool, str, MarketingPost | None]:
    """Posts a prompt to the Discord marketing channel asking what today's post should be
    about, and creates a placeholder row to track the reply. Rate-limited to roughly once a
    day (see MARKETING_MIN_HOURS_BETWEEN_TOPICS) — safe to call this on a frequent poll without
    it re-asking every time the previous cycle happens to finish quickly.
    """
    if not discord_bot.is_configured():
        return False, "Discord bot is not configured (DISCORD_BOT_TOKEN / DISCORD_MARKETING_CHANNEL_ID)", None

    last = db.query(MarketingPost).order_by(MarketingPost.created_at.desc()).first()
    if last is not None:
        created_at = last.created_at if last.created_at.tzinfo else last.created_at.replace(tzinfo=timezone.utc)
        min_gap = timedelta(hours=settings.MARKETING_MIN_HOURS_BETWEEN_TOPICS)
        if datetime.now(timezone.utc) - created_at < min_gap:
            return False, f"Last topic was asked less than {settings.MARKETING_MIN_HOURS_BETWEEN_TOPICS}h ago", None

    try:
        message_id = discord_bot.post_topic_prompt(TOPIC_PROMPT)
    except Exception as exc:
        return False, f"Could not post topic prompt to Discord: {exc}", None

    post = MarketingPost(
        status=MarketingPostStatus.AWAITING_TOPIC,
        discord_channel_id=settings.DISCORD_MARKETING_CHANNEL_ID,
        discord_message_id=message_id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return True, "Asked for a topic in Discord", post


def advance_topic_to_draft(db: Session) -> tuple[bool, str, MarketingPost | None]:
    """Checks whether a human has replied to the topic prompt yet. If so, their reply becomes
    the post content. If the reply timeout has elapsed with no response, falls back to an
    auto-generated topic so the daily cadence doesn't silently stall.
    """
    awaiting = get_awaiting_topic(db)
    if awaiting is None:
        return False, "No topic prompt is awaiting a reply", None

    reply = discord_bot.get_latest_human_reply(awaiting.discord_channel_id, awaiting.discord_message_id)
    if reply is not None:
        topic, content = match_topic_from_reply(db, reply)
        return _post_draft(db, awaiting, topic, content)

    created_at = awaiting.created_at if awaiting.created_at.tzinfo else awaiting.created_at.replace(tzinfo=timezone.utc)
    timeout = timedelta(hours=settings.MARKETING_APPROVAL_TIMEOUT_HOURS)
    if datetime.now(timezone.utc) - created_at > timeout:
        topic, content = generate_topic_and_content(db)
        discord_bot.notify_channel(f"⌛ No topic reply — posting an auto-generated draft instead: *{topic}*")
        return _post_draft(db, awaiting, topic, content)

    return False, "Still waiting on a topic reply in Discord", awaiting


def generate_and_post_draft(db: Session) -> tuple[bool, str, MarketingPost | None]:
    """Advances the marketing pipeline by one step. Won't ask for a new topic (or create a
    second draft) while a previous one is still in flight — the daily cron should resolve or
    expire that one first, not silently pile up unreviewed drafts.
    """
    pending = get_pending(db)
    if pending is not None:
        return False, f"A draft is already pending approval (id={pending.id})", pending

    awaiting = get_awaiting_topic(db)
    if awaiting is not None:
        return advance_topic_to_draft(db)

    return request_topic(db)


def check_approvals(db: Session) -> dict:
    """Meant to be polled frequently (e.g. every 15-30 min) by an external cron — Discord
    reactions are read via REST here, there's no push/webhook telling us when you react.
    """
    result = {"checked": 0, "posted": 0, "rejected": 0, "expired": 0, "failed": 0}
    pending = db.query(MarketingPost).filter(MarketingPost.status == MarketingPostStatus.PENDING_APPROVAL).all()
    timeout = timedelta(hours=settings.MARKETING_APPROVAL_TIMEOUT_HOURS)
    now = datetime.now(timezone.utc)

    for post in pending:
        result["checked"] += 1
        created_at = post.created_at if post.created_at.tzinfo else post.created_at.replace(tzinfo=timezone.utc)

        if not post.discord_channel_id or not post.discord_message_id:
            continue

        try:
            reaction = discord_bot.get_human_reaction(post.discord_channel_id, post.discord_message_id)
        except Exception as exc:
            post.status = MarketingPostStatus.FAILED
            post.error_message = f"Could not read Discord reactions: {exc}"
            db.commit()
            result["failed"] += 1
            continue

        if reaction == "rejected":
            post.status = MarketingPostStatus.REJECTED
            post.decided_at = now
            db.commit()
            result["rejected"] += 1
            discord_bot.notify_channel(f"❌ Draft discarded: *{post.topic}*")
            continue

        if reaction == "approved":
            post.status = MarketingPostStatus.APPROVED
            post.decided_at = now
            db.commit()
            if not facebook.is_configured():
                post.status = MarketingPostStatus.FAILED
                post.error_message = "Facebook Page is not configured (FACEBOOK_PAGE_ID / FACEBOOK_PAGE_ACCESS_TOKEN)"
                db.commit()
                result["failed"] += 1
                discord_bot.notify_channel(f"⚠️ Approved but could not post — {post.error_message}")
                continue
            try:
                image_bytes = marketing_image.generate_post_image(
                    post.topic, marketing_image.content_to_subtext(post.content)
                )
                facebook_post_id = facebook.publish_page_post(post.content, image_bytes)
            except facebook.FacebookPostError as exc:
                post.status = MarketingPostStatus.FAILED
                post.error_message = str(exc)
                db.commit()
                result["failed"] += 1
                discord_bot.notify_channel(f"⚠️ Approved but the Facebook post failed: {exc}")
                continue
            post.status = MarketingPostStatus.POSTED
            post.facebook_post_id = facebook_post_id
            post.posted_at = now
            db.commit()
            result["posted"] += 1
            discord_bot.notify_channel(f"✅ Posted to Facebook: *{post.topic}*")
            continue

        if now - created_at > timeout:
            post.status = MarketingPostStatus.EXPIRED
            post.decided_at = now
            db.commit()
            result["expired"] += 1
            discord_bot.notify_channel(f"⌛ Draft expired with no response: *{post.topic}*")

    return result
