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
| BG-006 | todo | planning | Provide representative Douban paste fixtures | Fixtures documented |
| BG-007 | todo | implementation | Add SQLite import session schema/repository | API tests pass |
| BG-008 | todo | implementation | Add `POST /api/imports` and `GET /api/imports/:id` | API tests pass |
| BG-009 | todo | implementation | Implement deterministic Douban paste parser | Parser tests pass |
| BG-010 | todo | implementation | Add import parse endpoint | API tests pass |
| BG-011 | todo | planning | Define review/commit acceptance cases | Cases documented |
| BG-012 | todo | implementation | Add review and commit backend flow | API tests pass |
| BG-013 | todo | implementation | Add validation report endpoint | API tests pass |
| BG-014 | todo | implementation | Add basic import/review UI | Manual flow works |
| BG-015 | todo | planning | Define graph edge scoring v1 | Tests specified |
| BG-016 | todo | implementation | Add graph DTOs and deterministic edge builder | Edge tests pass |
| BG-017 | todo | implementation | Adapt `book_graph_v2.html` design into React graph page | Web build + manual check |

## Completed Implementation Packet

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

Recommended next packet:

```md
## Task: BG-006 Douban Paste Fixtures

Context:
The parser should be test-driven against realistic copied Douban reading records. Before implementing parser logic, define representative fixtures and expected parsed rows.

Scope:
- Own `apps/api/tests/fixtures/douban_paste/**`
- May add parser fixture documentation under `docs/fixtures/`
- Do not implement parser logic yet

Requirements:
- Add at least 3 raw paste fixtures:
  - read list sample
  - want-to-read list sample
  - noisy mixed sample
- Add expected parsed JSON for each fixture.
- Preserve raw fragments and expected warnings.

Acceptance Criteria:
- Fixture files are committed.
- Expected outputs document title, status, rating/comment/date when available, and parser confidence expectations.

Constraints:
- No parser code.
- No database changes.

Handoff Required:
- Added fixture files
- Explanation of assumptions
- Open questions about real Douban copy format
```
