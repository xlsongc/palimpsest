# Implementation Plan

## North Star

Build a low-coupling, local-first reading intelligence system that first improves the user's own ability to capture, recall, connect, apply, and synthesize reading.

The first milestone is not a beautiful graph. It is a trusted personal reading database with an auditable import loop.

## Architecture Target

Default stack:

- Frontend: React + TypeScript + Vite.
- Backend: FastAPI.
- Database: SQLite for MVP, Postgres-compatible schema discipline.
- Graph rendering: D3 isolated inside a React graph component.
- Metadata: provider adapters behind backend services.

Dependency rule:

```text
web -> api -> services -> repositories -> database
                 |
                 -> importers
                 -> metadata providers
                 -> graph builders
                 -> agent tools
```

## Milestone 0: Scaffold

Goal:

Create a runnable local app shell with separated frontend and backend, health checks, DTO conventions, and test commands.

Deliverables:

- `apps/api` FastAPI app.
- `apps/web` React + TypeScript + Vite app.
- Health endpoint: `GET /api/health`.
- Frontend API client that calls health endpoint.
- Basic dev instructions.
- Initial test commands for API and web.

Acceptance:

- API starts locally.
- Web starts locally.
- Web can display backend health status.
- Tests/checks run from documented commands.

Suggested owner:

- Implementation agent.

Planning-agent review focus:

- Directory boundaries.
- Commands are simple.
- No premature abstractions.

## Milestone 1: Import Session Core

Goal:

Create the auditable import foundation before enrichment or graph work.

Deliverables:

- SQLite schema for `import_sessions` and `import_rows`.
- Repository layer for import sessions.
- `POST /api/imports`.
- `GET /api/imports/:id`.
- Raw input hashing.
- Session status and count fields.
- Tests for session creation and retrieval.

Acceptance:

- Pasted raw input is stored unchanged.
- Same raw input hash can be reproduced.
- API returns a stable `ImportSessionDTO`.
- Tests cover normal and empty input behavior.

Suggested owner:

- Implementation agent.

Planning-agent review focus:

- Parser is not mixed into repository.
- DTO is not a direct database dump unless intentionally stable.

## Milestone 2: Douban Paste Parser

Goal:

Extract candidate book rows from copied Douban text or HTML without writing durable book records.

Deliverables:

- `packages/importers/douban_paste` or equivalent backend module.
- `parse_douban_paste(raw_input)` contract.
- Parser tests with sample pasted text fixtures.
- `POST /api/imports/:id/parse`.
- Import rows with raw fragments, parsed JSON, warnings, confidence.

Acceptance:

- Parser returns structured rows from representative Douban paste samples.
- Unparsed fragments are retained or reported.
- Parse step updates session extracted count.
- Tests cover at least:
  - read/want/reading status if available
  - title extraction
  - rating/comment/date when visible
  - noisy lines

Suggested owner:

- Planning agent should define fixtures first.
- Implementation agent can implement parser against fixtures.

Planning-agent review focus:

- Parser is deterministic first.
- LLM extraction is not required for the first parser.
- Raw source evidence is preserved.

## Milestone 3: Review And Commit

Goal:

Let the user review parsed rows and commit verified book entries into the library database.

Deliverables:

- Schema for `books` and `user_book_entries`.
- Review DTO.
- Commit endpoint: `POST /api/imports/:id/commit`.
- Duplicate detection by title/author/ISBN where available.
- Validation endpoint: `GET /api/imports/:id/validate`.
- Basic Review UI.

Acceptance:

- Low-confidence rows are not silently committed.
- Every committed user entry links to source session and row.
- Validation report reconciles extracted, reviewed, inserted, duplicate, failed counts.
- Tests cover duplicate handling and source linkage.

Suggested owner:

- Split backend and frontend into separate task packets.

Planning-agent review focus:

- Commit service owns validation.
- Repository only persists reviewed records.

## Milestone 4: Metadata Enrichment

Goal:

Add book metadata lookup without making external providers part of the core domain.

Deliverables:

- Provider interface.
- Open Library provider.
- Google Books provider.
- Metadata candidate DTO.
- Matching service.
- `book_metadata_sources` persistence.
- `POST /api/imports/:id/enrich`.

Acceptance:

- Provider failures do not break import sessions.
- Raw provider response is stored after user/commit flow requires it.
- Candidate matching includes confidence and mismatch reasons.
- Tests use mocked provider responses.

Suggested owner:

- Implementation agent for provider interface and mocks.
- Planning agent for matching acceptance criteria.

Planning-agent review focus:

- No frontend direct provider calls.
- No provider direct DB writes.

## Milestone 5: Graph From Real Data

Goal:

Generate explainable graph nodes and edges from committed library data.

Deliverables:

- `GraphNodeDTO`.
- `GraphEdgeDTO`.
- Deterministic edge builder.
- Edge scoring tests.
- `GET /api/graph`.
- `POST /api/graph/rebuild`.
- React graph page adapted from `book_graph_v2.html`.

Acceptance:

- Graph loads from API, not hard-coded arrays.
- Every edge has type, weight, reason, and evidence.
- Graph renderer does not know edge-generation rules.
- Book card shows user reading info, metadata, related books, and edge reasons.

Suggested owner:

- Planning agent handles graph scoring design.
- Implementation agent handles backend DTO/API and React/D3 component in separate tasks.

Planning-agent review focus:

- D3 stays inside graph component.
- Edge reasons are useful, not just labels.

## Milestone 6: Personal Reflection Fields

Goal:

Start improving the user's own reading leverage beyond raw book tracking.

Deliverables:

- Fields for one-sentence summary, disagreement, project relevance, and problems helped.
- Book card editing UI.
- Audit for books missing personal reflection fields.

Acceptance:

- User can add personal meaning to a book quickly.
- These fields appear in search/card/graph context.
- No long required form blocks the import workflow.

Suggested owner:

- Implementation agent for CRUD and UI.
- Planning agent for UX acceptance criteria.

## Milestone 7: Optional Highlights

Goal:

Add highlights as enrichment, not as required import input.

Deliverables:

- `annotations` schema.
- Manual paste importer.
- Later: Kindle `My Clippings.txt` parser.
- Concept extraction interface.
- Book card highlights section.

Acceptance:

- Core library works without annotations.
- Highlights can be linked to books.
- Extracted concepts preserve evidence.

Suggested owner:

- Later milestone, not started until import and graph are stable.

## Milestone 8: Ask My Library

Goal:

Retrieve and synthesize from the verified personal library.

Deliverables:

- Retrieval endpoint over books, notes, highlights, and graph edges.
- Answers with citations.
- Saved answer/digest output.
- Reading path suggestions.

Acceptance:

- The answer cites internal evidence.
- The answer can be inspected and corrected.
- The system helps with at least one real user question.

Suggested owner:

- Planning agent leads design.
- Implementation agent implements retrieval infrastructure after data quality is sufficient.

## Immediate Next Tasks

1. Scaffold app directories and toolchain.
2. Add API health endpoint and tests.
3. Add React shell and health check display.
4. Create first parser fixtures from real or representative Douban paste samples.
5. Implement import session database and API.

## Execution Strategy

Use small task packets.

Recommended task size:

- 1-4 files for parser/service tasks.
- 1 API feature at a time.
- 1 frontend screen or component family at a time.

Do not combine:

- Scaffold and parser.
- Parser and metadata enrichment.
- Metadata provider and commit flow.
- Graph rendering and graph scoring.

Each task should update `TASKS.md` when status changes.
