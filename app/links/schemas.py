"""Schemas Pydantic para validação e serialização."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class LinkCreate(BaseModel):
    original_url: HttpUrl


class LinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_url: str
    short_code: str
    created_at: datetime
    click_count: int


class DashboardStats(BaseModel):
    total_links: int
    total_clicks: int
