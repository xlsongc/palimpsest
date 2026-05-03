import json
import sqlite3
from dataclasses import dataclass


@dataclass
class BookEdge:
    id: int
    source_book_id: int
    target_book_id: int
    edge_type: str
    weight: float
    reason: str | None
    evidence_json: str | None
    generated_by: str
    created_at: str
    updated_at: str


@dataclass
class BookWithEntry:
    book_id: int
    title: str
    authors_json: str | None
    status: str | None
    rating: float | None
    tags_json: str | None
    read_finished_at: str | None


def get_all_books_with_entries(conn: sqlite3.Connection) -> list[BookWithEntry]:
    rows = conn.execute("""
        SELECT b.id AS book_id, b.title, b.authors_json,
               ube.status, ube.rating, ube.tags_json, ube.read_finished_at
        FROM books b
        LEFT JOIN user_book_entries ube ON ube.book_id = b.id
        ORDER BY b.id
    """).fetchall()
    return [
        BookWithEntry(
            book_id=r["book_id"],
            title=r["title"],
            authors_json=r["authors_json"],
            status=r["status"],
            rating=r["rating"],
            tags_json=r["tags_json"],
            read_finished_at=r["read_finished_at"],
        )
        for r in rows
    ]


def clear_all_edges(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM book_edges")
    conn.commit()


def insert_edge(
    conn: sqlite3.Connection,
    source_book_id: int,
    target_book_id: int,
    edge_type: str,
    weight: float,
    reason: str | None = None,
    evidence_json: str | None = None,
) -> BookEdge:
    cur = conn.execute(
        """INSERT INTO book_edges (source_book_id, target_book_id, edge_type, weight, reason, evidence_json)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (source_book_id, target_book_id, edge_type, weight, reason, evidence_json),
    )
    conn.commit()
    return _get_edge(conn, cur.lastrowid)


def get_all_edges(conn: sqlite3.Connection) -> list[BookEdge]:
    rows = conn.execute("SELECT * FROM book_edges ORDER BY id").fetchall()
    return [_row_to_edge(r) for r in rows]


def _get_edge(conn: sqlite3.Connection, edge_id: int) -> BookEdge:
    row = conn.execute("SELECT * FROM book_edges WHERE id = ?", (edge_id,)).fetchone()
    return _row_to_edge(row)


def _row_to_edge(row: sqlite3.Row) -> BookEdge:
    return BookEdge(
        id=row["id"],
        source_book_id=row["source_book_id"],
        target_book_id=row["target_book_id"],
        edge_type=row["edge_type"],
        weight=row["weight"],
        reason=row["reason"],
        evidence_json=row["evidence_json"],
        generated_by=row["generated_by"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
