"""Agregações SQL para analytics."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Click, Link


class AnalyticsRepository:
    DISTRIBUTION_FIELDS = {
        "device_type": Click.device_type,
        "browser": Click.browser,
        "referrer_category": Click.referrer_category,
    }

    def __init__(self, db: Session) -> None:
        self.db = db

    def count_links(self, user_id: int) -> int:
        return self.db.scalar(
            select(func.count()).select_from(Link).where(Link.user_id == user_id)
        ) or 0

    def total_clicks(self, user_id: int, link_id: int | None = None) -> int:
        conditions = [Link.user_id == user_id]
        if link_id is not None:
            conditions.append(Link.id == link_id)
        detailed = self.db.scalar(
            select(func.count()).select_from(Click).join(Link).where(*conditions)
        ) or 0
        legacy = self.db.scalar(
            select(func.coalesce(func.sum(Link.legacy_click_count), 0)).where(*conditions)
        ) or 0
        return detailed + legacy

    def clicks_since(self, user_id: int, since: datetime, link_id: int | None = None) -> int:
        conditions = [Link.user_id == user_id, Click.clicked_at >= since]
        if link_id is not None:
            conditions.append(Link.id == link_id)
        return self.db.scalar(
            select(func.count()).select_from(Click).join(Link).where(*conditions)
        ) or 0

    def top_link(self, user_id: int) -> Link | None:
        total = (Link.legacy_click_count + func.count(Click.id)).label("total")
        return self.db.scalar(
            select(Link)
            .outerjoin(Click)
            .where(Link.user_id == user_id)
            .group_by(Link.id)
            .order_by(total.desc(), Link.created_at.desc())
            .limit(1)
        )

    def timeline(
        self, user_id: int, since: datetime, link_id: int | None = None
    ) -> dict[str, int]:
        day = func.date(Click.clicked_at).label("day")
        conditions = [Link.user_id == user_id, Click.clicked_at >= since]
        if link_id is not None:
            conditions.append(Link.id == link_id)
        rows = self.db.execute(
            select(day, func.count(Click.id))
            .join(Link)
            .where(*conditions)
            .group_by(day)
            .order_by(day)
        )
        return {str(date): count for date, count in rows}

    def distribution(
        self, field: str, user_id: int, link_id: int | None = None
    ) -> list[tuple[str, int]]:
        column = self.DISTRIBUTION_FIELDS[field]
        conditions = [Link.user_id == user_id]
        if link_id is not None:
            conditions.append(Link.id == link_id)
        count = func.count(Click.id).label("count")
        rows = self.db.execute(
            select(column, count)
            .join(Link)
            .where(*conditions)
            .group_by(column)
            .order_by(count.desc(), column.asc())
        )
        return [(label or "Other", value) for label, value in rows]

    def get_owned_link(self, user_id: int, link_id: int) -> Link | None:
        return self.db.scalar(
            select(Link).where(Link.id == link_id, Link.user_id == user_id)
        )
