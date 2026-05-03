import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_connection, init_schema
from app.main import app
from app.repositories.import_repository import get_import_row, get_import_session
from app.routes.imports import get_db

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "douban_paste"


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


def _create_and_parse(client: TestClient, raw: str) -> int:
    resp = client.post("/api/imports", json={"raw_input": raw})
    session_id = resp.json()["id"]
    client.post(f"/api/imports/{session_id}/parse")
    return session_id


def _get_first_row_id(client: TestClient, session_id: int) -> int:
    resp = client.get(f"/api/imports/{session_id}/review")
    return resp.json()["rows"][0]["row_id"]


# --- GET /review ---

def test_get_review_returns_rows(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_and_parse(client, raw)

    resp = client.get(f"/api/imports/{session_id}/review")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["rows"]) == 5
    assert data["rows"][0]["status"] == "pending"


def test_get_review_parses_json(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_and_parse(client, raw)

    resp = client.get(f"/api/imports/{session_id}/review")
    rows = resp.json()["rows"]
    assert rows[0]["parsed_json"]["title"] == "思考，快与慢"


def test_get_review_missing_session_returns_404(client: TestClient):
    resp = client.get("/api/imports/99999/review")
    assert resp.status_code == 404


# --- POST /review accept ---

def test_review_accept_updates_row_status(client: TestClient, conn: sqlite3.Connection):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_and_parse(client, raw)
    row_id = _get_first_row_id(client, session_id)

    resp = client.post(f"/api/imports/{session_id}/review", json={
        "rows": [{"row_id": row_id, "action": "accept", "title": "思考，快与慢", "authors": ["丹尼尔·卡尼曼"], "status": "read"}]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["updated_rows"][0]["status"] == "accepted"

    # Verify DB
    row = get_import_row(conn, row_id)
    assert row.status == "accepted"


def test_review_accept_updates_parsed_json(client: TestClient, conn: sqlite3.Connection):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_and_parse(client, raw)
    row_id = _get_first_row_id(client, session_id)

    client.post(f"/api/imports/{session_id}/review", json={
        "rows": [{"row_id": row_id, "action": "accept", "title": "修改后的标题", "authors": ["新作者"], "rating": 9.0, "comment": "很棒"}]
    })

    row = get_import_row(conn, row_id)
    parsed = json.loads(row.parsed_json)
    assert parsed["title"] == "修改后的标题"
    assert parsed["authors"] == ["新作者"]
    assert parsed["rating"] == 9.0
    assert parsed["comment"] == "很棒"


def test_review_accept_empty_title_returns_422(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_and_parse(client, raw)
    row_id = _get_first_row_id(client, session_id)

    resp = client.post(f"/api/imports/{session_id}/review", json={
        "rows": [{"row_id": row_id, "action": "accept", "title": ""}]
    })
    assert resp.status_code == 422


def test_review_invalid_action_returns_422(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_and_parse(client, raw)
    row_id = _get_first_row_id(client, session_id)

    resp = client.post(f"/api/imports/{session_id}/review", json={
        "rows": [{"row_id": row_id, "action": "banana", "title": "test"}]
    })
    assert resp.status_code == 422


# --- POST /review reject ---

def test_review_reject_updates_row_status(client: TestClient, conn: sqlite3.Connection):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_and_parse(client, raw)
    row_id = _get_first_row_id(client, session_id)

    resp = client.post(f"/api/imports/{session_id}/review", json={
        "rows": [{"row_id": row_id, "action": "reject"}]
    })
    assert resp.status_code == 200
    assert resp.json()["updated_rows"][0]["status"] == "rejected"

    row = get_import_row(conn, row_id)
    assert row.status == "rejected"


# --- POST /review needs_edit ---

def test_review_needs_edit_updates_row_status(client: TestClient, conn: sqlite3.Connection):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_and_parse(client, raw)
    row_id = _get_first_row_id(client, session_id)

    resp = client.post(f"/api/imports/{session_id}/review", json={
        "rows": [{"row_id": row_id, "action": "needs_edit", "title": "需要修改的标题"}]
    })
    assert resp.status_code == 200
    assert resp.json()["updated_rows"][0]["status"] == "needs_edit"

    row = get_import_row(conn, row_id)
    assert row.status == "needs_edit"


# --- Validation ---

def test_review_invalid_row_id_returns_422(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_and_parse(client, raw)

    # Use a row_id that doesn't belong to this session
    resp = client.post(f"/api/imports/{session_id}/review", json={
        "rows": [{"row_id": 99999, "action": "accept", "title": "test"}]
    })
    assert resp.status_code == 422


def test_review_row_id_from_other_session_returns_422(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_and_parse(client, raw)
    other_session_id = _create_and_parse(client, raw)
    other_row_id = _get_first_row_id(client, other_session_id)

    resp = client.post(f"/api/imports/{session_id}/review", json={
        "rows": [{"row_id": other_row_id, "action": "accept", "title": "test"}]
    })
    assert resp.status_code == 422


def test_review_missing_session_returns_404(client: TestClient):
    resp = client.post("/api/imports/99999/review", json={
        "rows": [{"row_id": 1, "action": "accept", "title": "test"}]
    })
    assert resp.status_code == 404


# --- Session status ---

def test_review_updates_session_status(client: TestClient, conn: sqlite3.Connection):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_and_parse(client, raw)
    row_id = _get_first_row_id(client, session_id)

    client.post(f"/api/imports/{session_id}/review", json={
        "rows": [{"row_id": row_id, "action": "accept", "title": "test"}]
    })

    session = get_import_session(conn, session_id)
    assert session.status == "reviewed"


# --- Multiple rows ---

def test_review_multiple_rows(client: TestClient, conn: sqlite3.Connection):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_and_parse(client, raw)

    resp = client.get(f"/api/imports/{session_id}/review")
    rows = resp.json()["rows"]

    client.post(f"/api/imports/{session_id}/review", json={
        "rows": [
            {"row_id": rows[0]["row_id"], "action": "accept", "title": rows[0]["parsed_json"]["title"]},
            {"row_id": rows[1]["row_id"], "action": "reject"},
            {"row_id": rows[2]["row_id"], "action": "needs_edit", "title": "edit me"},
        ]
    })

    resp = client.get(f"/api/imports/{session_id}/review")
    updated = {r["row_id"]: r["status"] for r in resp.json()["rows"]}
    assert updated[rows[0]["row_id"]] == "accepted"
    assert updated[rows[1]["row_id"]] == "rejected"
    assert updated[rows[2]["row_id"]] == "needs_edit"
