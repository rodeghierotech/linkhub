"""Regras de criação, autorização e acesso de links."""

import re
from datetime import UTC, datetime

from fastapi import HTTPException, status
from pydantic import HttpUrl, TypeAdapter, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models import Link
from app.links.repository import LinkRepository
from app.links.schemas import ClickInput
from app.utils.short_code import generate_short_code
from app.utils.user_agent import parse_access_metadata

MAX_GENERATION_ATTEMPTS = 10
ALIAS_PATTERN = re.compile(r"^[a-z0-9_-]{3,32}$")
RESERVED_ALIASES = {
    "admin", "api", "dashboard", "links", "login", "logout", "register", "static"
}
url_adapter: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)


class LinkInputError(ValueError):
    pass


class InactiveLinkError(ValueError):
    pass


class LinkService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = LinkRepository(db)

    def _generate_unique_short_code(self) -> str:
        for _ in range(MAX_GENERATION_ATTEMPTS):
            code = generate_short_code()
            if not self.repository.exists_short_code(code):
                return code
        raise HTTPException(status_code=500, detail="Não foi possível gerar um código único.")

    def _prepare_alias(self, custom_alias: str) -> str:
        alias = custom_alias.strip().lower()
        if alias in RESERVED_ALIASES:
            raise LinkInputError("Este alias é reservado.")
        if not ALIAS_PATTERN.fullmatch(alias):
            raise LinkInputError(
                "O alias deve ter de 3 a 32 caracteres: letras minúsculas, números, - ou _."
            )
        return alias

    def create_link(self, *, user_id: int, original_url: str, custom_alias: str = "") -> Link:
        try:
            validated_url = str(url_adapter.validate_python(original_url.strip()))
        except ValidationError as exc:
            raise LinkInputError("Informe uma URL completa e válida.") from exc
        short_code = self._prepare_alias(custom_alias) if custom_alias.strip() else self._generate_unique_short_code()
        if self.repository.exists_short_code(short_code):
            raise LinkInputError("Este alias já está em uso.")
        try:
            return self.repository.create(
                user_id=user_id,
                original_url=validated_url,
                short_code=short_code,
            )
        except IntegrityError as exc:
            self.db.rollback()
            raise LinkInputError("Este alias já está em uso.") from exc

    def list_links(self, user_id: int, *, limit: int | None = None) -> list[Link]:
        return self.repository.list_owned(user_id, limit=limit)

    def get_owned_or_404(self, link_id: int, user_id: int) -> Link:
        link = self.repository.get_owned(link_id, user_id)
        if link is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link não encontrado.")
        return link

    def toggle(self, link_id: int, user_id: int) -> Link:
        return self.repository.toggle(self.get_owned_or_404(link_id, user_id))

    def delete(self, link_id: int, user_id: int) -> None:
        self.repository.delete(self.get_owned_or_404(link_id, user_id))

    def register_click(
        self, short_code: str, *, user_agent: str | None, referrer: str | None
    ) -> Link:
        link = self.repository.get_by_short_code(short_code)
        if link is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link não encontrado.")
        if not link.is_active:
            raise InactiveLinkError("Este link está inativo.")
        metadata = parse_access_metadata(user_agent, referrer)
        self.repository.create_click(
            link,
            ClickInput(
                clicked_at=datetime.now(UTC).replace(tzinfo=None),
                referrer=metadata.referrer,
                referrer_category=metadata.referrer_category,
                user_agent=metadata.user_agent,
                browser=metadata.browser,
                operating_system=metadata.operating_system,
                device_type=metadata.device_type,
            ),
        )
        return link
