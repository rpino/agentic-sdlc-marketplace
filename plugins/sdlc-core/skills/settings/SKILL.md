---
name: settings
description: Human-only change of Agentic SDLC gate settings — gated code paths, the test-on-commit rule, test file patterns, blocked production commands and the commit size limit.
argument-hint: "show | add-code-path P | remove-code-path P | require-tests on|off | add-test-pattern G | remove-test-pattern G | block-command RE | unblock-command RE | max-diff-lines N"
disable-model-invocation: true
---

# Change gate settings (human only)

Arguments: `$ARGUMENTS`

Some changes make a gate weaker: turning tests off, removing a code path, adding a test pattern, unblocking a command, or raising the commit size limit. Those need the one-time token that the `UserPromptSubmit` hook issues because the user typed `/sdlc-core:settings`. Changes that make a gate stricter work at any time.

1. If no arguments were given, run `SDLC settings show` and explain each value in one line. Here `SDLC` means `sh "${CLAUDE_PLUGIN_ROOT}/scripts/run_py.sh" "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_state.py"`.
2. Otherwise, before a weakening change, say in one sentence what it allows. Then run:
   ```
   SDLC settings <action> [value] --by "<user name>"
   ```
3. Show the result. If the script asks for a human, ask the user to type the slash command again (the token lasts 30 minutes and is used up by a single change).
