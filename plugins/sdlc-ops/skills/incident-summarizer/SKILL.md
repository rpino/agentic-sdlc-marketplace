---
name: incident-summarizer
description: Summarises an incident or post-release health check into a blameless root-cause analysis — timeline, impact, root cause (5 whys), fix, and follow-up actions including new acceptance criteria and standing rules. Use when something breaks in production, an alert fires, or for a post-release review.
argument-hint: "[incident description, alert, log or ticket]"
---

# Incident Summarizer (Phase 9 · Operate)

Input: `$ARGUMENTS` plus any logs, alerts, tickets or chat the user provides (or a monitoring/incident connector if available).

## Health check mode (no incident)
If there's no incident, write `docs/09-operate/monitoring.md`: rollout stage, each **SLO vs. target and error budget remaining**, health metrics vs. expectations, success metric vs. the brief's target, open defects, the result of a **rollback rehearsal / game day** if one was run, and a recommendation (advance rollout / hold / roll back). A burning error budget means hold. Advancing or rolling back is a human decision.

## Incident mode
Write `docs/09-operate/RCA-<yyyy>-<nn>.md` using `${CLAUDE_PLUGIN_ROOT}/templates/rca.md`:
1. **Summary** — what happened, in 2–3 sentences.
2. **Impact** — who/how many, duration, money, data.
3. **Timeline** — detection, escalation, mitigation, resolution (with times and time zone).
4. **Root cause** — 5 whys down to the process/system cause, not a person. **Blameless.**
5. **Why it wasn't caught** — which phase should have caught it (missing AC? missing test? design gap? review miss?).
6. **Fix** — immediate mitigation and permanent fix.
7. **Follow-ups** — each with owner and due date:
   - new/changed **acceptance criteria** → under the conductor, `sdlc-core:reopen requirements "<new AC>"`
   - new **tests**
   - a **standing rule** for `CLAUDE.md` (handed to `sdlc-knowledge:knowledge-updater`)

Under the conductor, record the incident for the DORA metrics: `record incident --ref RCA-<yyyy>-<nn>` when it starts, and `record restore --ref RCA-<yyyy>-<nn>` when service is restored. Change failure rate and time to restore come from these.

Customer/stakeholder communication and refunds/compensation are human decisions — draft them, don't send them.
