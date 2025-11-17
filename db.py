"""Database helpers for FoodID.

This module centralizes SQLite access logic. It resolves the `FOODID_DB`
path (environment variable) into a canonical absolute path located by
default next to this module, ensures the parent directory exists, and
provides helpers to obtain a connection, initialize the schema, migrate
legacy databases, and seed sample data for development.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path
from typing import Optional, Set

# Ensure logging is configured even if not set elsewhere
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("foodid.db")

_DEFAULT_DB_NAME = "foodid.db"


def _resolve_db_path(path: str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = Path(__file__).parent.joinpath(path)
    p = p.resolve()
    if not p.parent.exists():
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            logger.exception("Failed to create DB directory: %s", p.parent)
            raise
    return str(p)


def _get_db_path() -> str:
    env_path = os.getenv("FOODID_DB", _DEFAULT_DB_NAME)
    return _resolve_db_path(env_path)


def get_conn(check_same_thread: bool = False) -> sqlite3.Connection:
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
        logger.exception("Failed to open SQLite database at %s", db_path)
        raise


def init_db(schema_path: Optional[str] = None) -> None:
    schema_path = schema_path or str(Path(__file__).parent.joinpath("schema.sql"))
    if not Path(schema_path).exists():
        logger.error("Schema file not found: %s", schema_path)
        raise FileNotFoundError(schema_path)

    try:
        with get_conn() as con, open(schema_path, "r", encoding="utf-8") as f:
            con.executescript(f.read())
    except sqlite3.Error:
        logger.exception("Failed to initialize DB using schema %s", schema_path)
        raise


def migrate_db() -> None:
    try:
        with get_conn() as con:
            info = con.execute("PRAGMA table_info('items')").fetchall()
            if not info:
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

                try:
                    max_id = con.execute("SELECT MAX(id) FROM items").fetchone()[0]
                    if max_id is not None:
                        con.execute(
                            "UPDATE sqlite_sequence SET seq=? WHERE name='items'",
                            (max_id,),
                        )
                        if con.total_changes == 0:
                            con.execute(
                                "INSERT INTO sqlite_sequence(name, seq) VALUES('items', ?)",
                                (max_id,),
                            )
                except sqlite3.Error:
                    logger.debug("sqlite_sequence update skipped", exc_info=True)

            con.execute("CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)")
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
    """Insert sample rows for development if the table is empty.

    Silent on failure. Logs errors but does not raise.
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
