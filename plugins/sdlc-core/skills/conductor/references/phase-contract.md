# Phase contract (fallback when a phase plugin is missing)

Read this only when `next --json` lists a skill whose plugin is not installed. Do the phase yourself following this table, and tell the user that installing the plugin will make the phase consistent.

Paths are relative to the feature's `docs_root` (default `docs/`).

| # | Phase | Input | Output artifact |
|---|---|---|---|
| 1 | discovery | the idea | `01-discovery/problem-brief.md`: problem, users, hypothesis, success metric, constraints, out of scope |
| 2 | requirements | problem brief | `02-requirements/requirements.md`: user stories US-n, acceptance criteria AC-n.m (EARS: WHEN/WHILE/IF … THE SYSTEM SHALL …), NFRs including SLOs |
| 3 | design | requirements | `03-design/design.md` + `03-design/adr/ADR-nnn-*.md`: components, data model, APIs, sequence, edge cases, STRIDE threat model, AC→design map |
| 4 | planning | design | `04-planning/tasks.md`: small tasks T-n (each ≤ ~400 changed lines), each linked to ACs, dependencies, estimate, Definition of Ready/Done |
| 5 | build | tasks | code + tests, `05-build/build-log.md`: task, PR link, tests added, ACs covered |
| 6 | qa | requirements + build | `06-qa/test-cases.md`, `06-qa/test-report.md`: TC-n per AC, results (PASS/FAIL), gaps |
| 7 | review | PRs | `07-review/review-report.md`: findings by severity, scanner results, security checklist, sign-off |
| 8 | release | approved build | `08-release/release-plan.md`, `release-notes.md`: flags, rollout, rollback, SBOM, comms |
| 9 | operate | live system | `09-operate/monitoring.md`, `RCA-*.md`: SLOs, health, incidents, follow-up specs |
| 10 | knowledge | everything | `10-knowledge/retro.md` (with `SDLC metrics`) + new standing rules appended to `CLAUDE.md` |
