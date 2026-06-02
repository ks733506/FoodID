# FoodID

FoodID is a prototype service that identifies foods from images and tracks a simple inventory. It pairs a lightweight Flask API with a Gradio UI so classmates, instructors, and testers can explore the core CRUD flow and identification workflow.

## Quickstart

Run the API and UI in separate terminals:

```bash
python app.py   # API server
python ui.py    # Gradio UI
```

Open the Gradio link printed by `ui.py`, or access the API directly at:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## At a Glance

* **Flask REST API (`app.py`)** — CRUD endpoints for items, plus health check and identification stub.
* **Gradio UI (`ui.py`)** — Friendly interface with validation and inline feedback.
* **SQLite persistence** via `db.py` and `schema.sql`, including migration helpers.
* **CI pipeline** with pytest, linting, formatting, and permissive mypy checks (GitHub Actions).
* **Documentation** for rubric mapping, testing, and presentation planning in `docs/`.

## Architecture Overview

```
[Gradio UI] --HTTP--> [Flask API] --SQL--> [SQLite Database]
     |                                 ^
     +---- local validation + feedback |
                                       schema + migration
```

* `create_app()` wires endpoints, initializes/migrates DB, and seeds data when `SEED_DB=1`.
* `db.py` manages DB path, schema creation, migrations, and helper functions used by API + tests.
* `ui.py` provides client-side validation and shows clear API error messages during demos.

---

## Local Setup

### Prerequisites

* Python **3.11+** (tested with 3.13.2)
* SQLite (bundled with Python)

### Environment Configuration

This project uses environment variables for configuration.  
Copy `.env.example` to `.env` and adjust values as needed:

```bash
cp .env.example .env
```
Do not commit .env to version control.

Key settings:

- `FOODID_DB` — optional path to the SQLite DB (default: `foodid.db`).
- `FLASK_DEBUG=1` — enable debug mode.
- `SEED_DB=1` — load sample items after migrations.


### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -c "from db import init_db; init_db()"
python app.py
python ui.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -c "from db import init_db; init_db()"
python app.py
python ui.py
```
---

## Key Endpoints

| Method | Path          | Description                                  |
| ------ | ------------- | -------------------------------------------- |
| GET    | `/health`     | Health check; verifies DB connectivity       |
| GET    | `/items`      | List items                                   |
| POST   | `/items`      | Create an item (`name`, optional `quantity`) |
| GET    | `/items/<id>` | Retrieve an item                             |
| PUT    | `/items/<id>` | Update item (rejects negative quantity)      |
| DELETE | `/items/<id>` | Delete an item                               |
| POST   | `/identify`   | Placeholder identification endpoint          |

Additional examples are in inline docstrings within `app.py`.

---

## Design & Accessibility Notes

* Task-focused UI with simple, clear tabs.
* Form validation mirrors API rules: non-empty names, non-negative quantities.
* Clear error messages near inputs.
* Gradio defaults provide keyboard-accessible widgets.
* API returns structured JSON errors for automated or assistive clients.

Additional rationale:

* `docs/presentation_outline.md`
* `docs/rubric/requirements_mapping.md`

---

## Data & Migrations

* `init_db()` creates tables from `schema.sql` if DB does not yet exist.
* `migrate_db()` adds missing columns to older DB files without dropping data.
* `seed_sample()` loads sample inventory when `SEED_DB=1`.
* Development helpers: `inspect_db_schema.py`, `debug_inspect_db.py`.

---

## Quality & Testing

### Tests

```bash
pytest -q
```

### Linting / Formatting

```bash
black --check .
isort --check-only .
flake8
mypy --config-file mypy.ini || true
```

* GitHub Actions CI (`.github/workflows/ci.yml`) runs these checks on every push/PR.
* Testing evidence (latest: 2025-11-17) is in `docs/TESTING.md` and `docs/testing_results.csv`.

---

## Deployment Notes

* Use a production WSGI server such as gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

* Configure environment variables and disable debug mode.
* Consider PostgreSQL for multi-user scenarios or higher concurrency.
* Docker assets (`Dockerfile`, `docker-compose.yml`) are provided for development.

---

## Documentation Map

* `docs/rubric/requirements_mapping.md` — rubric crosswalk
* `docs/TESTING.md`, `docs/testing_results.csv` — test evidence
* `docs/presentation_outline.md` — slides/video script
* `todo.md` — project task history

---

## Contributing

See `CONTRIBUTING.md` for full guidelines on branching, testing, and submitting pull requests.


## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
