"""PIN-guarded partner documents -- e.g. the business-development walkthrough deck.

Served at test.yougottalent.lk/docs/<path>: the frontend rewrites /docs/* to this router (see
frontend/next.config.ts), so the browser only ever sees the site's own origin and the cookie set
here is scoped to /docs on that origin.

WHY THE BACKEND, AND WHY BLOB STORAGE. The repository is public. A deck committed to it, or a PIN
written into code or a workflow file, is readable on GitHub no matter what guards the site. So the
files live in a private blob container (DOCS_CONTAINER, uploaded by hand, never in git) and the PIN
exists only as an environment variable on the Container App. The backend already holds the storage
connection string; the frontend holds no secrets at all.

Unset DOCS_PIN and every path is a 404 -- which is how production behaves, so the same code can
merge to main without exposing anything there.
"""
import hashlib
import hmac
import html
import json
import mimetypes
import re
import uuid
from datetime import datetime, timezone
from typing import Iterator
from urllib.parse import quote

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse

from app.core.config import settings
from app.core.private_storage import LOCAL_PRIVATE_DIR
from app.core.rate_limit import limiter

router = APIRouter(prefix="/partner-docs", tags=["partner-docs"])

COOKIE_NAME = "ygt_docs"
COOKIE_MAX_AGE_SECONDS = 12 * 60 * 60
LOCAL_DOCS_DIR = LOCAL_PRIVATE_DIR.parent / "private_docs"

# Only what a static deck needs. Anything else -- including a path with a dot-dot or a separator
# trick -- is refused before it gets anywhere near storage.
_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_ALLOWED_EXTENSIONS = {".html", ".jpg", ".jpeg", ".png", ".webp", ".svg", ".css", ".js", ".pdf"}


def _forwarded_ip(request: Request) -> str:
    # Behind Azure ingress and the Next.js rewrite, the socket peer is a proxy shared by every
    # visitor; limiting on it would lock everyone out after one person's typos.
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")


def _clean_path(path: str) -> str:
    """Validate a requested path and return the storage path. /docs/questions means
    questions.html, so pages can be shared without the extension."""
    segments = path.split("/")
    if not path or len(segments) > 4 or not all(_SEGMENT.match(s) and ".." not in s for s in segments):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if "." not in segments[-1]:
        path += ".html"
    if "." + path.rsplit(".", 1)[-1].lower() not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return path


def _require_enabled() -> str:
    if not settings.DOCS_PIN:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return settings.DOCS_PIN


def _session_token(pin: str) -> str:
    # Keyed on SECRET_KEY as well as the PIN, so the cookie can't be minted by someone who only
    # knows the PIN's hashing scheme, and changing the PIN logs every viewer out.
    return hmac.new(settings.SECRET_KEY.encode(), f"partner-docs:{pin}".encode(), hashlib.sha256).hexdigest()


def _is_unlocked(request: Request, pin: str) -> bool:
    return hmac.compare_digest(request.cookies.get(COOKIE_NAME, ""), _session_token(pin))


def _open(path: str) -> Iterator[bytes]:
    if settings.AZURE_STORAGE_CONNECTION_STRING:
        from azure.core.exceptions import ResourceNotFoundError
        from azure.storage.blob import BlobServiceClient

        service = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        blob = service.get_container_client(settings.DOCS_CONTAINER).get_blob_client(path)
        try:
            return blob.download_blob().chunks()
        except ResourceNotFoundError as exc:
            raise FileNotFoundError(path) from exc

    file = LOCAL_DOCS_DIR / path
    if not file.is_file():
        raise FileNotFoundError(path)
    return iter([file.read_bytes()])


_PRIVATE_HEADERS = {
    "X-Robots-Tag": "noindex, nofollow",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}


def _pin_page(path: str, error: str | None = None, status_code: int = status.HTTP_401_UNAUTHORIZED) -> HTMLResponse:
    message = f'<p class="err" role="alert">{html.escape(error, quote=False)}</p>' if error else ""
    body = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Enter PIN · YouGotTalent</title>
<style>
  body {{ margin:0; min-height:100vh; display:grid; place-items:center; background:#0B0B0F; color:#FAFAFA;
         font-family:"Plus Jakarta Sans",ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }}
  form {{ width:min(360px,calc(100vw - 48px)); display:flex; flex-direction:column; gap:16px; }}
  .brand {{ display:flex; align-items:center; gap:10px; font-weight:800; font-size:18px; }}
  .mark {{ width:34px; height:34px; border-radius:8px; background:#E11D48; display:grid; place-items:center; font-size:14px; }}
  h1 {{ margin:10px 0 0; font-size:26px; letter-spacing:-.02em; }}
  p {{ margin:0; color:#A1A1AA; line-height:1.5; font-size:15px; }}
  input {{ font:inherit; font-size:24px; letter-spacing:.4em; text-align:center; padding:14px; border-radius:10px;
          border:2px solid #3A3A44; background:#16161C; color:#fff; }}
  input:focus {{ outline:none; border-color:#E11D48; }}
  button {{ font:inherit; font-weight:700; font-size:16px; padding:14px; border:0; border-radius:10px; background:#E11D48; color:#fff; cursor:pointer; }}
  button:focus-visible {{ outline:3px solid #FB7185; outline-offset:2px; }}
  .err {{ color:#FDA4AF; }}
</style></head>
<body><form method="post" action="/docs/{quote(path)}">
  <div class="brand"><span class="mark">YT</span>YouGotTalent</div>
  <h1>This page is private</h1>
  <p>Enter the PIN you were given to view it.</p>
  {message}
  <label for="pin" style="position:absolute;left:-9999px">PIN</label>
  <input id="pin" name="pin" type="password" inputmode="numeric" autocomplete="off" maxlength="12" required autofocus>
  <button type="submit">View</button>
</form></body></html>"""
    return HTMLResponse(body, status_code=status_code, headers={**_PRIVATE_HEADERS, "Cache-Control": "no-store"})


# ---------------------------------------------------------------------------------------------
# Survey responses -- e.g. /docs/questions.html posts its answers here.
#
# Stored as one JSON file per respondent, beside the documents in the same private container
# (responses/<survey>/<id>.json), so answers stay out of the public repository and out of the
# app database. The questions live in the page; this only validates shape and size, which keeps
# a question change from needing a deploy. Declared BEFORE the catch-all routes below, which
# would otherwise claim these paths as files.
# ---------------------------------------------------------------------------------------------

_SURVEY = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
_MAX_RESPONSE_BYTES = 100_000


def _require_unlocked(request: Request) -> None:
    pin = _require_enabled()
    if not _is_unlocked(request, pin):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Enter the PIN first.")


def _response_key(survey: str, response_id: str | None = None) -> str:
    if not _SURVEY.match(survey):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if response_id is None:
        return f"responses/{survey}/"
    try:
        return f"responses/{survey}/{uuid.UUID(response_id)}.json"
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


def _container():
    from azure.storage.blob import BlobServiceClient

    return BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING).get_container_client(
        settings.DOCS_CONTAINER
    )


def _read_json(key: str) -> dict | None:
    if settings.AZURE_STORAGE_CONNECTION_STRING:
        from azure.core.exceptions import ResourceNotFoundError

        try:
            return json.loads(_container().get_blob_client(key).download_blob().readall())
        except ResourceNotFoundError:
            return None
    file = LOCAL_DOCS_DIR / key
    return json.loads(file.read_text(encoding="utf-8")) if file.is_file() else None


def _write_json(key: str, data: dict) -> None:
    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    if settings.AZURE_STORAGE_CONNECTION_STRING:
        from azure.storage.blob import ContentSettings

        _container().get_blob_client(key).upload_blob(
            body, overwrite=True, content_settings=ContentSettings(content_type="application/json")
        )
        return
    file = LOCAL_DOCS_DIR / key
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(body)


def _list_json(prefix: str) -> list[dict]:
    if settings.AZURE_STORAGE_CONNECTION_STRING:
        container = _container()
        return [json.loads(container.get_blob_client(b.name).download_blob().readall())
                for b in container.list_blobs(name_starts_with=prefix) if b.name.endswith(".json")]
    folder = LOCAL_DOCS_DIR / prefix
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(folder.glob("*.json"))] if folder.is_dir() else []


async def _read_payload(request: Request) -> dict:
    raw = await request.body()
    if len(raw) > _MAX_RESPONSE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Response too large.")
    try:
        data = json.loads(raw)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Body must be JSON.")
    if not isinstance(data, dict) or not isinstance(data.get("answers", {}), dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Expected an object with answers.")
    return data


def _record(response_id: str, survey: str, data: dict, created_at: str) -> dict:
    return {
        "id": response_id,
        "survey": survey,
        "created_at": created_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "completed": bool(data.get("completed", False)),
        "respondent": data.get("respondent") if isinstance(data.get("respondent"), dict) else {},
        "answers": data.get("answers", {}),
    }


@router.post("/api/responses/{survey}", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute", key_func=_forwarded_ip)
async def create_survey_response(survey: str, request: Request):
    _require_unlocked(request)
    _response_key(survey)
    data = await _read_payload(request)
    response_id = str(uuid.uuid4())
    record = _record(response_id, survey, data, datetime.now(timezone.utc).isoformat())
    _write_json(_response_key(survey, response_id), record)
    return {"id": response_id, "updated_at": record["updated_at"]}


@router.put("/api/responses/{survey}/{response_id}")
@limiter.limit("60/minute", key_func=_forwarded_ip)
async def update_survey_response(survey: str, response_id: str, request: Request):
    _require_unlocked(request)
    key = _response_key(survey, response_id)
    existing = _read_json(key)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    data = await _read_payload(request)
    record = _record(existing["id"], survey, data, existing["created_at"])
    _write_json(key, record)
    return {"id": record["id"], "updated_at": record["updated_at"]}


@router.get("/api/responses/{survey}")
def download_survey_responses(survey: str, request: Request):
    _require_unlocked(request)
    records = sorted(_list_json(_response_key(survey)), key=lambda r: r.get("created_at", ""))
    body = json.dumps({"survey": survey, "exported_at": datetime.now(timezone.utc).isoformat(),
                       "count": len(records), "responses": records}, ensure_ascii=False, indent=2)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    return Response(body, media_type="application/json", headers={
        **_PRIVATE_HEADERS,
        "Cache-Control": "no-store",
        "Content-Disposition": f'attachment; filename="{survey}-responses-{stamp}.json"',
    })


@router.get("/{path:path}")
def read_partner_doc(path: str, request: Request):
    pin = _require_enabled()
    requested, path = path, _clean_path(path)

    if not _is_unlocked(request, pin):
        if path.endswith(".html"):
            return _pin_page(requested)
        return Response(status_code=status.HTTP_401_UNAUTHORIZED, headers=_PRIVATE_HEADERS)

    try:
        stream = _open(path)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    media_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    cache = "private, no-store" if path.endswith(".html") else "private, max-age=3600"
    return StreamingResponse(stream, media_type=media_type, headers={**_PRIVATE_HEADERS, "Cache-Control": cache})


@router.post("/{path:path}")
@limiter.limit("5/minute", key_func=_forwarded_ip)
def unlock_partner_doc(path: str, request: Request, pin: str = Form("")):
    expected = _require_enabled()
    _clean_path(path)

    if not hmac.compare_digest(pin.strip().encode(), expected.encode()):
        return _pin_page(path, error="That PIN isn't right. Check it and try again.")

    # Back to the address as typed -- /docs/questions stays /docs/questions.
    response = RedirectResponse(url=f"/docs/{quote(path)}", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        COOKIE_NAME,
        _session_token(expected),
        max_age=COOKIE_MAX_AGE_SECONDS,
        path="/docs",
        httponly=True,
        secure=settings.FRONTEND_URL.startswith("https://"),
        samesite="lax",
    )
    return response
