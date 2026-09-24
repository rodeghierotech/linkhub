from datetime import datetime, timedelta

from sqlalchemy import select

from app.analytics.service import AnalyticsService
from app.database.models import Click, Link, User


def seed_analytics(session_factory):
    now = datetime(2026, 9, 24, 15, 0, 0)
    with session_factory() as db:
        owner = User(name="Owner", email="owner@example.com", password_hash="unused")
        other = User(name="Other", email="other@example.com", password_hash="unused")
        db.add_all([owner, other])
        db.flush()
        portfolio = Link(
            user_id=owner.id,
            original_url="https://example.com/portfolio",
            short_code="portfolio",
            legacy_click_count=3,
        )
        campaign = Link(
            user_id=owner.id,
            original_url="https://example.com/campaign",
            short_code="campaign",
        )
        foreign = Link(
            user_id=other.id,
            original_url="https://other.example.com",
            short_code="foreign",
        )
        db.add_all([portfolio, campaign, foreign])
        db.flush()
        db.add_all(
            [
                Click(link_id=portfolio.id, clicked_at=now, browser="Chrome", operating_system="Windows", device_type="Desktop", referrer_category="Direct"),
                Click(link_id=portfolio.id, clicked_at=now - timedelta(hours=2), browser="Chrome", operating_system="Windows", device_type="Desktop", referrer_category="Google"),
                Click(link_id=portfolio.id, clicked_at=now - timedelta(days=2), browser="Safari", operating_system="iOS", device_type="Mobile", referrer_category="Instagram"),
                Click(link_id=campaign.id, clicked_at=now - timedelta(days=8), browser="Firefox", operating_system="Android", device_type="Tablet", referrer_category="WhatsApp"),
                Click(link_id=foreign.id, clicked_at=now, browser="Edge", operating_system="Windows", device_type="Desktop", referrer_category="Outros"),
            ]
        )
        db.commit()
        return owner.id, portfolio.id, now


def test_dashboard_aggregates_only_the_owners_links(session_factory):
    owner_id, _, now = seed_analytics(session_factory)
    with session_factory() as db:
        result = AnalyticsService(db).dashboard(owner_id, now=now)

    assert result.stats.total_links == 2
    assert result.stats.total_clicks == 7
    assert result.stats.last_7_days == 3
    assert result.stats.top_link == "/portfolio"
    assert result.clicks.labels == ["18/09", "19/09", "20/09", "21/09", "22/09", "23/09", "24/09"]
    assert result.clicks.values == [0, 0, 0, 0, 1, 0, 2]
    assert [(item.label, item.count) for item in result.devices] == [
        ("Desktop", 2),
        ("Mobile", 1),
        ("Tablet", 1),
    ]
    assert result.browsers[0].label == "Chrome"
    assert result.browsers[0].percent == 50


def test_link_detail_excludes_clicks_from_other_links(session_factory):
    owner_id, link_id, now = seed_analytics(session_factory)
    with session_factory() as db:
        result = AnalyticsService(db).link_detail(owner_id, link_id, now=now)

    assert result.link.id == link_id
    assert result.total_clicks == 6
    assert result.last_7_days == 3
    assert sum(item.count for item in result.devices) == 3
    assert {item.label for item in result.referrers} == {"Direct", "Google", "Instagram"}


def test_dashboard_page_renders_chart_ready_data(client, register_user):
    register_user()

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Últimos 7 dias" in response.text
    assert "chart.umd.min.js" in response.text
