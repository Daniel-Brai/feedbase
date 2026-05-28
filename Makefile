UV ?= uv
PYTHON ?= python
PUSH ?= false
APP_DIR := app
VENV := .venv
ACTIVATE := . $(VENV)/bin/activate
ALEMBIC := python -m alembic
ALEMBIC_INI := alembic.ini

.PHONY: help migration-create run-migrations migration-check run-user-setup setup-vapid-keys build-assets run-worker run-server run-triggers precommit release serve-site serve-locust-report test load-test

help:
	@printf "Available targets:\n"
	@printf "  make help\t\t\t\t\t\tShow this help message\n"
	@printf "  make build-assets\t\t\t\t\tRun the assets build script\n"
	@printf "  make generate-vapid-keys\t\t\t\tRun the VAPID keys generation script\n"
	@printf "  make load-test HOST=<host> USERS=<users> SPAWN_RATE=<spawn_rate> DURATION=<duration>\tRun Locust load tests with specified parameters\n"
	@printf "  make migration-check\t\t\t\t\tShow current Alembic database revision from $(APP_DIR) folder\n"
	@printf "  make migration-create msg=\"<message>\"\t\t\tCreate a new Alembic migration in $(APP_DIR) folder\n"
	@printf "  make precommit\t\t\t\t\tRun pre-commit checks on all Python files in $(APP_DIR) folder\n"
	@printf "  make release VERSION=<version> PUSH=<true|false>\tCreate a new git commit and tag for release. Optionally push to remote repository\n"
	@printf "  make run-triggers\t\t\t\t\tRun the triggers setup script\n"
	@printf "  make run-migrations\t\t\t\t\tRun Alembic migration upgrade script\n"
	@printf "  make run-scheduler\t\t\t\t\tRun the Celery beat\n"
	@printf "  make run-server\t\t\t\t\tRun the server\n"
	@printf "  make run-user-setup\t\t\t\t\tRun superadmin user setup script\n"
	@printf "  make run-worker\t\t\t\t\tRun the Celery worker\n"
	@printf "  make serve-locust-report\t\t\t\tServe the latest Locust load test report\n"
	@printf "  make serve-site\t\t\t\t\tRun the feedbase landing site\n"
	@printf "  make test\t\t\t\t\t\tRun tests with pytest\n"

build-assets:
	@cd $(APP_DIR) && $(ACTIVATE) && bin/build_assets

generate-vapid-keys: 
	@cd $(APP_DIR) && $(ACTIVATE) && bin/generate_vapid_keys

generate-changelog:
	@cd $(APP_DIR) && $(ACTIVATE) && $(UV) run git-changelog \
		--bump $(VERSION) \
		--convention conventional \
		--output ../CHANGELOG.md \
		.

migration-check:
	@cd $(APP_DIR) && $(ACTIVATE) && $(ALEMBIC) -c $(ALEMBIC_INI) current

migration-create:
	@cd $(APP_DIR) && $(ACTIVATE) && $(ALEMBIC) -c $(ALEMBIC_INI) revision --autogenerate -m "$(msg)"

load-test:
	@cd $(APP_DIR) && $(ACTIVATE) && mkdir -p load_tests/reports
	@cd $(APP_DIR) && $(ACTIVATE) && python -m locust -f load_tests/locustfile.py --host $${HOST:-http://localhost:5555} --headless -u $${USERS:-100} -r $${SPAWN_RATE:-10} --run-time $${DURATION:-1m} --html load_tests/reports/index.html

precommit:
	@cd $(APP_DIR) && $(ACTIVATE) && cd .. && pre-commit run --files $(APP_DIR)/**/*.py

run-benchmark:
	@cd $(APP_DIR) && $(ACTIVATE) && pytest --benchmark-only --benchmark-autosave --benchmark-save=latest

run-migrations:
	@cd $(APP_DIR) && $(ACTIVATE) && bin/run_migrations

run-scheduler:
	@cd $(APP_DIR) && $(ACTIVATE) && bin/run_scheduler

run-server:
	@cd $(APP_DIR) && $(ACTIVATE) && bin/run_server

run-user-setup:
	@cd $(APP_DIR) && $(ACTIVATE) && bin/run_user_setup

run-triggers:
	@cd $(APP_DIR) && $(ACTIVATE) && bin/run_triggers

run-worker:
	@cd $(APP_DIR) && $(ACTIVATE) && bin/run_worker

serve-site:
	@$(PYTHON) -m http.server --directory site 5556

serve-locust-report:
	@$(PYTHON) -m http.server --directory $(APP_DIR)/load_tests/reports 5557

test:
	@cd $(APP_DIR) && $(ACTIVATE) && pytest -n auto --benchmark-skip

test-cov:
	@cd $(APP_DIR) && $(ACTIVATE) && mkdir -p coverage && pytest --benchmark-skip --cov=. --cov-report=html:coverage/htmlcov --cov-report=xml:coverage/coverage.xml

release:
	@git add .
	@git commit -m "chore(release): $(VERSION)"
	@git tag $(VERSION)
ifeq ($(PUSH),true)
	@git push
	@git push --tags
else
	@printf "PUSH is false, skipping git push. To push, run: make release VERSION=$(VERSION) PUSH=true\n"
endif

