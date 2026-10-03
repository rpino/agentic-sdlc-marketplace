# Contributing

This repository is a Claude Code plugin marketplace. Most of it is prompts (skills, agents and templates). The only executable code is in `plugins/sdlc-core/scripts/`. Changes to either kind are welcome, and the rules below keep them consistent.

## Setup

You need Python 3.9 or newer, git, and Claude Code (for plugin validation and evals). Nothing else needs installing, because the scripts and tests use only the Python standard library.

To try your working copy in Claude Code:

```
claude plugin marketplace add ./agentic-sdlc-marketplace
```

## Before you open a PR

Run these four commands. CI runs the first three on every PR.

```
python -m unittest discover -s tests        # state machine, gates and every hook
python tools/check_consistency.py           # PHASES, plugins, docs/process.md and README agree
claude plugin validate --strict .           # the marketplace manifest
claude plugin validate --strict plugins/<plugin>   # each plugin you changed
```

If you changed what a skill or agent does, also run its evals. They call the model, so they cost a little:

```
claude plugin eval plugins/<plugin> --runs 3
```

## Where things live

| You want to… | Change | Also update |
|---|---|---|
| Add, remove or reorder a phase | `PHASES` in `plugins/sdlc-core/scripts/sdlc_state.py` | `docs/process.md` phase table, conductor "Phase contract", README |
| Add a work type (lane) | `LANES` in `sdlc_state.py` | lanes tables in `docs/process.md`, README, conductor |
| Change what blocks a phase from going to review | `PHASE_TRACE_CHECKS` / `PHASE_HEADING_CHECKS` in `sdlc_state.py` | the matching skill and template, `docs/process.md` |
| Add or change a gate | `plugins/sdlc-core/scripts/sdlc_gate.py` | tests in `tests/test_sdlc_gate.py`, the hooks table in README and `docs/process.md` |
| Add a skill to a phase | `plugins/<plugin>/skills/<name>/SKILL.md` and that phase's `skills` list in `PHASES` | README plugin table |
| Add a reviewer agent | `plugins/<plugin>/agents/<name>.md` (read-only `tools`) and that phase's `agents` list | README plugin table, `docs/process.md` |
| Add a plugin | `plugins/<name>/.claude-plugin/plugin.json` and an entry in `.claude-plugin/marketplace.json` | README plugin table and install list |

`tools/check_consistency.py` catches most of the cross-file drift. `docs/guide.html` isn't checked automatically, so update the affected sections by hand.

## Rules for code in `sdlc-core/scripts`

- **Standard library only, Python 3.9 compatible.** In particular, don't reuse the outer quote character inside an f-string expression. That only parses on Python 3.12+, and CI tests 3.9.
- **Hooks must never break a session.** If the input is bad or state is missing, allow and exit 0. Deny only on a rule you're sure of, and tell the agent what to do instead.
- **Test every new rule both ways:** a test that it denies what it should, and a test that it still allows ordinary work (reading files, writing docs, `2>/dev/null`, and so on).
- **State changes go through `sdlc_state.py`.** Bump `SCHEMA_VERSION` and extend `migrate()` whenever the state shape changes, and add a migration test.

## Rules for skills, agents and templates

- A skill should do one thing and end by handing back to `sdlc-core:conductor`.
- Reviewer agents are **read-only**. They get `Read, Grep, Glob`, plus `Bash` only for read-only git, tests and scanners, and the prompt must say so.
- When the state script parses a template's output, keep the format it relies on: ID formats (`US-1`, `AC-1.2`, `T-3`, `TC-01`, `DEF-1`), `PASS`/`FAIL` in Result columns, and `Open` in Status columns.
- Add or update an eval case under `plugins/<plugin>/evals/<case>/` when you change a skill's core behaviour.

## Commits, versions and the changelog

- Use [Conventional Commits](https://www.conventionalcommits.org/): `feat(sdlc-core): …`, `fix(sdlc-review): …`, `docs: …`.
- Bump `version` in the `plugin.json` of every plugin you changed. Pre-1.0, use a minor bump for new behaviour and a patch for fixes. The `sdlc-core` version is the marketplace version.
- Add your change under an **Unreleased** heading in `CHANGELOG.md`, including upgrade notes if users must do anything.
- Work on a branch and open a PR to `main`. CI must be green before merging.

## Security issues

Don't open a public issue for a way to bypass a gate. See [SECURITY.md](SECURITY.md).
