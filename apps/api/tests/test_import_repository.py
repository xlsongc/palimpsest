import sqlite3
import tempfile
from pathlib import Path

import pytest

from app.db import get_connection, init_schema
from app.repositories import (
    add_import_row,
    compute_raw_hash,
    create_import_session,
    get_import_session,
    list_import_rows,
)


@pytest.fixture
def conn(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "test.db"
    c = get_connection(db_path)
    init_schema(c)
    yield c
    c.close()


# --- hash determinism ---


def test_raw_hash_is_deterministic():
    text = "some pasted douban content"
    assert compute_raw_hash(text) == compute_raw_hash(text)


def test_raw_hash_changes_with_input():
    assert compute_raw_hash("a") != compute_raw_hash("b")


# --- session CRUD ---


def test_create_and_retrieve_session(conn):
    raw = "怎样选择成长股2026-05-02"
    session = create_import_session(conn, raw_input=raw, source="douban")
    assert session.id is not None
    assert session.raw_input == raw
    assert session.raw_hash == compute_raw_hash(raw)
    assert session.status == "pending"

    fetched = get_import_session(conn, session.id)
    assert fetched is not None
    assert fetched.raw_input == raw


def test_raw_input_stored_unchanged(conn):
    raw = "  怎样选择成长股2026-05-02\n\n  另一本书 2026-01-01  "
    session = create_import_session(conn, raw_input=raw)
    fetched = get_import_session(conn, session.id)
    assert fetched.raw_input == raw


def test_get_nonexistent_session_returns_none(conn):
    assert get_import_session(conn, 99999) is None


# --- import rows ---


def test_add_and_list_rows(conn):
    session = create_import_session(conn, raw_input="page 1")
    add_import_row(conn, session.id, row_index=1, raw_fragment="book A")
    add_import_row(conn, session.id, row_index=0, raw_fragment="book B")

    rows = list_import_rows(conn, session.id)
    assert len(rows) == 2
    assert rows[0].row_index == 0
    assert rows[1].row_index == 1
    assert rows[0].raw_fragment == "book B"
    assert rows[1].raw_fragment == "book A"


def test_rows_linked_to_session(conn):
    s1 = create_import_session(conn, raw_input="s1")
    s2 = create_import_session(conn, raw_input="s2")
    add_import_row(conn, s1.id, row_index=0, raw_fragment="x")
    add_import_row(conn, s2.id, row_index=0, raw_fragment="y")

    assert len(list_import_rows(conn, s1.id)) == 1
    assert len(list_import_rows(conn, s2.id)) == 1


def test_row_optional_fields_default(conn):
    session = create_import_session(conn, raw_input="s")
    row = add_import_row(conn, session.id, row_index=0, raw_fragment="f")
    fetched = list_import_rows(conn, session.id)[0]
    assert fetched.parsed_json is None
    assert fetched.normalized_json is None
    assert fetched.warnings_json is None
    assert fetched.confidence == 0.0
    assert fetched.status == "pending"
