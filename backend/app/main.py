import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import admin, applications, auth, bookings, casting_calls, conversations, follows, invitations, recruiters, talents
from app.core.config import settings
from app.core.storage import LOCAL_MEDIA_DIR

logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.PROJECT_NAME)

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
app.include_router(follows.router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health():
    return {"status": "ok"}
