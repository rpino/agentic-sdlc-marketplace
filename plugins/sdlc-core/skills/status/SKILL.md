---
name: status
description: Show where an Agentic SDLC project stands — every phase's status, who approved what, open issues awaiting decisions, and what happens next.
---

# Project status

1. Run `sh "${CLAUDE_PLUGIN_ROOT}/scripts/run_py.sh" "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_state.py" status` (add `--all` if the user asks about every feature).
2. Show the output as-is in a code block.
3. Underneath, add one or two sentences: what's next and who needs to act (e.g. "Design is waiting for the Tech Lead's approval → `/sdlc-core:approve design`").

If the output shows `approved (STALE)`, say which artifact changed since approval and suggest `verify` or reopening the phase. If the user asks about coverage, also run `trace`. If they ask about delivery performance, run `metrics`.

If no project is found, say so and suggest `/sdlc-core:init "<Project Name>"`.
