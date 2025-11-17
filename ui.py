"""Gradio UI for FoodID.

This module provides a lightweight frontend that talks to the Flask API defined
in `app.py`. It exposes Create / Read / Update / Delete operations against the
`/items` endpoints. The UI functions validate inputs, call the API, and normalize
responses for Gradio widgets.

Notes:
- The API base URL can be overridden with the FOODID_API environment variable.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Tuple

import gradio as gr
import requests  # type: ignore[import]

# Configure logging
level = getattr(logging, os.getenv("LOG_LEVEL", "INFO"), logging.INFO)
logging.basicConfig(level=level)
logger = logging.getLogger("foodid.ui")

API = os.getenv("FOODID_API", "http://127.0.0.1:5000").rstrip("/")
_session = requests.Session()


def _handle_response(resp: requests.Response) -> Tuple[int, Any]:
    """Normalize API response into (status_code, JSON)."""
    try:
        data = resp.json()
    except ValueError:
        logger.exception("Invalid JSON response from %s", resp.url)
        data = {
            "error": "Invalid JSON from server",
            "status": resp.status_code,
            "text": resp.text,
        }
    return resp.status_code, data


def _build_url(path: str) -> str:
    """Build full API URL from base and path."""
    return f"{API}/{path.lstrip('/')}".rstrip("/")


def create(name: str, qty: Any) -> Tuple[int, Dict[str, Any]]:
    """Create a new inventory item."""
    if not name or not str(name).strip():
        return 400, {"error": "Item name is required.", "status": 400}

    try:
        quantity = int(qty) if qty is not None else 0
        if quantity < 0:
            return 400, {
                "error": "Quantity must be a non-negative integer.",
                "status": 400,
            }
    except Exception:
        logger.exception("Invalid quantity provided: %r", qty)
        return 400, {"error": "Quantity must be an integer.", "status": 400}

    payload = {"name": name.strip(), "quantity": quantity}
    try:
        resp = _session.post(_build_url("/items"), json=payload, timeout=5)
        return _handle_response(resp)
    except requests.RequestException as exc:
        logger.exception("Error creating item: %s", exc)
        return 500, {"error": str(exc), "status": 500}


def read_all() -> List[List[Any]]:
    """Fetch all inventory items."""
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
    """Fetch a single inventory item by ID."""
    if item_id is None or item_id == "":
        return 400, {"error": "Item ID is required.", "status": 400}

    try:
        iid = int(item_id)
    except Exception:
        return 400, {"error": "Item ID must be an integer.", "status": 400}

    try:
        resp = _session.get(_build_url(f"/items/{iid}"), timeout=5)
        return _handle_response(resp)
    except requests.RequestException as exc:
        logger.exception("Error fetching item %s: %s", iid, exc)
        return 500, {"error": str(exc), "status": 500}


def update(item_id: Any, name: str, qty: Any) -> Tuple[int, Any]:
    """Update an inventory item by ID."""
    if item_id is None or item_id == "":
        return 400, {"error": "Item ID is required.", "status": 400}

    try:
        iid = int(item_id)
    except Exception:
        return 400, {"error": "Item ID must be an integer.", "status": 400}

    payload: Dict[str, Any] = {}
    if name and str(name).strip():
        payload["name"] = str(name).strip()
    if qty is not None and qty != "":
        try:
            qval = int(qty)
            if qval < 0:
                return 400, {
                    "error": "Quantity must be a non-negative integer.",
                    "status": 400,
                }
            payload["quantity"] = qval
        except Exception:
            return 400, {"error": "Quantity must be an integer.", "status": 400}

    if not payload:
        return 400, {"error": "No fields provided to update.", "status": 400}

    try:
        resp = _session.put(_build_url(f"/items/{iid}"), json=payload, timeout=5)
        return _handle_response(resp)
    except requests.RequestException as exc:
        logger.exception("Error updating item %s: %s", iid, exc)
        return 500, {"error": str(exc), "status": 500}


def delete(item_id: Any, confirm: bool) -> Tuple[int, Any]:
    """Delete an inventory item by ID."""
    if not confirm:
        return 400, {
            "error": "Please confirm deletion before proceeding.",
            "status": 400,
        }

    try:
        iid = int(item_id)
    except Exception:
        return 400, {"error": "Item ID must be an integer.", "status": 400}

    try:
        resp = _session.delete(_build_url(f"/items/{iid}"), timeout=5)
        return _handle_response(resp)
    except requests.RequestException as exc:
        logger.exception("Error deleting item %s: %s", iid, exc)
        return 500, {"error": str(exc), "status": 500}


with gr.Blocks(title="FoodID") as demo:
    gr.Markdown("# 🥫 FoodID — Inventory Manager")

    with gr.Tab("Create"):
        name = gr.Textbox(label="Item Name", placeholder="e.g., Rice")
        qty = gr.Number(label="Quantity", value=0, precision=0)
        code = gr.Number(label="HTTP Status", interactive=False, precision=0)
        out = gr.JSON(label="Response")
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
        out1 = gr.JSON(label="Response")
        gr.Button("Read One").click(read_one, [rid], [code1, out1])

    with gr.Tab("Update"):
        uid = gr.Number(label="Item ID", precision=0)
        new_name = gr.Textbox(label="New Name (optional)")
        new_qty = gr.Number(label="New Quantity (optional)", precision=0)
        code2 = gr.Number(label="HTTP Status", interactive=False, precision=0)
        out2 = gr.JSON(label="Response")
        gr.Button("Update").click(update, [uid, new_name, new_qty], [code2, out2])

    with gr.Tab("Delete"):
        gr.Markdown("### Delete Item\nCheck the box below to confirm deletion.")
        did = gr.Number(label="Item ID", precision=0)
        confirm = gr.Checkbox(label="Confirm deletion")
        code3 = gr.Number(label="HTTP Status", interactive=False, precision=0)
        out3 = gr.JSON(label="Response")
        gr.Button("Delete").click(delete, [did, confirm], [code3, out3])


if __name__ == "__main__":
    host = os.getenv("FOODID_UI_HOST", "127.0.0.1")
    port = int(os.getenv("FOODID_UI_PORT", "7860"))
    logger.info("Launching Gradio UI at http://%s:%s", host, port)
    demo.launch(server_name=host, server_port=port)
