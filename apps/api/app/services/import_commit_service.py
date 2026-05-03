import json
import sqlite3
from dataclasses import dataclass

from app.repositories.import_repository import (
    ImportSession,
    get_import_session,
    list_import_rows,
    update_import_row_status,
)
from app.repositories.library_repository import (
    create_book,
    create_user_book_entry,
    find_book_by_title_authors,
    get_user_book_entry_by_source_row,
)


@dataclass
class CommittedRow:
    row_id: int
    book_id: int
    entry_id: int


@dataclass
class DuplicateRow:
    row_id: int
    existing_book_id: int


@dataclass
class SkippedRow:
    row_id: int
    reason: str


@dataclass
class CommitResult:
    session: ImportSession
    committed: list[CommittedRow]
    duplicates: list[DuplicateRow]
    skipped: list[SkippedRow]
    error: str | None = None


def commit_import_session(
    conn: sqlite3.Connection, session_id: int
) -> CommitResult:
    session = get_import_session(conn, session_id)
    if session is None:
        return CommitResult(
            session=None, committed=[], duplicates=[], skipped=[],
            error="session_not_found",
        )

    if session.status == "committed":
        return CommitResult(
            session=session, committed=[], duplicates=[], skipped=[],
            error="already_committed",
        )

    rows = list_import_rows(conn, session_id)

    committed: list[CommittedRow] = []
    duplicates: list[DuplicateRow] = []
    skipped: list[SkippedRow] = []
    inserted_count = 0
    duplicate_count = 0

    for row in rows:
        if row.status != "accepted":
            reason = row.status if row.status != "pending" else "not_reviewed"
            skipped.append(SkippedRow(row_id=row.id, reason=reason))
            continue

        existing_entry = get_user_book_entry_by_source_row(conn, row.id)
        if existing_entry is not None:
            update_import_row_status(conn, row.id, "committed")
            skipped.append(SkippedRow(row_id=row.id, reason="already_committed"))
            continue

        parsed = {}
        if row.parsed_json:
            try:
                parsed = json.loads(row.parsed_json)
            except json.JSONDecodeError:
                skipped.append(SkippedRow(row_id=row.id, reason="invalid_parsed_json"))
                continue

        title = parsed.get("title", "").strip()
        if not title:
            skipped.append(SkippedRow(row_id=row.id, reason="empty_title"))
            continue

        authors = parsed.get("authors") or []
        existing_book = find_book_by_title_authors(conn, title, authors)

        if existing_book:
            book_id = existing_book.id
            duplicates.append(DuplicateRow(row_id=row.id, existing_book_id=book_id))
            duplicate_count += 1
        else:
            book = create_book(conn, title=title, authors=authors)
            book_id = book.id

        read_date = parsed.get("read_date")
        marked_date = parsed.get("marked_date")
        row_status = parsed.get("status")

        read_started_at = None
        read_finished_at = None
        marked_at = None
        if row_status == "reading" and read_date:
            read_started_at = read_date
        elif row_status == "read" and read_date:
            read_finished_at = read_date
        elif row_status == "want" and marked_date:
            marked_at = marked_date

        entry = create_user_book_entry(
            conn,
            book_id=book_id,
            source_session_id=session_id,
            source_row_id=row.id,
            status=row_status,
            rating=parsed.get("rating"),
            tags=parsed.get("tags"),
            comment=parsed.get("comment"),
            read_started_at=read_started_at,
            read_finished_at=read_finished_at,
            marked_at=marked_at,
            confidence=row.confidence,
        )

        update_import_row_status(conn, row.id, "committed")
        committed.append(CommittedRow(row_id=row.id, book_id=book_id, entry_id=entry.id))
        inserted_count += 1

    # Update session
    conn.execute(
        """UPDATE import_sessions
           SET inserted_count = ?, duplicate_count = ?, status = 'committed'
           WHERE id = ?""",
        (inserted_count, duplicate_count, session_id),
    )
    conn.commit()

    updated_session = get_import_session(conn, session_id)
    if updated_session is None:
        raise RuntimeError("Committed import session could not be retrieved")

    return CommitResult(
        session=updated_session,
        committed=committed,
        duplicates=duplicates,
        skipped=skipped,
    )
