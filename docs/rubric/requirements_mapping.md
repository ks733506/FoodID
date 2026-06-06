# Rubric Requirement Mapping

This table links the expected final project rubric criteria to the concrete deliverables already in the repository. Update the "Notes" column if your instructor's rubric phrases the requirement differently.

| Criterion | Expectation (per rubric) | Evidence / Links | Status | Notes |
|-----------|--------------------------|------------------|--------|-------|
| Problem Definition & Goals | Communicate project purpose, audience, and success goals | `README.md` (intro, features), `app.py` (endpoint docstrings) | Complete | Consider adding brief user personas if desired. |
| Design Rationale & Accessibility | Explain key interface decisions, accessibility considerations, and how UI supports user goals | `README.md` (Design & Accessibility section), `ui.py`, `docs/presentation_outline.md` | Complete | Accessibility built into Gradio defaults + custom validation. |
| Prototype Functionality | Working interactive prototype demonstrating core scenarios | `app.py`, `ui.py`, live demo flow in `docs/presentation_outline.md` | Complete | Demo script covers the CRUD workflow end-to-end. |
| Data Persistence & Migration | Reliable data storage with documented schema changes | `db.py` (`migrate_db`, helpers), `schema.sql`, seeding via `init_db()` | Complete | Mention legacy migration pattern if upgrading from older DB. |
| Testing & Quality Assurance | Evidence of automated tests and recent execution results | `test_api.py`, `docs/TESTING.md`, `docs/testing_results.csv`, `.github/workflows/ci.yml` | Complete | Re-run and update CSV before final submission. |
| Code Quality & Process | Linting, formatting, typing, and contribution guidance | `.flake8`, `requirements-dev.txt`, `.pre-commit-config.yaml`, `CONTRIBUTING.md`, CI job in `.github/workflows/ci.yml` | Complete | All checks passing. |
| Deployment & Environment Setup | Clear instructions to install, run locally, and optionally in containers | `README.md` (quick start), `.env.example`, `Dockerfile`, `docker-compose.yml` | Complete | Both Unix and Windows paths provided. |
| Presentation & Demonstration | Prepared walkthrough highlighting design goals, implementation, and testing proof | `docs/presentation_outline.md` | Complete | Customize timing cues once the slide deck is finalized. |
