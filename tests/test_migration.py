import sqlite3

import pytest
from alembic import command
from alembic.config import Config


def test_v1_database_is_upgraded_without_losing_link_or_click_total(tmp_path):
    database_path = tmp_path / "v1.db"
    connection = sqlite3.connect(database_path)
    connection.executescript(
        """
        CREATE TABLE links (
            id INTEGER NOT NULL PRIMARY KEY,
            original_url VARCHAR(2048) NOT NULL,
            short_code VARCHAR(16) NOT NULL UNIQUE,
            created_at DATETIME NOT NULL,
            click_count INTEGER NOT NULL
        );
        INSERT INTO links
            (id, original_url, short_code, created_at, click_count)
        VALUES
            (1, 'https://example.com/legacy', 'legacy', '2026-09-20 12:00:00', 7);
        """
    )
    connection.commit()
    connection.close()

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")
    command.upgrade(config, "head")

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    link = connection.execute("SELECT * FROM links WHERE id = 1").fetchone()
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    connection.close()

    assert link["original_url"] == "https://example.com/legacy"
    assert link["short_code"] == "legacy"
    assert link["legacy_click_count"] == 7
    assert link["user_id"] is None
    assert link["is_active"] == 1
    assert {"users", "links", "clicks", "alembic_version"} <= tables


def test_alembic_cli_uses_database_url_from_environment(tmp_path, monkeypatch):
    database_path = tmp_path / "configured.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path.as_posix()}")

    command.upgrade(Config("alembic.ini"), "head")

    connection = sqlite3.connect(database_path)
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    connection.close()
    assert {"users", "links", "clicks", "alembic_version"} <= tables


def test_unsupported_downgrade_fails_before_deleting_clicks(tmp_path):
    database_path = tmp_path / "fresh.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")
    command.upgrade(config, "head")
    connection = sqlite3.connect(database_path)
    connection.execute(
        "INSERT INTO users (id, name, email, password_hash, created_at) VALUES (1, 'A', 'a@example.com', 'hash', '2026-09-24')"
    )
    connection.execute(
        "INSERT INTO links (id, user_id, original_url, short_code, created_at, is_active, legacy_click_count) VALUES (1, 1, 'https://example.com', 'example', '2026-09-24', 1, 0)"
    )
    connection.execute(
        "INSERT INTO clicks (id, link_id, clicked_at, referrer_category, browser, operating_system, device_type) VALUES (1, 1, '2026-09-24', 'Direct', 'Chrome', 'Windows', 'Desktop')"
    )
    connection.commit()
    connection.close()

    with pytest.raises(NotImplementedError, match="backup"):
        command.downgrade(config, "base")

    connection = sqlite3.connect(database_path)
    assert connection.execute("SELECT count(*) FROM clicks").fetchone()[0] == 1
    connection.close()
