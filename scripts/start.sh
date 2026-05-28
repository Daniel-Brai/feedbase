#!/bin/bash

set -a
source .env
set +a

if [ "$APP_MONITORING_ENABLED" = "true" ] && [ "$PROMETHEUS_METRICS_ENABLED" = "true" ]; then
  export COMPOSE_PROFILES=monitoring
else
  export COMPOSE_PROFILES=
fi

docker compose up "$@"