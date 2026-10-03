# Security policy

## What the gates protect against

The Agentic SDLC gates exist to keep a **well-intentioned but over-eager AI agent** inside the process. The agent shouldn't skip phases, approve its own work, write code before the plan is approved, commit without tests, or deploy to production. Each gate has layered checks:

| Gate | Layers |
|---|---|
| Human-only approval | A one-time token issued by the `UserPromptSubmit` hook when the user types `/sdlc-core:approve`. The state script refuses an approval without it, and the `PreToolUse` hook denies agent-run approve commands. |
| State integrity | `PreToolUse` denies edit-tool, shell and PowerShell writes under `.sdlc/`. Every change goes through `sdlc_state.py`, which validates each transition. |
| Code lock, tests with commits, blocked production commands | `PreToolUse` checks on edit tools, Bash and PowerShell. |
| Tampering after approval | Artifact hashes are stored at approval time, and `verify` and `status` flag changes. |

## What they are not

- **Not a sandbox.** The shell checks parse commands best-effort. A process set on writing a file can find another way to do it. Use OS-level sandboxing or permission rules in Claude Code if you need a hard boundary.
- **Not authentication.** The approval token proves that a person typed the slash command in this project within the last 30 minutes. It doesn't prove who they are. The approver name is still what `--by` says, plus the recorded git identity. For approvals tied to an identity, require PR reviews or CODEOWNERS on your git host as well.
- **Not protection from someone at the keyboard.** Anyone who can type in the session or edit files directly can change the state.

## Supported versions

| Version | Supported |
|---|---|
| 0.2.x | ✅ |
| < 0.2 | ❌ No human-intent token, and shell writes to code paths were not checked. Please upgrade. |

## Reporting a vulnerability

If you find a way for an **agent** to get past a gate without a human typing a command, for example by approving a phase, unlocking code, or editing `.sdlc/`:

1. Don't open a public issue or PR with the bypass.
2. Report it privately through GitHub's **Report a vulnerability** form (Security tab → Advisories) on this repository, or by email to the maintainer listed in `.claude-plugin/marketplace.json`.
3. Include the Claude Code version, the OS and shell, and the minimal command or tool call that gets through.

You'll get an acknowledgement within 7 days. Confirmed bypasses get a test in `tests/test_sdlc_gate.py` and a fix in the next patch release, with credit in `CHANGELOG.md` unless you'd rather not be named.
