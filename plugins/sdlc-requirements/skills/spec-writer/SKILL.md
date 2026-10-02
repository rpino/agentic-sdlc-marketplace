---
name: spec-writer
description: Writes requirements.md from an approved problem brief — user stories with IDs, non-functional requirements, assumptions and open questions. Use when moving from an idea or brief to requirements, or when asked to "write the spec", "write user stories" or "turn this into requirements".
---

# Spec Writer (Phase 2 · Requirements, step 1)

Input: `docs/01-discovery/problem-brief.md` (approved). Output: `docs/02-requirements/requirements.md` using `${CLAUDE_PLUGIN_ROOT}/templates/requirements.md`.

## Steps

1. **Read the brief.** List its in-scope capabilities, users and constraints. Anything out of scope stays out.
2. **Ask clarifying questions** (max 5, one at a time) only where the brief is silent on a behaviour that changes the stories. Otherwise record the gap as an open question.
3. **Write user stories** — one per user-visible capability:
   - ID `US-n`, format: *As a <role>, I want <capability> so that <benefit>.*
   - Each story is **independent, small and valuable** (INVEST). Split stories bigger than ~1 sprint.
   - Add a **priority** (Must / Should / Could) and the **brief section** it traces to.
4. **Non-functional requirements** — `NFR-n` for performance, security, privacy, accessibility, audit, availability, compliance. Make each measurable ("p95 < 300 ms", "WCAG 2.1 AA").
5. **Business rules** — `BR-n` for policies the system must enforce (limits, eligibility, fees).
6. **Out of scope** and **open questions** — carried over from the brief plus new ones.
7. Leave the **Acceptance criteria** placeholders under each story — the `acceptance-criteria` skill fills them next.

## Quality bar
- No solution/design language ("use a table", "call the API") — describe behaviour.
- No vague words: *fast, easy, user-friendly, robust, etc.* → replace with measurable terms or raise an open question.
- Every Must story traces to the brief's hypothesis or success metric.

Then continue with `sdlc-requirements:acceptance-criteria`.
