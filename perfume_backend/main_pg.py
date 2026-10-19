
import uuid

from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from psycopg.errors import UniqueViolation

try:
    from perfume_backend.database_pg import get_connection
except ModuleNotFoundError as exc:
    if exc.name != "perfume_backend":
        raise
    from database_pg import get_connection

app = Flask(__name__)
CORS(app)
app.json.compact = False
app.json.ensure_ascii = False

COLUMNS = 'id, parfume_name, volume AS "Volume", brand, order_date, price'


@app.get("/")
def home():
    return jsonify({
        "service": "perfume-backend",
        "status": "ok"
    })


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/orders")
def get_orders():
    query = f"SELECT {COLUMNS} FROM orders"

    with get_connection() as conn:
        orders = conn.execute(query).fetchall()

    return jsonify(orders)


@app.get("/orders/<id>")
def get_order(id):
    with get_connection() as conn:
        order = conn.execute(
            f"SELECT {COLUMNS} FROM orders WHERE id = %s",
            (id,)
        ).fetchone()

    if order is None:
        abort(404, description="Order not found")

    return jsonify(order)


@app.post("/orders")
def create_order():
    data = request.get_json(silent=True)

    required = ["parfume_name", "Volume", "brand",
                "order_date", "price"]

    if not isinstance(data, dict) or any(
        field not in data for field in required
    ):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        values = (
            str(data.get("id") or uuid.uuid4().hex[:8]),
            str(data["parfume_name"]),
            str(data["Volume"]),
            str(data["brand"]),
            str(data["order_date"]),
            int(data["price"])
        )
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid price"}), 400

    try:
        with get_connection() as conn:
            order = conn.execute(
                f"""
                INSERT INTO orders
                (id, parfume_name, volume, brand, order_date, price)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING {COLUMNS}
                """,
                values
            ).fetchone()
    except UniqueViolation:
        return jsonify({"error": "ID already exists"}), 409

    return jsonify(order), 201


@app.route("/orders/<id>", methods=["PUT", "PATCH"])
def update_order(id):
    data = request.get_json(silent=True)

    allowed = {
        "parfume_name": "parfume_name",
        "Volume": "volume",
        "brand": "brand",
        "order_date": "order_date",
        "price": "price"
    }

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON"}), 400

    fields = {k: v for k, v in data.items() if k in allowed}

    if not fields:
        return jsonify({"error": "No fields to update"}), 400

    try:
        values = [
            int(value) if key == "price" else str(value)
            for key, value in fields.items()
        ]
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid price"}), 400

    assignments = ", ".join(
        f"{allowed[key]} = %s" for key in fields
    )

    with get_connection() as conn:
        order = conn.execute(
            f"""
            UPDATE orders SET {assignments}
            WHERE id = %s
            RETURNING {COLUMNS}
            """,
            values + [id]
        ).fetchone()

    if order is None:
        abort(404, description="Order not found")

    return jsonify(order)


@app.delete("/orders/<id>")
def delete_order(id):
    with get_connection() as conn:
        deleted = conn.execute(
            "DELETE FROM orders WHERE id = %s RETURNING id",
            (id,)
        ).fetchone()

    if deleted is None:
        abort(404, description="Order not found")

    return "", 204


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8088, debug=False)
