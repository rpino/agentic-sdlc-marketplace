---
name: idea-interviewer
description: Turns a raw idea or stakeholder request into a problem brief by interviewing the user — problem, who is affected, hypothesis, success metric, constraints, scope. Use at the start of a new feature, initiative or project, or when someone says "I have an idea", "the business wants…", or "should we build…".
---

# Idea Interviewer (Phase 1 · Discovery)

Goal: produce `docs/01-discovery/problem-brief.md` that a stakeholder can approve. **Do not propose solutions yet** — this phase is about the problem.

## 1. Interview (one question at a time)

Ask, wait for the answer, then ask the next. Skip anything the user already answered. Push gently on vague answers ("How would we know?", "Roughly how many?").

1. **Problem** — What is happening today that hurts? Who said so, and what evidence is there (data, tickets, complaints)?
2. **Who** — Which users/roles are affected? Who else is touched (support, billing, ops, partners)?
3. **Why now** — What happens if we do nothing for 6 months?
4. **Outcome & metric** — What changes if we succeed? Which number moves, from what to what, by when?
5. **Constraints** — Contracts, regulation, legacy systems, budget, deadlines, team capacity.
6. **Scope** — What is explicitly **out** of scope for the first release?
7. **Risks & assumptions** — What must be true for this to work? What could make it fail?

Stop after at most ~8 questions; record unknowns as open questions instead of interrogating.

## 2. Write the brief

Use the template at `${CLAUDE_PLUGIN_ROOT}/templates/problem-brief.md`. Fill every section; write "Unknown — open question" rather than inventing facts. Keep it to one page.

## 3. Flag decisions for the human

List anything only a person can decide (budget, priority vs. other work, risk appetite) under **Open questions**. If running under the conductor, also record each with `sdlc_state.py issue add discovery "<question>"`.

## 4. Hand back

Tell the user where the brief is and summarise it in 3 lines. If inside an SDLC project, return control to `sdlc-core:conductor` (it submits the phase for review).
