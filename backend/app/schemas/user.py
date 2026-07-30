import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    phone: str | None = None
    password: str
    full_name: str
    # Deliberately excludes "admin" — self-service registration can only ever create a talent
    # or recruiter account. Admin accounts are provisioned via scripts/create_admin.py.
    role: Literal["talent", "recruiter"]
    consent_given: bool


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class EmailVerifyRequest(BaseModel):
    email: EmailStr
    code: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    phone: str | None
    full_name: str
    role: UserRole
    is_active: bool
    email_verified: bool
    created_at: datetime
