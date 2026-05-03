import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_connection, init_schema
from app.main import app
from app.repositories.import_repository import get_import_session
from app.repositories.library_repository import get_book
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


def _create_parse_review_accept(client: TestClient, raw: str, titles: list[str] | None = None) -> int:
    resp = client.post("/api/imports", json={"raw_input": raw})
    session_id = resp.json()["id"]
    client.post(f"/api/imports/{session_id}/parse")

    review_resp = client.get(f"/api/imports/{session_id}/review")
    rows = review_resp.json()["rows"]

    actions = []
    for i, row in enumerate(rows):
        title = titles[i] if titles and i < len(titles) else row["parsed_json"].get("title", "")
        actions.append({"row_id": row["row_id"], "action": "accept", "title": title})

    client.post(f"/api/imports/{session_id}/review", json={"rows": actions})
    return session_id


# --- Basic commit ---

def test_commit_creates_books_and_entries(client: TestClient, conn: sqlite3.Connection):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_parse_review_accept(client, raw)

    resp = client.post(f"/api/imports/{session_id}/commit")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["committed"]) == 5
    assert data["session"]["inserted_count"] == 5
    assert data["session"]["status"] == "committed"

    # Verify books exist
    for c in data["committed"]:
        book = get_book(conn, c["book_id"])
        assert book is not None
        assert book.title


def test_commit_source_linkage(client: TestClient, conn: sqlite3.Connection):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_parse_review_accept(client, raw)

    resp = client.post(f"/api/imports/{session_id}/commit")
    committed = resp.json()["committed"]

    # Verify source linkage in DB
    for c in committed:
        row = conn.execute(
            "SELECT * FROM user_book_entries WHERE id = ?", (c["entry_id"],)
        ).fetchone()
        assert row["source_session_id"] == session_id
        assert row["source_row_id"] == c["row_id"]


def test_commit_want_entry_persists_marked_date(
    client: TestClient, conn: sqlite3.Connection
):
    raw = (FIXTURES_DIR / "want_list_page_raw.txt").read_text()
    session_id = _create_parse_review_accept(client, raw)

    resp = client.post(f"/api/imports/{session_id}/commit")
    first_entry_id = resp.json()["committed"][0]["entry_id"]

    row = conn.execute(
        "SELECT status, marked_at FROM user_book_entries WHERE id = ?",
        (first_entry_id,),
    ).fetchone()
    assert row["status"] == "want"
    assert row["marked_at"] == "2026-05-02"


# --- Rejected rows skipped ---

def test_commit_rejected_rows_skipped(client: TestClient, conn: sqlite3.Connection):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    resp = client.post("/api/imports", json={"raw_input": raw})
    session_id = resp.json()["id"]
    client.post(f"/api/imports/{session_id}/parse")

    review_resp = client.get(f"/api/imports/{session_id}/review")
    rows = review_resp.json()["rows"]

    # Accept first, reject second
    client.post(f"/api/imports/{session_id}/review", json={
        "rows": [
            {"row_id": rows[0]["row_id"], "action": "accept", "title": rows[0]["parsed_json"]["title"]},
            {"row_id": rows[1]["row_id"], "action": "reject"},
        ]
    })

    resp = client.post(f"/api/imports/{session_id}/commit")
    data = resp.json()

    assert len(data["committed"]) == 1
    assert len(data["skipped"]) == 4  # 1 rejected + 3 pending

    skipped_ids = {s["row_id"] for s in data["skipped"]}
    assert rows[1]["row_id"] in skipped_ids


# --- Pending rows not committed ---

def test_commit_pending_rows_not_committed(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    resp = client.post("/api/imports", json={"raw_input": raw})
    session_id = resp.json()["id"]
    client.post(f"/api/imports/{session_id}/parse")

    # Commit without review - all rows are pending
    resp = client.post(f"/api/imports/{session_id}/commit")
    data = resp.json()

    assert data["session"]["inserted_count"] == 0
    assert len(data["skipped"]) == 5


# --- Duplicate detection ---

def test_commit_duplicate_same_title_same_author(client: TestClient, conn: sqlite3.Connection):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()

    # First commit
    session_id1 = _create_parse_review_accept(client, raw)
    client.post(f"/api/imports/{session_id1}/commit")

    # Second commit with same data
    session_id2 = _create_parse_review_accept(client, raw)
    resp = client.post(f"/api/imports/{session_id2}/commit")
    data = resp.json()

    # All 5 rows should be duplicates (reuse existing books)
    assert len(data["duplicates"]) == 5
    assert len(data["committed"]) == 5  # entries still created
    assert data["session"]["duplicate_count"] == 5


def test_commit_same_title_different_author_creates_new_book(client: TestClient, conn: sqlite3.Connection):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()

    # First commit
    session_id1 = _create_parse_review_accept(client, raw)
    client.post(f"/api/imports/{session_id1}/commit")

    # Second session, only accept first row with different author
    resp = client.post("/api/imports", json={"raw_input": raw})
    session_id2 = resp.json()["id"]
    client.post(f"/api/imports/{session_id2}/parse")

    review_resp = client.get(f"/api/imports/{session_id2}/review")
    rows = review_resp.json()["rows"]

    # Accept only first row with different author, reject rest
    client.post(f"/api/imports/{session_id2}/review", json={
        "rows": [
            {"row_id": rows[0]["row_id"], "action": "accept", "title": "思考，快与慢", "authors": ["不同作者"]},
            {"row_id": rows[1]["row_id"], "action": "reject"},
            {"row_id": rows[2]["row_id"], "action": "reject"},
            {"row_id": rows[3]["row_id"], "action": "reject"},
            {"row_id": rows[4]["row_id"], "action": "reject"},
        ]
    })

    resp = client.post(f"/api/imports/{session_id2}/commit")
    data = resp.json()

    # First row should create new book (different author)
    assert len(data["committed"]) == 1
    assert len(data["duplicates"]) == 0

    # Verify new book was created with different author
    new_book = get_book(conn, data["committed"][0]["book_id"])
    assert new_book.title == "思考，快与慢"
    assert "不同作者" in new_book.authors_json


# --- 409 on re-commit ---

def test_commit_already_committed_returns_409(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    session_id = _create_parse_review_accept(client, raw)
    client.post(f"/api/imports/{session_id}/commit")

    resp = client.post(f"/api/imports/{session_id}/commit")
    assert resp.status_code == 409


# --- 404 on missing session ---

def test_commit_missing_session_returns_404(client: TestClient):
    resp = client.post("/api/imports/99999/commit")
    assert resp.status_code == 404


# --- No accepted rows ---

def test_commit_no_accepted_returns_zero(client: TestClient):
    raw = (FIXTURES_DIR / "read_list_raw.txt").read_text()
    resp = client.post("/api/imports", json={"raw_input": raw})
    session_id = resp.json()["id"]
    client.post(f"/api/imports/{session_id}/parse")

    review_resp = client.get(f"/api/imports/{session_id}/review")
    rows = review_resp.json()["rows"]

    # Reject all
    client.post(f"/api/imports/{session_id}/review", json={
        "rows": [{"row_id": r["row_id"], "action": "reject"} for r in rows]
    })

    resp = client.post(f"/api/imports/{session_id}/commit")
    data = resp.json()

    assert data["session"]["inserted_count"] == 0
    assert len(data["committed"]) == 0
    assert len(data["skipped"]) == 5
    assert data["session"]["status"] == "committed"
