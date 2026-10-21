import os
from pathlib import Path
from unittest.mock import patch

import psycopg
import pytest

from perfume_backend.main_pg import app

PAYLOAD = {"parfume_name": "Rose", "Volume": "50ml", "brand": "Lab",
           "order_date": "2026-10-20", "price": 100}


@pytest.fixture
def client():
    return app.test_client()


@pytest.mark.parametrize("data", [None, [], {}, {**PAYLOAD, "price": -1},
    {**PAYLOAD, "price": True}, {**PAYLOAD, "price": 1.5},
    {**PAYLOAD, "brand": None}, {**PAYLOAD, "order_date": "tomorrow"},
    {**PAYLOAD, "unexpected": 1}])
def test_validation(client, data):
    assert client.post("/orders", json=data).status_code == 400


def test_errors(client):
    assert client.get("/missing").is_json
    assert client.post("/health").status_code == 405
    assert client.put("/orders/test", json={"price": 1}).status_code == 400
    assert client.patch("/orders/test", json={"id": "new"}).status_code == 400
    with patch("perfume_backend.main_pg.get_connection", side_effect=psycopg.OperationalError()):
        assert client.get("/health").status_code == 503
        assert client.get("/orders").status_code == 503


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Requires isolated PostgreSQL TEST_DATABASE_URL")
def test_postgres_crud(client, monkeypatch):
    # This test refuses to use the application's existing database credentials.
    url = os.environ["TEST_DATABASE_URL"]
    with psycopg.connect(url) as conn:
        conn.execute(Path("perfume_backend/schema.sql").read_text())
    from psycopg.rows import dict_row
    monkeypatch.setattr("perfume_backend.main_pg.get_connection", lambda: psycopg.connect(url, row_factory=dict_row))
    import uuid
    identity = "test-" + uuid.uuid4().hex
    payload = {**PAYLOAD, "id": identity}
    try:
        assert client.get("/health").status_code == 200
        assert client.post("/orders", json=payload).status_code == 201
        assert client.post("/orders", json=payload).status_code == 409
        assert client.get("/orders/" + identity).json == payload
        assert any(row["id"] == identity for row in client.get("/orders").json)
        assert client.patch("/orders/" + identity, json={"price": 200}).json["price"] == 200
        assert client.put("/orders/" + identity, json=PAYLOAD).json["price"] == 100
        assert client.delete("/orders/" + identity).status_code == 204
        assert client.get("/orders/" + identity).status_code == 404
        assert client.patch("/orders/" + identity, json={"price": 1}).status_code == 404
        assert client.put("/orders/" + identity, json=PAYLOAD).status_code == 404
        assert client.delete("/orders/" + identity).status_code == 404
    finally:
        with psycopg.connect(url) as conn:
            conn.execute("DELETE FROM orders WHERE id = %s", (identity,))
