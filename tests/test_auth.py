import pytest
from sqlalchemy import func, select

from app.database.models import User
from app.auth.schemas import RegistrationData
from app.auth.service import AuthError, AuthService
from tests.conftest import csrf_token


def test_private_dashboard_redirects_guest_to_login(client):
    response = client.get("/dashboard")

    assert response.status_code == 303
    assert response.headers["location"] == "/login?next=/dashboard"


def test_registration_hashes_password_starts_session_and_claims_legacy_links(
    client, session_factory, register_user
):
    from app.database.models import Link

    with session_factory() as db:
        db.add(
            Link(
                original_url="https://example.com/legacy",
                short_code="legacy",
                legacy_click_count=4,
            )
        )
        db.commit()

    response = register_user(email="  HENRI@Example.COM ")

    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    with session_factory() as db:
        user = db.scalar(select(User))
        link = db.scalar(select(Link))
        assert user is not None
        assert user.email == "henri@example.com"
        assert user.password_hash != "Senha-forte-123"
        assert user.password_hash.startswith("$argon2")
        assert link.user_id == user.id

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert "Henri" in dashboard.text


def test_duplicate_email_is_rejected_case_insensitively(client, register_user):
    assert register_user(email="person@example.com").status_code == 303
    logout_token = csrf_token(client, "/dashboard")
    client.post("/logout", data={"csrf_token": logout_token})

    token = csrf_token(client, "/register")
    response = client.post(
        "/register",
        data={
            "name": "Outra pessoa",
            "email": "PERSON@example.com",
            "password": "Outra-senha-123",
            "password_confirmation": "Outra-senha-123",
            "csrf_token": token,
        },
    )

    assert response.status_code == 400
    assert "já está em uso" in response.text


def test_login_and_logout_control_private_session(client, register_user):
    register_user(email="login@example.com", password="Senha-forte-123")
    token = csrf_token(client, "/dashboard")
    logout = client.post("/logout", data={"csrf_token": token})
    assert logout.status_code == 303
    assert logout.headers["location"] == "/login"
    assert client.get("/dashboard").status_code == 303

    token = csrf_token(client, "/login")
    login = client.post(
        "/login",
        data={
            "email": "LOGIN@example.com",
            "password": "Senha-forte-123",
            "csrf_token": token,
        },
    )
    assert login.status_code == 303
    assert login.headers["location"] == "/dashboard"
    assert client.get("/dashboard").status_code == 200


def test_registration_rejects_invalid_csrf_token(client):
    response = client.post(
        "/register",
        data={
            "name": "Henri",
            "email": "henri@example.com",
            "password": "Senha-forte-123",
            "password_confirmation": "Senha-forte-123",
            "csrf_token": "invalid",
        },
    )

    assert response.status_code == 403


def test_registration_turns_unique_constraint_race_into_auth_error(session_factory):
    with session_factory() as db:
        db.add(User(name="Existing", email="race@example.com", password_hash="hash"))
        db.commit()
        service = AuthService(db)
        service.repository.get_by_email = lambda _: None

        with pytest.raises(AuthError, match="já está em uso"):
            service.register(
                RegistrationData(
                    "Racer", "race@example.com", "Senha-forte-123", "Senha-forte-123"
                )
            )

        assert db.scalar(select(func.count()).select_from(User)) == 1


def test_unicode_csrf_token_is_rejected_instead_of_crashing(client):
    csrf_token(client, "/login")
    response = client.post(
        "/login",
        data={"email": "a@example.com", "password": "password", "csrf_token": "inválido"},
    )

    assert response.status_code == 403
