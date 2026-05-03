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

Recommended next packet for opencode + MiMo. The planning agent will review the handoff before parser implementation starts.

```md
## Task: BG-006 Douban Paste Fixtures

Context:
We need realistic parser fixtures before writing parser code. The goal is to make Douban import test-driven and auditable.

Scope:
- Own `apps/api/tests/fixtures/douban_paste/**`
- May add `docs/fixtures/douban-paste.md`
- Do not implement parser logic yet
- Do not change database or API code

Requirements:
- Add at least 3 raw fixture files:
  - `read_list_raw.txt`
  - `want_list_raw.txt`
  - `mixed_noisy_raw.txt`
- Add expected parsed JSON files for each fixture:
  - `read_list_expected.json`
  - `want_list_expected.json`
  - `mixed_noisy_expected.json`
- Each expected row should include `raw_fragment`, `title`, `status`, optional visible fields, `confidence`, and `warnings`.
- Document assumptions about copied Douban formats.

Acceptance Criteria:
- Fixture files are readable and expected JSON is valid.
- Fixtures cover happy path and noisy input.
- No parser implementation is added.

Constraints:
- No parser code.
- No database changes.

Verification:
- `python -m json.tool <expected-json-file>` works for all expected JSON files.

Handoff Required:
- Changed files.
- Assumptions about Douban copied text.
- Any real sample gaps that need user input.
- Verification results.
```
