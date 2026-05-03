# Development Checklist

This checklist governs the full development phase. The planning agent owns architecture, task boundaries, and code review. The implementation agent, usually opencode + MiMo, owns scoped implementation packets.

## Planning Agent Responsibilities

- Keep `SPEC.md`, `IMPLEMENTATION_PLAN.md`, `TASKS.md`, and `AGENT_PROTOCOL.md` current.
- Define one implementation packet at a time.
- Provide clear acceptance criteria and verification commands.
- Review implementation handoffs before merging or assigning the next dependent task.
- Watch for coupling violations.
- Handle framework-level decisions and difficult cross-module design.
- Update task status after review.

## Implementation Agent Responsibilities

- Work only on the assigned task packet.
- Keep changes scoped to owned files.
- Prefer TDD for parsers, validation, matching, graph scoring, and API contracts.
- Run required verification before handoff.
- Report changed files, verification results, risks, and open questions.
- Stop and ask if a task requires changing architecture, schemas, or module boundaries.

## Before Assigning A Task

- The task maps to a milestone in `IMPLEMENTATION_PLAN.md`.
- The task has a single owner.
- The task has explicit non-goals.
- The task names files or directories the implementation agent may edit.
- The task includes at least one verification command or manual check.
- The task does not combine unrelated concerns.

## During Implementation

- Parser code does not write to the database.
- LLM output does not write durable records directly.
- Metadata providers do not decide final library entries.
- React components do not call external book APIs directly.
- Graph rendering does not depend on raw Douban text.
- Repositories do not contain business rules from services.
- DTOs are explicit and stable.
- Raw source evidence is preserved for import and AI-derived outputs.

## Review Checklist

- Does the implementation satisfy the task packet?
- Did it avoid scope expansion?
- Are tests/checks included and passing?
- Are new dependencies justified?
- Are generated/cache/build files excluded from git?
- Are raw imports, parser outputs, and generated decisions auditable?
- Are low-confidence or ambiguous results surfaced instead of silently committed?
- Does the code remain understandable for the next agent?

## Merge / Commit Checklist

- `git status --short` contains only intentional changes.
- API checks pass when API code changed:

```bash
cd apps/api
.venv/bin/python -m pytest
```

- Web checks pass when frontend code changed:

```bash
cd apps/web
npm run build
```

- Commit message follows `GIT_CONVENTIONS.md`.
- `TASKS.md` status is updated when appropriate.
- Remote push succeeds.

## Current Development Stage

Stage: Import foundation.

Priority order:

1. Create realistic Douban paste fixtures.
2. Implement deterministic parser against fixtures.
3. Add import session persistence.
4. Add parse endpoint.
5. Add review/commit acceptance cases.
6. Add validation report.
7. Only then move to metadata enrichment and graph generation.

## Next MiMo Task Packet

```md
## Task: BG-006 Douban Paste Fixtures

Context:
We need realistic parser fixtures before writing parser code. The goal is to make Douban import test-driven and auditable.

Scope:
- Own `apps/api/tests/fixtures/douban_paste/**`
- May add `docs/fixtures/douban-paste.md`
- Do not implement parser logic
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
- Each expected row should include:
  - `raw_fragment`
  - `title`
  - `status`
  - `authors` when visible
  - `rating` when visible
  - `comment` when visible
  - `tags` when visible
  - `read_date` or `marked_date` when visible
  - `douban_url` when visible
  - `confidence`
  - `warnings`
- Document assumptions about copied Douban formats.

Acceptance Criteria:
- Fixture files are readable and valid JSON where applicable.
- Fixtures cover happy path and noisy input.
- No parser implementation is added.
- Handoff explains assumptions and open questions.

Verification:
- `python -m json.tool <expected-json-file>` works for all expected JSON files.

Handoff Required:
- Changed files.
- Assumptions about Douban copied text.
- Any real sample gaps that need user input.
- Verification results.
```
