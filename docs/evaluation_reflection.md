# Evaluation & Reflection

## Summary of Findings
- Database migrations were required to add `created_at` and `updated_at` columns; automated helpers now prevent 500 errors when reading legacy rows.
- The Gradio UI benefits from explicit quantity validation and shared sessions, reducing duplicate requests and clarifying error messages for users.
- Running the full pytest suite during development surfaced edge cases around deleting and re-fetching items, resulting in more robust API responses.

## User & Peer Feedback
- Classmates testing the prototype preferred plain-language error messages over numeric codes, informing the current JSON error payloads.
- Reviewers requested evidence of persistence beyond a single session, leading to the addition of timestamps and the migration helper demo during presentations.
- Informal hallway tests confirmed that the CRUD flow is understandable without prior training, though participants asked for richer identification results (future work).

## Quality Assurance Recap
- Automated tests: `pytest -q` (6 tests covering CRUD, health check, and DB creation).
- Static analysis: `black --check`, `isort --check-only`, `flake8`, and permissive `mypy` run locally and in CI.
- Manual smoke tests: launching API + UI concurrently, running through the create/update/delete demo script, and verifying database state with `inspect_db_schema.py`.
- Test evidence is documented in `docs/TESTING.md` and `docs/testing_results.csv` with the latest execution dated 2025-11-10.

## Lessons Learned
- Establishing a repeatable migration path early prevents regressions when schema changes accelerate late in the project.
- Pairing automated tests with a human-facing presentation script ensures both code health and communication readiness.
- Maintaining documentation (README, rubric mapping, outline) in the repository shortens the hand-off time for course deliverables.

## Next Steps
- Integrate or simulate a real image classification model to replace the current placeholder response for `/identify`.
- Conduct structured usability testing sessions and capture findings to expand the reflection section with quantitative metrics.
- Tighten type checking by configuring mypy in strict mode once any third-party typing gaps are resolved.
- Explore hosting options (e.g., Render, Railway) and document deployment steps for reproducibility.
