"""Resultados prontos para templates de analytics."""

from dataclasses import dataclass

from app.database.models import Link


@dataclass(frozen=True)
class DashboardStats:
    total_links: int
    total_clicks: int
    last_7_days: int
    top_link: str


@dataclass(frozen=True)
class ChartSeries:
    labels: list[str]
    values: list[int]


@dataclass(frozen=True)
class DistributionItem:
    label: str
    count: int
    percent: int


@dataclass(frozen=True)
class DashboardAnalytics:
    stats: DashboardStats
    clicks: ChartSeries
    devices: list[DistributionItem]
    browsers: list[DistributionItem]
    referrers: list[DistributionItem]


@dataclass(frozen=True)
class LinkAnalytics:
    link: Link
    total_clicks: int
    last_7_days: int
    clicks: ChartSeries
    devices: list[DistributionItem]
    browsers: list[DistributionItem]
    referrers: list[DistributionItem]
