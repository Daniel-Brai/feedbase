# Contributing to Feedbase

This guide explains how to set up the project locally, run tests, and submit contributions.

## Project structure

Feedbase's Python app lives under the `app/` directory. Most development work happens there, including:

- `app/pyproject.toml` — dependency and test configuration
- `app/tests/` — pytest test suites and fixtures
- `Makefile` — development commands for build, test, and runtime targets

## Getting started

1. Fork the repository.
2. Clone your fork:

   ```bash
   git clone https://github.com/Daniel-Brai/feedbase.git
   cd feedbase
   ```

3. Create a feature branch from `main`:

   ```bash
   git checkout -b feature/your-change
   ```

## Local development setup

From the repository root, install dependencies inside `app/`.

### Recommended UV setup

If you have `uv` installed, this is the preferred setup path.

```bash
cd app
uv sync --all-groups
```

### Optional pip setup

If you do not use `uv`, install dependencies with pip:

```bash
cd app
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .[dev,test,perf]
```

### Activate an existing virtual environment

```bash
cd app
source .venv/bin/activate
python -m pip install -e .[dev,test,perf]
```

## Running the application

Useful commands from the repository root:

```bash
make run-server
make run-worker
make run-scheduler
make run-triggers
make run-migrations
```

These commands activate `app/.venv` and run the matching scripts in `app/bin/`.

## Running tests

Feedbase uses `pytest` with async support and xdist for parallel execution.

### Recommended command

```bash
make test
```

This runs:

```bash
cd app
source .venv/bin/activate
pytest -n auto
```

### Run a specific test file

```bash
cd app
source .venv/bin/activate
pytest tests/services/test_feed_subscription_service.py
```

### Run only integration tests

Integration tests are marked with `@pytest.mark.integration`.

```bash
cd app
source .venv/bin/activate
pytest -m integration
```

## Code quality and formatting

Use the repository's pre-commit hooks and style checks before submitting code.

```bash
make precommit
```

This runs `pre-commit` against Python files under `app/`.

## Contribution workflow

- Open an issue first for larger features or behavioral changes.
- Keep branches small and focused.
- Add or update tests for bug fixes and new features.
- If the change affects behavior, update docs or add notes in the PR.
- Use clear commit messages and PR titles.

A useful PR summary should include:

- What changed
- Why it changed
- How it was tested

## Test environment notes

- The test suite config lives in `app/pyproject.toml`.
- `app/tests/conftest.py` sets `APP_ENVIRONMENT=test` and creates a dedicated PostgreSQL test database for each worker.
- Parallel test execution with `pytest-xdist` is supported because each worker uses its own temporary database name.

## Additional resources

- `README.md` — project overview and usage
- `docs/TESTING.md` — detailed testing instructions
- `.github/PULL_REQUEST_TEMPLATE.md` — PR template with summary and testing sections

Thanks again for contributing to Feedbase!
