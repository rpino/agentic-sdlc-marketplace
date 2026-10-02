---
name: knowledge-updater
description: Writes team-approved lessons into the project's CLAUDE.md "Standing rules" section (and optionally into skill improvements for the marketplace), keeping rules concise, deduplicated and traceable to their source. Use after a retro or RCA when the team agrees on new rules, or when asked to "remember this for next time" at project level.
---

# Knowledge Updater (Phase 10 · Knowledge)

Input: rules marked **Adopted** in `docs/10-knowledge/retro.md` or an RCA follow-up. Only write rules a human has agreed to.

## Steps
1. Read `CLAUDE.md` and find the `## Standing rules learned on this project` section (create it if missing).
2. For each adopted rule:
   - Check for duplicates or conflicts with existing rules; merge or replace instead of appending near-duplicates.
   - Write it as one imperative, checkable line with its source: `- All date logic uses the club's local time zone. (RCA-2026-031)`
3. Keep the section short — if it grows past ~30 rules, propose consolidating.
4. **Marketplace feedback (optional):** if a lesson applies to *every* project (e.g. "acceptance-criteria skill should always ask about time zones"), draft the change to the relevant skill in the Agentic SDLC marketplace repo and show it to the user as a proposed improvement — don't edit the installed plugin.
5. Show the user the diff of `CLAUDE.md`.

Hand back to `sdlc-core:conductor`.
