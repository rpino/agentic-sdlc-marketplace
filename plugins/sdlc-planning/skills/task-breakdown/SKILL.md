---
name: task-breakdown
description: Breaks an approved design into small, independently verifiable implementation tasks (T-n) linked to acceptance criteria, with dependencies, sequence, estimates and definition of done; optionally creates tickets in Jira or Linear. Use when asked to "plan this", "break it down", "create the backlog" or "make tickets".
---

# Task Breakdown (Phase 4 · Planning)

Inputs: approved `docs/02-requirements/requirements.md` and `docs/03-design/design.md`. Output: `docs/04-planning/tasks.md` (template `${CLAUDE_PLUGIN_ROOT}/templates/tasks.md`).

## Rules for a good task
- **Small:** one PR, ideally ≤ 1 day of work for a developer pairing with an agent, and ≤ ~400 changed lines (the commit hook warns above the project's `max_diff_lines`). Small batches are the strongest predictor of delivery performance.
- **Vertical where possible:** delivers a testable slice, not "all the DB work".
- **Traceable:** lists the AC IDs it satisfies. Every AC is covered by at least one task.
- **Verifiable:** has its own definition of done including the tests that prove it.
- **Ordered:** explicit `depends on` links; migrations and contracts first, UI last; risky/unknown work early (spikes).

## Steps
1. List design components and changes; turn each into one or more tasks.
2. Add cross-cutting tasks the design implies: migrations (expand/contract so they're backward compatible), a feature flag (default OFF) for every user-visible change, telemetry for each SLO, threat-model mitigations, docs, config.
3. Sequence into a dependency order and group into **milestones** (e.g. "API usable behind flag").
4. Estimate (S/M/L or points) — mark estimates as the agent's guess for the team to adjust.
5. Build the **coverage check**: AC → tasks. Any AC without a task is a defect, so fix it. Under the conductor, `trace` checks this, and the phase can't go to review with gaps.
6. Check each task against the **Definition of Ready** in the template. Mark tasks that aren't ready as `blocked` with the reason.
7. **Ticket sync (optional):** if a Jira/Linear/Azure DevOps connector is available and the user wants it, create one ticket per task with the AC IDs, DoD and links back to the docs. Never create tickets without asking.

## Human gate
Priorities, capacity and what goes into the sprint are the **team's** decisions in sprint planning — present the plan; don't commit to dates.

Hand back to `sdlc-core:conductor`.
