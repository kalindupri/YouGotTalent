"""PIN-guarded partner documents (/docs/* on the frontend, /partner-docs/* here)."""
import pytest

from app.api.routes import partner_docs
from app.core.config import settings

BASE = "/api/v1/partner-docs"
PIN = "246810"


@pytest.fixture
def docs(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "DOCS_PIN", PIN)
    monkeypatch.setattr(settings, "AZURE_STORAGE_CONNECTION_STRING", "")
    monkeypatch.setattr(partner_docs, "LOCAL_DOCS_DIR", tmp_path)
    (tmp_path / "walkthrough.html").write_text("<h1>The deck</h1>", encoding="utf-8")
    (tmp_path / "shots").mkdir()
    (tmp_path / "shots" / "home.jpg").write_bytes(b"\xff\xd8\xff\xe0fake-jpeg")
    return tmp_path


def _unlock(client):
    return client.post(f"{BASE}/walkthrough.html", data={"pin": PIN}, follow_redirects=False)


def test_everything_is_a_404_when_no_pin_is_configured(client, monkeypatch):
    # Production's setting: the route exists in the code but must not reveal that it does.
    monkeypatch.setattr(settings, "DOCS_PIN", "")
    assert client.get(f"{BASE}/walkthrough.html").status_code == 404
    assert client.post(f"{BASE}/walkthrough.html", data={"pin": "anything"}).status_code == 404


def test_a_locked_page_shows_the_pin_form_not_the_document(client, docs):
    r = client.get(f"{BASE}/walkthrough.html")
    assert r.status_code == 401
    assert 'name="pin"' in r.text
    assert "The deck" not in r.text
    assert r.headers["x-robots-tag"].startswith("noindex")


def test_a_locked_asset_is_refused_without_a_form(client, docs):
    r = client.get(f"{BASE}/shots/home.jpg")
    assert r.status_code == 401
    assert r.content == b""


def test_wrong_pin_is_rejected_and_sets_no_cookie(client, docs):
    r = client.post(f"{BASE}/walkthrough.html", data={"pin": "000000"}, follow_redirects=False)
    assert r.status_code == 401
    assert "isn't right" in r.text
    assert partner_docs.COOKIE_NAME not in r.cookies


def test_right_pin_redirects_back_to_the_public_docs_path_with_a_scoped_cookie(client, docs):
    r = _unlock(client)
    assert r.status_code == 303
    # The browser only knows /docs/... (the frontend rewrites it here), so that is where it must
    # land and where the cookie must apply.
    assert r.headers["location"] == "/docs/walkthrough.html"
    set_cookie = r.headers["set-cookie"]
    assert "Path=/docs" in set_cookie and "HttpOnly" in set_cookie
    assert PIN not in set_cookie, "the cookie must not carry the PIN itself"


def test_unlocked_session_reads_the_page_and_its_images(client, docs):
    token = _unlock(client).cookies[partner_docs.COOKIE_NAME]
    client.cookies.set(partner_docs.COOKIE_NAME, token)

    page = client.get(f"{BASE}/walkthrough.html")
    assert page.status_code == 200
    assert "The deck" in page.text
    assert page.headers["cache-control"] == "private, no-store"

    image = client.get(f"{BASE}/shots/home.jpg")
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/jpeg"


def test_a_forged_cookie_does_not_unlock(client, docs):
    client.cookies.set(partner_docs.COOKIE_NAME, "not-a-real-token")
    assert client.get(f"{BASE}/walkthrough.html").status_code == 401


def test_changing_the_pin_logs_existing_viewers_out(client, docs, monkeypatch):
    client.cookies.set(partner_docs.COOKIE_NAME, _unlock(client).cookies[partner_docs.COOKIE_NAME])
    monkeypatch.setattr(settings, "DOCS_PIN", "135790")
    assert client.get(f"{BASE}/walkthrough.html").status_code == 401


@pytest.mark.parametrize(
    "path",
    ["..%2F..%2Fapp%2Fcore%2Fconfig.py", "shots/..%2F..%2Fsecret.html", ".env", "walkthrough.py", "a/b/c/d/e.html"],
)
def test_paths_outside_the_deck_are_refused(client, docs, path):
    client.cookies.set(partner_docs.COOKIE_NAME, _unlock(client).cookies[partner_docs.COOKIE_NAME])
    assert client.get(f"{BASE}/{path}").status_code == 404


def test_a_missing_file_is_a_404_once_unlocked(client, docs):
    client.cookies.set(partner_docs.COOKIE_NAME, _unlock(client).cookies[partner_docs.COOKIE_NAME])
    assert client.get(f"{BASE}/nope.html").status_code == 404
