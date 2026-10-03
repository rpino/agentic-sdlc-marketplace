#!/usr/bin/env python3
"""
sdlc_gate.py - PreToolUse hook that enforces the Agentic SDLC gates.

Rules (only inside a project that has .sdlc/state.json):
  1. Files under .sdlc/ (state, approval tokens) may only be changed through
     sdlc_state.py - never by Write/Edit or ad-hoc shell/PowerShell writes.
  2. Approvals are human-only: the agent may not run `sdlc_state.py approve`
     unless the user just typed /sdlc-core:approve (which issues a one-time token).
  3. No code may be written under settings.code_paths - by an edit tool OR a shell
     command - until every phase of the active feature's lane before Build is approved.
  4. `git commit` of code changes must include at least one test change
     (settings.require_tests_on_commit; test files matched by settings.test_patterns).
  5. Commands matching settings.blocked_commands (production deploys, force pushes)
     are denied: changing production is a human action.
  6. Commits larger than settings.max_diff_lines get a warning (small batches).

Outside an SDLC project the hook does nothing. Shell parsing is best-effort
defence in depth; the state script enforces approvals itself as well.
Reads the hook payload as JSON on stdin; denies with a JSON decision.
"""
import json
import os
import re
import shlex
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sdlc_state as S  # noqa: E402

SHELL_TOOLS = ("Bash", "PowerShell")
EDIT_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")

# Ops whose every path argument may be written.
ANY_TARGET_OPS = {"tee", "touch", "truncate", "rm", "rmdir", "unlink", "set-content", "add-content",
                  "out-file", "new-item", "remove-item", "clear-content"}
# Ops whose last argument is the destination.
DEST_OPS = {"cp", "mv", "install", "rsync", "copy-item", "move-item", "ln"}
INLINE_INTERPRETERS = re.compile(r"\b(python[0-9.]*|py|node|ruby|perl|php)\s+(-[a-zA-Z]*[ce]\b)")
REDIRECT = re.compile(r"(?:^|[^0-9&<>=\-])\d?>>?\s*([\"']?)([^\s\"';|&>]+)")


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


def warn(message):
    print(json.dumps({"systemMessage": f"[Agentic SDLC] {message}"}))
    sys.exit(0)


def project(start):
    root = S.find_root(start)
    if not root:
        return None, None
    state = S.read_state(root)
    if state is None:
        return None, None
    return root, state


def active_feature(state):
    feats = state.get("features", {})
    return feats.get(state.get("active_feature")) or next(iter(feats.values()), None)


def rel_to_root(token, cwd, root):
    """Project-relative path for a shell token, or None if it is outside the project."""
    t = token.strip("\"'")
    if t.startswith("of="):
        t = t[3:]
    if not t or t.startswith("-"):
        return None
    if os.name == "nt":
        m = re.match(r"^/([a-zA-Z])/(.*)", t)  # Git Bash style /c/Users/...
        if m:
            t = f"{m.group(1)}:/{m.group(2)}"
    path = t if os.path.isabs(t) else os.path.join(cwd, t)
    try:
        rel = os.path.relpath(os.path.abspath(path), root).replace(os.sep, "/")
    except ValueError:  # different drive
        return None
    if rel.startswith(".."):
        return None
    return rel


def protected_reason(rel, state):
    """Why writing this project-relative path is not allowed right now, or None."""
    if rel == ".sdlc" or rel.startswith(".sdlc/"):
        return ("Do not modify files under .sdlc/ directly. Use the sdlc-core skills "
                "(/sdlc-core:next, /sdlc-core:approve), which call scripts/sdlc_state.py.")
    feat = active_feature(state)
    code = S.is_code(rel, state["settings"]) or S.is_code(rel + "/", state["settings"])
    if feat and code and not S.code_unlocked(feat):
        return (f"Code changes to '{rel}' are blocked for feature '{feat['slug']}' "
                f"({S.code_lock_reason(feat)}). Finish the earlier phases first, "
                "or run /sdlc-core:status to see what's pending.")
    return None


def check_file_write(path, cwd):
    if not path:
        allow()
    abspath = path if os.path.isabs(path) else os.path.join(cwd, path)
    root, state = project(os.path.dirname(abspath) or cwd)
    if not root:
        allow()
    rel = os.path.relpath(abspath, root).replace(os.sep, "/")
    reason = protected_reason(rel, state)
    if reason:
        deny(reason)
    allow()


def split_segments(command):
    return [s for s in re.split(r"\s*(?:&&|\|\||;|\||\n)\s*", command) if s.strip()]


def tokens(segment):
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def write_targets(segment):
    """Paths a single shell segment may write to (best effort)."""
    targets = [m.group(2) for m in REDIRECT.finditer(segment)]
    toks = tokens(segment)
    if not toks:
        return targets
    op = os.path.basename(toks[0]).lower()
    args = [t for t in toks[1:] if not t.startswith("-") or t.startswith("of=")]
    if op in ANY_TARGET_OPS:
        targets += args
    elif op in DEST_OPS and args:
        targets.append(args[-1])
    elif op in ("sed", "perl") and any(re.match(r"^-[a-zA-Z]*i", t) for t in toks[1:]):
        targets += args[1:]
    elif op == "dd":
        targets += [t for t in toks[1:] if t.startswith("of=")]
    elif op == "git" and len(toks) > 1 and toks[1] in ("checkout", "restore", "apply", "mv", "rm"):
        targets += [t for t in toks[2:] if not t.startswith("-")]
    return targets


def staged_line_count(root):
    total = 0
    for line in git_lines(root, ["diff", "--cached", "--numstat"]):
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            total += int(parts[0]) + int(parts[1])
    return total


def git_lines(cwd, args):
    try:
        out = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=10)
        return [l.strip() for l in out.stdout.splitlines() if l.strip()]
    except Exception:
        return []


def check_shell(command, cwd):
    root, state = project(cwd)
    if not root:
        allow()
    settings = state["settings"]

    # Rule 5: production-changing commands are a human action.
    for pattern in settings.get("blocked_commands", []):
        try:
            if re.search(pattern, command):
                deny(f"'{command[:80]}' matches a blocked command ({pattern}). Deploying, changing "
                     "infrastructure and force-pushing are done by a human. Present the command "
                     "for the user to run instead.")
        except re.error:
            continue

    for seg in split_segments(command):
        if "sdlc_state.py" in seg:
            # Rule 2: approvals only right after the human typed /sdlc-core:approve.
            if re.search(r"\bapprove\b", seg) and not os.path.isfile(S.token_path(root)):
                deny("Approvals are made by a human. Ask the approver to type "
                     "/sdlc-core:approve <phase> - never run the approve command yourself.")
            continue
        # Rules 1 & 3 through the shell.
        if INLINE_INTERPRETERS.search(seg) and re.search(r"write|open\(|>|copy|move|remove|unlink", seg, re.I):
            if ".sdlc" in seg:
                deny("Do not modify .sdlc/ from inline scripts. Use scripts/sdlc_state.py.")
            feat = active_feature(state)
            if feat and not S.code_unlocked(feat):
                for p in settings.get("code_paths", []):
                    if re.search(r"(?<![A-Za-z0-9_])" + re.escape(p), seg):
                        deny(f"Inline scripts may not write to '{p}' yet "
                             f"({S.code_lock_reason(feat)}).")
        for target in write_targets(seg):
            rel = rel_to_root(target, cwd, root)
            if rel:
                reason = protected_reason(rel, state)
                if reason:
                    deny(reason)

    # Rule 4: commits with code changes must include a test change.
    if re.search(r"\bgit\s+commit\b", command):
        files = git_lines(root, ["diff", "--cached", "--name-only"])
        if re.search(r"\bgit\s+commit\b[^|;&]*\s-[a-zA-Z]*a", command):
            files += git_lines(root, ["diff", "--name-only"])
        if settings.get("require_tests_on_commit", True):
            code = [f for f in files if S.is_code(f, settings) and not S.is_test(f, settings)]
            tests = [f for f in files if S.is_test(f, settings)]
            if code and not tests:
                deny("This commit changes code (" + ", ".join(code[:5]) + ") but no test files. "
                     "The Agentic SDLC requires tests with every code change: write or update "
                     "a test first, then commit.")
        # Rule 6: small batches.
        limit = settings.get("max_diff_lines", 400)
        n = staged_line_count(root)
        if limit and n > limit:
            warn(f"This commit changes {n} lines (limit {limit}). Smaller commits are easier to "
                 "review and roll back; consider splitting the task.")
    allow()


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        allow()
    tool = payload.get("tool_name", "")
    tin = payload.get("tool_input", {}) or {}
    cwd = payload.get("cwd") or os.getcwd()

    if tool in EDIT_TOOLS:
        check_file_write(tin.get("file_path") or tin.get("notebook_path"), cwd)
    elif tool in SHELL_TOOLS:
        check_shell(tin.get("command", ""), cwd)
    allow()


if __name__ == "__main__":
    main()
