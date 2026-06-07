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

# Default database filename if FOODID_DB environment variable is not set
_DEFAULT_DB_NAME = "foodid.db"


def _resolve_db_path(path: str) -> str:
    """Resolve database path to an absolute path and ensure parent directory exists.

    Args:
        path: Relative or absolute path to database file

    Returns:
        Absolute path to database file as a string

    Raises:
        Exception: If unable to create parent directory
    """
    p = Path(path)
    # If relative path, resolve relative to this module's directory
    if not p.is_absolute():
        p = Path(__file__).parent.joinpath(path)
    # Resolve to canonical path (handles symlinks and relative components)
    p = p.resolve()
    # Create parent directory if it doesn't exist
    if not p.parent.exists():
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            logger.exception("Failed to create DB directory: %s", p.parent)
            raise
    return str(p)


def _get_db_path() -> str:
    """Get the database path from environment or use default.

    Returns:
        Absolute path to database file
    """
    env_path = os.getenv("FOODID_DB", _DEFAULT_DB_NAME)
    return _resolve_db_path(env_path)


def get_conn(check_same_thread: bool = False) -> sqlite3.Connection:
    """Establish and return a SQLite database connection.

    Configures the connection to:
    - Parse SQL declaration types and column names
    - Return rows as sqlite3.Row objects (dict-like access)
    - Allow cross-thread usage when check_same_thread=False

    Args:
        check_same_thread: If False, allows connection use across threads

    Returns:
        Configured sqlite3.Connection object

    Raises:
        sqlite3.Error: If unable to connect to database
    """
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            check_same_thread=check_same_thread,
        )
        # Enable row factory to access columns by name (like dict)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error:
        logger.exception("Failed to open SQLite database at %s", db_path)
        raise


def init_db(schema_path: Optional[str] = None) -> None:
    """Initialize database schema from SQL file.

    Creates all tables and indexes defined in schema.sql.

    Args:
        schema_path: Path to schema.sql file. Defaults to schema.sql
                     in same directory as this module.

    Raises:
        FileNotFoundError: If schema file does not exist
        sqlite3.Error: If unable to execute schema
    """
    schema_path = schema_path or str(Path(__file__).parent.joinpath("schema.sql"))
    if not Path(schema_path).exists():
        logger.error("Schema file not found: %s", schema_path)
        raise FileNotFoundError(schema_path)

    try:
        # Execute all SQL statements from schema file
        with get_conn() as con, open(schema_path, "r", encoding="utf-8") as f:
            con.executescript(f.read())
    except sqlite3.Error:
        logger.exception("Failed to initialize DB using schema %s", schema_path)
        raise


def migrate_db() -> None:
    """Migrate legacy database schema to current version.

    - Adds timestamp columns (created_at, updated_at) if missing
    - Creates index on items.name for query performance
    - Sets up trigger to auto-update updated_at on row changes

    Raises:
        sqlite3.Error: If migration fails
    """
    try:
        with get_conn() as con:
            # Check if items table exists and get its column info
            info = con.execute("PRAGMA table_info('items')").fetchall()
            if not info:
                # Table doesn't exist, no migration needed
                return

            # Extract column names from table info
            column_names: Set[str] = {row["name"] for row in info}

            # Check if timestamp columns are missing
            if not {"created_at", "updated_at"}.issubset(column_names):
                logger.info("Migrating legacy items table to include timestamp columns")
                # Rename old table, create new table with schema, copy data back
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

                # Restore the auto-increment sequence for the id column
                try:
                    max_id = con.execute("SELECT MAX(id) FROM items").fetchone()[0]
                    if max_id is not None:
                        # Update existing sequence if available
                        con.execute(
                            "UPDATE sqlite_sequence SET seq=? WHERE name='items'",
                            (max_id,),
                        )
                        # If no sequence exists, create one
                        if con.total_changes == 0:
                            con.execute(
                                "INSERT INTO sqlite_sequence(name, seq) VALUES('items', ?)",
                                (max_id,),
                            )
                except sqlite3.Error:
                    # Sequence updates are non-critical; log and continue
                    logger.debug("sqlite_sequence update skipped", exc_info=True)

            # Create index on name column for faster searches
            con.execute("CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)")
            # Create trigger to auto-update updated_at timestamp on row modifications
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
    This is useful for populating sample data in development/test environments.
    """
    try:
        with get_conn() as con:
            # Check if items table has any rows
            cur = con.execute("SELECT COUNT(1) as c FROM items")
            if cur.fetchone()["c"] == 0:
                # Insert sample food items with quantities
                con.executemany(
                    "INSERT INTO items(name, quantity) VALUES(?, ?)",
                    [("Rice", 2), ("Pasta", 5), ("Tomatoes", 12)],
                )
    except Exception:
        # Log error but don't raise - seeding is optional
        logger.exception("Failed to seed sample data into DB at %s", _get_db_path())
