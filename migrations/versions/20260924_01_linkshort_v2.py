"""Evolui o banco V1 para a estrutura multiusuário da V2."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260924_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_users() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def _create_links() -> None:
    op.create_table(
        "links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("original_url", sa.String(2048), nullable=False),
        sa.Column("short_code", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("legacy_click_count", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_links_user_id_users", ondelete="CASCADE"
        ),
    )
    op.create_index("ix_links_user_id", "links", ["user_id"])
    op.create_index("ix_links_short_code", "links", ["short_code"], unique=True)


def _upgrade_existing_links() -> None:
    with op.batch_alter_table("links") as batch:
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch.alter_column(
            "click_count",
            new_column_name="legacy_click_count",
            existing_type=sa.Integer(),
            existing_nullable=False,
        )
        batch.create_foreign_key(
            "fk_links_user_id_users", "users", ["user_id"], ["id"], ondelete="CASCADE"
        )
        batch.create_index("ix_links_user_id", ["user_id"])


def _create_clicks() -> None:
    op.create_table(
        "clicks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("link_id", sa.Integer(), sa.ForeignKey("links.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clicked_at", sa.DateTime(), nullable=False),
        sa.Column("referrer", sa.Text(), nullable=True),
        sa.Column("referrer_category", sa.String(40), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("browser", sa.String(80), nullable=False),
        sa.Column("operating_system", sa.String(80), nullable=False),
        sa.Column("device_type", sa.String(20), nullable=False),
    )
    op.create_index("ix_clicks_link_id", "clicks", ["link_id"])
    op.create_index("ix_clicks_clicked_at", "clicks", ["clicked_at"])
    op.create_index("ix_clicks_link_clicked_at", "clicks", ["link_id", "clicked_at"])


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "users" not in tables:
        _create_users()
    if "links" in tables:
        columns = {column["name"] for column in inspector.get_columns("links")}
        if "user_id" not in columns:
            _upgrade_existing_links()
    else:
        _create_links()
    if "clicks" not in tables:
        _create_clicks()


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade destrutivo não suportado; restaure um backup do banco V1."
    )
