# Testing

This document describes the testing strategy and setup for Feedbase.
I use `pytest` for automated testing and keeps test code under `app/tests/`.

## Test types

- `controllers` and `views` cover request handling and UI flow.
- `services` cover business logic and domain operations.
- `jobs` cover background job behavior.
- `notifications`, `factories`, `support`, and `utils` support test helpers, fixtures, and fake data.

## Test requirements

- Python 3.13+
- A PostgreSQL server available to the test environment
- A project virtual environment with dev/test dependencies installed

The test dependencies are declared in `app/pyproject.toml` under the `test` dependency group.

## Setting up the test environment

From the repository root:

### Recommended UV setup

If you have `uv` installed, use the preferred setup path:

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
python -m pip install -e .[test]
```

If you already have the virtual environment created, simply activate it and install the test extras.

## Running tests

The repository provides a Makefile shortcut:

```bash
make test
```

That target changes into `app`, activates the virtual environment, and runs:

```bash
pytest -n auto
```

This uses `pytest-xdist` to parallelize tests across available CPU cores.

### Run a specific test file

```bash
cd app
source .venv/bin/activate
pytest tests/services/test_feed_subscription_service.py
```

### Run only integration tests

Integration tests are marked with `@pytest.mark.integration`.
Use this marker when you want tests that require a real database.

```bash
cd app
source .venv/bin/activate
pytest -m integration
```

## Test configuration

`app/pyproject.toml` contains the pytest settings used by the project:

- `asyncio_mode = "auto"` so async tests work with `pytest-asyncio`
- `pythonpath = ["."]` so imports resolve from the `app` package root
- `testpaths = ["./tests/"]` and `python_files = ["test_*.py"]`

## Database lifecycle during tests

The test suite sets environment variables in `app/tests/conftest.py`:

- `APP_ENVIRONMENT=test`
- `APP_POSTGRES_DB=feedbase_test_db_<worker>`

A session-scoped fixture creates and initializes a dedicated PostgreSQL test database before tests start and drops it afterward.

That means tests can run in parallel safely with `pytest-xdist`, because each worker uses its own temporary database name.

## Useful tips

- If you add or update tests, run the relevant file or module first before running the full suite.
- Use `make precommit` to run formatting and linting checks on Python files under `app/`.
- If you need to inspect a fixture, look at `app/tests/conftest.py` and `app/tests/support/`.

## Troubleshooting

- Make sure PostgreSQL is reachable with the credentials configured by the test environment.
- If tests fail due to a stale database, the session fixture should recreate it automatically.
