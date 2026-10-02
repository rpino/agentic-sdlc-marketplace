---
name: pr-reviewer
description: First-pass review of a pull request or diff against its task, acceptance criteria and design — correctness, tests, readability, conventions, performance and risk — producing severity-ranked findings. Use when asked to "review this PR", "review the diff" or before a merge.
argument-hint: "[PR number, branch or 'all']"
---

# PR Reviewer (Phase 7 · Review)

Target: `$ARGUMENTS` (PR number/URL, branch, or all PRs listed in `docs/05-build/build-log.md`).

## For each PR / diff
1. Load the diff (`git diff main...<branch>`, or a GitHub connector/CLI), the linked task and ACs, and the design sections it implements.
2. Review for:
   - **Correctness** — does it do what the ACs say, including edge cases? Any logic errors, off-by-one, null handling, time zones, money rounding?
   - **Tests** — does each AC have a meaningful test? Do tests fail if the code is wrong?
   - **Design conformance** — matches design.md/ADRs; no unapproved deviations.
   - **Conventions & readability** — naming, structure, duplication, dead code, comments where needed.
   - **Performance** — N+1 queries, unbounded loops/lists, missing indexes.
   - **Operability** — logging, metrics, error messages, feature flag.
3. Run `sdlc-review:security-checklist` on the same diff.
4. Write findings to `docs/07-review/review-report.md` (template `${CLAUDE_PLUGIN_ROOT}/templates/review-report.md`): `File:line | Severity (Blocker/Major/Minor/Nit) | Finding | Suggested fix`. Post as PR comments if a connector is available and the user agrees.

## Rules
- Be specific and actionable; cite lines. No style nitpicks the linter already enforces.
- The AI review is the **first pass**. A human Tech Lead owns the merge decision.

Hand back to `sdlc-core:conductor`.
