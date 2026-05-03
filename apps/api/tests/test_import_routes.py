import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_connection, init_schema
from app.main import app
from app.routes.imports import get_db


@pytest.fixture
def conn(tmp_path: Path):
    db_path = tmp_path / "test.db"
    c = get_connection(db_path)
    init_schema(c)
    yield c
    c.close()


@pytest.fixture
def client(conn: sqlite3.Connection):
    def override_get_db():
        yield conn

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_create_import_returns_dto(client: TestClient):
    resp = client.post(
        "/api/imports",
        json={"source": "douban", "raw_input": "book A2026-01-01"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] is not None
    assert data["source"] == "douban"
    assert data["status"] == "pending"
    assert "raw_hash" in data
    assert "created_at" in data
    assert "raw_input" not in data


def test_create_import_persists_raw_input(client: TestClient, conn: sqlite3.Connection):
    raw = "  book A2026-01-01\nbook B 2026-02-02  "
    resp = client.post("/api/imports", json={"raw_input": raw})
    assert resp.status_code == 201
    session_id = resp.json()["id"]

    stored = conn.execute(
        "SELECT raw_input FROM import_sessions WHERE id = ?", (session_id,)
    ).fetchone()
    assert stored["raw_input"] == raw


def test_create_import_rejects_empty_input(client: TestClient):
    resp = client.post("/api/imports", json={"raw_input": ""})
    assert resp.status_code == 422


def test_create_import_rejects_whitespace_input(client: TestClient):
    resp = client.post("/api/imports", json={"raw_input": "   \n\t  "})
    assert resp.status_code == 422


def test_get_import_returns_404(client: TestClient):
    resp = client.get("/api/imports/99999")
    assert resp.status_code == 404


def test_create_and_get_roundtrip(client: TestClient):
    raw = "怎样选择成长股2026-05-02"
    create_resp = client.post(
        "/api/imports", json={"source": "douban", "raw_input": raw}
    )
    session_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/imports/{session_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == session_id
    assert data["source"] == "douban"
    assert data["raw_hash"] == create_resp.json()["raw_hash"]
