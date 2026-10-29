# Roadmap

Planned improvements to the Agentic SDLC marketplace. Each phase can be built on its own unless a dependency is listed. Status values: `planned`, `in progress`, `done`.

| Phase | Theme | Depends on | Status |
|---|---|---|---|
| 1 | Model standard and quick token wins | — | done (PR #3) |
| 2 | Slim the process | — (best after 1) | done (PR #4); moving more checks into scripts is deferred |
| 3 | Brownfield foundation | — | in progress (3a, 3b and 3c built; untested on a real codebase) |
| 4 | Change safety | 3 | planned |
| 5 | Feedback intake | 3 (better after 4) | planned |
| 6 | Web UI | — (shows more after 3 to 5) | in progress (6a built; 6b and 6c not started) |

Suggested order: 1, 2, 3, then 6a in parallel with 3, then 4 and 5, then 6b and 6c.

## Phase 1: Model standard and quick token wins

Goal: cut subagent token cost without lowering the quality of deliverables.

**Standard.** Every agent declares its own `model:` in its frontmatter, so the choice applies to every project with no per-project setting.

| Role | Model | Reason |
|---|---|---|
| `security-reviewer`, `test-auditor` | Opus | A missed vulnerability or a false-green test suite is the costliest failure. `test-auditor` on Sonnet missed a planted false green in 2 of 9 eval runs. |
| `code-reviewer`, `design-reviewer`, `requirements-reviewer` | Sonnet | Strong enough for judgment-heavy review, at a lower cost. Evals match the Opus baseline. |
| `task-executor` (parallel build workers) | Sonnet | Tests act as the safety net. |
| `context-gatherer` (new) | Haiku | Mechanical collection of diff, task IDs, ACs and relevant files into a brief. |

The main session keeps whatever model the user chose. Only subagents change tier.

Work items:
- Add `model:` to the five reviewer agents, and set the model when the conductor dispatches parallel build workers.
- Add the `context-gatherer` agent and use it before the code and security reviewers.
- Scope reviewer inputs to changed files and their direct callers, and cap reviewer output without ever dropping a Blocker, Critical or High finding.
- Compare the review evals before and after, and move a role back up a tier if its eval regresses.
- Record the standard and its reasons in `CONTRIBUTING.md` and `CHANGELOG.md`.

## Phase 2: Slim the process

- Split the conductor into a core file plus on-demand files (parallel build, reopen, stale approvals).
- Move more mechanical checks from prompts into scripts in `tools/` and `plugins/sdlc-core/scripts/`.
- Lighter review in the `chore` and `spike` lanes.
- Measure tokens before and after.

## Phase 3: Brownfield foundation

For enterprise apps that get a steady stream of hotfixes, bug fixes, enhancements and new features.

- **`adopt` command.** Scans an existing repo and drafts a baseline (architecture, modules, tests, current behavior) for human approval.
- **Living spec** in `docs/system/`, always describing how the system behaves today. The release phase merges each feature's approved changes into it. Required for `feature` and `enhancement`; scaled by lane:

  | Lane | Living spec update |
  |---|---|
  | `feature`, `enhancement` | Full merge at release, reviewed by a human |
  | `bugfix` | Only if the fix changes documented behavior |
  | `hotfix` | Short note at release, full reconcile in a follow-up |
  | `chore`, `spike` | None |
- **`enhancement` lane** for changes to existing behavior.

## Phase 4: Change safety

- Impact analysis in requirements and design (what existing behavior, modules and tests are touched), re-checked at review.
- Cross-feature links (`relates-to`, `changes`) and cross-feature reopen.
- A standing regression suite that QA grows with each feature.
- Conflict detection when two active features touch the same files or decisions.

## Phase 5: Feedback intake

- An intake lane: user reports, monitoring alerts and RCAs become typed work items, triaged into bugfix, enhancement, feature, hotfix or chore, and linked to the feature they came from.
- Retro and RCA outputs feed standing rules and new intake items.

## Phase 6: Web UI

A local web app to follow the process from `init` to completion: watch progress, approve gates and answer decisions.

**Stack.** Next.js (App Router) with TypeScript, Tailwind CSS and shadcn/ui. One codebase for the interface and the backend, mainstream tooling with extensive documentation, and a straightforward path to hosting later. The backend calls the existing Python scripts (`sdlc_state.py`) rather than re-implementing the process.

**Principles.**
- `.sdlc/state.json` stays the single source of truth. The UI keeps no copy of it.
- Multi-project from the start through a registry of local folders. Nothing is shared between projects.
- Only the UI backend can write an approval, using a credential the agent cannot reach, and bound to the hash of the artifact version being approved.

Steps:
- **6a. Read-only dashboard.** Project registry, home table with pending gates across projects, project view with pipeline, artifacts, traceability and activity feed.
- **6b. Gates and decisions.** Approve, reject and answer open issues from the UI. Starts with a security design and a review of `sdlc_gate.py`.
- **6c. Metrics.** Cycle time, waiting time, reopens and token cost per phase.

Not planned yet: launching agents from the UI, and a hosted team version.
