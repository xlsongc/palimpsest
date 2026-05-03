import json
import sqlite3
from dataclasses import dataclass


@dataclass
class Book:
    id: int
    title: str
    subtitle: str | None
    authors_json: str | None
    isbn10: str | None
    isbn13: str | None
    publisher: str | None
    published_date: str | None
    language: str | None
    page_count: int | None
    cover_url: str | None
    description: str | None
    created_at: str
    updated_at: str


@dataclass
class UserBookEntry:
    id: int
    book_id: int
    status: str | None
    rating: float | None
    tags_json: str | None
    comment: str | None
    read_started_at: str | None
    read_finished_at: str | None
    douban_url: str | None
    source_session_id: int
    source_row_id: int
    confidence: float
    review_status: str
    created_at: str
    updated_at: str


def find_book_by_title_authors(
    conn: sqlite3.Connection,
    title: str,
    authors: list[str],
) -> Book | None:
    authors_json = json.dumps(sorted(authors), ensure_ascii=False)

    # Same title + same authors (exact JSON match)
    row = conn.execute(
        "SELECT * FROM books WHERE title = ? AND authors_json = ?",
        (title, authors_json),
    ).fetchone()
    if row:
        return _row_to_book(row)

    # Same title + both missing authors
    if not authors:
        row = conn.execute(
            "SELECT * FROM books WHERE title = ? AND (authors_json IS NULL OR authors_json = '[]')",
            (title,),
        ).fetchone()
        if row:
            return _row_to_book(row)

    return None


def create_book(
    conn: sqlite3.Connection,
    title: str,
    authors: list[str] | None = None,
    subtitle: str | None = None,
    isbn10: str | None = None,
    isbn13: str | None = None,
    publisher: str | None = None,
    published_date: str | None = None,
) -> Book:
    authors_json = json.dumps(sorted(authors or []), ensure_ascii=False)
    cur = conn.execute(
        """INSERT INTO books (title, subtitle, authors_json, isbn10, isbn13, publisher, published_date)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (title, subtitle, authors_json, isbn10, isbn13, publisher, published_date),
    )
    conn.commit()
    book = get_book(conn, cur.lastrowid)
    if book is None:
        raise RuntimeError("Created book could not be retrieved")
    return book


def get_book(conn: sqlite3.Connection, book_id: int) -> Book | None:
    row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if row is None:
        return None
    return _row_to_book(row)


def create_user_book_entry(
    conn: sqlite3.Connection,
    book_id: int,
    source_session_id: int,
    source_row_id: int,
    status: str | None = None,
    rating: float | None = None,
    tags: list[str] | None = None,
    comment: str | None = None,
    read_started_at: str | None = None,
    read_finished_at: str | None = None,
    confidence: float = 0.0,
) -> UserBookEntry:
    tags_json = json.dumps(tags or [], ensure_ascii=False)
    cur = conn.execute(
        """INSERT INTO user_book_entries
           (book_id, source_session_id, source_row_id, status, rating, tags_json,
            comment, read_started_at, read_finished_at, confidence)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (book_id, source_session_id, source_row_id, status, rating, tags_json,
         comment, read_started_at, read_finished_at, confidence),
    )
    conn.commit()
    entry = _get_user_book_entry(conn, cur.lastrowid)
    if entry is None:
        raise RuntimeError("Created user book entry could not be retrieved")
    return entry


def _get_user_book_entry(
    conn: sqlite3.Connection, entry_id: int
) -> UserBookEntry | None:
    row = conn.execute(
        "SELECT * FROM user_book_entries WHERE id = ?", (entry_id,)
    ).fetchone()
    if row is None:
        return None
    return _row_to_entry(row)


def _row_to_book(row: sqlite3.Row) -> Book:
    return Book(
        id=row["id"],
        title=row["title"],
        subtitle=row["subtitle"],
        authors_json=row["authors_json"],
        isbn10=row["isbn10"],
        isbn13=row["isbn13"],
        publisher=row["publisher"],
        published_date=row["published_date"],
        language=row["language"],
        page_count=row["page_count"],
        cover_url=row["cover_url"],
        description=row["description"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_entry(row: sqlite3.Row) -> UserBookEntry:
    return UserBookEntry(
        id=row["id"],
        book_id=row["book_id"],
        status=row["status"],
        rating=row["rating"],
        tags_json=row["tags_json"],
        comment=row["comment"],
        read_started_at=row["read_started_at"],
        read_finished_at=row["read_finished_at"],
        douban_url=row["douban_url"],
        source_session_id=row["source_session_id"],
        source_row_id=row["source_row_id"],
        confidence=row["confidence"],
        review_status=row["review_status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
