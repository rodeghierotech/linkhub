"""Modelos ORM da aplicação."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    links: Mapped[list["Link"]] = relationship(back_populates="user")


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    original_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    short_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    legacy_click_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped[User | None] = relationship(back_populates="links")
    clicks: Mapped[list["Click"]] = relationship(
        back_populates="link", cascade="all, delete-orphan"
    )


class Click(Base):
    __tablename__ = "clicks"
    __table_args__ = (Index("ix_clicks_link_clicked_at", "link_id", "clicked_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    link_id: Mapped[int] = mapped_column(
        ForeignKey("links.id", ondelete="CASCADE"), index=True, nullable=False
    )
    clicked_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True, nullable=False)
    referrer: Mapped[str | None] = mapped_column(Text, nullable=True)
    referrer_category: Mapped[str] = mapped_column(String(40), default="Direct", nullable=False)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    browser: Mapped[str] = mapped_column(String(80), default="Other", nullable=False)
    operating_system: Mapped[str] = mapped_column(String(80), default="Other", nullable=False)
    device_type: Mapped[str] = mapped_column(String(20), default="Other", nullable=False)

    link: Mapped[Link] = relationship(back_populates="clicks")
