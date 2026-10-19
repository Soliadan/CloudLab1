
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    parfume_name TEXT NOT NULL,
    volume TEXT NOT NULL,
    brand TEXT NOT NULL,
    order_date TEXT NOT NULL,
    price INTEGER NOT NULL
);
