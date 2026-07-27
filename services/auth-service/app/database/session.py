from typing import Generator

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import Settings, get_current_settings
from app.database.base import Base


def get_engine(settings: Settings):
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, connect_args=connect_args, echo=False)


def get_session_factory(settings: Settings):
    engine = get_engine(settings)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db(settings: Settings) -> None:
    engine = get_engine(settings)
    Base.metadata.create_all(bind=engine)


def get_settings() -> Settings:
    return get_current_settings()


def get_db(settings: Settings = Depends(get_settings)) -> Generator[Session, None, None]:
    SessionLocal = get_session_factory(settings)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
