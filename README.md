# Agentic SDLC Marketplace

A Claude Code plugin marketplace that takes work **from idea to deployment** through up to 10 phases. Agents draft each phase, independent reviewer agents check it, and a named person approves it before the next one starts.

```
Idea → Discovery → Requirements → Design → Planning → Build → QA → Review → Release → Operate → Knowledge
        🚦 PO        🚦 PO          🚦 TL     🚦 Team   🚦 TL   🚦 QA  🚦 TL     🚦 PO      🚦 PO      🚦 Team
```

Not everything needs all 10 phases. Each piece of work has a **type** that picks its lane:

| Type | Phases |
|---|---|
| `feature` | all 10 |
| `bugfix` | requirements → build → qa → review → release |
| `hotfix` | build → review → release → operate → knowledge |
| `spike` | discovery → design |
| `chore` | planning → build → review |

You don't call skills one by one. You use a few commands, and the conductor runs the right skills for each phase:

| Command | What it does |
|---|---|
| `/sdlc-core:init "Name" [--type …]` | Creates the project (or a new feature in an existing one) and starts its first phase |
| `/sdlc-core:next` | Runs the next step of the current phase, or tells you an approval is pending |
| `/sdlc-core:approve` | **Human gate.** Records who approved the phase and moves the work forward. Only works when a human types it |
| `/sdlc-core:status` | Shows where the work stands, who approved what, stale approvals and open decisions |
| `/sdlc-core:settings` | Human-only changes to gate settings (code paths, test rule, blocked commands) |

The conductor can also reopen an earlier phase (`/sdlc-core:reopen`) when a later one finds a gap.

**Documentation:**
- [docs/guide.html](docs/guide.html): illustrated reference
- [docs/process.md](docs/process.md): process definition
- [CHANGELOG.md](CHANGELOG.md): what changed in each version, with upgrade notes
- [CONTRIBUTING.md](CONTRIBUTING.md): how to change the marketplace
- [SECURITY.md](SECURITY.md): what the gates do and don't protect against, and how to report a bypass

---

## Install

From Claude Code:

```
/plugin marketplace add rpino/agentic-sdlc-marketplace
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

Optional: `/plugin install sdlc-connectors@agentic-sdlc` adds MCP servers for GitHub (needs `GITHUB_PERSONAL_ACCESS_TOKEN`), Linear and Jira/Confluence (both OAuth). Remove the entries you don't use from `plugins/sdlc-connectors/.mcp.json`, and check the endpoints against each vendor's current MCP docs.

To test locally before pushing: `claude plugin marketplace add ./agentic-sdlc-marketplace`.

**Requirement:** Python 3.9+ (standard library only). Hooks and skills start it through `scripts/run_py.sh`, which tries `python3`, then `python`, then the Windows `py` launcher, and skips the Microsoft Store stub.

---

## How it works

### 1. State file: the process's memory
`/sdlc-core:init` creates `.sdlc/state.json` in your project. It holds one or more **features**. Each feature records its lane, every phase's status (`not_started → draft → in_review → approved`, or `reopened` / `needs_revalidation`), its artifacts and their hashes at approval, open issues needing a human decision, and who approved what, when, and how. A full history drives the metrics. Any session on any day reads it and knows where the work is. Version-1 state files are migrated automatically.

All changes go through `plugins/sdlc-core/scripts/sdlc_state.py`, so transitions are deterministic.

### 2. Conductor: the orchestrator
The `sdlc-core:conductor` skill reads the state, runs the current phase's skills in order, dispatches **independent reviewer agents** as subagents (maker ≠ checker), records open questions, checks traceability, submits the artifact for review, and **stops at the gate**. In Build it can run independent tasks in parallel git worktrees.

### 3. Gates you can't skip
| Hook | Rule |
|---|---|
| `SessionStart` | Injects the active feature, current phase, code-lock state, open decisions and stale approvals into every session |
| `UserPromptSubmit` | Issues a one-time token when **the user** types `/sdlc-core:approve` or `/sdlc-core:settings`. Without it, the script refuses to approve or to weaken a gate |
| `PreToolUse` (edit tools, Bash, PowerShell) | Blocks any write to `.sdlc/`, including shell redirects, `sed -i`, `cp` and inline scripts |
| `PreToolUse` | Blocks writing code under `src/ app/ lib/ services/ packages/ api/ web/ tests/ test/` until the lane's phases before Build are approved |
| `PreToolUse` (Bash) | Blocks `git commit` of code with no test changes. Warns on commits over 400 changed lines |
| `PreToolUse` | Blocks production-changing commands (`terraform apply`, `kubectl apply`, `vercel --prod`, force-push, push to main) |

The script itself also enforces the rules when a phase moves to review:
- **Exit checks.** Artifacts must exist and key sections must be present. Planning can't go to review with an AC that has no task. QA can't with an AC that has no passing test. Review can't with an open High finding.
- **Stale approvals.** Editing an approved artifact flags it `approved (STALE)` (see `verify`).
- **Reopen cascade.** Reopening a phase marks later approvals `needs_revalidation`.

Tune the gates with `/sdlc-core:settings` (for example `add-code-path tictactoe/`, `require-tests off`, `max-diff-lines 600`). Never edit the state file by hand.

### 4. Artifacts: the handoff chain
Each phase's output is the next phase's input, and IDs trace all the way through (US-1 → AC-1.2 → T-3 → TC-04 → PR → RCA). `sdlc_state.py trace` prints the matrix and every orphan.

```
docs/                          (first feature; later ones use docs/features/<slug>/)
├── 01-discovery/problem-brief.md
├── 02-requirements/requirements.md          (stories, EARS ACs, NFRs, SLOs)
├── 03-design/design.md, adr/ADR-001-*.md    (incl. STRIDE threat model)
├── 04-planning/tasks.md                     (Definition of Ready / Done)
├── 05-build/build-log.md
├── 06-qa/test-cases.md, test-report.md
├── 07-review/review-report.md               (incl. scanner results)
├── 08-release/release-plan.md, release-notes.md   (SemVer, CHANGELOG, SBOM)
├── 09-operate/monitoring.md, RCA-*.md
└── 10-knowledge/retro.md      (DORA metrics; standing rules appended to CLAUDE.md)
```

### 5. Metrics
`sdlc_state.py metrics` computes the **DORA** metrics (deployment frequency, lead time for changes, change failure rate, time to restore) and per-phase flow metrics (cycle time, time waiting for approval, review rounds, reopens). Record real deploys and incidents with `record deploy|incident|restore`.

---

## Plugins

| # | Plugin | Skills | Agents (independent reviewers) | Gate (approver) |
|---|---|---|---|---|
| — | **sdlc-core** | conductor, init, next, approve, status, reopen, settings | — | — |
| 1 | sdlc-discovery | idea-interviewer | — | Product Owner |
| 2 | sdlc-requirements | spec-writer, acceptance-criteria | requirements-reviewer | Product Owner |
| 3 | sdlc-design | design-drafter | design-reviewer | Tech Lead |
| 4 | sdlc-planning | task-breakdown | — | Team |
| 5 | sdlc-build | task-executor | — | Tech Lead |
| 6 | sdlc-qa | qa-from-acceptance-criteria | test-auditor | QA Lead |
| 7 | sdlc-review | pr-reviewer, security-checklist | code-reviewer, security-reviewer | Tech Lead |
| 8 | sdlc-release | release-notes, pipeline-fixer | — | Product Owner |
| 9 | sdlc-ops | incident-summarizer | — | Product Owner |
| 10 | sdlc-knowledge | retro-capture, knowledge-updater | — | Team |
| + | sdlc-connectors | — (MCP: GitHub, Linear, Atlassian) | — | — |

Every phase plugin depends on `sdlc-core`. If a phase plugin isn't installed, the conductor falls back to the built-in phase contract, so you can roll the plugins out gradually.

Every skill can also be used on its own outside a managed project (e.g. `/sdlc-review:pr-reviewer 142`).

---

## A typical run

```
/sdlc-core:init "Membership Freeze" Tito
  → idea-interviewer asks ~7 questions → problem-brief.md → in_review
/sdlc-core:approve                      → Discovery approved (token issued by your prompt)
/sdlc-core:next
  → spec-writer → acceptance-criteria → requirements-reviewer (subagent)
  → requirements.md in_review, 1 open issue: "check-in while frozen?"
"Deny check-in, offer early unfreeze"   → issue resolved
/sdlc-core:approve                      → Requirements approved
/sdlc-core:next                         → design-drafter (+ STRIDE) + design-reviewer …
…
/sdlc-core:init "Login 500s" --type hotfix   → second feature, code unlocked, review still required
/sdlc-core:status                       → any time, any session
```

---

## Developing this marketplace

```
python -m unittest discover -s tests          # state machine, gates and hooks (no dependencies)
python tools/check_consistency.py             # PHASES ↔ plugins ↔ docs/process.md ↔ README
claude plugin validate --strict plugins/<p>   # manifests, skills, agents
claude plugin eval plugins/<p>                # behaviour evals in plugins/<p>/evals/
```
CI (`.github/workflows/ci.yml`) runs the tests on Linux, macOS and Windows, plus the consistency check and strict validation. The evals run on demand (`workflow_dispatch`) because they call the model. See [CONTRIBUTING.md](CONTRIBUTING.md) for where each kind of change goes, and record user-visible changes in [CHANGELOG.md](CHANGELOG.md).

## Repository layout

```
.claude-plugin/marketplace.json   ← the catalog
plugins/<plugin>/                 ← one folder per plugin
  .claude-plugin/plugin.json
  skills/<skill>/SKILL.md
  agents/*.md
  templates/*.md
  evals/<case>/prompt.md, graders/*.md
  hooks/hooks.json, scripts/*.py  (sdlc-core only)
tests/                            ← unittest suite for sdlc-core scripts and hooks
tools/check_consistency.py
docs/process.md, docs/guide.html
CHANGELOG.md, CONTRIBUTING.md, SECURITY.md
```

## Roadmap
- Approvals mirrored from GitHub PR reviews / CODEOWNERS via the connectors plugin
- More eval cases per skill, plus eval runs in CI on a schedule
- Organisation-level policy packs (regulated-industry lanes, extra gates)

## License
MIT
