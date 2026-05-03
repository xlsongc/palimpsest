import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_connection, init_schema
from app.main import app
from app.repositories.graph_repository import get_all_edges
from app.repositories.import_repository import create_import_session, add_import_row
from app.repositories.library_repository import create_book, create_user_book_entry
from app.routes.graph import get_db
from app.services.graph_builder_service import rebuild_graph_edges


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


def _create_session_and_rows(conn: sqlite3.Connection, count: int = 4) -> int:
    """Create import session and rows for FK references."""
    session = create_import_session(conn, raw_input="test data")
    for i in range(count):
        add_import_row(conn, session_id=session.id, row_index=i, raw_fragment=f"row {i}")
    return session.id


def _seed_two_books_same_author(conn: sqlite3.Connection) -> tuple[int, int]:
    session_id = _create_session_and_rows(conn, 2)
    b1 = create_book(conn, title="Book A", authors=["Author X"])
    b2 = create_book(conn, title="Book B", authors=["Author X"])
    create_user_book_entry(conn, book_id=b1.id, source_session_id=session_id, source_row_id=1, status="read")
    create_user_book_entry(conn, book_id=b2.id, source_session_id=session_id, source_row_id=2, status="read")
    return b1.id, b2.id


def _seed_two_books_same_tag(conn: sqlite3.Connection) -> tuple[int, int]:
    session_id = _create_session_and_rows(conn, 4)
    b1 = create_book(conn, title="Book C", authors=["Author Y"])
    b2 = create_book(conn, title="Book D", authors=["Author Z"])
    create_user_book_entry(conn, book_id=b1.id, source_session_id=session_id, source_row_id=3, status="read", tags=["投资"])
    create_user_book_entry(conn, book_id=b2.id, source_session_id=session_id, source_row_id=4, status="read", tags=["投资"])
    return b1.id, b2.id


# --- Edge builder tests ---

def test_same_author_creates_edge(conn: sqlite3.Connection):
    b1_id, b2_id = _seed_two_books_same_author(conn)
    edges = rebuild_graph_edges(conn)

    same_author_edges = [e for e in edges if e.source_book_id == min(b1_id, b2_id)]
    assert len(same_author_edges) == 1
    # Weight is 5 (same_author) + 1 (same_status) = 6 since both are "read"
    assert same_author_edges[0].weight >= 5.0
    assert "same_author" in same_author_edges[0].edge_type


def test_same_tag_creates_edge(conn: sqlite3.Connection):
    b1_id, b2_id = _seed_two_books_same_tag(conn)
    edges = rebuild_graph_edges(conn)

    # Should have at least one edge with shared tag
    tag_edges = [e for e in edges if "tag" in e.reason.lower()]
    assert len(tag_edges) >= 1
    assert tag_edges[0].weight >= 3.0


def test_same_status_alone_does_not_create_edge(conn: sqlite3.Connection):
    session_id = _create_session_and_rows(conn, 2)
    b1 = create_book(conn, title="Book E", authors=["Author E"])
    b2 = create_book(conn, title="Book F", authors=["Author F"])
    create_user_book_entry(conn, book_id=b1.id, source_session_id=session_id, source_row_id=1, status="read")
    create_user_book_entry(conn, book_id=b2.id, source_session_id=session_id, source_row_id=2, status="read")

    edges = rebuild_graph_edges(conn)

    assert edges == []


def test_same_rating_alone_does_not_create_edge(conn: sqlite3.Connection):
    session_id = _create_session_and_rows(conn, 2)
    b1 = create_book(conn, title="Book E", authors=["Author E"])
    b2 = create_book(conn, title="Book F", authors=["Author F"])
    create_user_book_entry(conn, book_id=b1.id, source_session_id=session_id, source_row_id=1, rating=8.0)
    create_user_book_entry(conn, book_id=b2.id, source_session_id=session_id, source_row_id=2, rating=8.0)

    edges = rebuild_graph_edges(conn)

    assert edges == []


def test_rebuild_is_idempotent(conn: sqlite3.Connection):
    _seed_two_books_same_author(conn)
    edges1 = rebuild_graph_edges(conn)
    edges2 = rebuild_graph_edges(conn)

    assert len(edges1) == len(edges2)
    assert edges1[0].weight == edges2[0].weight


def test_empty_library_no_edges(conn: sqlite3.Connection):
    edges = rebuild_graph_edges(conn)
    assert len(edges) == 0


def test_single_book_no_edges(conn: sqlite3.Connection):
    session_id = _create_session_and_rows(conn, 1)
    b1 = create_book(conn, title="Solo Book", authors=["Solo Author"])
    create_user_book_entry(conn, book_id=b1.id, source_session_id=session_id, source_row_id=1)
    edges = rebuild_graph_edges(conn)
    assert len(edges) == 0


# --- API tests ---

def test_get_graph_returns_nodes_and_edges(client: TestClient, conn: sqlite3.Connection):
    _seed_two_books_same_author(conn)
    rebuild_graph_edges(conn)

    resp = client.get("/api/graph")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1


def test_rebuild_graph_endpoint(client: TestClient, conn: sqlite3.Connection):
    _seed_two_books_same_author(conn)

    resp = client.post("/api/graph/rebuild")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["edges"]) == 1
    assert data["edges"][0]["edge_type"] == "same_author"


def test_empty_graph(client: TestClient):
    resp = client.get("/api/graph")
    assert resp.status_code == 200
    data = resp.json()
    assert data["nodes"] == []
    assert data["edges"] == []
