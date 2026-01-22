from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


def normalize_database_url(url: str) -> str:
    if url.startswith("postgresql+"):
        return url
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return normalize_database_url(url)


def get_engine(url: str | None = None) -> Engine:
    database_url = normalize_database_url(url or get_database_url())
    return create_engine(database_url)


def get_sessionmaker(url: str | None = None) -> sessionmaker:
    return sessionmaker(bind=get_engine(url))
