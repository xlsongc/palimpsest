import json
import sqlite3
from pathlib import Path

import pytest

from app.db.database import get_connection, init_schema
from app.repositories.import_repository import (
    add_import_row,
    create_import_session,
)
from app.repositories.library_repository import (
    create_book,
    create_user_book_entry,
    find_book_by_title_authors,
    get_user_book_entry_by_source_row,
)


@pytest.fixture
def conn(tmp_path: Path):
    db_path = tmp_path / "test.db"
    c = get_connection(db_path)
    init_schema(c)
    yield c
    c.close()


def test_find_book_by_title_and_authors_is_order_stable(conn: sqlite3.Connection):
    created = create_book(conn, title="Example Book", authors=["B", "A"])

    found = find_book_by_title_authors(conn, title="Example Book", authors=["A", "B"])

    assert found is not None
    assert found.id == created.id
    assert json.loads(found.authors_json) == ["A", "B"]


def test_find_book_by_title_with_missing_authors(conn: sqlite3.Connection):
    created = create_book(conn, title="Anonymous Book", authors=[])

    found = find_book_by_title_authors(conn, title="Anonymous Book", authors=[])

    assert found is not None
    assert found.id == created.id


def test_create_user_book_entry_keeps_source_linkage(conn: sqlite3.Connection):
    session = create_import_session(conn, raw_input="Example Book 2026-01-01")
    row = add_import_row(
        conn,
        session_id=session.id,
        row_index=0,
        raw_fragment="Example Book 2026-01-01",
    )
    book = create_book(conn, title="Example Book", authors=["A"])

    entry = create_user_book_entry(
        conn,
        book_id=book.id,
        source_session_id=session.id,
        source_row_id=row.id,
        status="read",
        tags=["test"],
        marked_at="2026-01-01",
        confidence=0.95,
    )

    assert entry.book_id == book.id
    assert entry.source_session_id == session.id
    assert entry.source_row_id == row.id
    assert entry.status == "read"
    assert entry.marked_at == "2026-01-01"
    assert json.loads(entry.tags_json) == ["test"]


def test_get_user_book_entry_by_source_row(conn: sqlite3.Connection):
    session = create_import_session(conn, raw_input="Example Book 2026-01-01")
    row = add_import_row(
        conn,
        session_id=session.id,
        row_index=0,
        raw_fragment="Example Book 2026-01-01",
    )
    book = create_book(conn, title="Example Book", authors=["A"])
    created = create_user_book_entry(
        conn,
        book_id=book.id,
        source_session_id=session.id,
        source_row_id=row.id,
    )

    found = get_user_book_entry_by_source_row(conn, row.id)

    assert found is not None
    assert found.id == created.id
