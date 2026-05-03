from pydantic import BaseModel


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
