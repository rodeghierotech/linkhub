import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base, get_db
from app.main import create_app


@pytest.fixture()
def session_factory(tmp_path):
    database_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    yield factory
    engine.dispose()


@pytest.fixture()
def client(session_factory):
    app = create_app(migrate_on_start=False)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, follow_redirects=False) as test_client:
        yield test_client


def csrf_token(client: TestClient, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200
    match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
    assert match is not None
    return match.group(1)


@pytest.fixture()
def register_user(client):
    def register(
        *,
        name: str = "Henri",
        email: str = "henri@example.com",
        password: str = "Senha-forte-123",
    ):
        token = csrf_token(client, "/register")
        return client.post(
            "/register",
            data={
                "name": name,
                "email": email,
                "password": password,
                "password_confirmation": password,
                "csrf_token": token,
            },
        )

    return register
