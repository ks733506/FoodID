# Presentation & Video Outline

Use this outline to structure the final class presentation or screen-recorded demo. Target a 6–8 minute walkthrough; adjust timing to match course expectations.

## 1. Opening (30s)
- Briefly reintroduce the FoodID project, the problem it solves, and the target users.
- State the primary goal for the session (show working prototype + evidence of quality).

## 2. Design Rationale (60s)
- Highlight the key user needs that informed the interface (quick identification, inventory tracking).
- Call out validation/error messaging choices in `ui.py` and how they support usability.
- Mention any accessibility considerations (clear labels, error feedback, keyboard-friendly Gradio defaults).

## 3. Architecture Overview (60s)
- Show the high-level flow: Gradio UI → Flask API (`app.py`) → SQLite (`db.py`).
- Point out the database migration helper (`migrate_db`) and why it was added.
- Reference CI tooling and lint/test automation to demonstrate maintainability.

## 4. Live Demo (3–4 min)
1. Launch API (`python app.py`) and UI (`python ui.py`) — show both running.
2. Perform the CRUD walkthrough using the UI and/or API client:
   - Create a food item with image/quantity.
   - Show list view updating; retrieve item details.
   - Update an item and highlight validation on invalid quantities.
   - Delete the item and confirm removal.
3. (Optional) Trigger an identification request to emphasize model integration (or explain mock if not active).
4. Point out timestamps and data persistence in the SQLite DB (brief peek with `inspect_db_schema.py` if time allows).

## 5. Testing Evidence (60s)
- Display the `docs/testing_results.csv` table or `docs/TESTING.md` summary.
- Mention the pytest suite (`test_api.py`) and CI workflow (`.github/workflows/ci.yml`).
- Highlight recent run output (all tests passing on 2025-11-10).

## 6. Reflection & Next Steps (60s)
- Summarize major lessons learned (e.g., handling legacy DB rows, ensuring migrations).
- Note pending enhancements (improved identification model, richer UI feedback, user testing).
- Invite questions / feedback on design decisions.

## 7. Closing (30s)
- Reiterate project value and readiness for submission.
- Provide contact info or repository link for follow-up.

### Recording Tips
- Record fullscreen or focused window to keep UI legible.
- Narrate what is happening and why; keep pace steady.
- Trim dead air; add captions if accessibility is required.
