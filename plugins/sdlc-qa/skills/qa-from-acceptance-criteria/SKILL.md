---
name: qa-from-acceptance-criteria
description: Generates test cases from acceptance criteria (one or more TC-n per AC), automates them where possible (unit, API, Playwright e2e), runs them, and writes a test report that exposes gaps and untested criteria. Use for QA, test planning, regression suites, or when asked "how do we test this" or "is every AC covered".
---

# QA from Acceptance Criteria (Phase 6 · QA)

Inputs: approved requirements, design, the built code and its tests. Outputs: `docs/06-qa/test-cases.md` (template `${CLAUDE_PLUGIN_ROOT}/templates/test-cases.md`) and `docs/06-qa/test-report.md`.

## Steps
1. **Derive test cases.** For every AC write at least one TC-n: preconditions, steps, data, expected result, and the level (unit / integration / API / e2e / manual). Add negative and boundary cases (limits ±1, empty, duplicates, concurrency, time zones).
2. **Exploratory pass.** Think like a real user and a malicious user: what scenario is not covered by any AC? Each one is a **gap**.
3. **Automate.** Check which TCs already have tests from the Build phase (map by AC IDs in test names). Write the missing automated tests using the project's existing test framework (e.g. pytest/JUnit/Jest; Playwright for UI). Keep test data deterministic.
4. **Run** the suite. Record pass/fail, flaky tests, and defects (DEF-n with steps to reproduce, severity, linked AC).
5. **Report** in `test-report.md`: AC coverage matrix (AC → TCs → result), defects, gaps, risk assessment, recommendation (ready / not ready).

## Gaps go back upstream
A gap means the requirements are incomplete. **Don't invent the rule.** Under the conductor, run `sdlc-core:reopen requirements "<gap>"` and tell the user the decision is the Product Owner's (this is the feedback loop working as intended).

## Watch for false greens
Tests that assert nothing meaningful, mock the thing under test, or were changed to pass — flag them.

Hand back to `sdlc-core:conductor`; the QA Lead approves.
