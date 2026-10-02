---
name: status
description: Show where an Agentic SDLC project stands — every phase's status, who approved what, open issues awaiting decisions, and what happens next.
---

# Project status

1. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_state.py" status`.
2. Show the output as-is in a code block.
3. Underneath, add one or two sentences: what's next and who needs to act (e.g. "Design is waiting for the Tech Lead's approval → `/sdlc-core:approve design`").

If no project is found, say so and suggest `/sdlc-core:init "<Project Name>"`.
