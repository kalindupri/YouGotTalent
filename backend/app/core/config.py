from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "YouGotTalent"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+psycopg2://ygt:ygt@localhost:5432/ygt"

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Free-tier limits. Premium accounts (tier="premium") are exempt from these.
    FREE_TIER_MEDIA_LIMIT: int = 3
    FREE_TIER_OPEN_CASTING_CALL_LIMIT: int = 2

    # Assumed monthly price per premium subscriber, used only to project estimated revenue on
    # the admin financial overview — there is no real billing integration, so no money actually
    # moves at these prices yet.
    PREMIUM_TALENT_PRICE_LKR: int = 1500
    PREMIUM_RECRUITER_PRICE_LKR: int = 5000

    # SMTP config for outgoing email. If SMTP_HOST is unset, emails are logged instead of sent
    # (safe default for local/dev environments with no mail credentials configured).
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: str = "no-reply@yougottalent.lk"
    FRONTEND_URL: str = "http://localhost:3001"


settings = Settings()
