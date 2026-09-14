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
import mimetypes
import re
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
    segments = path.split("/")
    if not path or len(segments) > 4 or not all(_SEGMENT.match(s) and ".." not in s for s in segments):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
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


@router.get("/{path:path}")
def read_partner_doc(path: str, request: Request):
    pin = _require_enabled()
    path = _clean_path(path)

    if not _is_unlocked(request, pin):
        if path.endswith(".html"):
            return _pin_page(path)
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
    path = _clean_path(path)

    if not hmac.compare_digest(pin.strip().encode(), expected.encode()):
        return _pin_page(path, error="That PIN isn't right. Check it and try again.")

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
