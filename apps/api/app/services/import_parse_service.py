import json
import sqlite3
from dataclasses import dataclass

from app.importers.douban_paste import DoubanParsedRow, parse_douban_paste
from app.repositories.import_repository import (
    ImportSession,
    add_import_row,
    delete_import_rows_for_session,
    get_import_session,
    update_import_session_counts,
)


@dataclass
class ParsedRowDTO:
    row_index: int
    raw_fragment: str
    parsed_json: str | None
    status: str
    confidence: float
    warnings: list[str]


@dataclass
class ParseResultDTO:
    session: ImportSession
    rows: list[ParsedRowDTO]
    parser_warnings: list[str]


def _row_to_parsed_json(row: DoubanParsedRow) -> str:
    return json.dumps(
        {
            "title": row.title,
            "status": row.status,
            "authors": row.authors,
            "rating": row.rating,
            "comment": row.comment,
            "tags": row.tags,
            "read_date": row.read_date,
            "marked_date": row.marked_date,
            "douban_url": row.douban_url,
            "confidence": row.confidence,
            "warnings": row.warnings,
        },
        ensure_ascii=False,
    )


def parse_import_session(
    conn: sqlite3.Connection, session_id: int
) -> ParseResultDTO | None:
    session = get_import_session(conn, session_id)
    if session is None:
        return None

    result = parse_douban_paste(session.raw_input)

    # Idempotent: clear previous rows
    delete_import_rows_for_session(conn, session_id)

    # Insert new rows
    row_dtos: list[ParsedRowDTO] = []
    total_warnings = len(result.warnings)

    for row in result.rows:
        warnings_json = json.dumps(row.warnings, ensure_ascii=False)
        parsed_json = _row_to_parsed_json(row)

        add_import_row(
            conn,
            session_id=session_id,
            row_index=row.row_index,
            raw_fragment=row.raw_fragment,
            parsed_json=parsed_json,
            warnings_json=warnings_json,
            status="pending",
            confidence=row.confidence,
        )

        total_warnings += len(row.warnings)
        row_dtos.append(
            ParsedRowDTO(
                row_index=row.row_index,
                raw_fragment=row.raw_fragment,
                parsed_json=parsed_json,
                status="pending",
                confidence=row.confidence,
                warnings=row.warnings,
            )
        )

    # Update session counts
    new_status = "parsed" if result.rows else "parse_empty"
    update_import_session_counts(
        conn,
        session_id=session_id,
        expected_count=len(result.rows),
        extracted_count=len(result.rows),
        warning_count=total_warnings,
        status=new_status,
    )

    # Re-fetch session with updated counts
    updated_session = get_import_session(conn, session_id)
    if updated_session is None:
        raise RuntimeError("Parsed import session could not be retrieved")

    return ParseResultDTO(
        session=updated_session,
        rows=row_dtos,
        parser_warnings=result.warnings,
    )
