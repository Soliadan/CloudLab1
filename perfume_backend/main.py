# app.py
from __future__ import annotations
import os
import json
import uuid
import sqlite3
from typing import Optional
from flask import Flask, request, jsonify, abort, g
from flask_cors import CORS

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "perfume.db"))
SEED_JSON_PATH = os.environ.get("SEED_JSON_PATH", os.path.join(os.path.dirname(__file__), "db.json"))

app = Flask(__name__)
CORS(app)

# ---- DB helpers (sqlite, raw SQL only) ----

def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            parfume_name TEXT NOT NULL,
            Volume TEXT NOT NULL,
            brand TEXT NOT NULL,
            order_date TEXT NOT NULL,
            price INTEGER NOT NULL
        );
        """
    )
    cur = db.execute("SELECT 1 FROM orders LIMIT 1")
    has_any = cur.fetchone() is not None
    if (not has_any) and os.path.exists(SEED_JSON_PATH):
        try:
            with open(SEED_JSON_PATH, encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("orders", []):
                try:
                    db.execute(
                        "INSERT INTO orders (id, parfume_name, Volume, brand, order_date, price) VALUES (?,?,?,?,?,?)",
                        (
                            str(item.get("id") or uuid.uuid4().hex[:4]),
                            str(item.get("parfume_name", "")).strip() or "Unknown",
                            str(item.get("Volume", "")).strip(),
                            str(item.get("brand", "")).strip(),
                            str(item.get("order_date", "")).strip(),
                            int(item.get("price", 0)),
                        ),
                    )
                except Exception:
                    pass
            db.commit()
        except Exception:
            pass
    db.close()


# ---- API ----

@app.get("/")
def root():
    return jsonify({"status": "ok", "service": "perfume-backend", "endpoints": ["/orders"]})


@app.get("/orders")
def list_orders():
    q: Optional[str] = request.args.get("q")
    sort = request.args.get("sort", "")
    order = request.args.get("order", "asc").lower()
    limit = request.args.get("limit", type=int)
    offset = request.args.get("offset", type=int)

    # whitelist sorting columns
    sort_cols = {
        "price": "price",
        "order_date": "order_date",
        "brand": "brand",
        "name": "parfume_name",
        "parfume_name": "parfume_name",
    }
    sort_sql = ""
    if sort in sort_cols:
        dir_sql = "DESC" if order == "desc" else "ASC"
        sort_sql = f" ORDER BY {sort_cols[sort]} {dir_sql}"

    lim_sql = ""
    params = []

    db = get_db()

    if q:
        like = f"%{q}%"
        where_sql = (
            " WHERE LOWER(parfume_name) LIKE LOWER(?)"
            " OR LOWER(Volume) LIKE LOWER(?)"
            " OR LOWER(brand) LIKE LOWER(?)"
            " OR LOWER(order_date) LIKE LOWER(?)"
            " OR CAST(price AS TEXT) LIKE ?"
        )
        params.extend([like, like, like, like, like])
    else:
        where_sql = ""

    base_sql = (
        "SELECT id, parfume_name, Volume, brand, order_date, price FROM orders" + where_sql + sort_sql
    )

    if isinstance(limit, int):
        lim_sql += " LIMIT ?"
        params.append(limit)
        if isinstance(offset, int):
            lim_sql += " OFFSET ?"
            params.append(offset)

    rows = db.execute(base_sql + lim_sql, params).fetchall()
    items = [dict(r) for r in rows]
    return jsonify(items)


@app.get("/orders/<id>")
def get_order(id: str):
    db = get_db()
    row = db.execute(
        "SELECT id, parfume_name, Volume, brand, order_date, price FROM orders WHERE id = ?",
        (id,),
    ).fetchone()
    if not row:
        abort(404, description="Order not found")
    return jsonify(dict(row))


@app.post("/orders")
def create_order():
    data = request.get_json(force=True, silent=True) or {}
    required = ["parfume_name", "Volume", "brand", "order_date", "price"]
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    payload = (
        str(data.get("id") or uuid.uuid4().hex[:4]),
        str(data["parfume_name"]).strip(),
        str(data["Volume"]).strip(),
        str(data["brand"]).strip(),
        str(data["order_date"]).strip(),
        int(data["price"]),
    )

    db = get_db()
    try:
        db.execute(
            "INSERT INTO orders (id, parfume_name, Volume, brand, order_date, price) VALUES (?,?,?,?,?,?)",
            payload,
        )
        db.commit()
        return jsonify({
            "id": payload[0],
            "parfume_name": payload[1],
            "Volume": payload[2],
            "brand": payload[3],
            "order_date": payload[4],
            "price": payload[5],
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "ID already exists"}), 409


@app.patch("/orders/<id>")
@app.put("/orders/<id>")
def update_order(id: str):
    data = request.get_json(force=True, silent=True) or {}
    fields = {k: v for k, v in data.items() if k in {"parfume_name", "Volume", "brand", "order_date", "price"}}
    if not fields:
        return jsonify({"error": "No fields to update"}), 400

    sets = []
    params = []
    for k, v in fields.items():
        sets.append(f"{k} = ?")
        params.append(int(v) if k == "price" else str(v).strip())
    params.append(id)

    db = get_db()
    cur = db.execute(f"UPDATE orders SET {', '.join(sets)} WHERE id = ?", params)
    db.commit()
    if cur.rowcount == 0:
        abort(404, description="Order not found")
    row = db.execute(
        "SELECT id, parfume_name, Volume, brand, order_date, price FROM orders WHERE id = ?",
        (id,),
    ).fetchone()
    return jsonify(dict(row))


@app.delete("/orders/<id>")
def delete_order(id: str):
    db = get_db()
    cur = db.execute("DELETE FROM orders WHERE id = ?", (id,))
    db.commit()
    if cur.rowcount == 0:
        abort(404, description="Order not found")
    return ("", 204)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8088, debug=True)



