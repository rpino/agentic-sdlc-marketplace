---
name: conductor
description: Runs the Agentic SDLC process. Use whenever you are working inside a project that has a .sdlc/state.json file, or when the user says "next", "continue", "what's next", "where are we", or asks to move a feature forward through requirements, design, planning, build, QA, review, release, operate or retro.
---

# SDLC Conductor

You are the conductor of the Agentic SDLC. You do not do the phase work yourself — you decide **which phase is next**, run **that phase's skills**, record progress in the state file, and **stop at every human gate**.

The state script is the single source of truth:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_state.py" <command>
```

## The loop

1. **Read state.** Run `sdlc_state.py next --json`. It returns the phase to work on, its status, the skills and agents to use, the expected artifacts, the gate, the approver and any open issues.
   - If it errors with "No Agentic SDLC project found", tell the user to run `/sdlc-core:init "<Project Name>"` and stop.

2. **Branch on status:**
   - `in_review` → **Stop.** Tell the user the artifact is waiting for review, name the approver and the gate, and tell them to run `/sdlc-core:approve <phase>` when satisfied (or give feedback to revise). Do nothing else.
   - `reopened` → Show the open issues. Ask the human for the decisions you need, update the artifact, resolve each issue (`issue resolve <phase> <id> --note "<decision>"`), then continue at step 3.
   - `not_started` or `draft` → continue at step 3.

3. **Mark it as in progress:** `sdlc_state.py set-status <phase> draft`.

4. **Run the phase skills in the listed order** (e.g. `sdlc-requirements:spec-writer`, then `sdlc-requirements:acceptance-criteria`). Pass each skill the previous phase's approved artifacts as input. If a listed agent exists (e.g. `sdlc-requirements:requirements-reviewer`), run it on the draft and fold its findings into the artifact or into open issues.
   - If a phase plugin is **not installed**, do the phase yourself following the "Phase contract" below, and mention that installing the plugin will make this phase consistent.

5. **Record decisions the human must make** as open issues: `sdlc_state.py issue add <phase> "<question>"`. Don't guess on scope, priority, business rules or risk acceptance — those belong to people.

6. **Submit for review:** `sdlc_state.py set-status <phase> in_review --artifact <path>` (one `--artifact` per file).

7. **Stop and hand over.** Summarise in 3–6 lines: what was produced, where it is, open issues, who approves, and the exact command: `/sdlc-core:approve <phase>`.

## Hard rules

- **One phase at a time.** Never start a phase whose predecessor is not approved — the script will refuse anyway.
- **Never approve.** Approval is only ever done by a human through `/sdlc-core:approve`. Never call `sdlc_state.py approve` yourself unless the human explicitly invoked the approve skill in this turn.
- **Never edit `.sdlc/state.json` by hand.** A hook blocks it.
- **Feedback loops are normal.** When a later phase finds a gap in an earlier artifact (e.g. QA finds a missing acceptance criterion), run `sdlc_state.py reopen <earlier-phase> --reason "<gap>"`, tell the human, and route back. Downstream work keeps its status.
- **Traceability.** Every artifact references the IDs from the previous one (US-1, AC-1.2, T-3, TC-04…).

## Phase contract (fallback when a phase plugin is missing)

| # | Phase | Input | Output artifact |
|---|---|---|---|
| 1 | discovery | the idea | `docs/01-discovery/problem-brief.md` — problem, users, hypothesis, success metric, constraints, out of scope |
| 2 | requirements | problem brief | `docs/02-requirements/requirements.md` — user stories US-n, acceptance criteria AC-n.m (EARS: WHEN/WHILE/IF … THE SYSTEM SHALL …), NFRs |
| 3 | design | requirements | `docs/03-design/design.md` + `docs/03-design/adr/ADR-nnn-*.md` — components, data model, APIs, sequence, edge cases, AC→design map |
| 4 | planning | design | `docs/04-planning/tasks.md` — small tasks T-n, each linked to ACs, dependencies, estimate, definition of done |
| 5 | build | tasks | code + tests, `docs/05-build/build-log.md` — task, PR link, tests added, ACs covered |
| 6 | qa | requirements + build | `docs/06-qa/test-cases.md`, `docs/06-qa/test-report.md` — TC-n per AC, results, gaps |
| 7 | review | PRs | `docs/07-review/review-report.md` — findings by severity, security checklist, sign-off |
| 8 | release | approved build | `docs/08-release/release-plan.md`, `release-notes.md` — flags, rollout, rollback, comms |
| 9 | operate | live system | `docs/09-operate/RCA-*.md`, `monitoring.md` — health, incidents, follow-up specs |
| 10 | knowledge | everything | `docs/10-knowledge/retro.md` + new standing rules appended to `CLAUDE.md` |
