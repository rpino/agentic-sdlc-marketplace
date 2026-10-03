---
name: qa-from-acceptance-criteria
description: Generates test cases from acceptance criteria (one or more TC-n per AC), automates them where possible (unit, API, Playwright e2e), runs them, and writes a test report that exposes gaps and untested criteria. Use for QA, test planning, regression suites, or when asked "how do we test this" or "is every AC covered".
---

# QA from Acceptance Criteria (Phase 6 · QA)

Inputs: approved requirements, design, the built code and its tests. Outputs: `docs/06-qa/test-cases.md` (template `${CLAUDE_PLUGIN_ROOT}/templates/test-cases.md`) and `docs/06-qa/test-report.md`.

## Steps
1. **Derive test cases.** For every AC write at least one TC-n: preconditions, steps, data, expected result, and the level (unit / integration / contract / API / e2e / accessibility / performance / manual). Add negative and boundary cases (limits ±1, empty, duplicates, concurrency, time zones). Add an **accessibility** check (WCAG 2.2 AA, e.g. axe-core in Playwright) for UI changes and a **performance** check for each latency NFR or SLO.
2. **Exploratory pass.** Think like a real user and a malicious user: what scenario is not covered by any AC? Each one is a **gap**.
3. **Automate.** Check which TCs already have tests from the Build phase (map by AC IDs in test names). Write the missing automated tests using the project's existing test framework (e.g. pytest/JUnit/Jest; Playwright for UI). Keep test data deterministic.
4. **Run** the suite. In the Result column write exactly `PASS`, `FAIL`, `BLOCKED` or `SKIPPED`, because the state script reads it. Record flaky tests and defects (DEF-n with steps to reproduce, severity, linked AC, status `Open`/`Fixed`).
5. **Independent audit.** Run the `sdlc-qa:test-auditor` agent as a subagent. It looks for false greens, missing cases and flaky tests, and samples mutation testing. Fix what it finds, or record it as a gap.
6. **Report** in `test-report.md`: AC coverage matrix (AC → TCs → result), auditor findings, defects, gaps, risk assessment, recommendation (ready / not ready). Under the conductor, `trace` must show every AC with a passing TC before QA can go to review.

## Gaps go back upstream
A gap means the requirements are incomplete. **Don't invent the rule.** Under the conductor, run `sdlc-core:reopen requirements "<gap>"` and tell the user the decision is the Product Owner's (this is the feedback loop working as intended).

## Watch for false greens
Tests that assert nothing meaningful, mock the thing under test, or were changed to pass — flag them.

Hand back to `sdlc-core:conductor`; the QA Lead approves.
