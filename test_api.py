"""Small integration tests for the FoodID Flask API.

These tests exercise a running Flask app factory and the database initialization
helper in `db.py`. They use pytest fixtures to create a temporary SQLite file
and to provide a test client.

Assumptions:
- `create_app()` accepts an optional config dict (we pass `{"TESTING": True}`).
- `init_db()` will create the SQLite database file pointed to by the
  `FOODID_DB` environment variable.
"""

from pathlib import Path
from typing import Dict

import pytest

from app import create_app
from db import init_db


@pytest.fixture
def test_db_path(tmp_path, monkeypatch) -> Path:
    """Create a temporary path for the SQLite DB and export it via env var.

    Returning the Path lets tests assert the file was created.
    """
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("FOODID_DB", str(db_file))
    return db_file


@pytest.fixture
def app(test_db_path):
    """Create the Flask app in TESTING mode and initialize the DB."""
    # The app factory doesn't accept a config dict in this codebase, so
    # create the app and set TESTING on the returned object.
    app = create_app()
    app.config.setdefault("TESTING", True)

    # Initialize DB schema for a clean test database inside the app context
    with app.app_context():
        init_db()

    yield app


@pytest.fixture
def client(app):
    """A test client for the Flask app."""
    return app.test_client()


def test_health(client):
    """GET /health returns a 200 and a JSON status OK."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.content_type.startswith("application/json")
    body = resp.get_json()
    assert isinstance(body, dict)
    assert body.get("status") == "ok"


def test_db_file_created(test_db_path):
    """Confirm `init_db()` created the SQLite file during app setup."""
    # Ensure the schema is initialized for this isolated check. Some tests use
    # the `app` fixture to initialize the DB; call `init_db()` here to make
    # this test independent of test ordering.
    init_db()
    assert test_db_path.exists(), "Expected the test SQLite DB file to be created"


def _create_item(client) -> Dict[str, object]:
    """Helper to create a default item and return the JSON payload."""

    resp = client.post("/items", json={"name": "Apple", "quantity": 5})
    assert resp.status_code == 201, resp.get_data(as_text=True)
    payload = resp.get_json()
    assert isinstance(payload, dict)
    assert payload["name"] == "Apple"
    assert payload["quantity"] == 5
    assert payload["id"] > 0
    return payload


def test_create_and_list_items(client):
    """POST /items creates a record and GET /items lists it."""

    created = _create_item(client)

    resp = client.get("/items")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert any(item["id"] == created["id"] for item in data)


def test_get_item_by_id(client):
    """GET /items/<id> returns the created item."""

    created = _create_item(client)

    resp = client.get(f"/items/{created['id']}")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["id"] == created["id"]
    assert payload["name"] == "Apple"


def test_update_item(client):
    """PUT /items/<id> updates mutable fields."""

    created = _create_item(client)
    resp = client.put(
        f"/items/{created['id']}",
        json={"name": "Green Apple", "quantity": 7},
    )
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["name"] == "Green Apple"
    assert payload["quantity"] == 7


def test_delete_item(client):
    """DELETE /items/<id> removes the record and subsequent GET returns 404."""

    created = _create_item(client)

    resp = client.delete(f"/items/{created['id']}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["message"] == "Item deleted successfully."

    resp = client.get(f"/items/{created['id']}")
    assert resp.status_code == 404
