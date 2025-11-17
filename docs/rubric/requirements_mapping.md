# Rubric Requirement Mapping

This table links the expected final project rubric criteria to the concrete deliverables already in the repository. Update the "Notes" column if your instructor's rubric phrases the requirement differently.

| Criterion | Expectation (per rubric) | Evidence / Links | Status | Notes |
|-----------|--------------------------|------------------|--------|-------|
| Problem Definition & Goals | Communicate project purpose, audience, and success goals | `README.md` (intro, features), `app.py` (endpoint docstrings) | Complete | Consider adding brief user personas if rubric requests them explicitly. |
| Design Rationale & Accessibility | Explain key interface decisions, accessibility considerations, and how UI supports user goals | `README.md` (Design & Accessibility section), `ui.py`, `docs/presentation_outline.md` | Complete | Add screenshots or wireframes if rubric mandates visual artifacts. |
| Prototype Functionality | Working interactive prototype demonstrating core scenarios | `app.py`, `ui.py`, live demo flow in `docs/presentation_outline.md` | Complete | Demo script covers the CRUD flow and identification workflow. |
| Data Persistence & Migration | Reliable data storage with documented schema changes | `db.py` (`migrate_db`, helpers), `schema.sql`, seeding via `init_db()` | Complete | Mention legacy migration support during presentation Q&A. |
| Testing & Quality Assurance | Evidence of automated tests and recent execution results | `test_api.py`, `docs/TESTING.md`, `docs/testing_results.csv`, `.github/workflows/ci.yml` | Complete | Re-run `pytest -q` before submission and refresh the CSV date if needed. |
| Code Quality & Process | Linting, formatting, typing, and contribution guidance | `.flake8`, `requirements-dev.txt`, `.pre-commit-config.yaml`, `CONTRIBUTING.md`, CI job in `.github/workflows/ci.yml` | Complete | Note that mypy currently runs in permissive mode; tighten if rubric asks for strict typing. |
| Deployment & Environment Setup | Clear instructions to install, run locally, and optionally in containers | `README.md` (quick start), `.env.example`, `Dockerfile`, `docker-compose.yml` | Complete | Verify Docker path updates after any dependency changes. |
| Evaluation & Reflection | Summarize findings, user feedback, and planned improvements | `docs/evaluation_reflection.md`, `docs/TESTING.md`, `docs/testing_results.csv` | Complete | Incorporate additional user metrics if more formal studies are conducted. |
| Presentation & Demonstration | Prepared walkthrough highlighting design goals, implementation, and testing proof | `docs/presentation_outline.md` | Complete | Customize timing cues once the slide deck or recording is ready. |
