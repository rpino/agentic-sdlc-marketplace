---
name: approve
description: Human approval gate — records that a named person approved the current (or given) SDLC phase and advances the project to the next phase.
argument-hint: "[phase] [--note \"...\"]"
disable-model-invocation: true
---

# Approve a phase (human gate)

Arguments: `$ARGUMENTS`

This skill exists so that **a human** — not the agent — moves the project forward. It must only run because the user typed `/sdlc-core:approve`.

1. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_state.py" next --json` to find the phase awaiting review. If the user named a phase, use that one.

2. If that phase is **not** `in_review`, explain its status and stop (e.g. "Design is still a draft — run `/sdlc-core:next` first").

3. Show a compact **approval summary** before recording anything:
   - phase and gate (what the approver is confirming)
   - artifact paths
   - any open issues (approval with open issues requires the user to confirm explicitly)

4. Determine the **approver name**: the approver listed for this phase in the state file. If the person typing is someone else, ask who they are. Never invent a name.

5. Record the approval:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_state.py" approve <phase> --by "<Name>" [--note "<note>"] [--accept-open-issues]
   ```
   Only add `--accept-open-issues` if the user explicitly said to approve despite the open issues.

6. Report the result in one line and say what the next phase is. Do **not** start the next phase automatically — the user runs `/sdlc-core:next` when ready.
