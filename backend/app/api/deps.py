import uuid

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.crud.subscription import get_for_recruiter, get_for_talent, sync_if_expired
from app.crud.talent_profile import list_talent_profiles_by_user
from app.db.session import get_db
from app.models.recruiter_profile import RecruiterProfile
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
# auto_error=False so public endpoints can optionally recognize a logged-in recruiter
# (e.g. to log a profile view) without requiring auth for anonymous visitors.
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    subject = decode_access_token(token)
    if subject is None:
        raise credentials_exception
    user = db.query(User).filter(User.id == uuid.UUID(subject)).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_talent(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.TALENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Talent account required")
    return user


def require_recruiter(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.RECRUITER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recruiter account required")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin account required")
    return user


def get_current_talent_profile(
    db: Session = Depends(get_db),
    user: User = Depends(require_talent),
    active_profile_id: uuid.UUID | None = Header(default=None, alias="X-Talent-Profile-Id"),
):
    """Resolve which talent profile this request is acting as.

    An account can hold more than one profile (a guardian managing several children), so the
    caller picks with an X-Talent-Profile-Id header. Everyone with exactly one profile — which
    is every ordinary talent — is unaffected and never needs to send it.
    """
    profiles = list_talent_profiles_by_user(db, user.id)
    if active_profile_id is not None:
        profile = next((p for p in profiles if p.id == active_profile_id), None)
        if profile is None:
            # 403 not 404: don't confirm whether a profile with that id exists elsewhere.
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="That profile isn't yours to manage.")
    elif len(profiles) == 1:
        profile = profiles[0]
    elif not profiles:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent profile not found")
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You manage more than one profile. Choose which one you're working on.",
        )
    # Lazily reconciles a lapsed trial/billing period on every request that loads the profile —
    # there's no cron/queue in this app, so this is what keeps tier from drifting from reality.
    sync_if_expired(db, get_for_talent(db, profile.id))
    return profile


def get_current_recruiter_profile(db: Session = Depends(get_db), user: User = Depends(require_recruiter)) -> RecruiterProfile:
    profile = db.query(RecruiterProfile).filter(RecruiterProfile.user_id == user.id).first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter profile not found")
    sync_if_expired(db, get_for_recruiter(db, profile.id))
    return profile


def get_optional_recruiter_profile(
    db: Session = Depends(get_db), token: str | None = Depends(optional_oauth2_scheme)
) -> RecruiterProfile | None:
    if not token:
        return None
    subject = decode_access_token(token)
    if subject is None:
        return None
    user = db.query(User).filter(User.id == uuid.UUID(subject)).first()
    if user is None or not user.is_active or user.role != UserRole.RECRUITER:
        return None
    return db.query(RecruiterProfile).filter(RecruiterProfile.user_id == user.id).first()


# For routes usable by both guests and logged-in users of any role (e.g. starting a live-chat
# handoff) — the caller only needs to know who's asking, not enforce a role.
def get_optional_current_user(
    db: Session = Depends(get_db), token: str | None = Depends(optional_oauth2_scheme)
) -> User | None:
    if not token:
        return None
    subject = decode_access_token(token)
    if subject is None:
        return None
    user = db.query(User).filter(User.id == uuid.UUID(subject)).first()
    if user is None or not user.is_active:
        return None
    return user


# For content-visibility gating on public routes — needs the viewer's role (any role, or
# guest), unlike get_optional_recruiter_profile above which only cares about recruiters.
def get_optional_viewer_role(
    db: Session = Depends(get_db), token: str | None = Depends(optional_oauth2_scheme)
) -> UserRole | None:
    if not token:
        return None
    subject = decode_access_token(token)
    if subject is None:
        return None
    user = db.query(User).filter(User.id == uuid.UUID(subject)).first()
    if user is None or not user.is_active:
        return None
    return user.role
