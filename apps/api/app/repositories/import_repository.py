import hashlib
import sqlite3
from dataclasses import dataclass


def compute_raw_hash(raw_input: str) -> str:
    return hashlib.sha256(raw_input.encode("utf-8")).hexdigest()


@dataclass
class ImportSession:
    id: int
    source: str
    raw_input: str
    raw_hash: str
    created_at: str
    expected_count: int
    extracted_count: int
    reviewed_count: int
    inserted_count: int
    duplicate_count: int
    warning_count: int
    status: str


@dataclass
class ImportRow:
    id: int
    session_id: int
    row_index: int
    raw_fragment: str
    parsed_json: str | None
    normalized_json: str | None
    status: str
    confidence: float
    warnings_json: str | None
    created_at: str


def create_import_session(
    conn: sqlite3.Connection,
    raw_input: str,
    source: str = "",
) -> ImportSession:
    raw_hash = compute_raw_hash(raw_input)
    cur = conn.execute(
        """INSERT INTO import_sessions (source, raw_input, raw_hash)
           VALUES (?, ?, ?)""",
        (source, raw_input, raw_hash),
    )
    conn.commit()
    session = get_import_session(conn, cur.lastrowid)
    if session is None:
        raise RuntimeError("Created import session could not be retrieved")
    return session


def get_import_session(
    conn: sqlite3.Connection, session_id: int
) -> ImportSession | None:
    row = conn.execute(
        "SELECT * FROM import_sessions WHERE id = ?", (session_id,)
    ).fetchone()
    if row is None:
        return None
    return ImportSession(
        id=row["id"],
        source=row["source"],
        raw_input=row["raw_input"],
        raw_hash=row["raw_hash"],
        created_at=row["created_at"],
        expected_count=row["expected_count"],
        extracted_count=row["extracted_count"],
        reviewed_count=row["reviewed_count"],
        inserted_count=row["inserted_count"],
        duplicate_count=row["duplicate_count"],
        warning_count=row["warning_count"],
        status=row["status"],
    )


def add_import_row(
    conn: sqlite3.Connection,
    session_id: int,
    row_index: int,
    raw_fragment: str,
    parsed_json: str | None = None,
    normalized_json: str | None = None,
    status: str = "pending",
    confidence: float = 0.0,
    warnings_json: str | None = None,
) -> ImportRow:
    cur = conn.execute(
        """INSERT INTO import_rows
           (session_id, row_index, raw_fragment, parsed_json, normalized_json,
            status, confidence, warnings_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            session_id,
            row_index,
            raw_fragment,
            parsed_json,
            normalized_json,
            status,
            confidence,
            warnings_json,
        ),
    )
    conn.commit()
    row = get_import_row(conn, cur.lastrowid)
    if row is None:
        raise RuntimeError("Created import row could not be retrieved")
    return row


def get_import_row(conn: sqlite3.Connection, row_id: int) -> ImportRow | None:
    row = conn.execute(
        "SELECT * FROM import_rows WHERE id = ?", (row_id,)
    ).fetchone()
    if row is None:
        return None
    return ImportRow(
        id=row["id"],
        session_id=row["session_id"],
        row_index=row["row_index"],
        raw_fragment=row["raw_fragment"],
        parsed_json=row["parsed_json"],
        normalized_json=row["normalized_json"],
        status=row["status"],
        confidence=row["confidence"],
        warnings_json=row["warnings_json"],
        created_at=row["created_at"],
    )


def list_import_rows(
    conn: sqlite3.Connection, session_id: int
) -> list[ImportRow]:
    rows = conn.execute(
        "SELECT * FROM import_rows WHERE session_id = ? ORDER BY row_index",
        (session_id,),
    ).fetchall()
    return [
        ImportRow(
            id=r["id"],
            session_id=r["session_id"],
            row_index=r["row_index"],
            raw_fragment=r["raw_fragment"],
            parsed_json=r["parsed_json"],
            normalized_json=r["normalized_json"],
            status=r["status"],
            confidence=r["confidence"],
            warnings_json=r["warnings_json"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


def delete_import_rows_for_session(
    conn: sqlite3.Connection, session_id: int
) -> int:
    cur = conn.execute("DELETE FROM import_rows WHERE session_id = ?", (session_id,))
    conn.commit()
    return cur.rowcount


def update_import_session_counts(
    conn: sqlite3.Connection,
    session_id: int,
    expected_count: int,
    extracted_count: int,
    warning_count: int,
    status: str,
) -> None:
    conn.execute(
        """UPDATE import_sessions
           SET expected_count = ?, extracted_count = ?, warning_count = ?, status = ?
           WHERE id = ?""",
        (expected_count, extracted_count, warning_count, status, session_id),
    )
    conn.commit()
