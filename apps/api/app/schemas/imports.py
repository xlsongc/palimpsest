from typing import Literal

from pydantic import BaseModel, Field


class ImportCreateRequest(BaseModel):
    source: str = ""
    raw_input: str


class ImportSessionDTO(BaseModel):
    id: int
    source: str
    raw_hash: str
    created_at: str
    status: str
    expected_count: int
    extracted_count: int
    reviewed_count: int
    inserted_count: int
    duplicate_count: int
    warning_count: int


class ImportParseRowDTO(BaseModel):
    row_index: int
    raw_fragment: str
    parsed_json: str | None
    status: str
    confidence: float
    warnings: list[str]


class ImportParseResponseDTO(BaseModel):
    session: ImportSessionDTO
    rows: list[ImportParseRowDTO]
    parser_warnings: list[str]


class ReviewRowDTO(BaseModel):
    row_id: int
    row_index: int
    raw_fragment: str
    parsed_json: dict | None
    status: str
    confidence: float
    warnings: list[str]


class ImportReviewResponseDTO(BaseModel):
    session: ImportSessionDTO
    rows: list[ReviewRowDTO]


class ReviewRowAction(BaseModel):
    row_id: int
    action: Literal["accept", "reject", "needs_edit"]
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    status: str | None = None
    rating: float | None = None
    read_date: str | None = None
    marked_date: str | None = None
    comment: str | None = None
    tags: list[str] = Field(default_factory=list)


class ImportReviewRequestDTO(BaseModel):
    rows: list[ReviewRowAction]


class UpdatedRowDTO(BaseModel):
    row_id: int
    status: str


class ImportReviewSubmitResponseDTO(BaseModel):
    session: ImportSessionDTO
    updated_rows: list[UpdatedRowDTO]


class CommittedRowDTO(BaseModel):
    row_id: int
    book_id: int
    entry_id: int


class DuplicateRowDTO(BaseModel):
    row_id: int
    existing_book_id: int


class SkippedRowDTO(BaseModel):
    row_id: int
    reason: str


class ImportCommitResponseDTO(BaseModel):
    session: ImportSessionDTO
    committed: list[CommittedRowDTO]
    duplicates: list[DuplicateRowDTO]
    skipped: list[SkippedRowDTO]
