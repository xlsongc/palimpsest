from pydantic import BaseModel


class GraphNodeDTO(BaseModel):
    id: int
    title: str
    authors: list[str]
    status: str | None
    rating: float | None
    tags: list[str]


class GraphEdgeDTO(BaseModel):
    id: int
    source_book_id: int
    target_book_id: int
    edge_type: str
    weight: float
    reason: str | None


class GraphResponseDTO(BaseModel):
    nodes: list[GraphNodeDTO]
    edges: list[GraphEdgeDTO]
