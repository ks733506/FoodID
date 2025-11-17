"""Integration tests for the FoodID Flask API.

These tests exercise the Flask app factory and database initialization
helper in `db.py`. They use pytest fixtures to create a temporary SQLite file
and provide a test client.

Note:
- `create_app()` does not accept a config dict in this codebase; we set TESTING manually.
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
    # Redirect FOODID_DB to a temporary SQLite file for isolation
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("FOODID_DB", str(db_file))
    return db_file


@pytest.fixture
def app(test_db_path):
     # Create the Flask app and initialize a fresh DB for each test session
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        init_db()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get("status") == "ok"


def test_db_file_created(test_db_path):
    init_db()
    assert test_db_path.exists()


def _create_item(client) -> Dict[str, object]:
    # Helper that creates a valid item and returns its payload for reuse
    resp = client.post("/items", json={"name": "Apple", "quantity": 5})
    assert resp.status_code == 201
    payload = resp.get_json()
    assert payload["name"] == "Apple"
    assert payload["quantity"] == 5
    return payload


def test_create_and_list_items(client):
    created = _create_item(client)
    resp = client.get("/items")
    assert resp.status_code == 200
    data = resp.get_json()
    assert any(item["id"] == created["id"] for item in data)


def test_get_item_by_id(client):
    created = _create_item(client)
    resp = client.get(f"/items/{created['id']}")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["id"] == created["id"]


def test_update_item(client):
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
    created = _create_item(client)
    resp = client.delete(f"/items/{created['id']}")
    assert resp.status_code == 200
    resp = client.get(f"/items/{created['id']}")
    assert resp.status_code == 404

def test_create_item_missing_name(client):
    resp = client.post("/items", json={"quantity": 3})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_update_item_invalid_quantity(client):
    created = _create_item(client)
    resp = client.put(f"/items/{created['id']}", json={"quantity": -1})
    assert resp.status_code == 400


def test_delete_nonexistent_item(client):
    resp = client.delete("/items/9999")
    assert resp.status_code == 404


def test_identify_stub(client):
    resp = client.post("/identify")
    assert resp.status_code == 501
    assert "Not implemented" in resp.get_json()["error"]
