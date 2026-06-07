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

# API base URL from environment or default to local Flask app
API = os.getenv("FOODID_API", "http://127.0.0.1:5000").rstrip("/")
# Reusable session for connection pooling across API calls
_session = requests.Session()


def _handle_response(resp: requests.Response) -> Tuple[int, Any]:
    """Normalize API response into (status_code, JSON).

    Attempts to parse response as JSON; if parsing fails,
    creates an error response object with the raw text.

    Args:
        resp: requests.Response object from API call

    Returns:
        Tuple of (HTTP status code, JSON data dict)
    """
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
    """Build full API URL from base and path.

    Handles leading/trailing slashes to avoid double slashes.

    Args:
        path: API endpoint path (e.g., "/items", "items/5")

    Returns:
        Full URL ready for requests (e.g., "http://localhost:5000/items")
    """
    return f"{API}/{path.lstrip('/')}".rstrip("/")


def create(name: str, qty: Any) -> Tuple[int, Dict[str, Any]]:
    """Create a new inventory item via API.

    Validates name and quantity inputs before sending POST request
    to /items endpoint.

    Args:
        name: Item name (required, cannot be empty)
        qty: Item quantity (converted to int, must be >= 0)

    Returns:
        Tuple of (HTTP status code, response JSON dict)
        - HTTP 201 on success with created item
        - HTTP 400 on validation error
        - HTTP 500 on network/server error
    """
    # Validate name is not empty after trimming whitespace
    if not name or not str(name).strip():
        return 400, {"error": "Item name is required.", "status": 400}

    try:
        # Convert quantity to integer, default to 0 if None
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
        # Send POST request to create item
        resp = _session.post(_build_url("/items"), json=payload, timeout=5)
        return _handle_response(resp)
    except requests.RequestException as exc:
        logger.exception("Error creating item: %s", exc)
        return 500, {"error": str(exc), "status": 500}


def read_all() -> List[List[Any]]:
    """Fetch all inventory items from API.

    Returns items in a format suitable for Gradio Dataframe widget:
    list of [id, name, quantity] lists.

    Returns:
        List of [id, name, quantity] lists, empty list on error
    """
    try:
        # GET all items from API
        resp = _session.get(_build_url("/items"), timeout=5)
        if resp.status_code != 200:
            logger.warning("GET /items returned status %s", resp.status_code)
            return []
        data = resp.json()
        # Extract id, name, quantity from each item for dataframe
        if isinstance(data, list):
            return [[d.get("id"), d.get("name"), d.get("quantity")] for d in data]
        logger.warning("Unexpected /items response shape: %s", type(data))
        return []
    except requests.RequestException:
        logger.exception("Failed to fetch items from API")
        return []


def read_one(item_id: Any) -> Tuple[int, Any]:
    """Fetch a single inventory item by ID via API.

    Args:
        item_id: Numeric item ID (required)

    Returns:
        Tuple of (HTTP status code, response JSON dict)
        - HTTP 200 on success with item data
        - HTTP 400 on invalid item ID
        - HTTP 404 if item not found
        - HTTP 500 on network/server error
    """
    # Validate item_id is provided
    if item_id is None or item_id == "":
        return 400, {"error": "Item ID is required.", "status": 400}

    try:
        # Convert item_id to integer
        iid = int(item_id)
    except Exception:
        return 400, {"error": "Item ID must be an integer.", "status": 400}

    try:
        # GET specific item by ID
        resp = _session.get(_build_url(f"/items/{iid}"), timeout=5)
        return _handle_response(resp)
    except requests.RequestException as exc:
        logger.exception("Error fetching item %s: %s", iid, exc)
        return 500, {"error": str(exc), "status": 500}


def update(item_id: Any, name: str, qty: Any) -> Tuple[int, Any]:
    """Update an inventory item by ID via API.

    At least one of name or qty must be provided.

    Args:
        item_id: Numeric item ID (required)
        name: New item name (optional, if provided must not be empty)
        qty: New quantity (optional, must be >= 0 if provided)

    Returns:
        Tuple of (HTTP status code, response JSON dict)
        - HTTP 200 on success with updated item
        - HTTP 400 on validation or input error
        - HTTP 404 if item not found
        - HTTP 500 on network/server error
    """
    # Validate item_id is provided
    if item_id is None or item_id == "":
        return 400, {"error": "Item ID is required.", "status": 400}

    try:
        # Convert item_id to integer
        iid = int(item_id)
    except Exception:
        return 400, {"error": "Item ID must be an integer.", "status": 400}

    # Build payload with only provided fields
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

    # Ensure at least one field is being updated
    if not payload:
        return 400, {"error": "No fields provided to update.", "status": 400}

    try:
        # Send PUT request to update item
        resp = _session.put(_build_url(f"/items/{iid}"), json=payload, timeout=5)
        return _handle_response(resp)
    except requests.RequestException as exc:
        logger.exception("Error updating item %s: %s", iid, exc)
        return 500, {"error": str(exc), "status": 500}


def delete(item_id: Any, confirm: bool) -> Tuple[int, Any]:
    """Delete an inventory item by ID via API.

    Requires explicit confirmation to prevent accidental deletion.

    Args:
        item_id: Numeric item ID (required)
        confirm: Must be True to actually delete the item

    Returns:
        Tuple of (HTTP status code, response JSON dict)
        - HTTP 200 on success with deletion confirmation
        - HTTP 400 if not confirmed or invalid item ID
        - HTTP 404 if item not found
        - HTTP 500 on network/server error
    """
    # Require explicit confirmation before deletion
    if not confirm:
        return 400, {
            "error": "Please confirm deletion before proceeding.",
            "status": 400,
        }

    try:
        # Convert item_id to integer
        iid = int(item_id)
    except Exception:
        return 400, {"error": "Item ID must be an integer.", "status": 400}

    try:
        # Send DELETE request to remove item
        resp = _session.delete(_build_url(f"/items/{iid}"), timeout=5)
        return _handle_response(resp)
    except requests.RequestException as exc:
        logger.exception("Error deleting item %s: %s", iid, exc)
        return 500, {"error": str(exc), "status": 500}


# Build the Gradio UI with tabs for each CRUD operation
with gr.Blocks(title="FoodID") as demo:
    gr.Markdown("# 🥫 FoodID — Inventory Manager")

    # CREATE tab: Add new inventory items
    with gr.Tab("Create"):
        name = gr.Textbox(label="Item Name", placeholder="e.g., Rice")
        qty = gr.Number(label="Quantity", value=0, precision=0)
        code = gr.Number(label="HTTP Status", interactive=False, precision=0)
        out = gr.JSON(label="Response")
        gr.Button("Create").click(create, [name, qty], [code, out])

    # READ tab: Retrieve items (all or by ID)
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

    # UPDATE tab: Modify existing items
    with gr.Tab("Update"):
        uid = gr.Number(label="Item ID", precision=0)
        new_name = gr.Textbox(label="New Name (optional)")
        new_qty = gr.Number(label="New Quantity (optional)", precision=0)
        code2 = gr.Number(label="HTTP Status", interactive=False, precision=0)
        out2 = gr.JSON(label="Response")
        gr.Button("Update").click(update, [uid, new_name, new_qty], [code2, out2])

    # DELETE tab: Remove items (requires confirmation)
    with gr.Tab("Delete"):
        gr.Markdown("### Delete Item\nCheck the box below to confirm deletion.")
        did = gr.Number(label="Item ID", precision=0)
        confirm = gr.Checkbox(label="Confirm deletion")
        code3 = gr.Number(label="HTTP Status", interactive=False, precision=0)
        out3 = gr.JSON(label="Response")
        gr.Button("Delete").click(delete, [did, confirm], [code3, out3])


if __name__ == "__main__":
    # Configure host and port from environment variables
    host = os.getenv("FOODID_UI_HOST", "127.0.0.1")
    port = int(os.getenv("FOODID_UI_PORT", "7860"))
    logger.info("Launching Gradio UI at http://%s:%s", host, port)
    # Launch the Gradio demo server
    demo.launch(server_name=host, server_port=port)
