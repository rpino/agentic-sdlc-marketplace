---
name: acceptance-criteria
description: Adds testable acceptance criteria to every user story using EARS syntax (WHEN/WHILE/IF … THE SYSTEM SHALL …), covering happy path, validation, edge cases and errors. Use after user stories exist, or when asked to "write acceptance criteria", "make this testable" or "add Given/When/Then".
---

# Acceptance Criteria (Phase 2 · Requirements, step 2)

Input/output: `docs/02-requirements/requirements.md`.

## For every story US-n, write AC-n.m

Use **EARS** patterns (one behaviour per criterion):

| Pattern | Form |
|---|---|
| Event | WHEN <trigger> THE SYSTEM SHALL <response> |
| State | WHILE <state> THE SYSTEM SHALL <response> |
| Unwanted | IF <error/unwanted condition> THEN THE SYSTEM SHALL <response> |
| Optional | WHERE <feature/config applies> THE SYSTEM SHALL <response> |
| Ubiquitous | THE SYSTEM SHALL <response> |

Teams that prefer Gherkin may write `Given / When / Then` instead — keep the AC-n.m IDs either way.

## Coverage checklist per story
- [ ] Happy path
- [ ] Input validation and limits (min/max, formats, required fields)
- [ ] Permissions / who may do it
- [ ] State conflicts (already done, overlapping, expired, past-due…)
- [ ] Errors from dependencies (payment, external API down)
- [ ] What the user sees (messages, notifications)
- [ ] Audit / data retention if relevant

## Rules
- Each AC is **observable and testable** by QA without reading code.
- Exact values (limits, messages, fees) — or an open question if unknown. Never invent a business rule; ask.
- Add a **traceability table** at the end: AC → story → brief metric.

## Review
If the `requirements-reviewer` agent is available, run it on the finished file and fold its findings in: fix clear defects, and turn business decisions into **open questions** (and `sdlc_state.py issue add requirements "<question>"` when under the conductor).

Then hand back to `sdlc-core:conductor`.
