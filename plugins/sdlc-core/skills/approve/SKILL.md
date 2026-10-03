---
name: approve
description: Human approval gate — records that a named person approved the current (or given) SDLC phase and advances the project to the next phase.
argument-hint: "[phase] [--feature slug] [--note \"...\"]"
disable-model-invocation: true
---

# Approve a phase (human gate)

Arguments: `$ARGUMENTS`

This skill exists so that **a human**, not the agent, moves the project forward. It must only run because the user typed `/sdlc-core:approve`. When they do, a `UserPromptSubmit` hook issues a one-time token. That token is valid for 30 minutes and is used up by a single approval. Without it, the state script refuses to approve.

Below, `SDLC` means `sh "${CLAUDE_PLUGIN_ROOT}/scripts/run_py.sh" "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_state.py"`.

1. Run `SDLC next --json` (add `--feature <slug>` if the user named one) to find the phase awaiting review. If the user named a phase, use that one.

2. If that phase is **not** `in_review`, explain its status and stop (e.g. "Design is still a draft. Run `/sdlc-core:next` first").

3. Show a compact **approval summary** before recording anything:
   - feature, phase and gate (what the approver is confirming)
   - artifact paths
   - for planning, QA and review: the output of `SDLC trace` (coverage gaps, failing tests)
   - for build and review: if a GitHub CLI or connector is available, the linked PRs and their review state (`gh pr view <n> --json reviews,statusCheckRollup`)
   - any open issues, including "submitted despite failed exit checks". Approving with open issues requires the user to confirm explicitly.

4. Determine the **approver name**: the approver listed for this phase in the state file. If the person typing is someone else, ask who they are. Never invent a name.

5. Record the approval:
   ```
   SDLC approve <phase> --by "<Name>" [--feature <slug>] [--note "<note>"] [--accept-open-issues]
   ```
   Only add `--accept-open-issues` if the user explicitly said to approve despite the open issues.
   - If the script says the approval "must be requested by a human", the token is missing or expired (more than 30 minutes since the user typed the command). Ask the user to type `/sdlc-core:approve <phase>` again, or to run the command above themselves in a terminal, where it asks them to confirm. Do not try another way around it.

6. Report the result in one line and say what the next phase is. Do **not** start the next phase automatically. The user runs `/sdlc-core:next` when ready.
