import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.crud.subscription import get_for_recruiter, get_for_talent, sync_if_expired
from app.crud.talent_profile import get_talent_profile_by_user
from app.db.session import get_db
from app.models.recruiter_profile import RecruiterProfile
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


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


def get_current_talent_profile(db: Session = Depends(get_db), user: User = Depends(require_talent)):
    profile = get_talent_profile_by_user(db, user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent profile not found")
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
