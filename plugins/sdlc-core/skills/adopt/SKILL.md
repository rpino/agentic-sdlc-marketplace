---
name: adopt
description: Onboard an existing codebase into the Agentic SDLC - creates the project (or an adoption work item) and drafts a baseline of its architecture and current behaviour, for a human to approve, so later enhancements, bug fixes and hotfixes start from a known picture of the system.
argument-hint: "\"<Project Name>\" [approver name]"
disable-model-invocation: true
---

# Adopt an existing codebase

Arguments: `$ARGUMENTS`

`SDLC` means `sh "${CLAUDE_PLUGIN_ROOT}/scripts/run_py.sh" "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_state.py"`.

1. Work out the **name** (first quoted argument) and the **approver** (the second argument, otherwise ask once). The approver of the baseline is the Tech Lead; if someone else is the Tech Lead, ask once.

2. Check that the current directory is the root of the codebase to adopt. If it is not, say so and stop.

3. Create the work:
   - If there is no `.sdlc/state.json`: `SDLC init "<Name>" --approver "<Approver>" [--tech-lead "<Name>"] --type adopt`.
   - If a project already exists: `SDLC feature new "Adopt <Name>" --type adopt`.

4. **Run the phase immediately** by following the `sdlc-core:conductor` skill. The `adopt` lane has one phase, Design, and `next --json` gives the skill `sdlc-design:baseline-drafter` and the `design-reviewer` agent.

5. When the baseline is approved, tell the user that new work should now use `enhancement` (change existing behaviour), `bugfix`, `hotfix`, `chore` or `feature`, and that each of them starts from `docs/system/spec.md` and updates it at release.
