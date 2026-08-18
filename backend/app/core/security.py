from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Marks a token as a one-document viewing grant rather than a login. Both decoders check it,
# so neither kind of token can ever be replayed as the other.
_DOCUMENT_TOKEN_TYPE = "doc"


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.JWTError:
        return None
    # Access tokens carry no "typ". Anything that does is a narrower-purpose token (currently
    # document links) and must not authenticate a session.
    if payload.get("typ") is not None:
        return None
    return payload.get("sub")


def create_document_token(document_id: str, *, ttl_seconds: int) -> str:
    """Short-lived grant to view one specific stored document. Scoped to a single document id
    so a link to one file can't be used to fetch another, and revocable in bulk by rotating
    SECRET_KEY.
    """
    expire = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    payload = {"sub": document_id, "exp": expire, "typ": _DOCUMENT_TOKEN_TYPE}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_document_token(token: str) -> str | None:
    """Returns the document id the token grants access to, or None if it's invalid, expired,
    or not a document token (e.g. someone passing their access token instead).
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.JWTError:
        return None
    if payload.get("typ") != _DOCUMENT_TOKEN_TYPE:
        return None
    return payload.get("sub")
