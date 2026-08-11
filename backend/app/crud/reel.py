import uuid
from urllib.parse import urlparse

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.reel import Reel
from app.schemas.reel import ReelCreate


def detect_reel_platform(url: str) -> str:
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        host = ""
    host = host.lower().removeprefix("www.").removeprefix("m.").removeprefix("vm.")

    if host == "tiktok.com":
        return "tiktok"
    if host == "instagram.com":
        return "instagram"
    if host in ("facebook.com", "fb.watch"):
        return "facebook"
    raise ValueError("Please paste a TikTok, Instagram, or Facebook link.")


def count_reels(db: Session, talent_profile_id: uuid.UUID) -> int:
    return db.query(func.count(Reel.id)).filter(Reel.talent_profile_id == talent_profile_id).scalar() or 0


def get_reel(db: Session, reel_id: uuid.UUID) -> Reel | None:
    return db.query(Reel).filter(Reel.id == reel_id).first()


def create_reel(db: Session, talent_profile_id: uuid.UUID, reel_in: ReelCreate) -> Reel:
    platform = detect_reel_platform(reel_in.url)
    reel = Reel(talent_profile_id=talent_profile_id, platform=platform, url=reel_in.url, caption=reel_in.caption)
    db.add(reel)
    db.commit()
    db.refresh(reel)
    return reel


def delete_reel(db: Session, reel: Reel) -> None:
    db.delete(reel)
    db.commit()
