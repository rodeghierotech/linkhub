"""Camada de acesso a dados para Link."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Link


class LinkRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_short_code(self, short_code: str) -> Link | None:
        stmt = select(Link).where(Link.short_code == short_code)
        return self.db.scalar(stmt)

    def exists_short_code(self, short_code: str) -> bool:
        return self.get_by_short_code(short_code) is not None

    def get_all(self) -> list[Link]:
        stmt = select(Link).order_by(Link.created_at.desc())
        return list(self.db.scalars(stmt))

    def get_by_id(self, link_id: int) -> Link | None:
        return self.db.get(Link, link_id)

    def create(self, original_url: str, short_code: str) -> Link:
        link = Link(original_url=original_url, short_code=short_code)
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def increment_click(self, link: Link) -> Link:
        link.click_count += 1
        self.db.commit()
        self.db.refresh(link)
        return link

    def delete(self, link: Link) -> None:
        self.db.delete(link)
        self.db.commit()

    def count_links(self) -> int:
        return self.db.scalar(select(func.count()).select_from(Link)) or 0

    def sum_clicks(self) -> int:
        return self.db.scalar(select(func.coalesce(func.sum(Link.click_count), 0))) or 0
