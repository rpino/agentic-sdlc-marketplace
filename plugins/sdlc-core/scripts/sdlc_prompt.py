#!/usr/bin/env python3
"""
sdlc_prompt.py - UserPromptSubmit hook. Issues a one-time "human intent" token
when the user themself types /sdlc-core:approve or /sdlc-core:settings.

The model cannot submit user prompts, so the token proves a human asked for
the approval (or for a settings change that weakens a gate). sdlc_state.py
consumes the token; it expires after 30 minutes.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sdlc_state as S  # noqa: E402

COMMANDS = {
    "approve": re.compile(r"^/(?:sdlc-core:)?approve(?:\s|$)"),
    "settings": re.compile(r"^/(?:sdlc-core:)?settings(?:\s|$)"),
}


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    prompt = (payload.get("prompt") or "").strip()
    scope = next((s for s, rx in COMMANDS.items() if rx.match(prompt)), None)
    if not scope:
        sys.exit(0)
    root = S.find_root(payload.get("cwd") or os.getcwd())
    if not root:
        sys.exit(0)
    try:
        S.write_token(root, scope, prompt=prompt[:200], session_id=payload.get("session_id"))
    except OSError:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
