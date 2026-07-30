import json

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "YouGotTalent"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+psycopg2://ygt:ygt@localhost:5432/ygt"

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Plain string, not list[str] — pydantic-settings JSON-decodes list-typed env values at
    # the source level (before any validator runs), so a plain comma-separated value would
    # fail to even reach a validator. Accepting a string here and splitting it ourselves
    # supports both a real JSON array and a plain comma-separated value (the latter is much
    # easier to set correctly through a cloud platform's env-var UI, where quoting/escaping
    # a JSON array is awkward).
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        value = self.CORS_ORIGINS.strip()
        if value.startswith("["):
            return json.loads(value)
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    # Free-tier limits. Premium accounts (tier="premium") are exempt from these.
    FREE_TIER_MEDIA_LIMIT: int = 3
    FREE_TIER_OPEN_CASTING_CALL_LIMIT: int = 2

    # Video auditions are quota'd separately from the general media limit above — premium
    # accounts get a real cap here too (unlike the general limit, which they bypass entirely),
    # since uncompressed video is by far the most expensive media type to store and serve.
    FREE_TIER_VIDEO_LIMIT: int = 1
    PREMIUM_TIER_VIDEO_LIMIT: int = 5

    # Raw (pre-compression) upload size cap, enforced before any ffmpeg work is done.
    MAX_UPLOAD_SIZE_BYTES: int = 200 * 1024 * 1024

    # Azure Blob Storage for uploaded video/audio auditions. If unset (e.g. local dev), uploads
    # fall back to local disk served by this app itself — see app/core/storage.py.
    AZURE_STORAGE_CONNECTION_STRING: str | None = None
    AZURE_STORAGE_CONTAINER: str = "talent-media"

    # Only used to build absolute URLs for the local-disk upload fallback above.
    BACKEND_PUBLIC_URL: str = "http://localhost:8000"

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
