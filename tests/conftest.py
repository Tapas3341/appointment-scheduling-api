import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.db import DATABASE_URL, get_db
from app.main import app

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def get_test_database_url() -> URL:
    development_url = make_url(DATABASE_URL)
    if development_url.get_backend_name() != "postgresql":
        raise RuntimeError("Registration tests require a PostgreSQL development URL.")
    if not development_url.database:
        raise RuntimeError("DATABASE_URL must name a database before tests can run.")

    test_database_name = f"{development_url.database}_test"
    if test_database_name == development_url.database:
        raise RuntimeError("The test database must be separate from the development database.")
    return development_url.set(database=test_database_name)


@pytest.fixture(scope="session")
def test_database_url() -> URL:
    return get_test_database_url()


@pytest.fixture(scope="session")
def db_engine(test_database_url: URL):
    original_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = test_database_url.render_as_string(hide_password=False)
    try:
        alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
        command.upgrade(alembic_config, "head")
    finally:
        if original_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = original_database_url

    engine = create_engine(test_database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def clean_test_database(db_engine) -> Iterator[None]:
    with db_engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE services, provider_profiles, users"))
    yield
    with db_engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE services, provider_profiles, users"))


@pytest.fixture
def client(db_engine, clean_test_database) -> Iterator[TestClient]:
    test_session_factory = sessionmaker(
        bind=db_engine,
        class_=Session,
        autoflush=False,
        autocommit=False,
    )

    def override_get_db() -> Iterator[Session]:
        with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
