---
name: retro-capture
description: Runs or records a retrospective for a feature, sprint or release — what went well, what didn't, what the AI caught or missed at each phase, delivery metrics, and proposed standing rules. Use at the end of a sprint, release or project, or when asked for a retro or lessons learned.
---

# Retro Capture (Phase 10 · Knowledge)

Output: `docs/10-knowledge/retro.md` (template `${CLAUDE_PLUGIN_ROOT}/templates/retro.md`).

## 1. Gather evidence (before asking people)
- `.sdlc/state.json` history: phase durations, reopen events and their reasons, approvals.
- Open issues and how they were decided.
- QA gaps and defects, review findings, RCAs.
- Git/PR data if available: number of PRs, review cycles, lead time.

## 2. Compute delivery metrics
| Metric | How |
|---|---|
| Cycle time per phase | time between status changes in history |
| Feedback loops | count of `reopened` events, by phase |
| Gaps caught pre-production | QA/review findings that reopened earlier phases |
| Escaped defects | RCAs/defects found after release |
| AI catch rate | issues raised by reviewer agents vs. found later by humans |

## 3. Facilitate (ask the team, or the user on their behalf)
- What went well? What was painful? Where did the agents help most / least?
- Which gate added value; which felt like overhead?

## 4. Propose standing rules
Turn each lesson into a **concrete, checkable rule** ("All date logic uses the club's local time zone", not "be careful with dates"). Mark each *Proposed*. The team decides which to adopt — then `sdlc-knowledge:knowledge-updater` writes them into `CLAUDE.md`.

Hand back to `sdlc-core:conductor`.
