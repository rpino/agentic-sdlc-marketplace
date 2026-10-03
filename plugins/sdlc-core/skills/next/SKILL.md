---
name: next
description: Advance the current Agentic SDLC project to its next step — runs the skills for the current phase, or reports that a human approval is pending.
argument-hint: "[optional notes or feedback for this phase]"
disable-model-invocation: true
---

# Next step

User notes for this step (may be empty): `$ARGUMENTS`

Follow the `sdlc-core:conductor` skill exactly, starting from step 1 of its loop. If the user named a feature (e.g. `/sdlc-core:next --feature export-csv`), pass `--feature <slug>` to every state command.

If the user gave notes and the current phase is `in_review`, treat the notes as **review feedback**: set the phase back to `draft` (`sh "${CLAUDE_PLUGIN_ROOT}/scripts/run_py.sh" "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_state.py" set-status <phase> draft`), revise the artifact to address the feedback, then submit it for review again.
