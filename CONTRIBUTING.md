# Contributing to FoodID

Thanks for your interest in contributing! Small projects benefit a lot from
clear contribution guidelines. A quick checklist to follow:

- Fork the repository and open a feature branch for your work.
- Run the test suite locally before opening a PR:

  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  pip install -r requirements-dev.txt
  pytest -q
  ```

- Format code with `black` and sort imports with `isort`.
- Keep changes small and focused. Add tests for new features or bug fixes.
- Open a pull request against the `main` branch and describe the change.

If your PR changes public behavior, include a short note in the PR explaining
how users should migrate.
