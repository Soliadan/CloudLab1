
import os
import sqlite3
from pathlib import Path

import psycopg
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")

sqlite_db = sqlite3.connect(BASE_DIR / "perfume.db")

orders = sqlite_db.execute("""
    SELECT id, parfume_name, "Volume",
           brand, order_date, price
    FROM orders
""").fetchall()

sqlite_db.close()

with psycopg.connect(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=os.getenv("DB_PORT", "5432"),
    dbname=os.getenv("DB_NAME", "tasks_db"),
    user=os.getenv("DB_USER", "tasks_user"),
    password=os.environ["DB_PASSWORD"]
) as conn:

    for order in orders:
        conn.execute("""
            INSERT INTO orders
            (id, parfume_name, volume, brand, order_date, price)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, order)

print(f"Migration complete! Processed {len(orders)} orders.")
