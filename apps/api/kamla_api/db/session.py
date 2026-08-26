from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from kamla_api.config import Settings, get_settings


@lru_cache
def get_engine(url: str | None = None):
    return create_engine(url or get_settings().sqlalchemy_app_database_url, pool_pre_ping=True)


def session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    engine = get_engine(settings.sqlalchemy_app_database_url if settings else None)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    SessionLocal = session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def set_current_user(session: Session, user_id: str) -> None:
    session.execute(text("SELECT set_config('app.current_user_id', :uid, true)"), {"uid": user_id})
