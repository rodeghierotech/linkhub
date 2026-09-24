"""Regras de negócio para links."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.database.models import Link
from app.links.repository import LinkRepository
from app.links.schemas import DashboardStats
from app.utils.short_code import generate_short_code

MAX_GENERATION_ATTEMPTS = 10


class LinkService:
    def __init__(self, db: Session) -> None:
        self.repository = LinkRepository(db)

    def _generate_unique_short_code(self) -> str:
        for _ in range(MAX_GENERATION_ATTEMPTS):
            code = generate_short_code()
            if not self.repository.exists_short_code(code):
                return code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível gerar um código curto único. Tente novamente.",
        )

    def create_link(self, original_url: str) -> Link:
        short_code = self._generate_unique_short_code()
        return self.repository.create(original_url=original_url, short_code=short_code)

    def list_links(self) -> list[Link]:
        return self.repository.get_all()

    def get_link_or_404(self, short_code: str) -> Link:
        link = self.repository.get_by_short_code(short_code)
        if link is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link não encontrado.",
            )
        return link

    def register_click(self, short_code: str) -> Link:
        link = self.get_link_or_404(short_code)
        return self.repository.increment_click(link)

    def delete_link(self, link_id: int) -> None:
        link = self.repository.get_by_id(link_id)
        if link is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link não encontrado.",
            )
        self.repository.delete(link)

    def get_dashboard_stats(self) -> DashboardStats:
        return DashboardStats(
            total_links=self.repository.count_links(),
            total_clicks=self.repository.sum_clicks(),
        )
