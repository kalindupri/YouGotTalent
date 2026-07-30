import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreate

VERIFICATION_CODE_TTL_MINUTES = 15


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    user = User(
        email=user_in.email,
        phone=user_in.phone,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=UserRole(user_in.role),
        consent_given_at=datetime.now(timezone.utc) if user_in.consent_given else None,
        email_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def set_new_verification_code(db: Session, user: User) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    user.verification_code = code
    user.verification_code_expires_at = datetime.now(timezone.utc) + timedelta(minutes=VERIFICATION_CODE_TTL_MINUTES)
    db.commit()
    db.refresh(user)
    return code


def verify_email_code(db: Session, user: User, code: str) -> bool:
    if (
        not user.verification_code
        or user.verification_code != code
        or user.verification_code_expires_at is None
        or datetime.now(timezone.utc) > user.verification_code_expires_at
    ):
        return False
    user.email_verified = True
    user.verification_code = None
    user.verification_code_expires_at = None
    db.commit()
    db.refresh(user)
    return True


def set_password_reset_code(db: Session, user: User) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    user.password_reset_code = code
    user.password_reset_code_expires_at = datetime.now(timezone.utc) + timedelta(minutes=VERIFICATION_CODE_TTL_MINUTES)
    db.commit()
    db.refresh(user)
    return code


def reset_password_with_code(db: Session, user: User, code: str, new_password: str) -> bool:
    if (
        not user.password_reset_code
        or user.password_reset_code != code
        or user.password_reset_code_expires_at is None
        or datetime.now(timezone.utc) > user.password_reset_code_expires_at
    ):
        return False
    user.hashed_password = hash_password(new_password)
    user.password_reset_code = None
    user.password_reset_code_expires_at = None
    db.commit()
    db.refresh(user)
    return True
