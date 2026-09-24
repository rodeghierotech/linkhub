import pytest
from sqlalchemy import func, select

from app.database.models import Click, Link
from tests.conftest import csrf_token


def create_link(client, *, url="https://example.com/page", alias=""):
    token = csrf_token(client, "/links")
    return client.post(
        "/links",
        data={
            "original_url": url,
            "custom_alias": alias,
            "csrf_token": token,
        },
    )


def logout(client):
    token = csrf_token(client, "/dashboard")
    return client.post("/logout", data={"csrf_token": token})


def test_creates_owned_links_with_automatic_and_custom_alias(
    client, session_factory, register_user
):
    register_user()

    automatic = create_link(client, url="https://example.com/automatic")
    custom = create_link(client, url="https://example.com/portfolio", alias="Portfolio_2026")

    assert automatic.status_code == 303
    assert custom.status_code == 303
    with session_factory() as db:
        links = list(db.scalars(select(Link).order_by(Link.id)))
        assert len(links) == 2
        assert len(links[0].short_code) == 6
        assert links[1].short_code == "portfolio_2026"
        assert links[0].user_id == links[1].user_id


def test_duplicate_alias_is_rejected_without_creating_second_link(
    client, session_factory, register_user
):
    register_user()
    assert create_link(client, alias="portfolio").status_code == 303

    duplicate = create_link(client, url="https://other.example.com", alias="Portfolio")

    assert duplicate.status_code == 400
    assert "já está em uso" in duplicate.text
    with session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Link)) == 1


@pytest.mark.parametrize("alias", ["login", "admin", "ab", "inválido!", "has space"])
def test_rejects_reserved_or_unsafe_aliases(client, session_factory, register_user, alias):
    register_user()

    response = create_link(client, alias=alias)

    assert response.status_code == 400
    with session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Link)) == 0


def test_redirect_records_click_metadata_without_ip(
    client, session_factory, register_user
):
    register_user()
    create_link(client, alias="campaign")

    response = client.get(
        "/r/campaign",
        headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36",
            "referer": "https://www.google.com/search?q=linkshort",
        },
    )

    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/page"
    with session_factory() as db:
        click = db.scalar(select(Click))
        assert click is not None
        assert click.browser == "Chrome"
        assert click.operating_system == "Windows"
        assert click.device_type == "Desktop"
        assert click.referrer_category == "Google"
        assert "ip" not in Click.__table__.columns


def test_malformed_referrer_does_not_prevent_redirect(
    client, session_factory, register_user
):
    register_user()
    create_link(client, alias="safe-redirect")

    response = client.get("/r/safe-redirect", headers={"referer": "http://["})

    assert response.status_code == 302
    with session_factory() as db:
        click = db.scalar(select(Click))
        assert click.referrer_category == "Outros"


def test_lookalike_referrer_domain_is_not_classified_as_google(
    client, session_factory, register_user
):
    register_user()
    create_link(client, alias="lookalike")

    client.get("/r/lookalike", headers={"referer": "https://notgoogle.com/page"})

    with session_factory() as db:
        click = db.scalar(select(Click))
        assert click.referrer_category == "Outros"


def test_inactive_link_returns_gone_and_does_not_record_click(
    client, session_factory, register_user
):
    register_user()
    create_link(client, alias="paused")
    with session_factory() as db:
        link_id = db.scalar(select(Link.id).where(Link.short_code == "paused"))

    token = csrf_token(client, "/links")
    toggle = client.post(
        f"/links/{link_id}/toggle", data={"csrf_token": token}
    )
    response = client.get("/r/paused")

    assert toggle.status_code == 303
    assert response.status_code == 410
    assert "inativo" in response.text.lower()
    with session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Click)) == 0


def test_missing_link_returns_404(client):
    response = client.get("/r/does-not-exist")

    assert response.status_code == 404


def test_other_user_cannot_view_toggle_or_delete_link(
    client, session_factory, register_user
):
    register_user(email="owner@example.com")
    create_link(client, alias="private-link")
    with session_factory() as db:
        link_id = db.scalar(select(Link.id).where(Link.short_code == "private-link"))
    logout(client)
    register_user(email="intruder@example.com")
    token = csrf_token(client, "/links")

    detail = client.get(f"/links/{link_id}")
    toggle = client.post(f"/links/{link_id}/toggle", data={"csrf_token": token})
    delete = client.post(f"/links/{link_id}/delete", data={"csrf_token": token})

    assert detail.status_code == 404
    assert toggle.status_code == 404
    assert delete.status_code == 404
    with session_factory() as db:
        link = db.get(Link, link_id)
        assert link is not None
        assert link.is_active is True
