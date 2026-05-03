# Agent Collaboration Protocol

## Roles

This protocol defines project coordination roles, not model quality or status. The planning agent owns architecture and acceptance criteria. The implementation agent owns assigned execution packets. The goal is clear handoff and low-coupling development.

### Planning Agent

Primary responsibilities:

- Own product direction, architecture, module boundaries, and acceptance criteria.
- Maintain `SPEC.md`, `IMPLEMENTATION_PLAN.md`, and `TASKS.md`.
- Split work into small implementation packets.
- Review work for coupling, test coverage, and alignment with the reading-leverage goal.
- Take on framework-level or high-risk implementation when needed.

### Implementation Agent

Primary responsibilities:

- Implement scoped task packets.
- Follow existing architecture and contracts.
- Write or update tests before declaring work complete.
- Avoid broad refactors unless the task explicitly calls for them.
- Report changes, verification commands, risks, and handoff notes.

The implementation agent may be `opencode` using MiMo. It should receive one bounded task at a time, with clear file ownership and success criteria.

Coordination rule:

- The implementation agent should follow task packets from the planning agent.
- If it finds a better implementation detail inside the assigned scope, it may choose it and explain the decision in the handoff.
- If it needs to change architecture, data contracts, module boundaries, or the implementation plan, it should stop and ask for planning review.
- The implementation agent should not independently expand scope beyond the task packet.

Recommended instruction to give the implementation agent:

```text
You are the implementation agent for this project. Follow book_graph/SPEC.md,
book_graph/IMPLEMENTATION_PLAN.md, book_graph/AGENT_PROTOCOL.md, and the current
task packet in book_graph/TASKS.md. Keep changes scoped to the assigned task.
Do not change architecture docs unless explicitly asked. Report changed files,
verification commands, risks, and handoff notes when done.
```

## Working Agreement

All agents follow these constraints:

- Keep modules low-coupling.
- Do not let parser, LLM, provider, or graph code write directly to the database.
- Do not let React components call external book metadata APIs directly.
- Prefer typed DTOs and service boundaries over ad hoc data passing.
- Keep package `__init__.py` files thin. Put implementation in named modules and use `__init__.py` only for stable re-exports.
- Treat `SPEC.md` as the product source of truth.
- Treat `IMPLEMENTATION_PLAN.md` as the execution source of truth.
- Treat `TASKS.md` as the current backlog and status tracker.
- Every task must have a verification step.
- Do not mark a task complete if tests or checks were not run, unless the blocker is explicitly reported.

## Task Packet Format

When assigning work to another agent, use this format:

```md
## Task: <short name>

Context:
<why this exists and which spec section it supports>

Scope:
- <owned files/directories>
- <explicit non-goals>

Requirements:
- <behavior requirement>
- <test requirement>
- <interface requirement>

Acceptance Criteria:
- <observable success>
- <command or manual check>

Constraints:
- <dependency direction or coupling constraint>
- <style or implementation constraint>

Handoff Required:
- Changed files
- Verification commands and results
- Open questions
- Known risks
```

## Progress Update Format

Implementation agents should report progress with this structure:

```md
Status: <not started | in progress | blocked | ready for review | complete>

Done:
- <completed item>

Next:
- <next item>

Blocked:
- <blocker or "none">

Verification:
- <command/result or "not run yet">
```

## Completion Handoff Format

Every completed task must end with:

```md
Changed Files:
- <path>

Behavior:
- <what now works>

Tests / Checks:
- <command>: <result>

Architecture Notes:
- <anything relevant to coupling, contracts, or future work>

Risks / Follow-ups:
- <remaining risk or "none">
```

## Review Checklist

Before accepting another agent's work:

- Does it satisfy the task acceptance criteria?
- Are tests/checks included and passing?
- Are module boundaries preserved?
- Are DTOs stable and explicit?
- Are raw imports and generated outputs auditable?
- Is any AI/provider/parser output prevented from direct durable writes?
- Is unrelated code left untouched?
- Are new TODOs captured in `TASKS.md` instead of hidden in comments?

## Conflict Protocol

If an implementation reveals that the plan is wrong:

1. Stop the implementation at the smallest safe point.
2. Report the mismatch against `SPEC.md` or `IMPLEMENTATION_PLAN.md`.
3. Propose the smallest plan/spec change needed.
4. Wait for planning review before continuing if the change affects architecture, data model, or user workflow.

If the issue is local and does not alter architecture, the implementation agent may proceed and document the decision in the handoff.

## File Ownership Guidelines

During early scaffold:

- Planning agent owns `SPEC.md`, `IMPLEMENTATION_PLAN.md`, `AGENT_PROTOCOL.md`, and `TASKS.md`.
- Implementation agent may edit app code, tests, and README files assigned in a task packet.
- If a task requires changing architecture docs, propose the change in the handoff unless the task explicitly grants ownership.

## TDD Standard

Use TDD where the behavior is parseable, deterministic, or risky:

- Parser behavior.
- Normalization behavior.
- Metadata matching.
- Import validation.
- Graph edge scoring.
- API request/response contracts.

Recommended loop:

```text
write failing test -> implement smallest change -> pass test -> refactor if needed -> update task status
```

For UI-only work, use component-level checks and at least one manual verification path until a browser test setup exists.
