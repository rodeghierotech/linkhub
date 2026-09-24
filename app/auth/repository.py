"""Persistência de usuários."""

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.database.models import Link, User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def count(self) -> int:
        return self.db.scalar(select(func.count()).select_from(User)) or 0

    def create(self, *, name: str, email: str, password_hash: str) -> User:
        user = User(name=name, email=email, password_hash=password_hash)
        self.db.add(user)
        self.db.flush()
        return user

    def claim_legacy_links(self, user_id: int) -> None:
        self.db.execute(update(Link).where(Link.user_id.is_(None)).values(user_id=user_id))
