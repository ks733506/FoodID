Contributing to FoodID

Thank you for your interest in contributing to the FoodID project. This guide explains how to report issues, propose improvements, and submit code.

What to Expect Be respectful, concise, and transparent. Small, focused contributions are easiest to review. For larger changes, open an issue or discussion first so the maintainer can align with the proposal before you begin implementing it.

Reporting Issues and Feature Requests Before creating an issue, search open and closed issues to avoid duplicates. Include a clear title, steps to reproduce, expected versus actual behavior, logs or screenshots, and environment details such as operating system and Python version. For feature requests, describe the problem, explain your proposed approach, and include alternatives considered.

Getting the Code Clone the repository with git clone <repo-url>, change into the folder, and optionally add an upstream remote.

Development Setup Install prerequisites: Python 3.11 or newer and Git. Create and activate a virtual environment using python -m venv .venv. On Windows use .\.venv\Scripts\Activate.ps1. On macOS or Linux use source .venv/bin/activate. Install dependencies with pip install -r requirements.txt and pip install -r requirements-dev.txt.. Run the application locally with python app.py.. Run the test suite with pytest -q.

Branching and Commits Create feature branches from the default branch using git checkout -b feat/short-description. Keep commits small and atomic. Write commit messages in imperative present tense, for example: Add quantity validation to item update endpoint. Reference related issues in the commit body when appropriate. Rebase or merge main regularly to avoid conflicts.

Pull Request Process Push your branch and open a pull request against the default branch. Your PR description should include what the change does, why it is needed, linked issue numbers if applicable, and clear testing steps. Keep PRs focused and scoped, splitting large changes into smaller PRs. Address reviewer feedback promptly.

Code Style and Tests Match the existing code style. Run formatters before committing with black . and isort .. Add or update tests when you change or introduce behavior. Tests should be deterministic and include needed test data or mocks.

Review and CI Every pull request runs through automated checks including linting and tests. Fix all failures before requesting final review. Maintain backward compatibility when possible and document breaking changes clearly.

Code of Conduct Be constructive, respectful, and considerate in discussions and contributions. Report any violations directly to the project maintainers.