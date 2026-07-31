---
name: yougottalent-app-guide
description: Ground-truth architecture, feature inventory, and hard-won conventions for the YouGotTalent app. Load this before fixing bugs or extending any feature — it documents patterns (enum storage, pricing grandfathering, admin/public separation, moderation reuse, payment gateway abstraction) that are easy to silently break if you don't know they're intentional. The root README.md is stale — trust this file and the code over it.
---

# YouGotTalent — App Reference

Sri Lankan creative-talent marketplace. Talent (any category — acting, singing, dancing, painting,
script writing, photography, music, choreography, comedy, voice over, direction, modeling, design,
and more) build profiles with audition media; recruiters post talent hunts and search/hire. Backend
FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL; frontend Next.js 16 (App Router) + TypeScript +
Tailwind v4. Auth is JWT (OAuth2 password flow).

**The root `README.md` is stale** (it claims messaging, admin, and media upload aren't built —
they are, fully). Don't trust it for feature status; trust this file and the actual code.

## Repo layout

```
backend/app/
  models/        SQLAlchemy models (one file per domain concept, see inventory below)
  schemas/       Pydantic request/response schemas
  crud/          DB access + business logic, one file per domain concept
  api/routes/    FastAPI routers, mounted under /api/v1 in main.py
  core/          config, security, payments/, pricing.py, email, storage, discord
  db/            Base + session
backend/alembic/versions/   migrations, linear chain — check `down_revision` for the real head
backend/tests/   pytest, one file per feature area, run against a real `ygt_test` Postgres DB

frontend/src/
  app/           Next.js routes (see full site map below)
  components/    shared UI; components/admin/* only used inside /admin
  lib/api.ts     typed fetch client — every backend endpoint has a matching method here
  lib/ui.ts      shared style constants (btnPrimary, sectionClass, badgeClass, category colors, etc.)
  lib/auth-context.tsx   useAuth() — user/token/loading + login/register/logout
```

## Full feature inventory

### Backend models (`backend/app/models/*.py`)

| File | Model(s) | Purpose |
|---|---|---|
| `user.py` | `User` | Account (role: talent/recruiter/admin, email verification, password reset, PDPA consent timestamp) |
| `talent_profile.py` | `TalentProfile` | Talent's public profile (category, bio, skills, tier, verification, social links, JSONB per-category attributes) |
| `recruiter_profile.py` | `RecruiterProfile` | Recruiter/agency profile (company name, recruiter type, industry, tier, verification) |
| `media.py` | `Media` | Portfolio item (photo/video/audio/document) on a talent profile |
| `casting_call.py` | `CastingCall` | Job/audition posting (category, deadline, audition brief, tags, view count, featured) |
| `casting_call_role.py` | `CastingCallRole` | One applyable role/stream within a casting call |
| `application.py` | `Application` | Talent's application to a specific role (pending/shortlisted/rejected/accepted) |
| `saved_talent.py` | `SavedTalent` | Recruiter's shortlist bookmark |
| `conversation.py` / `message.py` | `Conversation`, `Message` | 1:1 talent↔recruiter messaging |
| `saved_search.py` | `SavedSearch` | Recruiter's saved talent-search filter set |
| `credit.py` | `Credit` | Past-project résumé entry on a talent profile |
| `invitation.py` | `Invitation` | Recruiter's direct invite of a talent to a casting call |
| `availability_window.py` / `booking.py` | `AvailabilityWindow`, `Booking` | Talent's weekly availability + scheduled engagements |
| `follow.py` | `Follow` | Talent following a recruiter |
| `review.py` | `Review` | Post-booking rating/comment |
| `report.py` | `Report` | Generic moderation report (bug or content report) — see "Report system reuse" below |
| `subscription.py` | `Subscription`, `SubscriptionPayment` | Premium subscription (plan, cycle, gateway, trial, cancel/retention/dunning state) + payment ledger |
| `pricing.py` | `PricingVersion` | Versioned price history — see "Pricing grandfathering" below |
| `title.py` | `Title`, `TitleReview` | Community film/TV/song catalog entry + rating/critique |
| `discussion.py` | `DiscussionThread`, `DiscussionReply` | Community discussion board |

No separate admin table — admin is just `User.role == "admin"`.

### Backend routes (`backend/app/api/routes/*.py`, all under `/api/v1`)

| File | Base path | Exposes |
|---|---|---|
| `auth.py` | `/auth` | register, verify/resend email, login, forgot/reset password, `GET /me` |
| `talents.py` | `/talents` | browse/search, own profile CRUD, media upload (file/cover/intro video), reviews, verification request, tier upgrade, credits, save/unsave |
| `recruiters.py` | `/recruiters` | own profile CRUD, analytics, reviews, saved-talents, verification, tier upgrade, saved searches, public profile |
| `casting_calls.py` | `/casting-calls` | list/browse, detail, view-count, create |
| `applications.py` | mixed | apply (+ file upload), list applicants, list own applications, update status |
| `conversations.py` | `/conversations` | start/list conversations, list/send messages |
| `invitations.py` | mixed | recruiter invites talent, talent views/responds |
| `admin.py` | `/admin` | stats, users, verification queues, casting-call moderation, financial overview, reports, subscriptions/payments, churn, dunning-sweep trigger, community moderation deletes, pricing view/create |
| `bookings.py` | mixed | availability CRUD, bookings create/list/respond/cancel, post-booking review |
| `follows.py` | mixed | follow/unfollow, list following |
| `reports.py` | `/reports` | submit a report |
| `billing.py` | `/billing` | current pricing (public), own subscription, checkout, cancel/reactivate, retention offer, payment history, PayHere/Stripe webhooks |
| `titles.py` | `/titles` | catalog list/create/detail, reviews list/mine/create/delete |
| `discussions.py` | `/discussions` | threads list/create/detail, replies list/create |

### Frontend site map (`frontend/src/app/`)

Public: `/`, `/pricing`. Auth: `/login`, `/register`, `/forgot-password`, `/reset-password`.
Talent discovery: `/talents`, `/talents/[id]`. Recruiter: `/recruiters/[id]`. Casting calls:
`/casting-calls`, `/casting-calls/[id]`. Messaging: `/messages`, `/messages/[id]`. Dashboard (talent
or recruiter, role-branched): `/dashboard`, `/dashboard/casting-calls/[id]`. Billing:
`/billing/success`. Community: `/community`, `/community/titles(+/new,+/[id])`,
`/community/discussions(+/new,+/[id])`. Admin (own layout, see below): `/admin`, `/admin/users`,
`/admin/verification`, `/admin/casting-calls`, `/admin/community`, `/admin/reports`,
`/admin/subscriptions`, `/admin/financial`, `/admin/pricing`.

### Payment gateways (`backend/app/core/payments/`)

Abstract `PaymentGateway` interface (`base.py`) with three implementations selected via
`settings.PAYMENT_GATEWAY` through `factory.py`: `mock.py` (instant activation, no external call,
default for dev/CI), `payhere.py` (Sri Lanka LKR, signed checkout + webhook), `stripe_gateway.py`
(international, USD, Stripe Checkout Sessions + webhooks). **Never call PayHere/Stripe SDKs
directly from routes/CRUD — always go through the interface via `get_gateway()`.**

## Critical conventions — do not violate these

1. **Postgres enum columns store the Python enum member's `.name` (uppercase), not `.value`.**
   Confirmed via `casting_call_status`, `user_role`, etc. Any new enum-backed column/migration must
   follow this — don't assume lowercase values in raw SQL or seed data.

2. **`op.add_column` with a brand-new `sa.Enum(...)` does NOT auto-create the Postgres enum type.**
   You must call `my_enum.create(op.get_bind(), checkfirst=True)` before `op.add_column`, or the
   migration fails with "type does not exist."

3. **`create_type=False` only works on `sqlalchemy.dialects.postgresql.ENUM`, not the generic
   `sa.Enum`.** If a new table's column reuses an enum type an earlier migration already created,
   you must import `postgresql.ENUM` and pass `create_type=False` on that specific class — passing
   it to `sa.Enum(...)` is silently ignored and `op.create_table` will crash with
   `DuplicateObject: type "..." already exists`. Hit this exact bug building `pricing_versions`.

4. **Extending an existing enum with new values**: `ALTER TYPE x ADD VALUE IF NOT EXISTS 'Y'` works
   fine inside Alembic's transactional DDL on modern Postgres — this is the pattern for adding new
   `ReportTargetType` values, not recreating the enum.

5. **Subscription pricing is grandfathered by design — never break this.**
   `Subscription.price_lkr` is a snapshot taken once at trial-start or checkout time via
   `price_lkr_for(db, plan, cycle)` in `core/pricing.py`, which reads the *current* `PricingVersion`
   row (admin-configurable via `/admin/pricing`). Renewal code (`apply_webhook_event`,
   `_finalize_if_due`, the dunning sweep) must **never** recompute or overwrite `price_lkr` — an
   existing subscriber keeps the price they signed up at for the life of their subscription. Only
   a fresh `start_checkout` call (new signup, or re-subscribing after full cancellation) re-reads
   the current price. `effective_price_lkr` (a computed property, not a column) applies a temporary
   retention discount on top of the stored `price_lkr` — don't confuse the two.

6. **Stripe pricing is a separate, un-grandfathered axis.** `STRIPE_TALENT_PRICE`/
   `STRIPE_RECRUITER_PRICE` in settings are USD cents, read live at Stripe Checkout Session
   creation — they are NOT wired into `PricingVersion` or the LKR grandfathering system. If you
   want Stripe prices admin-configurable/versioned too, that's a real gap, not yet built.

7. **No cron/queue exists in this app.** Time-based subscription transitions (trial expiry, period
   rollover, past-due grace period, downgrade-to-free) are reconciled lazily per-request via
   `sync_if_expired()` (called from auth deps that load a talent/recruiter profile) or in bulk via
   `run_dunning_sweep()`, meant to be hit by an external scheduler (Azure Container Apps scheduled
   job, GitHub Actions cron, cron-job.org) or manually from the admin Subscriptions page. Don't
   assume anything runs on a timer — it only runs on request or when explicitly triggered.

8. **Admin is fully separated from the public site, both visually and by route.** `app/admin/*`
   pages render inside `app/admin/layout.tsx`, which client-side redirects non-admins away and
   never renders the public `Header`/`Footer`. That chrome-hiding is controlled centrally by
   `components/AppShell.tsx`, which checks `usePathname().startsWith("/admin")` — if you add a new
   top-level section that needs its own shell (no public nav), extend `AppShell`, don't duplicate
   layout logic. Conversely, never put a public-facing page under `/admin`.

9. **The generic `Report` model + `ReportTargetType` enum is the one moderation system — reuse it,
   don't build a parallel one.** It already covers talent_profile, recruiter_profile, casting_call,
   message, title, title_review, discussion_thread, discussion_reply. To make a new content type
   reportable: add an enum value via an `ALTER TYPE ADD VALUE` migration, add a case to
   `reportTargetHref()` in `components/admin/ReportQueue.tsx` (so admins get a working link), and if
   there's a natural one-click delete action, add it to `DELETABLE_TARGET_TYPES` in that same file.

10. **Ad-hoc (unmapped) attributes on ORM instances are an intentional, established pattern** — e.g.
    `CastingCall.recruiter_company_name`, `Subscription.subscriber_name`,
    `Title.average_rating`/`review_count`. CRUD functions set these directly on the Python object
    before returning it, and Pydantic schemas with `from_attributes=True` pick them up. Don't
    "fix" these into real mapped columns; don't be surprised they're not in the `__table__`.

11. **Community content (titles/discussions) is public-read, login-gated-write, any role.** All GET
    endpoints require no auth; all POST/DELETE require `get_current_user` with no role restriction
    (talent, recruiter, or admin can all post/rate/reply). Follow this same split for any future
    community-style feature rather than restricting by role.

12. **Tests run against a real `ygt_test` Postgres database using `Base.metadata.create_all()`, NOT
    Alembic migrations** (see `tests/conftest.py`). Consequences:
    - Data-seeding logic that lives only in a migration's `upgrade()` (e.g. the `pricing_versions`
      seed rows) will **not** exist in tests — any CRUD reading such a table needs a safe fallback
      for the empty-table case (see `current_monthly_price_lkr`'s settings-based fallback).
    - Each test runs inside one Postgres transaction (outer transaction + SAVEPOINT-per-commit), so
      Postgres's `now()` (transaction-scoped) returns the **same value** for multiple inserts within
      one test. Any model whose row ordering/history matters (e.g. `PricingVersion.created_at`)
      should use a Python-side `default=lambda: datetime.now(timezone.utc)` instead of
      `server_default=func.now()`, or ordering will be ambiguous under test isolation.

13. **Docker on Windows has no reliable hot reload** for either service — after editing source,
    `docker restart <container>` before checking the browser, for both `frontend` (`next dev`) and
    `backend` (`uvicorn`, no `--reload` in the entrypoint).

14. **Deploys are manual, not via CI/CD.** GitHub Actions (`.github/workflows/deploy.yml`) is the
    documented/intended path but is currently broken — pushing to GHCR gets a 403 because the
    repo's Actions bot isn't granted write access to the `ygt-backend`/`ygt-frontend` packages (a
    GitHub UI fix only a repo admin can do; not fixable from code). Until that's fixed, deploy
    manually: build+push both images to `ghcr.io/kalindupri/ygt-{backend,frontend}` with a **new
    unique tag every time** (Azure Container Apps won't detect a reused tag as changed — tags have
    gone `azure-v6` → `v10` so far), then `az containerapp update --image ...` for both apps. The
    frontend build needs `--build-arg NEXT_PUBLIC_API_URL=https://<backend-fqdn>/api/v1` since
    Next.js bakes `NEXT_PUBLIC_*` vars in at build time, not runtime.

## Known gaps / not yet built

- CI/CD is broken (see #14 above) — needs a human with GitHub admin rights.
- Stripe pricing isn't versioned/grandfathered like the LKR path (see #6).
- Minors submitting auditions need a guardian-consent flow — not implemented (PDPA compliance note
  from the original README, still accurate).
- No automated E2E suite currently exercises the community, admin-split, or pricing features built
  in this most recent phase (Playwright specs exist for earlier features only) — this was verified
  manually in-browser instead each time.
