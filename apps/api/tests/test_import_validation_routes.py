import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_connection, init_schema
from app.main import app
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


def _create_parse_review_accept(client: TestClient, raw: str) -> int:
    resp = client.post("/api/imports", json={"raw_input": raw})
    session_id = resp.json()["id"]
    client.post(f"/api/imports/{session_id}/parse")

    review_resp = client.get(f"/api/imports/{session_id}/review")
    rows = review_resp.json()["rows"]

    actions = [
        {"row_id": r["row_id"], "action": "accept", "title": r["parsed_json"].get("title", "")}
        for r in rows
    ]
    client.post(f"/api/imports/{session_id}/review", json={"rows": actions})
    return session_id


# --- 404 ---

def test_validate_missing_session_returns_404(client: TestClient):
    resp = client.get("/api/imports/99999/validate")
    assert resp.status_code == 404


# --- Fresh parsed session ---

def test_validate_parsed_session_counts(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    resp = client.post("/api/imports", json={"raw_input": raw})
    session_id = resp.json()["id"]
    client.post(f"/api/imports/{session_id}/parse")

    resp = client.get(f"/api/imports/{session_id}/validate")
    assert resp.status_code == 200
    data = resp.json()

    assert data["parsed_count"] == 5
    assert data["accepted_count"] == 0
    assert data["rejected_count"] == 0
    assert data["committed_count"] == 0
    assert len(data["rows"]) == 5


def test_validate_parsed_rows_have_titles(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    resp = client.post("/api/imports", json={"raw_input": raw})
    session_id = resp.json()["id"]
    client.post(f"/api/imports/{session_id}/parse")

    resp = client.get(f"/api/imports/{session_id}/validate")
    rows = resp.json()["rows"]

    assert rows[0]["title"] == "思考，快与慢"
    assert rows[0]["status"] == "pending"
    assert rows[0]["book_id"] is None
    assert rows[0]["entry_id"] is None


# --- Reviewed session ---

def test_validate_reviewed_session_counts(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    resp = client.post("/api/imports", json={"raw_input": raw})
    session_id = resp.json()["id"]
    client.post(f"/api/imports/{session_id}/parse")

    review_resp = client.get(f"/api/imports/{session_id}/review")
    rows = review_resp.json()["rows"]

    # Accept 3, reject 1, needs_edit 1
    client.post(f"/api/imports/{session_id}/review", json={
        "rows": [
            {"row_id": rows[0]["row_id"], "action": "accept", "title": "A"},
            {"row_id": rows[1]["row_id"], "action": "accept", "title": "B"},
            {"row_id": rows[2]["row_id"], "action": "accept", "title": "C"},
            {"row_id": rows[3]["row_id"], "action": "reject"},
            {"row_id": rows[4]["row_id"], "action": "needs_edit", "title": "E"},
        ]
    })

    resp = client.get(f"/api/imports/{session_id}/validate")
    data = resp.json()

    assert data["parsed_count"] == 5
    assert data["accepted_count"] == 3
    assert data["rejected_count"] == 1
    assert data["needs_edit_count"] == 1


# --- Committed session ---

def test_validate_committed_session_counts(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_parse_review_accept(client, raw)
    client.post(f"/api/imports/{session_id}/commit")

    resp = client.get(f"/api/imports/{session_id}/validate")
    data = resp.json()

    assert data["parsed_count"] == 5
    assert data["accepted_count"] == 5
    assert data["committed_count"] == 5
    assert data["rejected_count"] == 0


def test_validate_committed_rows_have_book_and_entry_ids(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_parse_review_accept(client, raw)
    client.post(f"/api/imports/{session_id}/commit")

    resp = client.get(f"/api/imports/{session_id}/validate")
    rows = resp.json()["rows"]

    for row in rows:
        assert row["book_id"] is not None
        assert row["entry_id"] is not None
        assert row["status"] == "committed"


# --- Duplicate ---

def test_validate_duplicate_commit_reports_duplicate_count(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()

    # First commit
    session_id1 = _create_parse_review_accept(client, raw)
    client.post(f"/api/imports/{session_id1}/commit")

    # Second commit (all duplicates)
    session_id2 = _create_parse_review_accept(client, raw)
    client.post(f"/api/imports/{session_id2}/commit")

    resp = client.get(f"/api/imports/{session_id2}/validate")
    data = resp.json()

    assert data["duplicate_count"] == 5
    assert data["committed_count"] == 5


# --- Warnings ---

def test_validate_warning_rows_contribute_to_count(client: TestClient):
    raw = (FIXTURES_DIR / "mixed_noisy_raw.txt").read_text()
    resp = client.post("/api/imports", json={"raw_input": raw})
    session_id = resp.json()["id"]
    client.post(f"/api/imports/{session_id}/parse")

    resp = client.get(f"/api/imports/{session_id}/validate")
    data = resp.json()

    assert data["warning_count"] > 0
    # Check that rows with warnings have them listed
    warning_rows = [r for r in data["rows"] if r["warnings"]]
    assert len(warning_rows) > 0


def test_validate_empty_parse_keeps_session_warning_count(client: TestClient, conn: sqlite3.Connection):
    from app.repositories.import_repository import create_import_session

    session = create_import_session(conn, raw_input="   ")
    client.post(f"/api/imports/{session.id}/parse")

    resp = client.get(f"/api/imports/{session.id}/validate")
    data = resp.json()

    assert data["parsed_count"] == 0
    assert data["warning_count"] == 1


def test_validate_invalid_json_does_not_crash(client: TestClient, conn: sqlite3.Connection):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    resp = client.post("/api/imports", json={"raw_input": raw})
    session_id = resp.json()["id"]
    client.post(f"/api/imports/{session_id}/parse")

    row_id = client.get(f"/api/imports/{session_id}/review").json()["rows"][0]["row_id"]
    conn.execute(
        "UPDATE import_rows SET parsed_json = ?, warnings_json = ? WHERE id = ?",
        ("{not-json", "{bad-warnings", row_id),
    )
    conn.commit()

    resp = client.get(f"/api/imports/{session_id}/validate")
    row = resp.json()["rows"][0]

    assert resp.status_code == 200
    assert "invalid_parsed_json" in row["warnings"]
    assert "invalid_warnings_json" in row["warnings"]
    assert resp.json()["warning_count"] >= 2


# --- Hash ---

def test_validate_returns_raw_input_hash(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    resp = client.post("/api/imports", json={"raw_input": raw})
    session_id = resp.json()["id"]
    client.post(f"/api/imports/{session_id}/parse")

    resp = client.get(f"/api/imports/{session_id}/validate")
    data = resp.json()

    assert len(data["raw_input_hash"]) == 64  # SHA-256 hex
