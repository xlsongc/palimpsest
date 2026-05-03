import json
import sqlite3
from dataclasses import dataclass

from app.repositories.import_repository import (
    ImportSession,
    get_import_row,
    get_import_session,
    list_import_rows,
    update_import_row_parsed_json,
    update_import_row_status,
    update_import_session_status,
)


@dataclass
class ReviewRowView:
    row_id: int
    row_index: int
    raw_fragment: str
    parsed_json: dict | None
    status: str
    confidence: float
    warnings: list[str]


@dataclass
class UpdatedRow:
    row_id: int
    status: str


@dataclass
class ReviewListResult:
    session: ImportSession
    rows: list[ReviewRowView]


@dataclass
class ReviewSubmitResult:
    session: ImportSession
    updated_rows: list[UpdatedRow]
    error: str | None = None


def get_review_rows(
    conn: sqlite3.Connection, session_id: int
) -> ReviewListResult | None:
    session = get_import_session(conn, session_id)
    if session is None:
        return None

    db_rows = list_import_rows(conn, session_id)
    rows = []
    for r in db_rows:
        parsed = None
        if r.parsed_json:
            try:
                parsed = json.loads(r.parsed_json)
            except json.JSONDecodeError:
                parsed = None

        warnings = []
        if r.warnings_json:
            try:
                warnings = json.loads(r.warnings_json)
            except json.JSONDecodeError:
                warnings = []

        rows.append(
            ReviewRowView(
                row_id=r.id,
                row_index=r.row_index,
                raw_fragment=r.raw_fragment,
                parsed_json=parsed,
                status=r.status,
                confidence=r.confidence,
                warnings=warnings,
            )
        )

    return ReviewListResult(session=session, rows=rows)


def _build_updated_parsed_json(
    existing_json: str | None,
    title: str | None,
    authors: list[str],
    status: str | None,
    rating: float | None,
    read_date: str | None,
    marked_date: str | None,
    comment: str | None,
    tags: list[str],
) -> str:
    parsed = {}
    if existing_json:
        try:
            parsed = json.loads(existing_json)
        except json.JSONDecodeError:
            pass

    if title is not None:
        parsed["title"] = title
    if authors:
        parsed["authors"] = authors
    if status is not None:
        parsed["status"] = status
    if rating is not None:
        parsed["rating"] = rating
    if read_date is not None:
        parsed["read_date"] = read_date
        parsed.pop("marked_date", None)
    if marked_date is not None:
        parsed["marked_date"] = marked_date
        parsed.pop("read_date", None)
    if comment is not None:
        parsed["comment"] = comment
    if tags:
        parsed["tags"] = tags

    return json.dumps(parsed, ensure_ascii=False)


def submit_review(
    conn: sqlite3.Connection,
    session_id: int,
    row_actions: list[dict],
) -> ReviewSubmitResult:
    session = get_import_session(conn, session_id)
    if session is None:
        return ReviewSubmitResult(session=None, updated_rows=[], error="session_not_found")

    # Validate all row_ids belong to this session
    valid_row_ids = {r.id for r in list_import_rows(conn, session_id)}
    for action in row_actions:
        if action["row_id"] not in valid_row_ids:
            return ReviewSubmitResult(
                session=session,
                updated_rows=[],
                error=f"row_id {action['row_id']} does not belong to session {session_id}",
            )

    # Validate accept requires non-empty title
    for action in row_actions:
        if action["action"] == "accept":
            title = action.get("title")
            if not title or not title.strip():
                return ReviewSubmitResult(
                    session=session,
                    updated_rows=[],
                    error="accept requires non-empty title",
                )

    # Apply actions
    updated_rows = []
    for action in row_actions:
        row_id = action["row_id"]
        new_status = action["action"]
        db_row = get_import_row(conn, row_id)

        if new_status in ("accept", "needs_edit"):
            new_parsed_json = _build_updated_parsed_json(
                existing_json=db_row.parsed_json,
                title=action.get("title"),
                authors=action.get("authors", []),
                status=action.get("status"),
                rating=action.get("rating"),
                read_date=action.get("read_date"),
                marked_date=action.get("marked_date"),
                comment=action.get("comment"),
                tags=action.get("tags", []),
            )
            update_import_row_parsed_json(conn, row_id, new_parsed_json)

        final_status = "accepted" if new_status == "accept" else (
            "rejected" if new_status == "reject" else "needs_edit"
        )
        update_import_row_status(conn, row_id, final_status)
        updated_rows.append(UpdatedRow(row_id=row_id, status=final_status))

    # Update session status
    update_import_session_status(conn, session_id, "reviewed")
    updated_session = get_import_session(conn, session_id)

    return ReviewSubmitResult(session=updated_session, updated_rows=updated_rows)
