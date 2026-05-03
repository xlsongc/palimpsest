# AI Import and Metadata Enrichment Design

## Decision

The import pipeline should not depend on AI for basic capture. The default path is:

1. Store raw paste unchanged.
2. Run a tolerant deterministic candidate extractor.
3. Show every candidate in review.
4. Commit only reviewed rows.

AI and external metadata lookup are enrichment layers. They should improve recall and fill missing fields, but they must not directly write final library records.

## Why

User paste formats are messy. A strict parser fails too easily, but putting an LLM directly in the parser makes imports harder to audit and test. The right split is:

- Deterministic parser: cheap, local, testable, extracts obvious candidates.
- AI extractor: optional fallback for ambiguous fragments, returns structured candidates with confidence and evidence.
- Metadata providers: lookup tools for book facts such as author, ISBN, publisher, cover, subjects, and descriptions.
- Review flow: the only gate that turns candidates into durable user library entries.

## Proposed Interfaces

### `ExtractionProvider`

Input:

- raw fragment
- source label, such as `douban`
- optional locale hint

Output:

- candidate title
- authors
- status
- dates
- rating
- tags
- comment
- confidence
- warnings
- evidence spans from the raw text

Providers:

- `deterministic_v1`
- future `mimo_structured_extractor`
- future `openai_structured_extractor`

### `MetadataProvider`

Input:

- title
- authors
- ISBN if available

Output:

- normalized metadata candidates
- provider name and provider id
- provider URL
- raw provider JSON
- confidence hints

Providers:

- Open Library
- Google Books
- future Douban URL evidence when present in pasted text

## Tool Use

AI should be allowed to call metadata tools through the backend service, not through React. The AI prompt should ask for structured JSON only and cite which raw text or provider result supports each field.

The AI is not the authority. It proposes candidates. The review screen remains the authority before database commit.

## Failure Behavior

- If deterministic parsing finds low-confidence rows, keep them reviewable.
- If AI extraction fails, keep deterministic candidates and surface warnings.
- If metadata lookup has multiple matches, store all candidates and require review.
- If no provider match exists, commit the user-provided title with missing metadata warnings.

## Next Implementation Tasks

1. Add `book_metadata_sources` persistence.
2. Add mocked `MetadataProvider` interface and tests.
3. Add `POST /api/imports/{id}/enrich` using mocked providers first.
4. Add AI extractor interface with a fake provider for tests.
5. Wire MiMo/OpenAI-compatible provider only after the fake provider path is stable.
