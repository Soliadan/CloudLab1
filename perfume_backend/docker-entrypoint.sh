#!/bin/sh
set -eu

# Apply the idempotent schema before the API starts. This makes a fresh RDS
# instance (or a new compose volume) usable without a manual one-off ECS task.
attempt=0
until python database_pg.py; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 30 ]; then
        echo "Database schema initialization failed after $attempt attempts" >&2
        exit 1
    fi
    echo "Database not ready (attempt $attempt/30); retrying in 2s" >&2
    sleep 2
done

exec "$@"
