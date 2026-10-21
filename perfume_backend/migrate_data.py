"""Explicit SQLite import; requires owner approval before execution on real data."""
import sqlite3
from contextlib import closing
from pathlib import Path

try:
    from perfume_backend.database_pg import get_connection
except ModuleNotFoundError:
    from database_pg import get_connection


def main():
    source = Path(__file__).with_name('perfume.db')
    # Read-only URI prevents accidental creation or mutation of the source file.
    with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as sqlite_db:
        orders = sqlite_db.execute('SELECT id, parfume_name, "Volume", brand, order_date, price FROM orders').fetchall()
    with get_connection() as conn:
        for order in orders:
            conn.execute('''INSERT INTO orders (id, parfume_name, volume, brand, order_date, price)
                            VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING''', order)
    print(f'Migration complete: processed {len(orders)} source rows; existing IDs preserved.')


if __name__ == '__main__':
    main()
