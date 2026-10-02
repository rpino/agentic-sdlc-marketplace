#!/usr/bin/env python3
"""
sdlc_session.py - SessionStart hook. If the session starts inside an
Agentic SDLC project, inject a short status summary into Claude's context
so every session knows where the project stands.
"""
import json
import os
import sys

STATE_REL = os.path.join(".sdlc", "state.json")


def find_root(start):
    cur = os.path.abspath(start)
    while True:
        if os.path.isfile(os.path.join(cur, STATE_REL)):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    root = find_root(payload.get("cwd") or os.getcwd())
    if not root:
        sys.exit(0)
    try:
        with open(os.path.join(root, STATE_REL), encoding="utf-8") as f:
            state = json.load(f)
    except Exception:
        sys.exit(0)

    phases = state.get("phases", {})
    order = list(phases.keys())
    nxt = next((p for p in order if phases[p].get("status") != "approved"), None)
    issues = [
        f"[{p}] {i['id']}: {i['text']}"
        for p in order for i in phases[p].get("open_issues", []) if not i.get("resolved")
    ]
    summary = [
        f"This is an Agentic SDLC project: '{state.get('project')}'.",
        f"Current phase: {nxt or 'all phases approved'}"
        + (f" (status: {phases[nxt]['status']})" if nxt else "") + ".",
        "Follow the sdlc-core:conductor skill. Never skip a phase or approve on a human's behalf.",
    ]
    if issues:
        summary.append("Open issues awaiting a human decision: " + "; ".join(issues))
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(summary),
        }
    }))


if __name__ == "__main__":
    main()
