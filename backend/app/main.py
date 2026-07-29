import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, applications, auth, bookings, casting_calls, conversations, follows, invitations, recruiters, talents
from app.core.config import settings

logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
