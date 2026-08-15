from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.email import send_email
from app.core.rate_limit import limiter
from app.core.security import create_access_token, verify_password
from app.crud.user import (
    create_user,
    get_user_by_email,
    reset_password_with_code,
    set_new_verification_code,
    set_password_reset_code,
    verify_email_code,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import (
    EmailVerifyRequest,
    ForgotPasswordRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    UserCreate,
    UserRead,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _send_verification_email(background_tasks: BackgroundTasks, user: User, code: str) -> None:
    background_tasks.add_task(
        send_email,
        user.email,
        "Verify your YouGotTalent email",
        f"Your verification code is {code}. It expires in 15 minutes.\n\n"
        f"Enter it here: {settings.FRONTEND_URL}/register",
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, user_in: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    if not user_in.consent_given:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Consent to data processing is required")
    user = create_user(db, user_in)
    code = set_new_verification_code(db, user)
    _send_verification_email(background_tasks, user, code)
    return user


@router.post("/verify-email", response_model=Token)
@limiter.limit("10/minute")
def verify_email(request: Request, payload: EmailVerifyRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or code")
    if not user.email_verified and not verify_email_code(db, user, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


@router.post("/resend-verification", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("3/minute")
def resend_verification(
    request: Request, payload: ResendVerificationRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    user = get_user_by_email(db, payload.email)
    # Stay silent on unknown emails and already-verified accounts so this endpoint can't be
    # used to probe which addresses have registered.
    if user is None or user.email_verified:
        return
    code = set_new_verification_code(db, user)
    _send_verification_email(background_tasks, user, code)


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("3/minute")
def forgot_password(
    request: Request, payload: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    user = get_user_by_email(db, payload.email)
    # Stay silent on unknown emails so this endpoint can't be used to probe which addresses
    # have registered (same reasoning as resend-verification above).
    if user is None:
        return
    code = set_password_reset_code(db, user)
    background_tasks.add_task(
        send_email,
        user.email,
        "Reset your YouGotTalent password",
        f"Your password reset code is {code}. It expires in 15 minutes.\n\n"
        f"Enter it here: {settings.FRONTEND_URL}/reset-password",
    )


@router.post("/reset-password", response_model=Token)
@limiter.limit("10/minute")
def reset_password(request: Request, payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if user is None or not reset_password_with_code(db, user, payload.code, payload.new_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been suspended")
    if not user.email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please verify your email before logging in")
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


@router.get("/me", response_model=UserRead)
def read_current_user(user: User = Depends(get_current_user)):
    return user
