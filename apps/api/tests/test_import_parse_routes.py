import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_connection, init_schema
from app.main import app
from app.repositories.import_repository import create_import_session, list_import_rows
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


def _create_session(client: TestClient, raw_input: str) -> int:
    resp = client.post("/api/imports", json={"raw_input": raw_input})
    return resp.json()["id"]


def test_parse_returns_rows(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_session(client, raw)

    resp = client.post(f"/api/imports/{session_id}/parse")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["rows"]) == 5


def test_parse_titles_match_fixture(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    expected = json.loads((FIXTURES_DIR / "read_list_expected.json").read_text())
    session_id = _create_session(client, raw)

    resp = client.post(f"/api/imports/{session_id}/parse")
    rows = resp.json()["rows"]

    for row, exp in zip(rows, expected):
        parsed = json.loads(row["parsed_json"])
        assert parsed["title"] == exp["title"]


def test_parse_rows_persisted(client: TestClient, conn: sqlite3.Connection):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_session(client, raw)

    client.post(f"/api/imports/{session_id}/parse")

    db_rows = list_import_rows(conn, session_id)
    assert len(db_rows) == 5
    assert db_rows[0].parsed_json is not None
    assert db_rows[0].normalized_json is None


def test_parse_session_counts_update(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_session(client, raw)

    resp = client.post(f"/api/imports/{session_id}/parse")
    session = resp.json()["session"]

    assert session["expected_count"] == 5
    assert session["extracted_count"] == 5
    assert session["status"] == "parsed"


def test_parse_compact_page_fixture(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_page_raw.txt").read_text()
    expected = json.loads((FIXTURES_DIR / "read_list_page_expected.json").read_text())
    session_id = _create_session(client, raw)

    resp = client.post(f"/api/imports/{session_id}/parse")
    data = resp.json()

    assert data["session"]["expected_count"] == len(expected)
    assert data["session"]["extracted_count"] == len(expected)
    assert json.loads(data["rows"][0]["parsed_json"])["title"] == expected[0]["title"]


def test_parse_idempotent(client: TestClient, conn: sqlite3.Connection):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_session(client, raw)

    client.post(f"/api/imports/{session_id}/parse")
    client.post(f"/api/imports/{session_id}/parse")

    db_rows = list_import_rows(conn, session_id)
    assert len(db_rows) == 5  # not 10


def test_parse_missing_session_returns_404(client: TestClient):
    resp = client.post("/api/imports/99999/parse")
    assert resp.status_code == 404


def test_parse_empty_input_returns_parse_empty(client: TestClient, conn: sqlite3.Connection):
    # Create session directly via repository to bypass API validation.
    session = create_import_session(conn, raw_input="   ")

    resp = client.post(f"/api/imports/{session.id}/parse")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session"]["status"] == "parse_empty"
    assert data["session"]["expected_count"] == 0
    assert len(data["rows"]) == 0


def test_parse_persists_warning_json_array(client: TestClient, conn: sqlite3.Connection):
    raw = (FIXTURES_DIR / "mixed_noisy_raw.txt").read_text()
    session_id = _create_session(client, raw)

    client.post(f"/api/imports/{session_id}/parse")

    rows = list_import_rows(conn, session_id)
    assert json.loads(rows[0].warnings_json) == []
    assert "missing_rating" in json.loads(rows[1].warnings_json)


def test_parse_mixed_noisy(client: TestClient):
    raw = (FIXTURES_DIR / "mixed_noisy_raw.txt").read_text()
    session_id = _create_session(client, raw)

    resp = client.post(f"/api/imports/{session_id}/parse")
    data = resp.json()

    assert len(data["rows"]) == 6
    assert data["session"]["status"] == "parsed"

    # Check warnings are present
    rows_with_warnings = [r for r in data["rows"] if r["warnings"]]
    assert len(rows_with_warnings) >= 2  # missing_rating, missing_status


def test_parse_row_confidence_and_warnings(client: TestClient):
    raw = (FIXTURES_DIR / "mixed_noisy_raw.txt").read_text()
    session_id = _create_session(client, raw)

    resp = client.post(f"/api/imports/{session_id}/parse")
    rows = resp.json()["rows"]

    # Row 3 is the incomplete entry - should have low confidence
    incomplete_row = rows[3]
    assert incomplete_row["confidence"] < 0.5
    assert "missing_status" in incomplete_row["warnings"]
