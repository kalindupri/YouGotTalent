# YouGotTalent

A general creative-talent marketplace for Sri Lanka — not a modeling bank. Talent across any
skill (acting, singing, dancing, painting, script writing, photography, music, choreography,
comedy, voice over, direction, modeling, design, and more) builds a profile with audition pieces
(photo, video, audio, or document), and organizers post talent hunts / open calls and search for
matching talent by category, city, or skill keyword.

## Stack

- **Backend:** FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL
- **Frontend:** Next.js (App Router) + TypeScript + Tailwind
- **Auth:** JWT (OAuth2 password flow)

## Domain model

- `User` — talent, recruiter (talent hunt organizer), or admin account (email/password, PDPA consent timestamp)
- `TalentProfile` — one per talent user (category, bio, city, experience, free-text skill tags for search matching)
- `Media` — audition pieces attached to a talent profile: photo, video, audio, or document, each with an optional title
- `RecruiterProfile` — one per organizer user (company/agency name, industry)
- `CastingCall` — a talent hunt / open call posted by an organizer
- `Application` — a talent applying to a talent hunt
- `SavedTalent` — an organizer's shortlist of saved talent profiles

Talent categories and media types are stored as plain strings (not Postgres native enums)
specifically so new categories can be added in `TalentCategory`/`MediaType` (Python enums) without
an `ALTER TYPE` migration.

## Prerequisites

You'll need these installed locally (none were found on this machine):

- **Python 3.12+** — https://www.python.org/downloads/ (or `winget install Python.Python.3.12`)
- **PostgreSQL 16** — https://www.postgresql.org/download/windows/ (or `winget install PostgreSQL.PostgreSQL.16`), OR just use Docker Desktop and skip installing Postgres directly
- **Docker Desktop** (optional but easiest) — https://www.docker.com/products/docker-desktop/ (or `winget install Docker.DockerDesktop`)
- Node.js is already installed.

## Running with Docker (recommended)

```bash
cp .env.example .env
docker compose up --build
```

Then run migrations once the containers are up:

```bash
docker compose exec backend alembic revision --autogenerate -m "initial schema"
docker compose exec backend alembic upgrade head
```

- API: http://localhost:8000/docs
- Frontend: http://localhost:3001 (port 3000 is commonly taken by other local dev servers, so
  `docker-compose.yml` maps this project to 3001 instead — change it back if 3000 is free on your
  machine)

## Running without Docker

**Backend**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example .env   # then edit DATABASE_URL to point at your local Postgres
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend**

```bash
cd frontend
copy .env.local.example .env.local
npm install
npm run dev
```

## Compliance notes (Sri Lanka PDPA)

- `User.consent_given_at` records when a user consented to data processing at signup; registration is rejected without consent.
- Photos, videos, and audio auditions collected from talent profiles are personal data under the Personal Data Protection Act No. 9 of 2022 — before going to production, add: a documented retention/deletion policy, a data breach notification process, and (if processing at scale) a Data Protection Officer and DPIA. See the Data Protection Authority: https://www.dpa.gov.lk/
- Minors submitting auditions will need guardian-consent flows — not yet implemented.

## Project status

Built: auth, talent profiles + skill tags + multi-type media (photo/video/audio/document), organizer profiles, talent hunts (casting calls), applications with status tracking, saved-talent shortlist, skill/keyword search, and a full Tailwind UI for every flow (browse, profile pages, dashboards).

Not yet built: actual file upload to object storage (media URLs currently just accept a link, no upload endpoint), admin verification workflow, messaging/inbox between organizer and talent, notifications, and a "close talent hunt" action.
