"""Reviewed PostgreSQL migration runner for CLINIQ-FLOW.

Run explicitly during a deployment; the API never runs migrations at startup.
Each migration is checksummed and executed under a PostgreSQL advisory lock so
two deployment processes cannot create a partially applied schema.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy import text

from database.config import engine


MIGRATIONS_DIR = Path(__file__).with_name("migrations")
LOCK_KEY = 7_394_221_081


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_migrations() -> None:
    if engine is None:
        raise RuntimeError("DATABASE_URL must be configured before running migrations.")

    files = sorted(path for path in MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"))
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": LOCK_KEY})
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    checksum CHAR(64) NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )
        applied = {
            row["version"]: row["checksum"]
            for row in connection.execute(
                text("SELECT version, checksum FROM schema_migrations")
            ).mappings()
        }

        for path in files:
            version = path.name.split("_", 1)[0]
            checksum = _checksum(path)
            if version in applied:
                if applied[version] != checksum:
                    raise RuntimeError(
                        f"Migration {path.name} was changed after being applied. "
                        "Create a new migration instead."
                    )
                continue
            connection.exec_driver_sql(path.read_text(encoding="utf-8"))
            connection.execute(
                text("INSERT INTO schema_migrations (version, checksum) VALUES (:v, :c)"),
                {"v": version, "c": checksum},
            )
            print(f"Applied {path.name}")


if __name__ == "__main__":
    apply_migrations()
