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

    # Capped, rotating "Featured talent" slots — see list_featured_talent().
    PREMIUM_FEATURED_SLOT_LIMIT: int = 6

    # Reels showcase (TikTok / Instagram Reels / Facebook Reels links) is Premium-only.
    PREMIUM_REEL_LIMIT: int = 10

    # Raw (pre-compression) upload size cap, enforced before any ffmpeg work is done.
    MAX_UPLOAD_SIZE_BYTES: int = 200 * 1024 * 1024

    # Manually uploaded video files (not YouTube/Spotify links, which have no duration cap)
    # are rejected past this length — keeps storage/egress bounded regardless of tier.
    MAX_VIDEO_DURATION_SECONDS: int = 30

    # Azure Blob Storage for uploaded video/audio auditions. If unset (e.g. local dev), uploads
    # fall back to local disk served by this app itself — see app/core/storage.py.
    AZURE_STORAGE_CONNECTION_STRING: str | None = None
    AZURE_STORAGE_CONTAINER: str = "talent-media"

    # Only used to build absolute URLs for the local-disk upload fallback above.
    BACKEND_PUBLIC_URL: str = "http://localhost:8000"

    # Founding-member / year-1 monthly prices. Locked onto each Subscription as price_lkr at
    # signup, so raising these later never changes what an existing subscriber pays.
    PREMIUM_TALENT_PRICE_LKR: int = 490
    PREMIUM_RECRUITER_PRICE_LKR: int = 1500

    # Annual price = 10x monthly ("2 months free"), the standard SaaS annual-discount anchor.
    ANNUAL_BILLING_MONTHS_CHARGED: int = 10

    # How long a first-time upgrade stays in trial before payment is required.
    TALENT_TRIAL_DAYS: int = 90
    RECRUITER_TRIAL_DAYS: int = 90

    # Dunning: how long a subscriber keeps premium access after a renewal payment fails before
    # being downgraded to free, and when mid-grace-period the reminder email goes out.
    PAST_DUE_GRACE_DAYS: int = 7
    PAST_DUE_REMINDER_AFTER_DAYS: int = 4

    # One-time retention offer shown when a subscriber starts the cancel flow.
    RETENTION_DISCOUNT_PERCENT: int = 10
    RETENTION_DISCOUNT_MONTHS: int = 3

    # Which PaymentGateway implementation app/core/payments/factory.py hands out.
    # "mock" activates subscriptions instantly with no external call — the default, so dev/test
    # environments work with zero payment-provider setup. Switch to "payhere" (Sri Lanka, LKR)
    # or "stripe" (international expansion) once real merchant credentials are configured below.
    PAYMENT_GATEWAY: str = "mock"

    PAYHERE_MERCHANT_ID: str | None = None
    PAYHERE_MERCHANT_SECRET: str | None = None
    PAYHERE_SANDBOX: bool = True

    STRIPE_SECRET_KEY: str | None = None
    STRIPE_PUBLISHABLE_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    # Stripe doesn't settle in LKR — pricing for the Stripe path is charged in this currency
    # instead, independent of the LKR prices above which are only for the local PayHere path.
    STRIPE_CURRENCY: str = "usd"
    # Fallback used only when no pre-created Price object is configured below (e.g. for the
    # annual cycle, which doesn't have its own Price ID yet).
    STRIPE_TALENT_PRICE: int = 500  # cents
    STRIPE_RECRUITER_PRICE: int = 1500  # cents
    # Pre-created recurring Price IDs from the Stripe dashboard (monthly). When set, checkout
    # uses these directly instead of building price_data inline — the standard Stripe pattern,
    # and required for the customer-facing product/price name to show correctly at checkout.
    STRIPE_TALENT_PRICE_ID: str | None = None
    STRIPE_RECRUITER_PRICE_ID: str | None = None

    # Outgoing email. Checked in order: Azure Communication Services (production, sends via
    # the ACS Email REST API using key-based auth) -> SMTP (local/dev, e.g. Gmail) -> log-only
    # if neither is configured, so the notification flow can still be exercised without any
    # mail credentials.
    AZURE_COMMUNICATION_CONNECTION_STRING: str | None = None
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: str = "no-reply@yougottalent.lk"
    FRONTEND_URL: str = "http://localhost:3001"

    # Discord webhook that new reports (bug reports, profile/content reports) are posted to for
    # triage. If unset, notifications are logged instead of sent (see app/core/discord.py).
    DISCORD_WEBHOOK_URL: str | None = None

    # Marketing auto-poster: daily draft -> Discord approval (bot, not the webhook above, since
    # reading a reaction back requires bot REST calls) -> Facebook Page post. See
    # app/core/discord_bot.py, app/core/facebook.py, app/crud/marketing_post.py.
    DISCORD_BOT_TOKEN: str | None = None
    DISCORD_MARKETING_CHANNEL_ID: str | None = None
    FACEBOOK_PAGE_ID: str | None = None
    FACEBOOK_PAGE_ACCESS_TOKEN: str | None = None
    # Separate from admin JWT auth on purpose: these two endpoints are meant to be hit by an
    # unattended external cron (same "no scheduler in this app" pattern as the dunning sweep),
    # and a JWT would expire long before a long-running cron job's next run.
    MARKETING_CRON_SECRET: str | None = None
    # How long a draft waits for a Discord reaction before it's considered expired and dropped.
    MARKETING_APPROVAL_TIMEOUT_HOURS: int = 24
    # generate-draft is meant to be polled frequently (so a topic reply is picked up quickly),
    # but a brand-new topic should only be asked for about once a day — this gates request_topic
    # so frequent polling doesn't re-ask the moment the previous cycle finishes.
    MARKETING_MIN_HOURS_BETWEEN_TOPICS: int = 20

    # Backend crash/error alerts (see app/core/error_monitoring.py) post here via the same
    # Discord bot used for marketing, not the webhook in DISCORD_WEBHOOK_URL — a separate
    # channel from user-filed content reports, which still use that webhook.
    DISCORD_ERROR_CHANNEL_ID: str | None = None


settings = Settings()
