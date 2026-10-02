#!/usr/bin/env python3
"""
sdlc_gate.py - PreToolUse hook that enforces the Agentic SDLC gates.

Rules (only inside a project that has .sdlc/state.json):
  1. The state file may only be changed through sdlc_state.py, never by
     direct Write/Edit or ad-hoc shell redirection.
  2. No code may be written under settings.code_paths until the
     `planning` phase is approved by a human.
  3. `git commit` of code changes must include at least one test change
     (settings.require_tests_on_commit).

Outside an SDLC project the hook does nothing.
Reads the hook payload as JSON on stdin; denies with a JSON decision.
"""
import json
import os
import re
import subprocess
import sys

STATE_REL = os.path.join(".sdlc", "state.json")


def allow():
    sys.exit(0)


def deny(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"[Agentic SDLC gate] {reason}",
        }
    }))
    sys.exit(0)


def find_root(start):
    cur = os.path.abspath(start)
    if not os.path.isdir(cur):
        cur = os.path.dirname(cur)
    while True:
        if os.path.isfile(os.path.join(cur, STATE_REL)):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def load_state(root):
    try:
        with open(os.path.join(root, STATE_REL), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def is_code(rel, settings):
    rel = rel.replace(os.sep, "/")
    return any(rel.startswith(p) for p in settings.get("code_paths", []))


def is_test(rel, settings):
    rel = rel.replace(os.sep, "/").lower()
    return any(m in rel for m in settings.get("test_markers", ["test", "spec"]))


def check_file_write(path, cwd):
    if not path:
        allow()
    abspath = path if os.path.isabs(path) else os.path.join(cwd, path)
    root = find_root(os.path.dirname(abspath) or cwd)
    if not root:
        allow()
    state = load_state(root)
    if state is None:
        allow()
    rel = os.path.relpath(abspath, root)
    if rel.replace(os.sep, "/") == ".sdlc/state.json":
        deny("Do not edit .sdlc/state.json directly. Use the sdlc-core skills "
             "(/sdlc-core:approve, /sdlc-core:next), which call scripts/sdlc_state.py.")
    settings = state.get("settings", {})
    planning = state.get("phases", {}).get("planning", {}).get("status")
    if is_code(rel, settings) and planning != "approved":
        deny(f"Code changes to '{rel}' are blocked until the Planning phase is approved "
             f"(planning is '{planning}'). Finish requirements -> design -> planning first, "
             "or run /sdlc-core:status to see what's pending.")
    allow()


def git_files(cwd, args):
    try:
        out = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=10)
        return [l.strip() for l in out.stdout.splitlines() if l.strip()]
    except Exception:
        return []


def check_bash(command, cwd):
    root = find_root(cwd)
    if not root:
        allow()
    state = load_state(root)
    if state is None:
        allow()

    # Rule 1: no ad-hoc writes to the state file from the shell.
    if ".sdlc/state.json" in command and "sdlc_state.py" not in command:
        if re.search(r"(>|>>|\btee\b|\bsed\s+-i|\bmv\b|\bcp\b|\brm\b|python[0-9.]*\s+-c)", command):
            deny("Do not modify .sdlc/state.json from the shell. Use scripts/sdlc_state.py "
                 "through the sdlc-core skills.")

    # Rule 3: commits with code changes must include a test change.
    settings = state.get("settings", {})
    if settings.get("require_tests_on_commit", True) and re.search(r"\bgit\s+commit\b", command):
        files = git_files(root, ["diff", "--cached", "--name-only"])
        if re.search(r"\bgit\s+commit\b[^|;&]*\s-[a-zA-Z]*a", command):
            files += git_files(root, ["diff", "--name-only"])
        code = [f for f in files if is_code(f, settings) and not is_test(f, settings)]
        tests = [f for f in files if is_test(f, settings)]
        if code and not tests:
            deny("This commit changes code (" + ", ".join(code[:5]) + ") but no test files. "
                 "The Agentic SDLC requires tests with every code change: write or update "
                 "a test first, then commit.")
    allow()


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        allow()
    tool = payload.get("tool_name", "")
    tin = payload.get("tool_input", {}) or {}
    cwd = payload.get("cwd") or os.getcwd()

    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        check_file_write(tin.get("file_path") or tin.get("notebook_path"), cwd)
    elif tool == "Bash":
        check_bash(tin.get("command", ""), cwd)
    allow()


if __name__ == "__main__":
    main()
