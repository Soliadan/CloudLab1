import os
from pathlib import Path
import uuid
from datetime import date

import psycopg
from werkzeug.exceptions import HTTPException

from flask import Flask, request, jsonify, abort, send_file
from psycopg.errors import UniqueViolation

try:
    from perfume_backend.database_pg import get_connection
except ModuleNotFoundError as exc:
    if exc.name != "perfume_backend":
        raise
    from database_pg import get_connection

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 65536

app.json.compact = False
app.json.ensure_ascii = False

COLUMNS = 'id, parfume_name, volume AS "Volume", brand, order_date, price'
APP_VERSION = os.getenv("APP_VERSION", "dev")


@app.get("/")
def home():
    return send_file(Path(__file__).with_name("index.html"))


@app.get("/health")
def health():
    with get_connection() as conn:
        conn.execute("SELECT 1 FROM orders LIMIT 0")
    return (
        jsonify({"status": "ok", "version": APP_VERSION}),
        200,
        {"X-App-Version": APP_VERSION},
    )


@app.get("/orders")
def get_orders():
    query = f"SELECT {COLUMNS} FROM orders ORDER BY order_date DESC, id"

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

    data = validate_payload(data, complete=True, allow_id=True)
    values = (data.get("id", uuid.uuid4().hex), data["parfume_name"],
              data["Volume"], data["brand"], data["order_date"], data["price"])

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

    fields = validate_payload(data, complete=request.method == "PUT")
    values = list(fields.values())

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


def validate_payload(data, complete=False, allow_id=False):
    required = {"parfume_name", "Volume", "brand", "order_date", "price"}
    allowed = required | ({"id"} if allow_id else set())
    if not isinstance(data, dict) or not data:
        abort(400, description="Expected a nonempty JSON object")
    if set(data) - allowed or (complete and required - set(data)):
        abort(400, description="Unknown or missing fields")
    for key, value in data.items():
        if key == "price":
            if type(value) is not int or not 0 <= value <= 2147483647:
                abort(400, description="price must be a nonnegative 32-bit integer")
        elif not isinstance(value, str) or not value.strip() or len(value) > 255:
            abort(400, description=f"{key} must be a nonempty string, at most 255 characters")
    if "order_date" in data:
        try:
            if date.fromisoformat(data["order_date"]).isoformat() != data["order_date"]:
                raise ValueError()
        except ValueError:
            abort(400, description="order_date must be YYYY-MM-DD")
    return data


@app.errorhandler(HTTPException)
def http_error(exc):
    response = exc.get_response()
    response.data = app.json.dumps({"error": exc.description})
    response.content_type = "application/json"
    return response


@app.errorhandler(psycopg.Error)
def database_error(exc):
    app.logger.error("Database operation failed: %s", type(exc).__name__)
    return jsonify(error="Database unavailable or operation failed"), 503


@app.errorhandler(Exception)
def unexpected_error(exc):
    app.logger.error("Unexpected error: %s", type(exc).__name__)
    return jsonify(error="Internal server error"), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8088, debug=False)
