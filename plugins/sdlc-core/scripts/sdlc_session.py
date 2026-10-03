#!/usr/bin/env python3
"""
sdlc_session.py - SessionStart hook. If the session starts inside an
Agentic SDLC project, inject a short status summary into Claude's context
so every session knows where the project stands.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sdlc_state as S  # noqa: E402


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    root = S.find_root(payload.get("cwd") or os.getcwd())
    if not root:
        sys.exit(0)
    state = S.read_state(root)
    if state is None:
        sys.exit(0)

    slug = state.get("active_feature")
    feat = state["features"].get(slug)
    if not feat:
        sys.exit(0)
    nxt = S.next_phase(feat)
    phases = feat["phases"]
    issues = [
        f"[{p}] {i['id']}: {i['text']}"
        for p in feat["lane"] for i in S.open_issues(phases[p])
    ]
    stale = [p for p in feat["lane"]
             if phases[p]["status"] == "approved" and S.stale_artifacts(root, phases[p])]
    summary = [
        f"This is an Agentic SDLC project: '{state.get('project')}'.",
        f"Active feature: '{feat['name']}' ({slug}, {feat['type']} lane: {' -> '.join(feat['lane'])}; "
        f"docs in {feat['docs_root']}/).",
        f"Current phase: {nxt or 'all phases approved'}"
        + (f" (status: {phases[nxt]['status']})" if nxt else "") + ".",
        "Code paths are " + ("unlocked." if S.code_unlocked(feat)
                             else f"locked ({S.code_lock_reason(feat)})."),
        "Follow the sdlc-core:conductor skill. Never skip a phase or approve on a human's behalf.",
    ]
    if issues:
        summary.append("Open issues awaiting a human decision: " + "; ".join(issues))
    if stale:
        summary.append("Approved phases whose artifacts changed since approval: " + ", ".join(stale)
                       + " (run `sdlc_state.py verify`).")
    others = [s for s in state["features"] if s != slug]
    if others:
        summary.append(f"Other features in this project: {', '.join(others)}.")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(summary),
        }
    }))


if __name__ == "__main__":
    main()
