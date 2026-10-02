# Agentic SDLC — Process Definition

This is the process the `sdlc-core` conductor enforces. The machine-readable version is the `PHASES` list in `plugins/sdlc-core/scripts/sdlc_state.py`. Keep the two in sync.

## Principles
1. **AI drafts, humans decide.** Every phase ends at a gate approved by a named person.
2. **Artifacts are the contract.** Each phase's output is the next phase's input.
3. **Traceability end to end.** US → AC → design element → task → test → PR → release → RCA.
4. **Feedback loops are normal.** A later phase that finds a gap reopens the earlier phase. It doesn't patch around the gap.
5. **Lessons compound.** Adopted lessons become standing rules in `CLAUDE.md` that every future agent follows.

## Phase lifecycle

```
not_started ──► draft ──► in_review ──► approved
                  ▲           │              │
                  └───────────┘              ▼
              (review feedback)          reopened ──► in_review ──► approved
                                       (later phase found a gap)
```

- Only the conductor moves a phase to `draft` or `in_review`.
- Only a human, through `/sdlc-core:approve`, moves it to `approved`.
- A phase can't start until the previous phase is approved.
- Open issues block approval unless the approver explicitly accepts them.

## Phases

| # | Phase | Skills (in order) | Reviewer agent | Output | Gate | Approver |
|---|---|---|---|---|---|---|
| 1 | Discovery | idea-interviewer | — | problem-brief.md | Problem is worth solving | Product Owner |
| 2 | Requirements | spec-writer → acceptance-criteria | requirements-reviewer | requirements.md | Stories + testable ACs | Product Owner |
| 3 | Design | design-drafter | design-reviewer | design.md, ADRs | Design + ADRs approved | Tech Lead |
| 4 | Planning | task-breakdown | — | tasks.md (+ tickets) | Sprint plan agreed | Team |
| 5 | Build | task-executor (per task) | — | code, tests, build-log.md | All task diffs reviewed | Tech Lead |
| 6 | QA | qa-from-acceptance-criteria | — | test-cases.md, test-report.md | Every AC has a passing test | QA Lead |
| 7 | Review | pr-reviewer → security-checklist | — | review-report.md | Merge sign-off, no open High | Tech Lead |
| 8 | Release | release-notes (+ pipeline-fixer) | — | release-plan.md, release-notes.md | Go / no-go | Product Owner |
| 9 | Operate | incident-summarizer | — | monitoring.md, RCA-*.md | Stable or incidents handled | Product Owner |
| 10 | Knowledge | retro-capture → knowledge-updater | — | retro.md, CLAUDE.md rules | Lessons adopted | Team |

## Enforcement (hooks)

| Rule | Mechanism |
|---|---|
| State changes only through the script | PreToolUse blocks Write/Edit/shell writes to `.sdlc/state.json` |
| No code before an approved plan | PreToolUse blocks writes under `settings.code_paths` until `planning` is approved |
| Tests with every code change | PreToolUse blocks `git commit` when staged code has no staged test |
| Every session knows where it is | SessionStart injects current phase and open decisions |

## State script reference

```
python3 plugins/sdlc-core/scripts/sdlc_state.py init "<Name>" --approver NAME [--tech-lead NAME] [--qa-lead NAME] [--dir PATH]
python3 …/sdlc_state.py status [--json]
python3 …/sdlc_state.py next [--json]
python3 …/sdlc_state.py set-status <phase> draft|in_review [--artifact PATH]...
python3 …/sdlc_state.py approve <phase> --by NAME [--note TEXT] [--accept-open-issues]
python3 …/sdlc_state.py reopen <phase> --reason TEXT [--by NAME]
python3 …/sdlc_state.py issue add <phase> "<question>"
python3 …/sdlc_state.py issue resolve <phase> <ISSUE-ID> --note "<decision>"
python3 …/sdlc_state.py phases
```

## Roles

| Role | Accountable for |
|---|---|
| Product Owner / Proxy PO | Problem, scope, business rules, priorities, go/no-go, stakeholder communication |
| Tech Lead | Design, ADRs, code ownership, merge sign-off |
| QA Lead | Test strategy, AC coverage, release quality |
| Team | Sprint plan, retro, adopting standing rules |
| Agents | Drafting, analysis, code, tests, reviews, documentation, and raising decisions to humans |
