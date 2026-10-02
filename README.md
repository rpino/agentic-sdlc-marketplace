# Agentic SDLC Marketplace

A Claude Code plugin marketplace that takes a feature **from idea to deployment** through 10 phases. Agents draft each phase, and a named person approves it before the next one starts.

```
Idea → Discovery → Requirements → Design → Planning → Build → QA → Review → Release → Operate → Knowledge
        🚦 PO        🚦 PO          🚦 TL     🚦 Team   🚦 TL   🚦 QA  🚦 TL     🚦 PO      🚦 PO      🚦 Team
```

You don't call skills one by one. You use **four commands**, and the conductor runs the right skills for each phase:

| Command | What it does |
|---|---|
| `/sdlc-core:init "Project Name"` | Creates the project skeleton and state file, then starts Discovery |
| `/sdlc-core:next` | Runs the next step of the current phase, or tells you an approval is pending |
| `/sdlc-core:approve` | **Human gate.** Records who approved the phase and moves the project forward |
| `/sdlc-core:status` | Shows where the project stands, who approved what, and open decisions |

The conductor can also reopen an earlier phase (`/sdlc-core:reopen`) when a later one finds a gap.

---

## Install

From Claude Code:

```
/plugin marketplace add <github-owner>/<repo>
/plugin install sdlc-core@agentic-sdlc
```

Then install the phase plugins you want (all recommended):

```
/plugin install sdlc-discovery@agentic-sdlc
/plugin install sdlc-requirements@agentic-sdlc
/plugin install sdlc-design@agentic-sdlc
/plugin install sdlc-planning@agentic-sdlc
/plugin install sdlc-build@agentic-sdlc
/plugin install sdlc-qa@agentic-sdlc
/plugin install sdlc-review@agentic-sdlc
/plugin install sdlc-release@agentic-sdlc
/plugin install sdlc-ops@agentic-sdlc
/plugin install sdlc-knowledge@agentic-sdlc
```

To test locally before pushing: `claude plugin marketplace add ./agentic-sdlc-marketplace`.

**Requirement:** `python3` on your PATH. The state manager and hooks use only the Python standard library.

---

## How it works

### 1. State file: the process's memory
`/sdlc-core:init` creates `.sdlc/state.json` in your project. It records every phase's status (`not_started → draft → in_review → approved`, or `reopened`), its artifacts, open issues needing a human decision, who approved what and when, and a full history. Any session on any day reads it and knows where the project is.

All changes go through `plugins/sdlc-core/scripts/sdlc_state.py`, so transitions are deterministic. A phase can't start before the previous one is approved, and only a named person can approve.

### 2. Conductor: the orchestrator
The `sdlc-core:conductor` skill reads the state, runs the current phase's skills in order, records open questions, submits the artifact for review, and **stops at the gate**.

### 3. Hooks: gates you can't skip
| Hook | Rule |
|---|---|
| `SessionStart` | Injects the project's current phase and open decisions into every new session |
| `PreToolUse` (Write/Edit) | Blocks direct edits to `.sdlc/state.json` |
| `PreToolUse` (Write/Edit) | Blocks writing code under `src/ app/ lib/ services/ packages/ api/ web/ tests/ test/` until **Planning is approved** |
| `PreToolUse` (Bash) | Blocks `git commit` of code changes that include no test changes |

You can adjust the code paths and the test rule in the `settings` block of `.sdlc/state.json` (through the script, not by hand).

### 4. Artifacts: the handoff chain
Each phase's output is the next phase's input, and IDs trace all the way through (US-1 → AC-1.2 → T-3 → TC-04 → PR → RCA).

```
docs/
├── 01-discovery/problem-brief.md
├── 02-requirements/requirements.md
├── 03-design/design.md, adr/ADR-001-*.md
├── 04-planning/tasks.md
├── 05-build/build-log.md
├── 06-qa/test-cases.md, test-report.md
├── 07-review/review-report.md
├── 08-release/release-plan.md, release-notes.md
├── 09-operate/monitoring.md, RCA-*.md
└── 10-knowledge/retro.md      (+ standing rules appended to CLAUDE.md)
```

---

## Plugins

| # | Plugin | Skills | Agents | Gate (approver) |
|---|---|---|---|---|
| — | **sdlc-core** | conductor, init, next, approve, status, reopen | — | — |
| 1 | sdlc-discovery | idea-interviewer | — | Product Owner |
| 2 | sdlc-requirements | spec-writer, acceptance-criteria | requirements-reviewer | Product Owner |
| 3 | sdlc-design | design-drafter | design-reviewer | Tech Lead |
| 4 | sdlc-planning | task-breakdown | — | Team |
| 5 | sdlc-build | task-executor | — | Tech Lead |
| 6 | sdlc-qa | qa-from-acceptance-criteria | — | QA Lead |
| 7 | sdlc-review | pr-reviewer, security-checklist | — | Tech Lead |
| 8 | sdlc-release | release-notes, pipeline-fixer | — | Product Owner |
| 9 | sdlc-ops | incident-summarizer | — | Product Owner |
| 10 | sdlc-knowledge | retro-capture, knowledge-updater | — | Team |

Every phase plugin depends on `sdlc-core`. If a phase plugin isn't installed, the conductor falls back to the built-in phase contract, so you can roll the plugins out gradually.

Every skill can also be used on its own outside a managed project (e.g. `/sdlc-review:pr-reviewer 142`).

---

## A typical run

```
/sdlc-core:init "Membership Freeze" Tito
  → idea-interviewer asks ~7 questions → problem-brief.md → in_review
/sdlc-core:approve                      → Discovery approved
/sdlc-core:next
  → spec-writer → acceptance-criteria → requirements-reviewer
  → requirements.md in_review, 1 open issue: "check-in while frozen?"
"Deny check-in, offer early unfreeze"   → issue resolved
/sdlc-core:approve                      → Requirements approved
/sdlc-core:next                         → design-drafter + design-reviewer …
…
/sdlc-core:status                       → any time, any session
```

See [docs/process.md](docs/process.md) for the full process definition.

## Repository layout

```
.claude-plugin/marketplace.json   ← the catalog
plugins/<plugin>/                 ← one folder per plugin
  .claude-plugin/plugin.json
  skills/<skill>/SKILL.md
  agents/*.md
  templates/*.md
  hooks/hooks.json, scripts/*.py  (sdlc-core only)
docs/process.md
```

## Roadmap
- Connectors (`.mcp.json`) for Jira and GitHub in planning, build and review
- Evals for each skill
- Configurable phase sets (e.g. a "lite" path for small changes)

## License
MIT
