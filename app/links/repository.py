"""Persistência de links e cliques."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Click, Link
from app.links.schemas import ClickInput


class LinkRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_short_code(self, short_code: str) -> Link | None:
        return self.db.scalar(select(Link).where(Link.short_code == short_code))

    def exists_short_code(self, short_code: str) -> bool:
        return self.db.scalar(
            select(Link.id).where(Link.short_code == short_code).limit(1)
        ) is not None

    def get_owned(self, link_id: int, user_id: int) -> Link | None:
        return self.db.scalar(
            select(Link).where(Link.id == link_id, Link.user_id == user_id)
        )

    def list_owned(self, user_id: int, *, limit: int | None = None) -> list[Link]:
        stmt = select(Link).where(Link.user_id == user_id).order_by(Link.created_at.desc())
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt))

    def create(self, *, user_id: int, original_url: str, short_code: str) -> Link:
        link = Link(user_id=user_id, original_url=original_url, short_code=short_code)
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def toggle(self, link: Link) -> Link:
        link.is_active = not link.is_active
        self.db.commit()
        self.db.refresh(link)
        return link

    def delete(self, link: Link) -> None:
        self.db.delete(link)
        self.db.commit()

    def create_click(self, link: Link, data: ClickInput) -> Click:
        click = Click(link_id=link.id, **data.__dict__)
        self.db.add(click)
        self.db.commit()
        return click

    def count_owned(self, user_id: int) -> int:
        return self.db.scalar(
            select(func.count()).select_from(Link).where(Link.user_id == user_id)
        ) or 0

    def count_clicks_owned(self, user_id: int) -> int:
        detailed = self.db.scalar(
            select(func.count())
            .select_from(Click)
            .join(Link)
            .where(Link.user_id == user_id)
        ) or 0
        legacy = self.db.scalar(
            select(func.coalesce(func.sum(Link.legacy_click_count), 0)).where(
                Link.user_id == user_id
            )
        ) or 0
        return detailed + legacy
