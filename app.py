"""FoodID Flask application factory and simple inventory API.

This module exposes `create_app()` which returns a configured Flask
application. The API provides CRUD operations for a simple `items` table in
SQLite. Keep the app factory lightweight so it can be used in tests and
WSGI deployments.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

from flask import Flask, jsonify, request

from db import get_conn, init_db, migrate_db, seed_sample

# Configure logging. Allow override via LOG_LEVEL env var.
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("foodid.app")


def create_app() -> Flask:
    """Create and configure the Flask application.

    This function intentionally accepts no parameters so tests can call
    `create_app()` without providing config. Configuration is read from
    environment variables where appropriate.
    """
    app = Flask(__name__)

    # Load config from environment
    app.config["DEBUG"] = bool(int(os.getenv("FLASK_DEBUG", "0")))

    # Initialize DB (safe to call multiple times). Run inside a try so that
    # the app can still be created even when DB initialization fails — the
    # health endpoint will reflect the unhealthy state.
    try:
        init_db()
        migrate_db()
        # Optional seed for local dev
        if os.getenv("SEED_DB", "0") == "1":
            seed_sample()
    except Exception:
        logger.exception("Failed to initialize database")

    def error_response(message: str, status: int = 400):
        """Return a consistent JSON error response."""

        return jsonify({"error": message}), status

    def row_to_dict(row: Any) -> Dict[str, Any]:
        """Convert a DB row to a JSON-serializable dict.

        The DB rows are expected to behave like sqlite3.Row and support
        mapping access by column name.
        """
        if not row:
            return {}

        # Convert to a plain dict to avoid IndexError when a column name is
        # unexpectedly missing (some SQLite rows may not expose mapping
        # access in all environments). Use .get() for resilience.
        d = dict(row)
        return {
            "id": d.get("id"),
            "name": d.get("name"),
            "quantity": d.get("quantity"),
            "created_at": d.get("created_at"),
            "updated_at": d.get("updated_at"),
        }

    @app.get("/")
    def home():
        """Landing page with a short usage hint."""
        return (
            "<h1>Welcome to FoodID API</h1>"
            "<p>Use /items to interact with inventory.</p>"
        ), 200

    @app.get("/health")
    def health():
        """Lightweight health check — verifies the DB is reachable."""
        try:
            with get_conn() as con:
                # Simple query to validate DB connectivity
                con.execute("SELECT 1").fetchone()
            return jsonify({"status": "ok"}), 200
        except Exception:
            logger.exception("Health check failed")
            return jsonify({"status": "unhealthy"}), 500

    def _parse_positive_int(value: Any) -> int:
        """Parse and validate a non-negative integer from input.

        Raises ValueError on invalid input.
        """
        iv = int(value)
        if iv < 0:
            raise ValueError("value must be non-negative")
        return iv

    @app.post("/items")
    def create_item():
        """Create a new inventory item.

        Expects JSON body with `name` (string) and optional `quantity` (int).
        Returns the created row.
        """
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        qty = data.get("quantity", 0)

        if not name:
            return error_response("Item name is required.", 400)

        try:
            qty = _parse_positive_int(qty)
        except (ValueError, TypeError):
            return error_response("Quantity must be a non-negative integer.", 400)

        try:
            with get_conn() as con:
                cur = con.execute(
                    "INSERT INTO items(name, quantity) VALUES(?, ?)", (name, qty)
                )
                item_id = cur.lastrowid
                row = con.execute(
                    "SELECT * FROM items WHERE id = ?", (item_id,)
                ).fetchone()
                return jsonify(row_to_dict(row)), 201
        except Exception:
            logger.exception("Failed to create item")
            return error_response("Internal server error", 500)

    @app.get("/items")
    def list_items():
        """Return a list of all items."""
        try:
            with get_conn() as con:
                rows = con.execute("SELECT * FROM items ORDER BY id").fetchall()
                return jsonify([row_to_dict(r) for r in rows]), 200
        except Exception:
            logger.exception("Failed to list items")
            return error_response("Internal server error", 500)

    @app.get("/items/<int:item_id>")
    def get_item(item_id: int):
        """Return a single item by ID."""
        try:
            with get_conn() as con:
                row = con.execute(
                    "SELECT * FROM items WHERE id = ?", (item_id,)
                ).fetchone()
                if not row:
                    return error_response("Item not found.", 404)
                return jsonify(row_to_dict(row)), 200
        except Exception:
            logger.exception("Failed to get item %s", item_id)
            return error_response("Internal server error", 500)

    @app.put("/items/<int:item_id>")
    def update_item(item_id: int):
        """Update fields for an existing item.

        Accepts partial updates (name and/or quantity).
        """
        data = request.get_json(silent=True) or {}
        name = data.get("name")
        qty = data.get("quantity")

        if name is not None:
            name = name.strip()
            if not name:
                return error_response("Item name cannot be empty.", 400)

        if qty is not None:
            try:
                qty = _parse_positive_int(qty)
            except (ValueError, TypeError):
                return error_response("Quantity must be a non-negative integer.", 400)

        try:
            with get_conn() as con:
                row = con.execute(
                    "SELECT * FROM items WHERE id = ?", (item_id,)
                ).fetchone()
                if not row:
                    return error_response("Item not found.", 404)

                updated_name = name if name is not None else row["name"]
                updated_qty = qty if qty is not None else row["quantity"]

                con.execute(
                    "UPDATE items SET name = ?, quantity = ? WHERE id = ?",
                    (updated_name, updated_qty, item_id),
                )
                updated_row = con.execute(
                    "SELECT * FROM items WHERE id = ?", (item_id,)
                ).fetchone()
                return jsonify(row_to_dict(updated_row)), 200
        except Exception:
            logger.exception("Failed to update item %s", item_id)
            return error_response("Internal server error", 500)

    @app.delete("/items/<int:item_id>")
    def delete_item(item_id: int):
        """Delete an item by ID."""
        try:
            with get_conn() as con:
                row = con.execute(
                    "SELECT * FROM items WHERE id = ?", (item_id,)
                ).fetchone()
                if not row:
                    return error_response("Item not found.", 404)

                con.execute("DELETE FROM items WHERE id = ?", (item_id,))
                return jsonify(message="Item deleted successfully.", id=item_id), 200
        except Exception:
            logger.exception("Failed to delete item %s", item_id)
            return error_response("Internal server error", 500)

    return app


if __name__ == "__main__":
    # For local development only. Use a WSGI server in production (gunicorn/uvicorn)
    app = create_app()
    app.run(
        host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=app.config["DEBUG"]
    )
