"""Per-IP rate limiting for abuse-prone endpoints (login, registration, password reset,
report submission) -- these had no throttling at all, making them brute-forceable /
spammable. In-memory storage (slowapi's default) is per-process, so limits reset on
deploy and aren't shared across replicas -- an acceptable tradeoff for this app's scale
over adding a Redis dependency just for this; still a real deterrent against casual abuse.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

limiter = Limiter(key_func=get_remote_address, enabled=settings.RATE_LIMITING_ENABLED)
