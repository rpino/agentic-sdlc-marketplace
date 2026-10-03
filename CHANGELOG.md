# Changelog

All notable changes to this marketplace are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/). While the version is below 1.0.0, a minor bump may change behaviour; upgrade notes say what you need to do.

Plugin versions live in each `plugins/<plugin>/.claude-plugin/plugin.json`. The marketplace version is the `sdlc-core` version.

## [0.2.0] — 2026-10-02

### Added
- **Human-only approvals.** A new `UserPromptSubmit` hook (`sdlc_prompt.py`) issues a one-time token when the user types `/sdlc-core:approve` or `/sdlc-core:settings`. The token expires after 30 minutes and is used up by one action. `sdlc_state.py approve`, and any settings change that weakens a gate, need the token or an interactive terminal confirmation.
- **Stale-approval detection.** Approvals store a SHA-256 of each artifact. `status` shows `approved (STALE)` after an edit, and the new `verify` command lists the changes.
- **Exit checks** when a phase moves to `in_review`:
  - every phase: artifacts exist, and key sections are present
  - Planning: every AC has a task
  - QA: every AC has a passing test case
  - Review: no open Blocker, Major, Critical or High finding

  `--force-reason` overrides a failed check and records an open issue for the approver.
- **Traceability matrix.** `sdlc_state.py trace` prints AC → task → test case → result, plus every orphan.
- **Work-type lanes:** `feature`, `bugfix`, `hotfix`, `spike` and `chore`, chosen with `init --type` (see `lanes`).
- **Multiple features per project** with `feature new|list|switch`. The first feature keeps its docs in `docs/`; later ones use `docs/features/<slug>/`.
- **Metrics.** `metrics` computes the DORA metrics and per-phase flow metrics, and `record deploy|incident|restore` logs the events behind them.
- **Independent reviewer agents:** `code-reviewer` and `security-reviewer` (sdlc-review) and `test-auditor` (sdlc-qa). The conductor runs reviewers as subagents.
- `/sdlc-core:settings` skill, plus new settings: `test_patterns`, `blocked_commands` and `max_diff_lines`.
- **Practices built into the skills and templates:**
  - Requirements: SLOs and error budgets, WCAG 2.2 AA
  - Design: STRIDE threat model, SLO-driven observability
  - Planning: Definition of Ready/Done
  - Build: Conventional Commits with `Refs` and `AI-Assisted` trailers
  - QA: accessibility and performance tests, mutation-test sampling
  - Review: Semgrep, gitleaks and osv-scanner; OWASP Top 10 for LLM apps
  - Release: SemVer and CHANGELOG, SBOM and SLSA provenance
  - Operate: game days
- **Parallel build.** The conductor can run independent tasks in separate git worktrees.
- **`sdlc-connectors` plugin** (optional): MCP servers for GitHub, Linear and Atlassian.
- **Eval suites** for sdlc-core, sdlc-requirements, sdlc-planning, sdlc-build and sdlc-review.
- **Repository tooling:**
  - `tests/`: unittest suite, 46 tests
  - `tools/check_consistency.py`
  - GitHub Actions CI: tests on Linux, macOS and Windows with Python 3.9 and 3.13, consistency check, strict plugin validation, and evals run on demand

### Changed
- **State schema v2.** `.sdlc/state.json` now holds `features` and `active_feature`. v1 files migrate automatically the first time a v0.2 script reads them.
- **Code lock.** Code paths now unlock when every phase before Build in the feature's lane is approved; for the `feature` lane that's still Planning. The lock now also covers shell and PowerShell writes, not just edit tools.
- **Reopen cascade.** Reopening a phase marks later approved or in-review phases `needs_revalidation`. They used to keep their status.
- **Gate hook scope.** The hook protects everything under `.sdlc/`, not just `state.json`, and also runs on the `PowerShell` tool.
- **Python launcher.** Skills call the state script through `run_py.sh`, as the hooks already did.
- **Requirement.** Python 3.9 or newer is now required.

### Fixed
- Test-file detection no longer matches any path containing "test" or "spec". For example, `latest.py` and `src/contest/` no longer count as tests.
- Compound shell commands like `sdlc_state.py status && echo x > .sdlc/state.json` no longer get past the state-file guard.

### Upgrade notes
- Nothing to do for existing projects. The state file migrates itself, and your `code_paths` and `require_tests_on_commit` settings are kept. The old `test_markers` setting is replaced by the default `test_patterns`. If your tests use another naming convention, add it with `/sdlc-core:settings add-test-pattern <glob>`.
- Approvals must now come from you typing `/sdlc-core:approve`, or from running the script in a terminal. Scripts or automations that called `sdlc_state.py approve` will be refused.
- Moving a phase to review now runs exit checks, so artifacts that don't follow the templates may report gaps. Fix the artifact, or submit with `--force-reason`.

## [0.1.1] — 2026-10-01

### Added
- `sdlc_state.py settings` command to show and change gated code paths and the test-on-commit rule.

### Fixed
- Hooks start Python through `run_py.sh`, which tries `python3`, `python` and `py` and skips the Windows Store stub.
- Shell scripts keep LF line endings on checkout (`.gitattributes`), so `run_py.sh` works under `sh` on Windows.

## [0.1.0] — 2026-10-01

### Added
- First release: the `sdlc-core` conductor, state script and hooks, plus 10 phase plugins from Discovery to Knowledge, with human approval gates, artifact templates, and the `requirements-reviewer` and `design-reviewer` agents.
- HTML reference guide (`docs/guide.html`).

[0.2.0]: https://github.com/rpino/agentic-sdlc-marketplace/compare/38003c6...b75e946
[0.1.1]: https://github.com/rpino/agentic-sdlc-marketplace/compare/8a11af2...38003c6
[0.1.0]: https://github.com/rpino/agentic-sdlc-marketplace/commit/8a11af2
