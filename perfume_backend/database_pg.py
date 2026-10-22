
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "tasks_db"),
        user=os.getenv("DB_USER", "tasks_user"),
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
        sslmode=os.getenv("DB_SSLMODE", "prefer"),
        row_factory=dict_row
    )


if __name__ == "__main__":
    with get_connection() as conn:
        # Serialize concurrent task starts so CREATE TABLE IF NOT EXISTS cannot
        # race when ECS launches several replicas at once.
        conn.execute("SELECT pg_advisory_xact_lock(20261022)")
        conn.execute(Path(__file__).with_name("schema.sql").read_text())
    print("Schema initialized; existing orders preserved.")
