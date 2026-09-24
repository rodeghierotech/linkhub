"""Preparação de métricas e séries para a interface."""

from datetime import UTC, datetime, time, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.analytics.repository import AnalyticsRepository
from app.analytics.schemas import (
    ChartSeries,
    DashboardAnalytics,
    DashboardStats,
    DistributionItem,
    LinkAnalytics,
)


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.repository = AnalyticsRepository(db)

    @staticmethod
    def _window(now: datetime) -> tuple[datetime, list]:
        dates = [now.date() - timedelta(days=offset) for offset in range(6, -1, -1)]
        return datetime.combine(dates[0], time.min), dates

    def _series(self, user_id: int, now: datetime, link_id: int | None = None) -> ChartSeries:
        since, dates = self._window(now)
        values = self.repository.timeline(user_id, since, link_id)
        return ChartSeries(
            labels=[day.strftime("%d/%m") for day in dates],
            values=[values.get(day.isoformat(), 0) for day in dates],
        )

    @staticmethod
    def _distribution(rows: list[tuple[str, int]]) -> list[DistributionItem]:
        total = sum(count for _, count in rows)
        return [
            DistributionItem(
                label=label,
                count=count,
                percent=round((count / total) * 100) if total else 0,
            )
            for label, count in rows
        ]

    def dashboard(self, user_id: int, *, now: datetime | None = None) -> DashboardAnalytics:
        now = now or datetime.now(UTC).replace(tzinfo=None)
        since, _ = self._window(now)
        top = self.repository.top_link(user_id)
        return DashboardAnalytics(
            stats=DashboardStats(
                total_links=self.repository.count_links(user_id),
                total_clicks=self.repository.total_clicks(user_id),
                last_7_days=self.repository.clicks_since(user_id, since),
                top_link=f"/{top.short_code}" if top else "—",
            ),
            clicks=self._series(user_id, now),
            devices=self._distribution(self.repository.distribution("device_type", user_id)),
            browsers=self._distribution(self.repository.distribution("browser", user_id)),
            referrers=self._distribution(
                self.repository.distribution("referrer_category", user_id)
            ),
        )

    def link_detail(
        self, user_id: int, link_id: int, *, now: datetime | None = None
    ) -> LinkAnalytics:
        link = self.repository.get_owned_link(user_id, link_id)
        if link is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link não encontrado.")
        now = now or datetime.now(UTC).replace(tzinfo=None)
        since, _ = self._window(now)
        return LinkAnalytics(
            link=link,
            total_clicks=self.repository.total_clicks(user_id, link_id),
            last_7_days=self.repository.clicks_since(user_id, since, link_id),
            clicks=self._series(user_id, now, link_id),
            devices=self._distribution(
                self.repository.distribution("device_type", user_id, link_id)
            ),
            browsers=self._distribution(
                self.repository.distribution("browser", user_id, link_id)
            ),
            referrers=self._distribution(
                self.repository.distribution("referrer_category", user_id, link_id)
            ),
        )
