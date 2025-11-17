"""Gradio UI for FoodID.

This module provides a lightweight frontend that talks to the Flask API defined
in `app.py`. It exposes Create / Read / Update / Delete operations against the
`/items` endpoints. The UI functions are small adapters that validate inputs,
call the API and normalize the responses for Gradio widgets.

Notes:
- The API base URL can be overridden with the `FOODID_API` environment variable.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Tuple

import gradio as gr
import requests  # type: ignore[import]

# Configure simple logging for debugging UI/network issues
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("foodid.ui")

# Base API URL (can be overridden by env var)
API = os.getenv("FOODID_API", "http://127.0.0.1:5000").rstrip("/")

# Use a session to reuse HTTP connections across requests
_session = requests.Session()


def _handle_response(resp: requests.Response) -> Tuple[int, Any]:
    """Return (status_code, parsed_json_or_error).

    Always returns a tuple compatible with Gradio outputs used in this app
    (Number, JSON).
    """
    try:
        data = resp.json()
    except ValueError:
        logger.exception("Invalid JSON response from %s", resp.url)
        data = {"error": "Invalid JSON from server", "text": resp.text}
    return resp.status_code, data


def _build_url(path: str) -> str:
    """Helper to build full API URLs without duplicating slashes."""
    # Build the URL and remove any trailing slashes for consistency
    return f"{API}/{path.lstrip('/')}".rstrip("/")


def create(name: str, qty: float) -> Tuple[int, Dict[str, Any]]:
    """Create a new inventory item.

    Validates the name and coerces quantity to an int if possible.
    Returns (status_code, json).
    """
    if not name or not str(name).strip():
        return 400, {"error": "Item name is required."}

    try:
        quantity = int(qty) if qty is not None else 0
    except Exception:
        logger.exception("Invalid quantity provided: %r", qty)
        return 400, {"error": "Quantity must be a number."}

    payload = {"name": name.strip(), "quantity": quantity}
    try:
        resp = _session.post(_build_url("/items"), json=payload, timeout=5)
        return _handle_response(resp)
    except requests.RequestException as exc:
        logger.exception("Error creating item: %s", exc)
        return 500, {"error": str(exc)}


def read_all() -> List[List[Any]]:
    """Return all items as a list-of-rows suitable for Gradio Dataframe.

    On error returns an empty list (the UI shows no rows).
    """
    try:
        resp = _session.get(_build_url("/items"), timeout=5)
        if resp.status_code != 200:
            logger.warning("GET /items returned status %s", resp.status_code)
            return []
        data = resp.json()
        if isinstance(data, list):
            return [[d.get("id"), d.get("name"), d.get("quantity")] for d in data]
        logger.warning("Unexpected /items response shape: %s", type(data))
        return []
    except requests.RequestException:
        logger.exception("Failed to fetch items from API")
        return []


def read_one(item_id: Any) -> Tuple[int, Any]:
    """Fetch a single item by ID. Returns (status_code, json).

    The UI passes numbers for the ID; we coerce and validate.
    """
    if item_id is None or item_id == "":
        return 400, {"error": "Item ID required."}

    try:
        iid = int(item_id)
    except Exception:
        return 400, {"error": "Item ID must be an integer."}

    try:
        resp = _session.get(_build_url(f"/items/{iid}"), timeout=5)
        return _handle_response(resp)
    except requests.RequestException as exc:
        logger.exception("Error fetching item %s: %s", iid, exc)
        return 500, {"error": str(exc)}


def update(item_id: Any, name: str, qty: Any) -> Tuple[int, Any]:
    """Update an item. Only sends fields provided by the user."""
    if item_id is None or item_id == "":
        return 400, {"error": "Item ID required."}

    try:
        iid = int(item_id)
    except Exception:
        return 400, {"error": "Item ID must be an integer."}

    payload: Dict[str, Any] = {}
    if name and str(name).strip():
        payload["name"] = str(name).strip()
    if qty is not None and qty != "":
        try:
            payload["quantity"] = int(qty)
        except Exception:
            return 400, {"error": "Quantity must be a number."}

    if not payload:
        return 400, {"error": "No fields to update."}

    try:
        resp = _session.put(_build_url(f"/items/{iid}"), json=payload, timeout=5)
        return _handle_response(resp)
    except requests.RequestException as exc:
        logger.exception("Error updating item %s: %s", iid, exc)
        return 500, {"error": str(exc)}


def delete(item_id: Any, confirm: bool) -> Tuple[int, Any]:
    """Delete an item when `confirm` is True."""
    if not confirm:
        return 400, {"error": "Please confirm deletion."}

    try:
        iid = int(item_id)
    except Exception:
        return 400, {"error": "Item ID must be an integer."}

    try:
        resp = _session.delete(_build_url(f"/items/{iid}"), timeout=5)
        return _handle_response(resp)
    except requests.RequestException as exc:
        logger.exception("Error deleting item %s: %s", iid, exc)
        return 500, {"error": str(exc)}


with gr.Blocks(title="FoodID") as demo:
    gr.Markdown("# 🥫 FoodID — Inventory Manager")

    with gr.Tab("Create"):
        name = gr.Textbox(label="Item Name", placeholder="e.g., Rice")
        qty = gr.Number(label="Quantity", value=0, precision=0)
        code = gr.Number(label="HTTP Status", interactive=False, precision=0)
        out = gr.JSON(label="Result")
        gr.Button("Create").click(create, [name, qty], [code, out])

    with gr.Tab("Read"):
        gr.Markdown("### View All Items")
        tbl = gr.Dataframe(
            headers=["ID", "Name", "Quantity"],
            datatype=["number", "str", "number"],
            interactive=False,
        )
        gr.Button("Refresh Inventory").click(read_all, [], [tbl])

        gr.Markdown("### Lookup Item by ID")
        rid = gr.Number(label="Item ID", precision=0)
        code1 = gr.Number(label="HTTP Status", interactive=False, precision=0)
        out1 = gr.JSON(label="Result")
        gr.Button("Read One").click(read_one, [rid], [code1, out1])

    with gr.Tab("Update"):
        uid = gr.Number(label="Item ID", precision=0)
        new_name = gr.Textbox(label="New Name (optional)")
        new_qty = gr.Number(label="New Quantity (optional)", precision=0)
        code2 = gr.Number(label="HTTP Status", interactive=False, precision=0)
        out2 = gr.JSON(label="Result")
        gr.Button("Update").click(update, [uid, new_name, new_qty], [code2, out2])

    with gr.Tab("Delete"):
        did = gr.Number(label="Item ID", precision=0)
        confirm = gr.Checkbox(label="Confirm deletion")
        code3 = gr.Number(label="HTTP Status", interactive=False, precision=0)
        out3 = gr.JSON(label="Result")
        gr.Button("Delete").click(delete, [did, confirm], [code3, out3])


if __name__ == "__main__":
    # Allow overriding host/port via environment for easy testing in Docker
    host = os.getenv("FOODID_UI_HOST", "127.0.0.1")
    port = int(os.getenv("FOODID_UI_PORT", "7860"))
    demo.launch(server_name=host, server_port=port)
