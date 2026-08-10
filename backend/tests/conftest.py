import subprocess
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

import app.models  # noqa: F401  (registers every model on Base.metadata before create_all)
from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole

TEST_DB_NAME = "ygt_test"


def _test_database_url() -> str:
    return settings.DATABASE_URL.rsplit("/", 1)[0] + f"/{TEST_DB_NAME}"


@pytest.fixture(scope="session", autouse=True)
def _ensure_test_database():
    """Create the dedicated test database on the same Postgres server, if it doesn't exist yet.

    Tests never touch the `ygt` dev database (which holds the manually-verified demo data) —
    everything here runs against `ygt_test` instead.
    """
    admin_engine = create_engine(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DB_NAME}).scalar()
        if not exists:
            conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
    admin_engine.dispose()


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(_test_database_url())
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db_session(engine):
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = Session(bind=connection)

    # Every CRUD function in this app calls db.commit(). A plain commit would end
    # outer_transaction early, so each commit is redirected into a SAVEPOINT that gets
    # restarted immediately — the real rollback below is the only thing that ever persists.
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, transaction):
        if transaction.nested and not transaction._parent.nested:
            sess.expire_all()
            sess.begin_nested()

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


DEFAULT_PASSWORD = "TestPass123!"


def register_user(client, email: str, *, password: str = DEFAULT_PASSWORD, full_name: str = "Test User", role: str = "talent") -> dict:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name, "role": role, "consent_given": True},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def get_verification_code(db_session, email: str) -> str:
    user = db_session.query(User).filter(User.email == email).first()
    assert user is not None, f"no user found for {email}"
    assert user.verification_code, f"no verification code set for {email}"
    return user.verification_code


def verify_email(client, db_session, email: str) -> str:
    code = get_verification_code(db_session, email)
    resp = client.post("/api/v1/auth/verify-email", json={"email": email, "code": code})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def register_and_verify(client, db_session, email: str, *, password: str = DEFAULT_PASSWORD, full_name: str = "Test User", role: str = "talent") -> str:
    register_user(client, email, password=password, full_name=full_name, role=role)
    return verify_email(client, db_session, email)


def get_password_reset_code(db_session, email: str) -> str:
    user = db_session.query(User).filter(User.email == email).first()
    assert user is not None, f"no user found for {email}"
    assert user.password_reset_code, f"no password reset code set for {email}"
    return user.password_reset_code


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_admin(db_session, email: str, *, password: str = DEFAULT_PASSWORD, full_name: str = "Test Admin") -> str:
    # Admins are never created through the public API (by design), so this bypasses it the
    # same way scripts/create_admin.py does: an ORM insert, straight to token issuance.
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=UserRole.ADMIN,
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return create_access_token(subject=str(user.id))


@pytest.fixture()
def talent_token(client, db_session):
    return register_and_verify(client, db_session, "talent_fixture@example.com", full_name="Fixture Talent", role="talent")


@pytest.fixture()
def talent_headers(talent_token):
    return auth_headers(talent_token)


@pytest.fixture()
def talent_profile(client, talent_headers):
    resp = client.post(
        "/api/v1/talents/me",
        json={"display_name": "Fixture Talent", "categories": ["acting"], "city": "Colombo"},
        headers=talent_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def recruiter_token(client, db_session):
    return register_and_verify(client, db_session, "recruiter_fixture@example.com", full_name="Fixture Recruiter", role="recruiter")


@pytest.fixture()
def recruiter_headers(recruiter_token):
    return auth_headers(recruiter_token)


@pytest.fixture()
def recruiter_profile(client, recruiter_headers):
    resp = client.post(
        "/api/v1/recruiters/me",
        json={"company_name": "Fixture Studios", "industry": "Film"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def admin_token(db_session):
    return create_admin(db_session, "admin_fixture@example.com", full_name="Fixture Admin")


@pytest.fixture()
def admin_headers(admin_token):
    return auth_headers(admin_token)


@pytest.fixture(scope="session")
def sample_video_bytes() -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.mp4"
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=10",
                "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
                "-shortest", "-pix_fmt", "yuv420p",
                str(path),
            ],
            check=True,
            capture_output=True,
        )
        return path.read_bytes()


@pytest.fixture(scope="session")
def sample_audio_bytes() -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.mp3"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1", str(path)],
            check=True,
            capture_output=True,
        )
        return path.read_bytes()


@pytest.fixture(scope="session")
def sample_photo_bytes() -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.jpg"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=size=320x240", "-frames:v", "1", str(path)],
            check=True,
            capture_output=True,
        )
        return path.read_bytes()


@pytest.fixture()
def casting_call(client, recruiter_headers, recruiter_profile):
    resp = client.post(
        "/api/v1/casting-calls",
        json={
            "title": "Lead role in short film",
            "description": "Seeking a lead actor.",
            "category": "acting",
            "roles": [{"title": "Lead role in short film"}],
        },
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
