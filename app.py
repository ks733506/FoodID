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
level = getattr(logging, os.getenv("LOG_LEVEL", "INFO"), logging.INFO)
logging.basicConfig(level=level)
logger = logging.getLogger("foodid.app")


def create_app() -> Flask:
    """Create and configure the Flask application.
    
    This factory function:
    - Initializes the SQLite database schema
    - Runs database migrations for legacy schema compatibility
    - Seeds sample data if SEED_DB=1 is set
    - Registers API route handlers for CRUD operations
    
    Returns:
        Configured Flask application instance ready for use
    """
    app = Flask(__name__)
    app.config["DEBUG"] = bool(int(os.getenv("FLASK_DEBUG", "0")))

    # Initialize database: create schema, run migrations, optionally seed data
    try:
        init_db()
        migrate_db()
        if os.getenv("SEED_DB", "0") == "1":
            seed_sample()
    except Exception:
        logger.exception("Failed to initialize database")

    def error_response(message: str, status: int = 400):
        """Return a consistent JSON error response.
        
        Args:
            message: Human-readable error description
            status: HTTP status code (default 400)
            
        Returns:
            Tuple of (JSON response dict, status code)
        """
        return jsonify({"error": message, "status": status}), status

    def row_to_dict(row: Any) -> Dict[str, Any]:
        """Convert a DB row to a JSON-serializable dict.
        
        Extracts relevant columns from sqlite3.Row object and returns
        a clean dictionary suitable for JSON serialization in API responses.
        
        Args:
            row: sqlite3.Row object from database query
            
        Returns:
            Dictionary with keys: id, name, quantity, created_at, updated_at
        """
        if not row:
            return {}
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
        """Return API welcome message.
        
        Provides basic info about the API endpoint structure.
        
        Returns:
            JSON message with HTTP 200
        """
        return (
            jsonify(
                {
                    "message": "Welcome to FoodID API. Use /items to interact with inventory."
                }
            ),
            200,
        )

    @app.get("/health")
    def health():
        """Check database connectivity and service health.
        
        Performs a simple SELECT 1 query to verify the database
        connection is working.
        
        Returns:
            JSON status object with HTTP 200 if healthy, 500 otherwise
        """
        try:
            with get_conn() as con:
                con.execute("SELECT 1").fetchone()
            return jsonify({"status": "ok"}), 200
        except Exception:
            logger.exception("Health check failed")
            return error_response("Service unhealthy.", 500)

    def _parse_positive_int(value: Any) -> int:
        """Parse and validate a positive integer.
        
        Ensures the value can be converted to int and is non-negative.
        
        Args:
            value: Input value to parse (can be string, int, etc.)
            
        Returns:
            Validated positive integer
            
        Raises:
            ValueError: If value is negative or cannot be parsed as int
            TypeError: If value is of incompatible type
        """
        iv = int(value)
        if iv < 0:
            raise ValueError("Value must be non-negative")
        return iv

    @app.post("/items")
    def create_item():
        """Create a new inventory item.
        
        Accepts JSON payload with:
        - name (string, required): Item name
        - quantity (int, optional): Item quantity (default 0)
        
        Validates inputs and returns the created item with auto-generated ID.
        
        Returns:
            JSON item object with HTTP 201 on success
            JSON error with HTTP 400/500 on failure
        """
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        qty = data.get("quantity", 0)

        # Validate name is not empty
        if not name:
            return error_response("Item name is required.", 400)

        # Validate quantity is a non-negative integer
        try:
            qty = _parse_positive_int(qty)
        except (ValueError, TypeError):
            return error_response("Quantity must be a non-negative integer.", 400)

        try:
            with get_conn() as con:
                # Insert new item and get its auto-generated ID
                cur = con.execute(
                    "INSERT INTO items(name, quantity) VALUES(?, ?)", (name, qty)
                )
                item_id = cur.lastrowid
                # Fetch and return the newly created item
                row = con.execute(
                    "SELECT * FROM items WHERE id = ?", (item_id,)
                ).fetchone()
                return jsonify(row_to_dict(row)), 201
        except Exception:
            logger.exception("Failed to create item")
            return error_response("Internal server error.", 500)

    @app.get("/items")
    def list_items():
        """List all inventory items.
        
        Retrieves all items from the database ordered by ID.
        
        Returns:
            JSON array of item objects with HTTP 200
            JSON error with HTTP 500 on failure
        """
        try:
            with get_conn() as con:
                rows = con.execute("SELECT * FROM items ORDER BY id").fetchall()
                return jsonify([row_to_dict(r) for r in rows]), 200
        except Exception:
            logger.exception("Failed to list items")
            return error_response("Internal server error.", 500)

    @app.get("/items/<int:item_id>")
    def get_item(item_id: int):
        """Retrieve a single inventory item by ID.
        
        Args:
            item_id: Numeric item ID from URL path
            
        Returns:
            JSON item object with HTTP 200 if found
            JSON error with HTTP 404 if not found
            JSON error with HTTP 500 on database error
        """
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
            return error_response("Internal server error.", 500)

    @app.put("/items/<int:item_id>")
    def update_item(item_id: int):
        """Update an inventory item by ID.
        
        Accepts JSON payload with any combination of:
        - name (string, optional): New item name
        - quantity (int, optional): New item quantity
        
        At least one field must be provided to update.
        Non-provided fields retain their current values.
        
        Args:
            item_id: Numeric item ID from URL path
            
        Returns:
            JSON updated item object with HTTP 200 on success
            JSON error with HTTP 400/404/500 on failure
        """
        data = request.get_json(silent=True) or {}
        name = data.get("name")
        qty = data.get("quantity")

        # Validate name if provided
        if name is not None:
            name = name.strip()
            if not name:
                return error_response("Item name cannot be empty.", 400)

        # Validate quantity if provided
        if qty is not None:
            try:
                qty = _parse_positive_int(qty)
            except (ValueError, TypeError):
                return error_response("Quantity must be a non-negative integer.", 400)

        try:
            with get_conn() as con:
                # Check if item exists
                row = con.execute(
                    "SELECT * FROM items WHERE id = ?", (item_id,)
                ).fetchone()
                if not row:
                    return error_response("Item not found.", 404)

                # Use provided values or keep existing values
                updated_name = name if name is not None else row["name"]
                updated_qty = qty if qty is not None else row["quantity"]

                # Update the item
                con.execute(
                    "UPDATE items SET name = ?, quantity = ? WHERE id = ?",
                    (updated_name, updated_qty, item_id),
                )
                # Fetch and return the updated item
                updated_row = con.execute(
                    "SELECT * FROM items WHERE id = ?", (item_id,)
                ).fetchone()
                return jsonify(row_to_dict(updated_row)), 200
        except Exception:
            logger.exception("Failed to update item %s", item_id)
            return error_response("Internal server error.", 500)

    @app.delete("/items/<int:item_id>")
    def delete_item(item_id: int):
        """Delete an inventory item by ID.
        
        Permanently removes the item from the database.
        
        Args:
            item_id: Numeric item ID from URL path
            
        Returns:
            JSON confirmation with HTTP 200 on success
            JSON error with HTTP 404 if not found
            JSON error with HTTP 500 on database error
        """
        try:
            with get_conn() as con:
                # Check if item exists
                row = con.execute(
                    "SELECT * FROM items WHERE id = ?", (item_id,)
                ).fetchone()
                if not row:
                    return error_response("Item not found.", 404)

                # Delete the item
                con.execute("DELETE FROM items WHERE id = ?", (item_id,))
                return (
                    jsonify({"message": "Item deleted successfully.", "id": item_id}),
                    200,
                )
        except Exception:
            logger.exception("Failed to delete item %s", item_id)
            return error_response("Internal server error.", 500)

    @app.post("/identify")
    def identify():
        """Stub endpoint for future image classification.
        
        Currently not implemented. This endpoint will be used to
        identify food items from images in a future release.
        
        Returns:
            JSON error with HTTP 501 (Not Implemented)
        """
        return error_response("Not implemented.", 501)

    return app


if __name__ == "__main__":
    # Create app and run development server
    app = create_app()
    app.run(
        host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=app.config["DEBUG"]
    )
