# Git Conventions

## Repository Strategy

Use this repository as the source of truth for the Book Graph product, architecture, agent protocol, backend, frontend, and design artifacts.

Default branch:

- `main`

Branch naming:

- `feature/BG-003-api-scaffold`
- `feature/BG-009-douban-parser`
- `fix/BG-013-validation-counts`
- `docs/BG-002-agent-protocol`
- `chore/dev-tooling`

## Commit Style

Use small, reviewable commits. Prefer one task or one coherent behavior change per commit.

Commit format:

```text
<type>(<scope>): <summary>
```

Types:

- `docs`: documentation and planning files.
- `feat`: user-facing or API behavior.
- `fix`: bug fix.
- `test`: tests or fixtures only.
- `refactor`: behavior-preserving code change.
- `chore`: tooling, config, repo maintenance.

Examples:

```text
docs(project): add reading leverage spec
feat(api): add import session creation
test(parser): cover noisy douban paste samples
chore(repo): add git ignore rules
```

## Task Traceability

Every meaningful change should map to a task ID in `TASKS.md` when possible.

Recommended commit body:

```text
Task: BG-009
Verification: pytest apps/api/tests
```

## Pull Request Expectations

Even for a solo project, use PR-style discipline:

- State the task ID.
- Summarize behavior changed.
- List verification commands.
- Mention risks and follow-ups.
- Note if architecture docs need updates.

## Agent Workflow

Planning agent:

- Owns architecture docs and task boundaries.
- Reviews coupling, tests, and acceptance criteria.

Implementation agent:

- Works from one task packet at a time.
- Reports changed files, verification, risks, and handoff notes.
- Does not expand scope without review.

## Protected Files

Implementation agents should not edit these unless assigned:

- `SPEC.md`
- `IMPLEMENTATION_PLAN.md`
- `AGENT_PROTOCOL.md`
- `TASKS.md`
- `GIT_CONVENTIONS.md`

## What Not To Commit

Do not commit:

- API keys or `.env` files.
- SQLite/local DB files.
- `node_modules/`
- `.venv/`
- Vite `dist/`
- Python caches or pytest caches.

Design screenshots in `assets/` are okay to commit when they document product direction.
