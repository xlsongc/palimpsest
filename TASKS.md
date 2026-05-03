# Tasks

Status key:

- `todo`
- `in_progress`
- `blocked`
- `review`
- `done`

## Current Focus

Build the project foundation without coupling future parser, metadata, graph, and LLM behavior into the app shell.

## Backlog

| ID | Status | Owner | Task | Verification |
| --- | --- | --- | --- | --- |
| BG-000 | done | planning | Write product and architecture spec | `SPEC.md` exists |
| BG-001 | done | planning | Write agent collaboration protocol | `AGENT_PROTOCOL.md` exists |
| BG-002 | done | planning | Write implementation plan | `IMPLEMENTATION_PLAN.md` exists |
| BG-003 | done | implementation | Scaffold FastAPI app under `apps/api` | `.venv/bin/python -m pytest` passes |
| BG-004 | done | implementation | Scaffold React + TypeScript + Vite app under `apps/web` | `npm run build` passes |
| BG-005 | done | implementation | Add frontend API client and health status display | Web calls `/api/health` |
| BG-006 | done | implementation | Provide representative Douban paste fixtures | Fixtures documented |
| BG-007 | done | implementation | Add SQLite import session schema/repository | API tests pass |
| BG-008 | done | implementation | Add `POST /api/imports` and `GET /api/imports/:id` | API tests pass |
| BG-009 | done | implementation | Implement deterministic Douban paste parser | Parser tests pass |
| BG-010 | done | implementation | Add import parse endpoint | API tests pass |
| BG-011 | done | planning | Define review/commit acceptance cases | Cases documented |
| BG-012a | done | implementation | Add review backend foundation | API tests pass |
| BG-012 | done | implementation | Add review and commit backend flow | API tests pass |
| BG-013 | todo | implementation | Add validation report endpoint | API tests pass |
| BG-014 | todo | implementation | Add basic import/review UI | Manual flow works |
| BG-015 | todo | planning | Define graph edge scoring v1 | Tests specified |
| BG-016 | todo | implementation | Add graph DTOs and deterministic edge builder | Edge tests pass |
| BG-017a | done | planning | Replace repo preview with high-fidelity static reading graph mock | Web build passes |
| BG-017 | todo | implementation | Adapt `book_graph_v2.html` design into React graph page | Web build + manual check |

## Completed Implementation Packet

BG-006 completed by implementation agent and reviewed by planning agent:

```md
## Task: BG-006 Douban Paste Fixtures

Result:
- Added representative Douban paste fixtures under `apps/api/tests/fixtures/douban_paste/`.
- Added fixture assumptions under `docs/fixtures/douban-paste.md`.
- No parser, database, or API implementation was added.
- Review fix: anonymized user-like copied text before public commit.

Verification:
- `python3 -m json.tool apps/api/tests/fixtures/douban_paste/*_expected.json`
- `cd apps/api && .venv/bin/python -m pytest`
```

First packet completed by implementation agent:

```md
## Task: BG-003/BG-004/BG-005 Scaffold Local App

Context:
This creates the project foundation from `SPEC.md` and `IMPLEMENTATION_PLAN.md`. Keep it minimal. Do not implement import parsing, metadata lookup, or graph logic yet.

Scope:
- Own `apps/api/**`
- Own `apps/web/**`
- May add root-level dev docs if needed
- Do not edit `SPEC.md`, `IMPLEMENTATION_PLAN.md`, or `AGENT_PROTOCOL.md` unless asked

Requirements:
- Create a FastAPI backend with `GET /api/health`.
- Create a React + TypeScript + Vite frontend.
- Add a small API client in the frontend.
- Show backend health status in the frontend.
- Add minimal test/check commands.

Acceptance Criteria:
- Backend can start locally.
- Frontend can start locally.
- Frontend can call `/api/health`.
- Backend tests pass.
- Frontend build or typecheck passes.

Constraints:
- No parser logic.
- No database schema yet unless required for project bootstrap.
- No graph implementation yet.
- Keep modules simple and boring.

Handoff Required:
- Changed files
- How to run API
- How to run web
- Verification commands and results
- Any blocker or dependency issue
```

## Next Implementation Packet

Recommended next packet for opencode + MiMo. The planning agent will review before any API endpoint or parser task starts.

```md
## Task: BG-007 SQLite Import Session Repository

Context:
Now that parser fixtures exist, create the durable import-session foundation. This task should define SQLite-backed persistence for import sessions and import rows, but it should not expose API endpoints or implement parser logic yet.

Scope:
- Own `apps/api/app/db/**`
- Own `apps/api/app/repositories/**`
- Own `apps/api/app/schemas/imports.py` if useful for typed DTOs
- Own `apps/api/tests/test_import_repository.py`
- May update `apps/api/pyproject.toml` only if adding a justified DB dependency
- Do not change route files except imports required by tests
- Do not add import API endpoints yet
- Do not implement Douban parser logic

Requirements:
- Add a minimal SQLite connection/session utility.
- Add schema creation for:
  - `import_sessions`
  - `import_rows`
- Add repository functions or class methods for:
  - creating an import session with `source`, `raw_input`, and computed `raw_hash`
  - retrieving an import session by id
  - adding import rows linked to a session
  - listing import rows for a session in `row_index` order
- Preserve raw input unchanged.
- Use deterministic SHA-256 hashing for raw input.
- Keep repository code free of parser/provider/LLM behavior.
- Prefer simple, explicit code over a broad ORM abstraction.

Acceptance Criteria:
- Tests can create an isolated temporary SQLite database.
- Tests prove raw input is stored unchanged.
- Tests prove `raw_hash` is deterministic.
- Tests prove import rows are linked to sessions and returned in row order.
- No parser code, metadata lookup, or route endpoint is added.

Constraints:
- Low coupling: repository does persistence only.
- Do not introduce Alembic/migrations yet unless strongly justified.
- Do not store local DB files in git.

Verification:
- `cd apps/api && .venv/bin/python -m pytest`

Handoff Required:
- Changed files.
- DB dependency decision, if any.
- Repository API summary.
- Verification results.
- Risks or follow-ups.
```
