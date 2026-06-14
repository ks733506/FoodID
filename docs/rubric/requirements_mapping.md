# Rubric Requirement Mapping


| Criterion | Expectation (per rubric) | Evidence / Links | Status | Notes |
|-----------|--------------------------|------------------|--------|-------|
| Problem Definition & Goals | Communicate project purpose, audience, and success goals | `README.md` (intro, features), `app.py` (endpoint docstrings) | Complete |
| Design Rationale & Accessibility | Explain key interface decisions, accessibility considerations, and how UI supports user goals | `README.md` (Design & Accessibility section), `ui.py`, `docs/presentation_outline.md` | Complete | Accessibility built into Gradio defaults + custom validation. |
| Prototype Functionality | Working interactive prototype demonstrating core scenarios | `app.py`, `ui.py`, live demo flow in `docs/presentation_outline.md` | Complete |
| Data Persistence & Migration | Reliable data storage with documented schema changes | `db.py` (`migrate_db`, helpers), `schema.sql`, seeding via `init_db()` | Complete |
| Testing & Quality Assurance | Evidence of automated tests and recent execution results | `test_api.py`, `docs/TESTING.md`, `docs/testing_results.csv`, `.github/workflows/ci.yml` | Complete |
| Code Quality & Process | Linting, formatting, typing, and contribution guidance | `.flake8`, `requirements-dev.txt`, `.pre-commit-config.yaml`, `CONTRIBUTING.md`, CI job in `.github/workflows/ci.yml` | Complete | All checks passing. |
| Deployment & Environment Setup | Clear instructions to install, run locally, and optionally in containers | `README.md` (quick start), `.env.example`, `Dockerfile`, `docker-compose.yml` | Complete | Both Unix and Windows paths provided. |
| Presentation & Demonstration | Prepared walkthrough highlighting design goals, implementation, and testing proof | `docs/presentation_outline.md` | Complete |
