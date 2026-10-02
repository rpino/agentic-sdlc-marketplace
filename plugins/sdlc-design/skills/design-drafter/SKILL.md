---
name: design-drafter
description: Produces design.md and Architecture Decision Records from approved requirements, grounded in the existing codebase — components, data model, APIs, sequence flows, edge cases and an AC-to-design map. Use when asked to "design this", "propose an architecture", "how should we build it" or write an ADR.
---

# Design Drafter (Phase 3 · Design)

Inputs: `docs/02-requirements/requirements.md` (approved), the codebase. Outputs: `docs/03-design/design.md` (template `${CLAUDE_PLUGIN_ROOT}/templates/design.md`) and one `docs/03-design/adr/ADR-nnn-<slug>.md` per significant decision (template `${CLAUDE_PLUGIN_ROOT}/templates/adr.md`).

## Steps

1. **Understand the system first.** Explore the repo: entry points, modules touched by the stories, data stores, integrations, existing patterns and conventions (naming, error handling, testing). Note anything in `CLAUDE.md` under "Standing rules". If there is no code yet, say so and design greenfield.
2. **Map requirements to change.** For each AC, decide which component(s) change. Every AC must land somewhere.
3. **Draft the design** — keep it as small as the requirements allow:
   - Context and component diagram (Mermaid)
   - Data model changes (tables/fields, migrations, backward compatibility)
   - API / interface contracts (request, response, errors)
   - Sequence diagram for the main flow(s) (Mermaid)
   - Edge cases & failure modes, with how each is handled
   - Security & privacy (authz, PII, audit), observability (logs/metrics/alerts)
   - Rollout: feature flag, migration order, rollback
4. **Options for big decisions.** Where there is a real choice (sync vs. async, new service vs. module, vendor A vs. B), write an ADR with at least two options, trade-offs and a recommendation. Mark it *Proposed* — the Tech Lead decides.
5. **Risks & open questions** — integration unknowns, performance doubts, anything needing a spike → open questions (and `sdlc_state.py issue add design "<question>"` under the conductor).
6. **Review.** Run the `design-reviewer` agent if available and fold in its findings.

## Quality bar
- Follows existing codebase patterns unless an ADR justifies deviating.
- No gold-plating: nothing that isn't needed by an AC or NFR.
- The AC → component table is complete.

Hand back to `sdlc-core:conductor`.
