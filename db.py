"""Database helpers for FoodID.

This module centralizes SQLite access logic. It resolves the `FOODID_DB`
path (environment variable) into a canonical absolute path located by
default next to this module, ensures the parent directory exists, and
provides helpers to obtain a connection, initialize the schema, and seed
sample data for development.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path
from typing import Optional, Set

logger = logging.getLogger("foodid.db")

# Default DB filename (used when FOODID_DB env var is not set)
_DEFAULT_DB_NAME = "foodid.db"


def _resolve_db_path(path: str) -> str:
    """Resolve a DB path to an absolute path located next to this module by
    default. Also ensure the parent directory exists so SQLite can create the
    file when first connecting.
    """
    p = Path(path)
    if not p.is_absolute():
        p = Path(__file__).parent.joinpath(path)
    p = p.resolve()
    # Ensure directory exists
    if not p.parent.exists():
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            logger.exception("Failed to create DB directory: %s", p.parent)
            raise
    return str(p)


def _get_db_path() -> str:
    """Return the resolved DB path based on the current environment.

    This is computed at call-time (not import-time) so tests can monkeypatch
    the `FOODID_DB` environment variable and have the change picked up.
    """
    env_path = os.getenv("FOODID_DB", _DEFAULT_DB_NAME)
    return _resolve_db_path(env_path)


def get_conn(check_same_thread: bool = False) -> sqlite3.Connection:
    """Return a sqlite3.Connection configured for named-column access.

    Parameters
    - check_same_thread: passed to sqlite3.connect. The default here is
      False to allow access from other threads if the app requires it
      (e.g., UI threads). Change with care.
    """
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            check_same_thread=check_same_thread,
        )
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error:
        logger.exception("Unable to open SQLite database at %s", db_path)
        raise


def init_db(schema_path: Optional[str] = None) -> None:
    """Initialize the database schema.

    By default the schema file `schema.sql` located next to this module is
    used. Raises FileNotFoundError if the schema file cannot be found, or
    sqlite3.Error when the schema cannot be applied.
    """
    schema_path = schema_path or str(Path(__file__).parent.joinpath("schema.sql"))
    if not Path(schema_path).exists():
        logger.error("Schema file not found: %s", schema_path)
        raise FileNotFoundError(schema_path)

    try:
        # Use get_conn() which resolves the DB path at call time
        with get_conn() as con, open(schema_path, "r", encoding="utf-8") as f:
            con.executescript(f.read())
    except sqlite3.Error:
        logger.exception("Failed to initialize DB using schema %s", schema_path)
        raise


def migrate_db() -> None:
    """Apply lightweight, idempotent migrations for existing installations.

    Older database files may be missing columns (e.g., created_at/updated_at)
    that newer application versions rely on. This helper inspects the current
    schema and applies the minimal ALTER statements required to bring the
    database up to date without dropping data.
    """

    try:
        with get_conn() as con:
            info = con.execute("PRAGMA table_info('items')").fetchall()
            if not info:
                # No items table yet; nothing to migrate.
                return

            column_names: Set[str] = {row["name"] for row in info}

            if not {"created_at", "updated_at"}.issubset(column_names):
                logger.info("Migrating legacy items table to include timestamp columns")
                con.executescript(
                    """
                    PRAGMA foreign_keys=off;
                    BEGIN TRANSACTION;
                    ALTER TABLE items RENAME TO items_legacy;
                    CREATE TABLE items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        quantity INTEGER NOT NULL CHECK (quantity >= 0),
                        created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
                        updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
                    );
                    INSERT INTO items (id, name, quantity, created_at, updated_at)
                    SELECT
                        id,
                        name,
                        quantity,
                        CURRENT_TIMESTAMP,
                        CURRENT_TIMESTAMP
                    FROM items_legacy;
                    DROP TABLE items_legacy;
                    COMMIT;
                    PRAGMA foreign_keys=on;
                    """
                )

                # Ensure AUTOINCREMENT continues from the highest existing id.
                try:
                    max_id = con.execute("SELECT MAX(id) FROM items").fetchone()[0]
                    if max_id is not None:
                        con.execute(
                            "UPDATE sqlite_sequence SET seq=? WHERE name='items'",
                            (max_id,),
                        )
                        if con.total_changes == 0:
                            con.execute(
                                (
                                    "INSERT INTO sqlite_sequence(name, seq) "
                                    "VALUES('items', ?)"
                                ),
                                (max_id,),
                            )
                except sqlite3.Error:
                    logger.debug(
                        "sqlite_sequence update skipped", exc_info=True
                    )

            # Ensure supporting index and trigger exist even on older databases.
            con.execute(
                "CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)"
            )
            con.executescript(
                """
                CREATE TRIGGER IF NOT EXISTS items_updated_at
                AFTER UPDATE ON items
                FOR EACH ROW
                WHEN NEW.updated_at = OLD.updated_at
                BEGIN
                    UPDATE items
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = OLD.id;
                END;
                """
            )
    except sqlite3.Error:
        logger.exception("Database migration failed")
        raise


def seed_sample() -> None:
    """Insert a few sample rows for development when the table is empty.

    This is a best-effort helper used in development. It will not raise on
    failure but will log the error instead.
    """
    try:
        with get_conn() as con:
            cur = con.execute("SELECT COUNT(1) as c FROM items")
            if cur.fetchone()["c"] == 0:
                con.executemany(
                    "INSERT INTO items(name, quantity) VALUES(?, ?)",
                    [("Rice", 2), ("Pasta", 5), ("Tomatoes", 12)],
                )
    except Exception:
        logger.exception("Failed to seed sample data into DB at %s", _get_db_path())
