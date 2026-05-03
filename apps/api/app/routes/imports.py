import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.db.database import get_app_connection
from app.repositories.import_repository import (
    ImportSession,
    create_import_session,
    get_import_session,
)
from app.schemas.imports import (
    ImportCreateRequest,
    ImportParseResponseDTO,
    ImportParseRowDTO,
    ImportReviewRequestDTO,
    ImportReviewResponseDTO,
    ImportReviewSubmitResponseDTO,
    ImportSessionDTO,
    ReviewRowDTO,
    UpdatedRowDTO,
)
from app.services.import_parse_service import parse_import_session
from app.services.import_review_service import get_review_rows, submit_review

router = APIRouter()


def get_db():
    conn = get_app_connection()
    try:
        yield conn
    finally:
        conn.close()


DbDep = Annotated[sqlite3.Connection, Depends(get_db)]


def _to_dto(session: ImportSession) -> ImportSessionDTO:
    return ImportSessionDTO(
        id=session.id,
        source=session.source,
        raw_hash=session.raw_hash,
        created_at=session.created_at,
        status=session.status,
        expected_count=session.expected_count,
        extracted_count=session.extracted_count,
        reviewed_count=session.reviewed_count,
        inserted_count=session.inserted_count,
        duplicate_count=session.duplicate_count,
        warning_count=session.warning_count,
    )


@router.post("/imports", response_model=ImportSessionDTO, status_code=201)
def create_import(body: ImportCreateRequest, conn: DbDep):
    if not body.raw_input or not body.raw_input.strip():
        raise HTTPException(status_code=422, detail="raw_input must not be empty")
    session = create_import_session(conn, raw_input=body.raw_input, source=body.source)
    return _to_dto(session)


@router.get("/imports/{session_id}", response_model=ImportSessionDTO)
def get_import(session_id: int, conn: DbDep):
    session = get_import_session(conn, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Import session not found")
    return _to_dto(session)


@router.post("/imports/{session_id}/parse", response_model=ImportParseResponseDTO)
def parse_import(session_id: int, conn: DbDep):
    result = parse_import_session(conn, session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Import session not found")

    return ImportParseResponseDTO(
        session=_to_dto(result.session),
        rows=[
            ImportParseRowDTO(
                row_index=r.row_index,
                raw_fragment=r.raw_fragment,
                parsed_json=r.parsed_json,
                status=r.status,
                confidence=r.confidence,
                warnings=r.warnings,
            )
            for r in result.rows
        ],
        parser_warnings=result.parser_warnings,
    )


@router.get("/imports/{session_id}/review", response_model=ImportReviewResponseDTO)
def get_review(session_id: int, conn: DbDep):
    result = get_review_rows(conn, session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Import session not found")

    return ImportReviewResponseDTO(
        session=_to_dto(result.session),
        rows=[
            ReviewRowDTO(
                row_id=r.row_id,
                row_index=r.row_index,
                raw_fragment=r.raw_fragment,
                parsed_json=r.parsed_json,
                status=r.status,
                confidence=r.confidence,
                warnings=r.warnings,
            )
            for r in result.rows
        ],
    )


@router.post("/imports/{session_id}/review", response_model=ImportReviewSubmitResponseDTO)
def submit_review_action(session_id: int, body: ImportReviewRequestDTO, conn: DbDep):
    row_actions = [r.model_dump() for r in body.rows]
    result = submit_review(conn, session_id, row_actions)

    if result.error == "session_not_found":
        raise HTTPException(status_code=404, detail="Import session not found")
    if result.error:
        raise HTTPException(status_code=422, detail=result.error)

    return ImportReviewSubmitResponseDTO(
        session=_to_dto(result.session),
        updated_rows=[
            UpdatedRowDTO(row_id=r.row_id, status=r.status)
            for r in result.updated_rows
        ],
    )
