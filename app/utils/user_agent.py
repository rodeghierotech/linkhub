"""Normalização de User-Agent e origem de tráfego."""

from dataclasses import dataclass
from urllib.parse import urlparse

from user_agents import parse


@dataclass(frozen=True)
class AccessMetadata:
    user_agent: str | None
    browser: str
    operating_system: str
    device_type: str
    referrer: str | None
    referrer_category: str


def _device_type(user_agent) -> str:
    if user_agent.is_tablet:
        return "Tablet"
    if user_agent.is_mobile:
        return "Mobile"
    if user_agent.is_pc:
        return "Desktop"
    return "Other"


def categorize_referrer(referrer: str | None) -> str:
    if not referrer:
        return "Direct"
    try:
        hostname = (urlparse(referrer).hostname or "").lower()
    except ValueError:
        return "Outros"
    if hostname in {"google.com", "google.com.br"} or hostname.endswith(
        (".google.com", ".google.com.br")
    ):
        return "Google"
    if hostname == "instagram.com" or hostname.endswith(".instagram.com"):
        return "Instagram"
    if hostname in {"whatsapp.com", "wa.me"} or hostname.endswith(".whatsapp.com"):
        return "WhatsApp"
    return "Outros"


def parse_access_metadata(user_agent_value: str | None, referrer: str | None) -> AccessMetadata:
    parsed = parse(user_agent_value or "")
    return AccessMetadata(
        user_agent=user_agent_value or None,
        browser=parsed.browser.family or "Other",
        operating_system=parsed.os.family or "Other",
        device_type=_device_type(parsed),
        referrer=referrer or None,
        referrer_category=categorize_referrer(referrer),
    )
