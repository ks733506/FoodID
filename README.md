gunicorn -w 4 -b 0.0.0.0:8000 app:app
# FoodID

FoodID is a prototype service that helps identify foods from images and track an accompanying inventory. It pairs a lightweight Flask API with a Gradio-based UI so classmates, instructors, and testers can explore the experience quickly.

## At a Glance
- Flask REST API (`app.py`) exposes CRUD endpoints for items plus a health check and identification stub.
- Gradio front end (`ui.py`) wraps the API in a friendly interface with validation and inline feedback.
- SQLite persistence (`db.py`, `schema.sql`) with migration helpers that keep legacy databases compatible.
- Automated quality checks: pytest suite, linting, formatting, and permissive mypy run via GitHub Actions CI.
- Documentation for rubric mapping, testing evidence, and presentation planning lives under `docs/`.

## Architecture Overview
```
[Gradio UI] --HTTP--> [Flask API] --SQL--> [SQLite Database]
			 |                                 ^
			 +---- local validation + feedback  |
											 schema + migration|
```
- `create_app()` wires up endpoints, runs `init_db()` and `migrate_db()`, and seeds sample data when `SEED_DB=1`.
- `db.py` resolves the database file path at runtime, performs schema migrations, and exposes helpers used by the API and tests.
- `ui.py` maintains a shared HTTP session, validates quantities, and surfaces API errors so usability issues are obvious during demos.

## Local Setup

### Prerequisites
- Python 3.10 or newer (3.13.2 used in development)
- SQLite (included with Python)

### Environment Variables
Copy `.env.example` to `.env`. Key settings:
- `DATABASE_PATH` — optional override for the SQLite file (defaults to `foodid.db`).
- `FLASK_DEBUG` — set to `1` to enable debug mode locally.
- `SEED_DB` — set to `1` to load the sample items after migrations.

### Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -c "from db import init_db; init_db()"
python app.py              # API server
python ui.py               # UI in a second terminal
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -c "from db import init_db; init_db()"
python app.py              # API server
python ui.py               # UI in a second terminal
```

Point the browser to the Gradio link printed by `ui.py`, or exercise the API directly at `http://127.0.0.1:5000`.

## Key Endpoints
- `GET /health` — lightweight health probe; verifies DB connectivity.
- `GET /items` — list inventory items.
- `POST /items` — create a new item (`name`, optional `quantity`).
- `GET /items/<id>` — retrieve a specific item.
- `PUT /items/<id>` — update fields; rejects negative quantities.
- `DELETE /items/<id>` — remove an item.
- `POST /identify` — placeholder that demonstrates the intended image-identification response shape.

See inline docstrings in `app.py` for request/response examples.

## Design & Accessibility Notes
- UI keeps the task-focused layout: upload/select image, enter item metadata, and view recent results in a single screen.
- Form validation mirrors API rules (non-empty names, non-negative quantities) and surfaces clear error messages near inputs.
- Gradio defaults provide keyboard-accessible controls; descriptive labels and status messages aid screen-reader users.
- API returns structured JSON errors so alternative clients (e.g., assistive tech, automated scripts) can react programmatically.

Additional narrative and rationale: `docs/presentation_outline.md` (Sections 2–4) and `docs/rubric/requirements_mapping.md`.

## Data & Migrations
- `init_db()` creates tables using `schema.sql` when the database file is missing.
- `migrate_db()` ensures legacy tables gain `created_at` / `updated_at` columns without dropping data.
- `seed_sample()` populates example rows for demos when `SEED_DB=1`.
- Use `inspect_db_schema.py` or `debug_inspect_db.py` to review schema state during development.

## Quality & Testing
- Unit / integration tests live in `test_api.py`. Run them locally:
	```bash
	pytest -q
	```
- Linting and formatting checks:
	```bash
	black --check .
	isort --check-only .
	flake8
	mypy --config-file .flake8 || true  # permissive type checking
	```
- GitHub Actions workflow at `.github/workflows/ci.yml` runs the same commands on push/PR.
- Testing evidence (latest run 2025-11-10) is captured in `docs/TESTING.md` and `docs/testing_results.csv`.

## Deployment Notes
- For production, run behind a WSGI server such as gunicorn:
	```bash
	gunicorn -w 4 -b 0.0.0.0:8000 app:app
	```
- Update environment variables for production secrets and disable debug mode.
- Consider migrating to PostgreSQL if concurrency or multi-user support becomes critical.
- Docker assets (`Dockerfile`, `docker-compose.yml`) provide a containerized dev/devops starting point.

## Evaluation & Reflection
- Lessons learned and future enhancements are summarized in `docs/evaluation_reflection.md`.
- Known next steps: integrate a real image classification model, expand accessibility testing, gather additional user feedback sessions, and tighten mypy settings.

## Documentation Map
- `docs/rubric/requirements_mapping.md` — rubric criterion crosswalk.
- `docs/TESTING.md` and `docs/testing_results.csv` — manual + automated testing evidence.
- `docs/presentation_outline.md` — slide/video script for the final presentation.
- `todo.md` — historical project tracking (all tasks complete).

## Contributing
- Fork the repository, create a feature branch, and submit pull requests.
- Follow the formatting and linting commands above before opening a PR.
- See `CONTRIBUTING.md` for detailed guidelines.

## License
This project currently ships with the `LICENSE` file in the repository root. Update the text if your course or organization requires a different license.

## Contact
Questions or feedback? Open an issue or reach out to the project maintainer listed in your course portal.
