---
name: task-executor
description: Implements a single planned task (T-n) test-first — reads its acceptance criteria and design, writes failing tests, makes them pass with the smallest change, then commits and opens a PR linked to the task. Use when asked to "build T-3", "implement the next task", or start coding a planned item.
argument-hint: "[task id, e.g. T-3]"
---

# Task Executor (Phase 5 · Build)

Task: `$ARGUMENTS` (if empty, pick the first `todo` task in `docs/04-planning/tasks.md` whose dependencies are done, and confirm with the user).

## Before writing code
1. Read the task in `docs/04-planning/tasks.md`, its ACs in `docs/02-requirements/requirements.md`, and the relevant design sections.
2. Read the code you will touch and follow its conventions. Check `CLAUDE.md` standing rules.
3. Create a branch: `feature/<task-id>-<slug>` (if git is in use).

## Test-first loop
4. **Write failing tests** that express each AC the task satisfies (name tests after the AC, e.g. `test_ac_1_2_rejects_freeze_over_3_months`). Run them and confirm they fail for the right reason.
5. **Implement the smallest change** that makes them pass. No unrelated refactors; no features beyond the task.
6. **Run the full relevant test suite** and linters. Fix what you broke.
7. **Self-review the diff**: naming, error handling, logging, security (authz, input validation), no secrets, no debug leftovers.

## Finish
8. Commit with a message that references the task and ACs: `T-3: freeze endpoint validation (AC-1.1, AC-1.2)`. (A hook blocks commits of code without test changes.)
9. Open a PR if a GitHub/GitLab connector or CLI is available; the PR description lists task, ACs, tests added, and how to verify.
10. Update the task status in `tasks.md` and append a line to `docs/05-build/build-log.md` (template `${CLAUDE_PLUGIN_ROOT}/templates/build-log.md`).
11. **Stop.** A developer reviews the diff — they own the code. Say which task is next.

If the design turns out to be wrong or an AC is ambiguous while coding: stop, explain, and use `sdlc-core:reopen` on the design or requirements phase instead of improvising.

When **all** tasks are done, hand back to `sdlc-core:conductor` to submit the Build phase for review.
