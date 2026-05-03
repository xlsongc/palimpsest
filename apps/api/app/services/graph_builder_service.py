import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime

from app.repositories.graph_repository import (
    BookWithEntry,
    BookEdge,
    clear_all_edges,
    get_all_books_with_entries,
    get_all_edges,
    insert_edge,
)


def _parse_json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        val = json.loads(raw)
        return [str(v) for v in val] if isinstance(val, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _parse_authors(raw: str | None) -> list[str]:
    return _parse_json_list(raw)


def _parse_tags(raw: str | None) -> list[str]:
    return _parse_json_list(raw)


@dataclass
class RawEdge:
    source_book_id: int
    target_book_id: int
    edge_type: str
    weight: float
    reason: str


def _build_same_author_edges(books: list[BookWithEntry]) -> list[RawEdge]:
    edges = []
    by_author: dict[str, list[int]] = {}

    for b in books:
        for author in _parse_authors(b.authors_json):
            by_author.setdefault(author, []).append(b.book_id)

    for author, book_ids in by_author.items():
        for i in range(len(book_ids)):
            for j in range(i + 1, len(book_ids)):
                edges.append(RawEdge(
                    source_book_id=book_ids[i],
                    target_book_id=book_ids[j],
                    edge_type="same_author",
                    weight=5.0,
                    reason=f"Shared author: {author}",
                ))
    return edges


def _build_same_tag_edges(books: list[BookWithEntry]) -> list[RawEdge]:
    edges = []
    by_tag: dict[str, list[int]] = {}

    for b in books:
        for tag in _parse_tags(b.tags_json):
            by_tag.setdefault(tag, []).append(b.book_id)

    for tag, book_ids in by_tag.items():
        for i in range(len(book_ids)):
            for j in range(i + 1, len(book_ids)):
                edges.append(RawEdge(
                    source_book_id=book_ids[i],
                    target_book_id=book_ids[j],
                    edge_type="same_tag",
                    weight=3.0,
                    reason=f"Shared tag: {tag}",
                ))
    return edges


def _build_same_status_edges(books: list[BookWithEntry]) -> list[RawEdge]:
    edges = []
    by_status: dict[str, list[int]] = {}

    for b in books:
        if b.status:
            by_status.setdefault(b.status, []).append(b.book_id)

    for status, book_ids in by_status.items():
        for i in range(len(book_ids)):
            for j in range(i + 1, len(book_ids)):
                edges.append(RawEdge(
                    source_book_id=book_ids[i],
                    target_book_id=book_ids[j],
                    edge_type="same_status",
                    weight=1.0,
                    reason=f"Both {status}",
                ))
    return edges


def _build_reading_sequence_edges(books: list[BookWithEntry]) -> list[RawEdge]:
    edges = []
    read_books = []

    for b in books:
        if b.read_finished_at:
            try:
                dt = datetime.fromisoformat(b.read_finished_at)
                read_books.append((b.book_id, dt))
            except ValueError:
                continue

    read_books.sort(key=lambda x: x[1])

    for i in range(len(read_books)):
        for j in range(i + 1, len(read_books)):
            book_a, date_a = read_books[i]
            book_b, date_b = read_books[j]
            days = (date_b - date_a).days
            if days <= 90:
                edges.append(RawEdge(
                    source_book_id=book_a,
                    target_book_id=book_b,
                    edge_type="reading_sequence",
                    weight=1.0,
                    reason=f"Read within {days} days of each other",
                ))
    return edges


def _build_same_rating_edges(books: list[BookWithEntry]) -> list[RawEdge]:
    edges = []
    by_rating: dict[float, list[int]] = {}

    for b in books:
        if b.rating is not None:
            by_rating.setdefault(b.rating, []).append(b.book_id)

    for rating, book_ids in by_rating.items():
        for i in range(len(book_ids)):
            for j in range(i + 1, len(book_ids)):
                edges.append(RawEdge(
                    source_book_id=book_ids[i],
                    target_book_id=book_ids[j],
                    edge_type="same_rating",
                    weight=1.0,
                    reason=f"Both rated {rating}",
                ))
    return edges


@dataclass
class MergedEdge:
    source_book_id: int
    target_book_id: int
    primary_type: str
    total_weight: float
    reasons: list[str]
    types: list[str]


def _merge_edges(raw_edges: list[RawEdge]) -> list[MergedEdge]:
    by_pair: dict[tuple[int, int], MergedEdge] = {}

    for re in raw_edges:
        key = (min(re.source_book_id, re.target_book_id),
               max(re.source_book_id, re.target_book_id))

        if key not in by_pair:
            by_pair[key] = MergedEdge(
                source_book_id=key[0],
                target_book_id=key[1],
                primary_type=re.edge_type,
                total_weight=0.0,
                reasons=[],
                types=[],
            )

        me = by_pair[key]
        me.total_weight += re.weight
        me.reasons.append(re.reason)
        if re.edge_type not in me.types:
            me.types.append(re.edge_type)

    return list(by_pair.values())


def rebuild_graph_edges(conn: sqlite3.Connection) -> list[BookEdge]:
    books = get_all_books_with_entries(conn)

    raw_edges: list[RawEdge] = []
    raw_edges.extend(_build_same_author_edges(books))
    raw_edges.extend(_build_same_tag_edges(books))
    raw_edges.extend(_build_reading_sequence_edges(books))

    merged = _merge_edges(raw_edges)

    clear_all_edges(conn)

    result = []
    for me in merged:
        edge = insert_edge(
            conn,
            source_book_id=me.source_book_id,
            target_book_id=me.target_book_id,
            edge_type=me.primary_type,
            weight=me.total_weight,
            reason="; ".join(me.reasons),
            evidence_json=json.dumps({
                "types": me.types,
                "reasons": me.reasons,
            }, ensure_ascii=False),
        )
        result.append(edge)

    return result
