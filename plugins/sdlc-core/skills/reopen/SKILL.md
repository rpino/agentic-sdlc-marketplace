---
name: reopen
description: Reopen an earlier SDLC phase when a later phase discovers a gap (e.g. QA finds a missing acceptance criterion, review finds a design flaw), recording the reason as an open issue.
argument-hint: "<phase> \"<reason>\""
---

# Reopen a phase (feedback loop)

Arguments: `$ARGUMENTS`

Use this when work in a later phase reveals that an earlier, approved artifact is wrong or incomplete.

1. Identify the **earliest** phase whose artifact must change (a missing business rule → `requirements`; a wrong integration approach → `design`).
2. Run:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_state.py" reopen <phase> --reason "<concise gap description>" --by "<who found it>"
   ```
3. Tell the user in two lines: what gap was found, which phase was reopened, and that the decision needed is theirs. The conductor will route back to that phase on the next `/sdlc-core:next`.
