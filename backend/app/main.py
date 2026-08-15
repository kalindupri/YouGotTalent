import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import (
    admin,
    applications,
    auth,
    billing,
    bookings,
    calendar,
    casting_calls,
    conversations,
    discussions,
    follows,
    invitations,
    library,
    marketing,
    notifications,
    recruiters,
    reels,
    reports,
    support_chat,
    talents,
    titles,
)
from app.core.config import settings
from app.core.error_monitoring import setup_error_monitoring
from app.core.rate_limit import limiter
from app.core.storage import LOCAL_MEDIA_DIR

logging.basicConfig(level=logging.INFO)
setup_error_monitoring()

app = FastAPI(title=settings.PROJECT_NAME)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serves uploads saved by the local-disk storage fallback (used when AZURE_STORAGE_CONNECTION_STRING
# isn't set, e.g. local dev). Unused in environments where Azure Blob Storage is configured.
LOCAL_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=LOCAL_MEDIA_DIR), name="media")

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(talents.router, prefix=settings.API_V1_PREFIX)
app.include_router(recruiters.router, prefix=settings.API_V1_PREFIX)
app.include_router(casting_calls.router, prefix=settings.API_V1_PREFIX)
app.include_router(applications.router, prefix=settings.API_V1_PREFIX)
app.include_router(conversations.router, prefix=settings.API_V1_PREFIX)
app.include_router(invitations.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)
app.include_router(bookings.router, prefix=settings.API_V1_PREFIX)
app.include_router(calendar.router, prefix=settings.API_V1_PREFIX)
app.include_router(library.router, prefix=settings.API_V1_PREFIX)
app.include_router(follows.router, prefix=settings.API_V1_PREFIX)
app.include_router(reports.router, prefix=settings.API_V1_PREFIX)
app.include_router(billing.router, prefix=settings.API_V1_PREFIX)
app.include_router(titles.router, prefix=settings.API_V1_PREFIX)
app.include_router(discussions.router, prefix=settings.API_V1_PREFIX)
app.include_router(marketing.router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX)
app.include_router(reels.router, prefix=settings.API_V1_PREFIX)
app.include_router(support_chat.router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health():
    return {"status": "ok"}
