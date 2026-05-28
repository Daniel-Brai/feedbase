#!/usr/bin/env bash
set -euo pipefail

cd /app

./bin/run_migrations
./bin/run_triggers
./bin/run_user_setup

exec "$@"
