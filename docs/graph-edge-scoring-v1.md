# Graph Edge Scoring v1

## Data Source

Graph edges are built from committed library data:
- `books` table: title, authors_json
- `user_book_entries` table: status, rating, tags_json, read_finished_at, source_row_id
- `import_rows` table: parsed_json (for tags extraction)

## Deterministic Edge Rules v1

Only rules that can be computed from existing data without LLM or external APIs.

### Rule 1: Same Author (+5)

If two books share at least one author (exact string match after normalization), create edge.

- Edge type: `same_author`
- Weight: 5
- Reason: `Shared author: {author_name}`

### Rule 2: Same Tag (+3 per shared tag)

If two books share at least one user tag, create edge.

- Edge type: `same_tag`
- Weight: 3 × number_of_shared_tags
- Reason: `Shared tags: {tag1}, {tag2}`

### Excluded v1 Rule: Same Reading Status

Do not create graph edges only because two books share the same reading status. This creates noisy clusters such as "all read books" or "all want books" and does not explain a knowledge relationship.

### Rule 3: Reading Sequence Proximity (+1)

If two books were read (status=finished) within 90 days of each other, create edge.

- Edge type: `reading_sequence`
- Weight: 1
- Reason: `Read within {N} days of each other`

### Excluded v1 Rule: Same Rating

Do not create graph edges only because two books have the same user rating. Rating is useful as node/card metadata, but it is too weak as a relationship by itself.

## Edge Storage

Edges are stored in the `book_edges` table (to be created if not exists):

```sql
CREATE TABLE IF NOT EXISTS book_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_book_id INTEGER NOT NULL REFERENCES books(id),
    target_book_id INTEGER NOT NULL REFERENCES books(id),
    edge_type TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 0,
    reason TEXT,
    evidence_json TEXT,
    generated_by TEXT NOT NULL DEFAULT 'deterministic_v1',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

## API Contract

### `GET /api/graph`

Returns nodes and edges for the graph visualization.

Response:
```json
{
  "nodes": [
    {
      "id": 1,
      "title": "思考，快与慢",
      "authors": ["丹尼尔·卡尼曼"],
      "status": "read",
      "rating": 8.1,
      "tags": ["心理学", "认知"]
    }
  ],
  "edges": [
    {
      "id": 1,
      "source_book_id": 1,
      "target_book_id": 2,
      "edge_type": "same_author",
      "weight": 5,
      "reason": "Shared author: 丹尼尔·卡尼曼"
    }
  ]
}
```

### `POST /api/graph/rebuild`

Rebuilds all edges from current library data.
Deletes existing edges, recomputes, returns new graph.

Response: Same as GET /api/graph.

## Test Cases

1. Two books with same author → edge created with weight 5
2. Two books with 2 shared tags → edge created with weight 6
3. Two books read within 90 days → edge created with weight 1
4. Same status alone → no edge
5. Same rating alone → no edge
6. Rebuild is idempotent → same edges after second rebuild
7. Empty library → empty graph
8. Single book → no edges
