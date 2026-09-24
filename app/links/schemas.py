"""Estruturas de dados do domínio de links."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ClickInput:
    clicked_at: datetime
    referrer: str | None
    referrer_category: str
    user_agent: str | None
    browser: str
    operating_system: str
    device_type: str
