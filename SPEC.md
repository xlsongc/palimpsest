# Palimpsest / 忘筌 MVP Spec

## Purpose

Palimpsest / 忘筌 is a personal reading data system with a web graph interface. Its job is to move a user's reading history out of Douban-style pages and into an owned database, enrich it with book metadata, verify that imports are complete, and render the resulting reading network as an explorable webpage.

The graph is not only a visual effect. It should explain how books connect through author, topic, tags, reading sequence, user notes, and external metadata.

The deeper product goal is to maximize the user's reading leverage. This project is not only a record of books read. It should turn reading into searchable, connected, reusable, and actionable knowledge assets.

Name thesis:

```text
Palimpsest: reading traces are layered, overwritten, and made visible again.
忘筌: books, notes, graphs, and AI are means, not ends.
得鱼而忘筌；得意而忘言。
```

Product thesis:

```text
Not "I have read many books."
Instead: "I can let what I have read return when a project, question, or decision needs it."
```

## Reading Leverage Goals

The long-term product should optimize four outcomes:

- `Recall`: Can the user quickly retrieve relevant books, notes, highlights, and ideas they have encountered before?
- `Connection`: Can the system discover useful relationships between books, notes, concepts, projects, and decisions?
- `Application`: Can the system connect reading to the user's active projects, questions, and judgments?
- `Compounding`: Does each new imported book make the older reading network more valuable?

These goals define the product direction. The graph is an interface, not the product itself. The product is a personal reading intelligence infrastructure.

## Personal-First Success Criteria

The first version should optimize the creator's own reading leverage before trying to become a general product. A feature is valuable only if it helps the user recall, connect, apply, or produce from their reading with less friction than their current workflow.

MVP success should be measured by personal utility:

- The user can import a meaningful slice of their Douban reading history and trust that the import is complete.
- The user can open a book card and immediately see why that book matters to them, not only generic metadata.
- The user can search a topic, project, or question and recover relevant books and notes faster than manual memory.
- The graph reveals at least a few non-obvious but explainable connections.
- The system can suggest a useful next reading path for one real user goal.
- Adding a new book makes at least one old book easier to rediscover or reuse.

This implies a design preference:

- Prefer one excellent personal workflow over many generic features.
- Prefer evidence-backed, editable outputs over impressive but unverifiable AI claims.
- Prefer low-friction capture over comprehensive forms.
- Prefer small synthesis loops that create reusable notes, summaries, and project links.

## Personal Workflow Loops

The app should support repeated loops that make reading compound.

### Import Loop

```text
Paste source -> parse -> review -> commit -> validation report
```

Question it answers:

```text
Did my reading record get captured completely and correctly?
```

### Reflection Loop

```text
Open book card -> add one-sentence summary -> add disagreement -> add project relevance
```

Question it answers:

```text
What did this book change, support, or challenge for me?
```

### Connection Loop

```text
Select book -> inspect suggested edges -> accept/edit/reject reasons
```

Question it answers:

```text
How does this book fit into my existing knowledge map?
```

### Retrieval Loop

```text
Ask a question -> retrieve books/notes/edges -> inspect citations -> save result
```

Question it answers:

```text
What have I already read that helps with this problem?
```

### Output Loop

```text
Choose project/question -> collect relevant reading evidence -> generate digest -> edit final note
```

Question it answers:

```text
How can I turn reading into a concrete decision, essay, plan, or project insight?
```

These loops should guide implementation priority more than visual polish.

## Reading Leverage Model

The system should evolve through five layers.

### 1. Capture

The first obligation is to capture reading data without losing source evidence.

Sources:

- Douban paste import.
- Manual entry.
- Kindle highlights and notes in a future optional importer.
- WeChat Reading, Apple Books, and other reading platforms in future optional importers.
- Reading notes pasted manually.
- Quotes, highlights, comments, tags, and post-reading summaries.

The key principles are low friction and verification. Every import should report what was provided, what was extracted, what was committed, what failed, and which fields remain incomplete.

### 2. Structure

Each book should become more than a title. Over time, the system should support structured attributes such as:

- Title.
- Author.
- Reading status.
- Reading dates.
- Rating.
- Themes and tags.
- Core concepts.
- Key people.
- Key events.
- Related disciplines.
- Problems this book helps solve.
- User one-sentence summary.
- Points the user disagrees with.
- Relevance to current projects.

Structured reading data enables search, comparison, graph building, recommendation, and later retrieval.

### 3. Connect

The graph should represent a knowledge landscape, not just category clusters.

Connections should answer questions like:

- What question does this book help answer?
- Which books disagree with it?
- Is this book prerequisite knowledge for another book?
- Which long-term project does this book support?
- Which judgment or belief did this book change?
- Which books form a shared mental model?

Additional long-term edge types:

- `prerequisite`: one book is useful before another.
- `contradicts`: books disagree or present incompatible claims.
- `extends`: one book extends another.
- `same_problem`: books address the same problem.
- `same_framework`: books use or teach the same mental model.
- `applies_to_project`: a book is relevant to a project.
- `changed_belief`: a book changed or challenged a user belief.

These edges are more valuable than simple theme clustering because they preserve how the reading can be used.

### 4. Retrieve

The system should eventually answer questions against the user's own reading memory.

Example:

```text
I want to understand long-term Japanese economic stagnation. Which books and notes are relevant?
```

Expected retrieval:

- Relevant books such as `失去的三十年`, `非理性繁荣`, `涛动周期论`, and `经济学原理`.
- User notes and highlights.
- Adjacent graph nodes.
- Edge explanations.
- Suggested reading path.

The long-term feature name is `Ask My Library`. It should be grounded in the user's books, notes, highlights, ratings, comments, and graph, not generic model knowledge.

### 5. Synthesize

Reading becomes more valuable when it produces reusable output.

Potential agents:

- `reading_digest_agent`: generates a personal summary of a book.
- `connection_agent`: explains why two books are connected.
- `project_relevance_agent`: maps books and notes to active projects.
- `belief_update_agent`: records how a book changed or challenged a user judgment.
- `reading_path_agent`: suggests next books based on a goal.
- `review_agent`: periodically resurfaces important books, notes, and unresolved ideas.

These agents should operate on verified library data and preserve citations back to books, notes, highlights, and import evidence.

## Product Positioning

Adjacent products exist, so the project should not position itself as merely an "AI reading graph".

Comparable categories:

- Readwise and Reader: strong at highlight capture, review, export, and API access.
- Emdash: close to AI-assisted highlight organization, semantic search, and offline-first reading snippets.
- Hikara: close to AI-powered book knowledge graphs and book-to-book relations.
- Obsidian Kindle plugins: strong at highlight import into a note vault.
- Goodreads and The StoryGraph: strong at book tracking, stats, recommendations, and social reading.

This project's differentiation should be:

- Douban-first import path for Chinese reading history.
- Import audit as a first-class feature.
- Explainable graph edges with evidence and reasons.
- Unified book cards combining user status, notes, highlights, metadata, and graph links.
- Optional highlights as enrichment, not a required workflow.
- Local-first, low-coupling architecture where providers, parsers, LLM tools, and graph algorithms can be replaced.
- Emphasis on personal project relevance and decision support, not only remembering highlights.

Positioning statement:

```text
A verifiable personal reading intelligence system.
```

Chinese positioning:

```text
可验证的个人阅读知识基础设施。
```

## Product Shape

The MVP is a local-first React + FastAPI web app:

- A paste-based import workflow for reading records copied from Douban.
- A review workflow that shows parsed books, uncertain matches, duplicates, and missing fields before committing.
- A database-backed reading library using SQLite first, with a migration path to Postgres.
- A metadata enrichment pipeline using online book databases.
- A graph page based on `book_graph_v2.html`, but backed by real API data instead of hard-coded nodes and links.
- A verification report for every import session.

## Architecture Principles

The project should be low-coupling by default. Modules that change often must not leak into stable modules.

Likely high-change areas:

- Douban copied-page formats.
- Metadata provider APIs.
- LLM prompts and extraction behavior.
- Graph edge scoring.
- Graph rendering mode, including 2D, timeline, and future 3D.

Likely lower-change areas:

- Domain models.
- Database schema.
- API DTO contracts.
- Import validation invariants.

Core rules:

- The frontend never calls metadata providers directly.
- Parsers never write to the database directly.
- LLM tools never write durable records directly.
- Metadata providers never decide final user library entries.
- Graph builders never depend on raw Douban text.
- Database repositories do not know about React, D3, LLM prompts, or external API clients.
- Every module passes structured DTOs instead of ad hoc dictionaries where practical.

Dependency direction:

```text
apps/web -> apps/api -> services -> repositories -> database
                         |
                         -> importers
                         -> metadata providers
                         -> graph builders
                         -> agent tools
```

Forbidden dependency direction:

```text
provider -> database write
parser -> database write
LLM -> database write
React component -> provider API
graph renderer -> Douban raw input
repository -> service business rules
```

## Technology Decisions

### Frontend

Use React + TypeScript + Vite.

Reason:

- The app is not just a static graph. It needs import, review, audit, library, graph, and book-card workflows.
- Review state will be interactive: user corrections, metadata candidates, confidence warnings, duplicate resolution, and commit gating.
- The graph can still use D3, but D3 should be scoped to the graph component.
- Future views such as timeline and 3D can be separate feature modules without rewriting the app shell.

React owns:

- Routing.
- API data fetching.
- Import/review/audit UI state.
- Book card state.
- Layout and navigation.

D3 owns:

- Force simulation.
- SVG graph rendering inside a bounded React component.
- Node dragging, zooming, and hover geometry.

D3 must not own the full page or global app state.

### Backend

Use FastAPI for the MVP API.

Reason:

- Python is practical for parsing, metadata cleanup, LLM extraction, and graph-building workflows.
- The API surface is small and benefits from typed request/response models.
- SQLite works cleanly for local MVP and can later migrate to Postgres.

### Database

Use SQLite first. Keep schema portable enough for Postgres.

Avoid:

- SQLite-only behavior in business logic.
- Provider-specific raw JSON as the only source of normalized fields.
- Hidden writes that bypass import validation.

## Project Layout

Target layout:

```text
book_graph/
  SPEC.md
  apps/
    api/
      app/
        main.py
        routes/
        services/
        repositories/
        schemas/
      tests/
    web/
      src/
        app/
        features/
          import/
          review/
          graph/
          library/
          audit/
        shared/
          api/
          types/
          ui/
  packages/
    core/
      domain/
      dto/
      validation/
    importers/
      douban_paste/
    metadata/
      providers/
      matching/
    graph/
      edge_builder/
      scoring/
    agents/
      extraction/
      prompts/
  data/
    local/
```

The exact directory structure can be adjusted during implementation, but these ownership boundaries should stay intact.

## Non-Goals For MVP

- No automatic scraping of logged-in Douban pages.
- No dependency on unstable unofficial Douban APIs.
- No account system or multi-user support.
- No fully autonomous write-to-database behavior without review for low-confidence records.
- No 3D graph until the 2D data model, import pipeline, and validation loop are reliable.
- No requirement to import Kindle or other highlights in the first MVP.

## Data Sources

### Primary Input

The first supported input is manual paste from Douban reading pages. The user can copy text or HTML from lists such as:

- Want to read
- Reading
- Read
- Book detail snippets
- User comments, ratings, dates, and tags if visible in the copied content

The raw pasted content must be stored unchanged in an import session so every parsed field can be traced back to source evidence.

### Metadata Providers

Book metadata lookup should be provider-based:

- Open Library for free public title, author, ISBN, cover, and edition data.
- Google Books for broader title/ISBN lookup and Chinese/English coverage.
- Future provider: Douban page evidence when the pasted content includes a Douban URL or ISBN.

Provider results are suggestions, not ground truth. Each result must keep raw provider JSON and a confidence score.

### Highlights And Notes

Highlights, notes, and clippings are valuable but optional enrichment data. They should not block the basic book import workflow.

Recommended modes:

- `zero_friction`: only import reading records and metadata.
- `optional_paste`: paste notes or highlights for a book when available.
- `batch_enrichment`: periodically import Kindle `My Clippings.txt` or other exported highlight files.

The product should never require the user to clean and organize highlights after every reading session. Highlights should make the system smarter when available, while the core library remains useful without them.

## Import Flow

1. User pastes Douban reading content into the import page.
2. The app creates an `import_session` with the raw text/html and a content hash.
3. The parser extracts candidate reading entries.
4. The normalizer cleans titles, authors, dates, statuses, ratings, tags, comments, and URLs.
5. Metadata lookup runs for each candidate.
6. The matcher selects the best metadata candidate or marks the row as uncertain.
7. The review page shows:
   - Extracted books
   - Duplicates
   - Missing fields
   - Low-confidence metadata matches
   - Rows that could not be parsed
8. The user confirms or edits the review result.
9. Confirmed entries are written to the database.
10. The validation report compares expected, extracted, reviewed, inserted, duplicate, and failed counts.

## Module Contracts

Each module returns a narrow result type. These contracts are more important than implementation details.

### Importer Contract

Input:

- Raw copied text or HTML.
- Source type.

Output:

- `ParsedImportRow[]`
- Each row includes `raw_fragment`, extracted fields, warnings, and parser confidence.

No database writes.

### Normalizer Contract

Input:

- `ParsedImportRow`

Output:

- `NormalizedBookCandidate`
- Canonical title, authors, ISBN candidates, status, rating, dates, tags, comment, and source URL.

No provider calls.
No database writes.

### Metadata Provider Contract

Input:

- Title, author, ISBN, or provider ID.

Output:

- `MetadataCandidate[]`
- Each candidate includes provider name, provider ID, normalized fields, raw JSON, and confidence hints.

No final matching decision.
No database writes.

### Matcher Contract

Input:

- `NormalizedBookCandidate`
- `MetadataCandidate[]`

Output:

- `MatchDecision`
- Selected candidate, confidence score, mismatch reasons, and review requirement.

No database writes.

### Repository Contract

Input:

- Already reviewed DTOs from services.

Output:

- Durable records and read models.

Repositories do not call parsers, providers, or LLM tools.

### Graph Builder Contract

Input:

- Normalized books.
- User entries.
- Metadata.
- Existing manual edges.

Output:

- `BookEdge[]`
- Edge type, weight, reason, and evidence.

No rendering logic.

## Agent Tools

The coding/data agent should expose small, auditable tools:

- `parse_douban_paste(raw_input)` extracts candidate entries from copied text or HTML.
- `normalize_book(candidate)` standardizes book fields.
- `lookup_book_metadata(title, author, isbn)` queries metadata providers.
- `match_book(candidate, provider_results)` ranks metadata candidates and returns confidence.
- `validate_import(session_id)` audits parsed rows against committed database rows.
- `build_graph_edges(library_id)` creates or refreshes book graph links.
- `explain_edge(source_book_id, target_book_id)` returns a human-readable connection reason.
- `audit_library()` reports incomplete metadata, duplicate candidates, orphan books, and low-confidence records.

LLM-based extraction can be used, but all LLM outputs must include source evidence, confidence, and review status before durable writes.

Agent tools are service-layer helpers, not owners of persistence. They return structured results that the API service validates and commits.

## Database Model

SQLite is the MVP database. The schema should avoid SQLite-specific features that would block a later Postgres migration.

### `import_sessions`

- `id`
- `source`
- `raw_input`
- `raw_hash`
- `created_at`
- `expected_count`
- `extracted_count`
- `reviewed_count`
- `inserted_count`
- `duplicate_count`
- `warning_count`
- `status`

### `import_rows`

- `id`
- `session_id`
- `row_index`
- `raw_fragment`
- `parsed_json`
- `normalized_json`
- `status`
- `confidence`
- `warnings_json`
- `created_at`

### `books`

- `id`
- `title`
- `subtitle`
- `authors_json`
- `isbn10`
- `isbn13`
- `publisher`
- `published_date`
- `language`
- `page_count`
- `cover_url`
- `description`
- `created_at`
- `updated_at`

### `user_book_entries`

- `id`
- `book_id`
- `status`
- `rating`
- `tags_json`
- `comment`
- `read_started_at`
- `read_finished_at`
- `douban_url`
- `source_session_id`
- `source_row_id`
- `confidence`
- `review_status`
- `created_at`
- `updated_at`

### `book_metadata_sources`

- `id`
- `book_id`
- `provider`
- `provider_id`
- `provider_url`
- `raw_json`
- `confidence`
- `created_at`

### `book_edges`

- `id`
- `source_book_id`
- `target_book_id`
- `edge_type`
- `weight`
- `reason`
- `evidence_json`
- `generated_by`
- `created_at`
- `updated_at`

### `annotations`

- `id`
- `book_id`
- `source`
- `raw_text`
- `highlight_text`
- `note_text`
- `location`
- `captured_at`
- `confidence`
- `created_at`

### `annotation_concepts`

- `id`
- `annotation_id`
- `concept`
- `confidence`
- `created_at`

### `book_insights`

- `id`
- `book_id`
- `insight_type`
- `content`
- `evidence_json`
- `generated_by`
- `confidence`
- `created_at`

## Graph Edge Rules

Edges should be deterministic first, AI-assisted second. Each edge needs a type, weight, and explanation.

Base scoring:

- Same author: `+5`
- Same explicit user tag: `+3`
- Same topic/category: `+3`
- Same series or canonical work/translation pair: `+4`
- Reading sequence proximity: `+1`
- Similar description or notes: `+2` to `+5`
- Shared external subject/classification: `+2`
- User manually confirmed edge: `+10`

Example edge types:

- `same_author`
- `same_topic`
- `knowledge_progression`
- `historical_context`
- `investment_framework`
- `technical_foundation`
- `literary_style`
- `reading_sequence`
- `manual`
- `prerequisite`
- `contradicts`
- `extends`
- `same_problem`
- `same_framework`
- `applies_to_project`
- `changed_belief`

## API Surface

MVP endpoints:

- `POST /api/imports` creates an import session from pasted content.
- `GET /api/imports/:id` returns session status and rows.
- `POST /api/imports/:id/parse` parses raw input into rows.
- `POST /api/imports/:id/enrich` runs metadata lookup and matching.
- `POST /api/imports/:id/commit` writes reviewed rows to the library.
- `GET /api/imports/:id/validate` returns the audit report.
- `GET /api/books` returns the library list.
- `GET /api/books/:id` returns a book card payload.
- `GET /api/graph` returns graph nodes and edges.
- `POST /api/graph/rebuild` refreshes graph edges from current data.

API response models should be typed and stable. The React app should depend on these DTOs, not on database table shapes.

Important DTOs:

- `ImportSessionDTO`
- `ImportRowDTO`
- `ReviewRowDTO`
- `ValidationReportDTO`
- `BookListItemDTO`
- `BookCardDTO`
- `GraphNodeDTO`
- `GraphEdgeDTO`

The graph page should load `GraphNodeDTO[]` and `GraphEdgeDTO[]` from `/api/graph`. It should not know how those edges were generated.

## Frontend Views

### Import View

- Paste area for Douban copied content.
- Source selector.
- Parse button.
- Import session summary.

### Review View

- Table of parsed rows.
- Confidence badges.
- Duplicate warnings.
- Missing field warnings.
- Metadata candidate selector for uncertain matches.
- Commit button disabled until blocking warnings are handled.

### Graph View

Based on the `book_graph_v2.html` design:

- Paper-like background.
- Courier Prime style typography.
- Top search and status filters.
- D3 force graph.
- Theme-colored nodes.
- Curved links.
- Right-side book card on node click.
- Card includes user reading info and enriched metadata.
- Link explanations shown in related-reading list.

Implementation rule:

- The existing HTML prototype is visual reference, not the production structure.
- Recreate the relevant appearance and interactions as React components.
- Keep D3 isolated inside `features/graph/components/BookGraphCanvas`.
- The card, filters, search box, and audit affordances should be React components.

### Audit View

- Import count reconciliation.
- Missing metadata.
- Low-confidence rows.
- Duplicates.
- Books without graph edges.
- Edges without clear explanation.

## Validation Rules

Every import session must produce a validation report:

- Raw input hash is stored.
- Number of extracted rows is recorded.
- Number of committed entries is recorded.
- Duplicate rows are listed.
- Failed rows keep raw fragments.
- Low-confidence matches are review-blocking by default.
- Every committed `user_book_entry` links back to an import row.
- Every graph edge has a deterministic reason or manual confirmation.

## Implementation Plan

### Phase 0: Scaffold

- Create React + TypeScript + Vite frontend.
- Create FastAPI backend.
- Add shared DTO naming conventions.
- Add SQLite configuration.
- Add basic health-check endpoint.
- Add frontend API client.

### Phase 1: Import + Validation MVP

- Create SQLite schema.
- Add paste import API.
- Implement parser for common Douban copied text/html.
- Add review and commit flow.
- Add validation report.

### Phase 2: Metadata Enrichment

- Add Open Library provider.
- Add Google Books provider.
- Add matching and confidence scoring.
- Store raw metadata source records.

### Phase 3: Graph From Real Data

- Replace hard-coded `book_graph_v2.html` data with `/api/graph`.
- Build deterministic graph edge generation.
- Add card payload endpoint.
- Show metadata and edge explanations in the card.

### Phase 4: Better Import Ergonomics

- Add browser-side helper for copying structured page content.
- Add CSV/JSON export/import.
- Consider RSS or third-party Douban export compatibility if reliable.

### Phase 5: Optional Highlights And Notes

- Add manual note/highlight paste.
- Add Kindle `My Clippings.txt` importer.
- Extract concepts from highlights.
- Connect highlights to books, graph edges, and book-card insights.

### Phase 6: Ask My Library

- Add retrieval over books, notes, highlights, and graph edges.
- Return answers with citations to library evidence.
- Add reading path suggestions for user questions and projects.
- Add synthesis agents only after import validation and graph evidence are reliable.

### Phase 7: Optional 3D View

- Add Three.js graph only after the 2D graph and data pipeline are stable.
- Keep 3D as an alternate view, not the primary data validation interface.

## Open Questions

- Should user edits be stored as patch history for auditability?
- How much manual graph editing should be supported in MVP?
- Should AI extraction be mandatory, or should a deterministic parser run first with AI fallback?
- Should the local dev workflow use one command to start both FastAPI and Vite?
- Should shared DTOs be generated from OpenAPI, or manually mirrored in TypeScript for the MVP?
