import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/kamla_test",
)
os.environ.setdefault(
    "APP_DATABASE_URL",
    "postgresql+psycopg://kamla_app:kamla_app_test_only@localhost:5432/kamla_test",
)
os.environ.setdefault("CLERK_ISSUER", "https://clerk.test")
os.environ.setdefault("CLERK_AUDIENCE", "test-audience")
os.environ.setdefault("CLERK_JWKS_URL", "https://clerk.test/.well-known/jwks.json")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

from collections.abc import Generator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import Engine, make_url  # noqa: E402
from sqlalchemy.exc import OperationalError  # noqa: E402

from kamla_api.auth import get_verifier  # noqa: E402
from kamla_api.config import sqlalchemy_url  # noqa: E402
from kamla_api.main import app  # noqa: E402


class FakeJwtVerifier:
    def verify(self, token: str) -> dict:
        if token.startswith("user-a"):
            return {"sub": "clerk_user_a", "email": "a@example.com", "aud": "test-audience"}
        if token.startswith("user-b"):
            return {"sub": "clerk_user_b", "email": "b@example.com", "aud": "test-audience"}
        raise ValueError("unknown test token")


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_verifier] = lambda: FakeJwtVerifier()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    url = sqlalchemy_url(os.environ["DATABASE_URL"])
    db_engine = create_engine(url, pool_pre_ping=True)
    try:
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        pytest.skip("PostgreSQL is not available")
    alembic_ini = Path(__file__).resolve().parents[1] / "alembic.ini"
    cfg = Config(str(alembic_ini))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    with db_engine.begin() as conn:
        # kamla_app is created NOLOGIN by the migration (it's meant to be granted to a
        # real login role, not connected to directly). Give it a login for the lifetime
        # of this disposable test database only, so RLS tests exercise the actual
        # NOBYPASSRLS role the app is supposed to run as, instead of the Postgres
        # superuser (which always bypasses RLS regardless of FORCE ROW LEVEL SECURITY).
        conn.execute(text("ALTER ROLE kamla_app LOGIN PASSWORD 'kamla_app_test_only'"))
    yield db_engine
    db_engine.dispose()


@pytest.fixture(scope="session")
def app_engine(engine: Engine) -> Generator[Engine, None, None]:
    """Connects as kamla_app (NOBYPASSRLS) so tests exercise real RLS enforcement."""
    app_url = make_url(str(engine.url)).set(
        username="kamla_app", password="kamla_app_test_only"
    )
    db_engine = create_engine(app_url, pool_pre_ping=True)
    yield db_engine
    db_engine.dispose()
