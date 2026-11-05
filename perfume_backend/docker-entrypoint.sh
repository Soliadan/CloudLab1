#!/bin/sh
set -eu

# готує все перед запуском
# маленький скрипт, який працює перед запуском Flask
#вперше запуска лабу, але таблиці для парфумів у PostgreSQL ще немає
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
