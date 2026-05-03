import json
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from app.db.database import get_app_connection
from app.repositories.graph_repository import get_all_books_with_entries, get_all_edges
from app.repositories.library_repository import get_book
from app.schemas.graph import GraphEdgeDTO, GraphNodeDTO, GraphResponseDTO
from app.services.graph_builder_service import rebuild_graph_edges

router = APIRouter()


def get_db():
    conn = get_app_connection()
    try:
        yield conn
    finally:
        conn.close()


DbDep = Annotated[sqlite3.Connection, Depends(get_db)]


@router.get("/graph", response_model=GraphResponseDTO)
def get_graph(conn: DbDep):
    books = get_all_books_with_entries(conn)
    edges = get_all_edges(conn)

    # Deduplicate books (may have multiple entries per book)
    seen_book_ids: set[int] = set()
    nodes: list[GraphNodeDTO] = []

    for b in books:
        if b.book_id in seen_book_ids:
            continue
        seen_book_ids.add(b.book_id)

        authors = []
        if b.authors_json:
            try:
                authors = json.loads(b.authors_json)
            except (json.JSONDecodeError, TypeError):
                pass

        tags = []
        if b.tags_json:
            try:
                tags = json.loads(b.tags_json)
            except (json.JSONDecodeError, TypeError):
                pass

        nodes.append(GraphNodeDTO(
            id=b.book_id,
            title=b.title,
            authors=authors,
            status=b.status,
            rating=b.rating,
            tags=tags,
        ))

    edge_dtos = [
        GraphEdgeDTO(
            id=e.id,
            source_book_id=e.source_book_id,
            target_book_id=e.target_book_id,
            edge_type=e.edge_type,
            weight=e.weight,
            reason=e.reason,
        )
        for e in edges
    ]

    return GraphResponseDTO(nodes=nodes, edges=edge_dtos)


@router.post("/graph/rebuild", response_model=GraphResponseDTO)
def rebuild_graph(conn: DbDep):
    rebuild_graph_edges(conn)
    return get_graph(conn)
