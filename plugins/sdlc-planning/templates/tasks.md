# Implementation Plan — <Feature>

| Field | Value |
|---|---|
| Design | docs/03-design/design.md (vX) |
| Status | Draft / In review / Approved |

## Milestones
1. M1 — <e.g. data model + API behind flag>
2. M2 — <…>

## Tasks
| ID | Title | ACs | Depends on | Est. | Size (~lines) | Owner | Status |
|---|---|---|---|---|---|---|---|
| T-1 | | AC-1.1 | — | S | <200 | | todo |

### T-1: <title>
- **What:** <change, with file/module paths from the design>
- **Satisfies:** AC-1.1
- **Tests that prove it:** <unit/integration/e2e>
- **Ready?** [ ] ACs clear [ ] dependencies done [ ] design section linked [ ] test approach known [ ] fits in one PR (≤ ~400 changed lines)
- **Definition of done:** see below, plus anything specific to this task

## Definition of Ready (applies to every task)
- [ ] Linked to at least one AC, and the AC is unambiguous
- [ ] Dependencies are `done`
- [ ] Design section and files to touch are named
- [ ] Test approach is known (unit / integration / e2e)
- [ ] Small enough for one PR (≤ ~400 changed lines); otherwise split

## Definition of Done (applies to every task)
- [ ] Failing test written first, now passing; full suite green
- [ ] Code reviewed by a human; no open Blocker/Major findings
- [ ] Behind a feature flag if user-visible (default OFF)
- [ ] Telemetry for new paths (logs/metrics/traces)
- [ ] Docs / runbook updated if behaviour or operations changed
- [ ] Conventional Commit messages referencing the task and ACs

## Coverage check
| AC | Tasks |
|---|---|
| AC-1.1 | T-1 |

## Risks / spikes
-
