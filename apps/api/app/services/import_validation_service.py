import json
import sqlite3
from dataclasses import dataclass

from app.repositories.import_repository import (
    get_import_session,
    list_import_rows,
)
from app.repositories.library_repository import get_user_book_entry_by_source_row


@dataclass
class ValidationRow:
    row_id: int
    row_index: int
    title: str
    status: str
    book_id: int | None
    entry_id: int | None
    warnings: list[str]


@dataclass
class ValidationReport:
    session_id: int
    raw_input_hash: str
    parsed_count: int
    accepted_count: int
    rejected_count: int
    needs_edit_count: int
    committed_count: int
    duplicate_count: int
    failed_count: int
    warning_count: int
    rows: list[ValidationRow]


def _parse_json_safe(raw: str | None) -> dict | list | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def _extract_title(parsed_json: str | None) -> str:
    parsed = _parse_json_safe(parsed_json)
    if isinstance(parsed, dict):
        title = parsed.get("title", "")
        if isinstance(title, str):
            return title
    return ""


def _extract_warnings(warnings_json: str | None) -> list[str]:
    parsed = _parse_json_safe(warnings_json)
    if isinstance(parsed, list):
        return [w for w in parsed if isinstance(w, str)]
    return []


def _has_invalid_json(raw: str | None) -> bool:
    return bool(raw) and _parse_json_safe(raw) is None


def get_validation_report(
    conn: sqlite3.Connection, session_id: int
) -> ValidationReport | None:
    session = get_import_session(conn, session_id)
    if session is None:
        return None

    rows = list_import_rows(conn, session_id)

    accepted_count = 0
    rejected_count = 0
    needs_edit_count = 0
    committed_count = 0
    failed_count = 0
    total_warnings = 0
    stored_row_warning_count = 0
    validation_rows: list[ValidationRow] = []

    for row in rows:
        title = _extract_title(row.parsed_json)
        row_warnings = _extract_warnings(row.warnings_json)
        stored_row_warning_count += len(row_warnings)

        # Count by status
        if row.status in ("accepted", "committed"):
            accepted_count += 1
        elif row.status == "rejected":
            rejected_count += 1
        elif row.status == "needs_edit":
            needs_edit_count += 1

        # Committed rows: look up user_book_entries
        book_id = None
        entry_id = None
        if row.status == "committed":
            entry = get_user_book_entry_by_source_row(conn, row.id)
            if entry:
                book_id = entry.book_id
                entry_id = entry.id
                committed_count += 1
            else:
                # Accepted but no entry = failed
                failed_count += 1
                row_warnings.append("commit_failed_no_entry")

        # Detect accepted rows with invalid title (potential failure)
        if row.status == "accepted" and not title:
            failed_count += 1
            row_warnings.append("accepted_with_empty_title")

        # Detect invalid JSON
        if _has_invalid_json(row.parsed_json):
            row_warnings.append("invalid_parsed_json")

        if _has_invalid_json(row.warnings_json):
            row_warnings.append("invalid_warnings_json")

        total_warnings += len(row_warnings)

        validation_rows.append(
            ValidationRow(
                row_id=row.id,
                row_index=row.row_index,
                title=title,
                status=row.status,
                book_id=book_id,
                entry_id=entry_id,
                warnings=row_warnings,
            )
        )

    global_warning_count = max(session.warning_count - stored_row_warning_count, 0)

    return ValidationReport(
        session_id=session.id,
        raw_input_hash=session.raw_hash,
        parsed_count=len(rows),
        accepted_count=accepted_count,
        rejected_count=rejected_count,
        needs_edit_count=needs_edit_count,
        committed_count=committed_count,
        duplicate_count=session.duplicate_count,
        failed_count=failed_count,
        warning_count=total_warnings + global_warning_count,
        rows=validation_rows,
    )
