# Import Review/Commit Acceptance Spec

This document defines the acceptance criteria for BG-012 (review/commit backend flow).
It is a planning artifact, not implementation code.

## 1. Review State Model

Import rows (`import_rows.status`) can have these states:

| State | Meaning | Committable |
|-------|---------|-------------|
| `pending` | Parsed but not reviewed by user | No |
| `accepted` | User confirmed this row should be committed | Yes |
| `rejected` | User marked this row as not a real book entry | No |
| `needs_edit` | User wants to fix fields before commit | No (must become `accepted`) |
| `committed` | Successfully written to `books` + `user_book_entries` | N/A (already done) |

**Rules:**
- Only `accepted` rows are eligible for commit.
- `pending` rows with `confidence < 0.5` must NOT be silently committed.
- After commit, row status changes to `committed`.
- `rejected` rows are never committed but remain for audit.

## 2. Commit Inputs

### Review payload (`POST /api/imports/{id}/review`)

Each row in the review request:

```json
{
  "row_id": 42,
  "action": "accept",
  "title": "思考，快与慢",
  "authors": ["丹尼尔·卡尼曼"],
  "status": "read",
  "rating": 8.1,
  "read_date": "2019-03-15",
  "marked_date": null,
  "comment": "系统1和系统2的框架很实用",
  "tags": ["心理学", "认知"]
}
```

`action` values: `"accept"`, `"reject"`, `"needs_edit"`.

When `action` is `"accept"` or `"needs_edit"`, the editable fields are applied to `import_rows.parsed_json` before state change.

**Field handling:**
- `title`: required for accept. If empty, reject or mark `needs_edit`.
- `authors`: list of strings. Empty list means unknown, accept with warning.
- `status`: one of `"read"`, `"want"`, `"reading"`, or `null`.
- `rating`: float or null. Null is acceptable.
- `read_date` / `marked_date`: ISO date string or null.
- `comment`: string or null.
- `tags`: list of strings. Empty list is acceptable.

## 3. Durable Library Tables

### `books`

Stores the canonical book record. One book per unique identity.

```sql
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    subtitle TEXT,
    authors_json TEXT,           -- JSON array, e.g. '["丹尼尔·卡尼曼"]'
    isbn10 TEXT,
    isbn13 TEXT,
    publisher TEXT,
    published_date TEXT,
    language TEXT,
    page_count INTEGER,
    cover_url TEXT,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### `user_book_entries`

Stores the user's personal reading record created from a reviewed source row.
MVP allows multiple entries to point to the same `book_id` when the same book is
imported from different sessions, because each entry preserves its own source
audit trail. Later product work may merge duplicate user entries into a single
canonical reading record.

```sql
CREATE TABLE IF NOT EXISTS user_book_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL REFERENCES books(id),
    status TEXT,                 -- read / want / reading
    rating REAL,
    tags_json TEXT,              -- JSON array
    comment TEXT,
    read_started_at TEXT,
    read_finished_at TEXT,
    marked_at TEXT,              -- date the user marked the book as want/reading
    douban_url TEXT,
    source_session_id INTEGER NOT NULL REFERENCES import_sessions(id),
    source_row_id INTEGER NOT NULL REFERENCES import_rows(id),
    confidence REAL NOT NULL DEFAULT 0.0,
    review_status TEXT NOT NULL DEFAULT 'accepted',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

**Source linkage:**
- `source_session_id` and `source_row_id` provide full audit trail back to raw input.
- Every committed entry must have these set.

## 4. Duplicate Handling

### Detection strategy

Before inserting a new `user_book_entry`, check for existing entries:

| Condition | Strategy |
|-----------|----------|
| Same title + same author | Treat as duplicate. Link new entry to existing book. |
| Same title + both missing author | Treat as duplicate. Link to existing book. |
| Same title + different author | Different book. Insert new `books` row. |
| Same title imported twice from same session | Skip second source row. Increment `import_sessions.duplicate_count`. |

### User override

The review payload can include `"force_insert": true` per row to bypass duplicate detection and create a new `books` row even if a similar one exists.

### Duplicate response

When a duplicate is detected during commit:
- Row status stays `committed`.
- `import_sessions.duplicate_count` increments when an existing book is reused or a repeated source row is skipped.
- Response includes `duplicate_row_ids` list.

## 5. Validation Report

`GET /api/imports/{id}/validate` returns reconciliation:

```json
{
  "session_id": 1,
  "raw_input_hash": "abc123...",
  "parsed_count": 5,
  "accepted_count": 4,
  "rejected_count": 1,
  "committed_count": 4,
  "duplicate_count": 0,
  "failed_count": 0,
  "warning_count": 2,
  "rows": [
    {
      "row_id": 1,
      "row_index": 0,
      "title": "思考，快与慢",
      "status": "committed",
      "book_id": 1,
      "warnings": []
    }
  ]
}
```

**Reconciliation rules:**
- `parsed_count` = rows in `import_rows` for this session.
- `accepted_count` = rows with status `accepted` or `committed`.
- `rejected_count` = rows with status `rejected`.
- `committed_count` = rows with status `committed` that have `user_book_entries`.
- `duplicate_count` = committed rows where existing book was reused.
- `failed_count` = rows that failed during commit (should be 0 in normal flow).
- `warning_count` = sum of row-level warnings.

## 6. API Acceptance Cases

### `GET /api/imports/{id}/review`

Returns current review state of all rows.

**Request:** None.

**Response 200:**
```json
{
  "session": { ... },
  "rows": [
    {
      "row_id": 1,
      "row_index": 0,
      "raw_fragment": "...",
      "parsed_json": { "title": "...", ... },
      "status": "pending",
      "confidence": 0.95,
      "warnings": []
    }
  ]
}
```

**Errors:** 404 if session not found.

### `POST /api/imports/{id}/review`

Submit review decisions for rows.

**Request:**
```json
{
  "rows": [
    { "row_id": 1, "action": "accept", "title": "...", ... },
    { "row_id": 2, "action": "reject" },
    { "row_id": 3, "action": "needs_edit", "title": "...", "comment": "fix me" }
  ]
}
```

**Response 200:**
```json
{
  "session": { "status": "reviewed", ... },
  "updated_rows": [
    { "row_id": 1, "status": "accepted" },
    { "row_id": 2, "status": "rejected" },
    { "row_id": 3, "status": "needs_edit" }
  ]
}
```

**Errors:**
- 404 if session not found.
- 422 if any `row_id` does not belong to this session.
- 422 if action is `accept` but title is empty.

### `POST /api/imports/{id}/commit`

Write accepted rows to durable library.

**Request:** None (reads accepted rows from DB).

**Response 200:**
```json
{
  "session": { "status": "committed", "inserted_count": 4, ... },
  "committed": [
    { "row_id": 1, "book_id": 1, "entry_id": 1 },
    { "row_id": 4, "book_id": 2, "entry_id": 2 }
  ],
  "duplicates": [
    { "row_id": 3, "existing_book_id": 1 }
  ],
  "skipped": [
    { "row_id": 2, "reason": "rejected" }
  ]
}
```

**Errors:**
- 404 if session not found.
- 409 if session already committed (status is `committed`). Commit is NOT idempotent by default.

### `GET /api/imports/{id}/validate`

Returns reconciliation report.

**Request:** None.

**Response 200:** Validation report JSON (see section 5).

**Errors:** 404 if session not found.

## 7. Tests To Implement In BG-012

### Review tests

```
test_review_accept_updates_row_status
  - POST review with action=accept
  - Assert row.status == "accepted"
  - Assert parsed_json fields are updated

test_review_reject_updates_row_status
  - POST review with action=reject
  - Assert row.status == "rejected"

test_review_needs_edit_updates_row_status
  - POST review with action=needs_edit
  - Assert row.status == "needs_edit"

test_review_accept_empty_title_returns_422
  - POST review with action=accept, title=""
  - Assert 422 response

test_review_invalid_row_id_returns_422
  - POST review with row_id that belongs to different session
  - Assert 422 response
```

### Commit tests

```
test_commit_accepted_rows_creates_books_and_entries
  - Create session, parse, review accept, commit
  - Assert books row exists with correct title
  - Assert user_book_entries row exists with source linkage
  - Assert import_row.status == "committed"

test_commit_rejected_rows_are_skipped
  - Create session, parse, review accept+reject, commit
  - Assert only accepted row is committed
  - Assert rejected row has no user_book_entries

test_commit_low_confidence_pending_rows_not_silently_committed
  - Create session with incomplete data (low confidence)
  - Call commit without review
  - Assert no books created for pending rows

test_commit_duplicate_same_title_same_author
  - Commit book A, then commit book A again from different session
  - Assert only one books row exists
  - Assert two user_book_entries point to same book_id with different source rows
  - Assert duplicate_count incremented

test_commit_source_linkage_audit_trail
  - Commit a row
  - Assert user_book_entries.source_session_id == session.id
  - Assert user_book_entries.source_row_id == row.id

test_commit_already_committed_returns_409
  - Commit session, then try to commit again
  - Assert 409 response

test_commit_empty_accepted_returns_zero
  - Session with only rejected rows, call commit
  - Assert inserted_count == 0
```

### Validation tests

```
test_validate_reconciles_counts
  - Session with 5 parsed, 3 accepted, 1 rejected, 3 committed
  - Assert validation report counts match

test_validate_after_commit_matches_db_state
  - Commit session
  - Call validate
  - Assert committed_count matches actual user_book_entries count
```

## 8. Design Constraints Summary

- Parser output (`import_rows`) is never directly committed.
- Review step is mandatory before commit.
- Repository persists reviewed data only.
- Every `user_book_entry` has full audit trail to `import_sessions` + `import_rows`.
- Commit is explicit, not silent.
- No metadata lookup, no graph generation, no LLM.
- Duplicate detection is title+author based, not fuzzy.
