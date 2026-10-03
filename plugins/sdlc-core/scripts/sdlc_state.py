#!/usr/bin/env python3
"""
sdlc_state.py - the single source of truth for an Agentic SDLC project.

All reads and writes of .sdlc/state.json go through this script so that
phase transitions and human approvals are deterministic and auditable.

A project holds one or more *features* (work items). Each feature follows a
*lane* - the subset of the 10 phases its work type needs (a hotfix skips
discovery and design, a spike stops after design, ...).

Usage:
  sdlc_state.py init "<Project Name>" [--approver NAME] [--tech-lead NAME] [--qa-lead NAME]
                [--type LANE] [--dir PATH]
  sdlc_state.py feature new "<Name>" [--type LANE] [--docs-root PATH]
  sdlc_state.py feature list | switch <slug>
  sdlc_state.py status [--json] [--all]
  sdlc_state.py next [--json]
  sdlc_state.py set-status <phase> <draft|in_review> [--artifact PATH ...] [--force-reason TEXT]
  sdlc_state.py approve <phase> --by NAME [--note TEXT] [--accept-open-issues]
  sdlc_state.py reopen <phase> --reason TEXT [--by NAME]
  sdlc_state.py issue add <phase> "<text>"
  sdlc_state.py issue resolve <phase> <issue-id> [--note TEXT]
  sdlc_state.py verify [--json]              # approvals whose artifacts changed since
  sdlc_state.py trace [--json]               # US -> AC -> T -> TC -> result matrix + orphans
  sdlc_state.py metrics [--json]             # DORA + flow metrics from the history
  sdlc_state.py record deploy|incident|restore [--note TEXT] [--ref ID]
  sdlc_state.py settings show | add-code-path P | remove-code-path P | require-tests on|off
                | add-test-pattern G | remove-test-pattern G | block-command RE | unblock-command RE
                | max-diff-lines N
  sdlc_state.py phases [--json] | lanes [--json]

Every command except init/phases/lanes accepts --feature SLUG (default: the active feature).

Approvals (and settings that weaken a gate) need proof that a human asked for
them: either a one-time token written by the UserPromptSubmit hook when the user
typed /sdlc-core:approve (or /sdlc-core:settings), or an interactive confirmation
when the script is run from a real terminal.

Only the Python standard library is used.
"""
import argparse
import copy
import datetime as _dt
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import time

STATE_DIR = ".sdlc"
STATE_FILE = "state.json"
TOKEN_FILE = "approval-token.json"
TOKEN_TTL_SECONDS = 30 * 60
SCHEMA_VERSION = 2

# ---------------------------------------------------------------------------
# Phase map: the process definition. Order matters.
# Artifact paths are relative to the feature's docs_root (default "docs");
# root_artifacts are relative to the project root.
# ---------------------------------------------------------------------------
PHASES = [
    {
        "id": "discovery",
        "title": "Discovery",
        "folder": "01-discovery",
        "skills": ["sdlc-discovery:idea-interviewer"],
        "artifacts": ["01-discovery/problem-brief.md"],
        "gate": "Product Owner + stakeholder agree the problem is worth solving",
        "approver_role": "product_owner",
    },
    {
        "id": "requirements",
        "title": "Requirements",
        "folder": "02-requirements",
        "skills": ["sdlc-requirements:spec-writer", "sdlc-requirements:acceptance-criteria"],
        "agents": ["sdlc-requirements:requirements-reviewer"],
        "artifacts": ["02-requirements/requirements.md"],
        "gate": "Product Owner approves stories and testable acceptance criteria",
        "approver_role": "product_owner",
    },
    {
        "id": "design",
        "title": "Architecture / Design",
        "folder": "03-design",
        "skills": ["sdlc-design:design-drafter"],
        "agents": ["sdlc-design:design-reviewer"],
        "artifacts": ["03-design/design.md"],
        "optional_artifacts": ["03-design/adr/"],
        "gate": "Tech Lead approves design, threat model and ADRs",
        "approver_role": "tech_lead",
    },
    {
        "id": "planning",
        "title": "Planning",
        "folder": "04-planning",
        "skills": ["sdlc-planning:task-breakdown"],
        "artifacts": ["04-planning/tasks.md"],
        "gate": "Team agrees on tasks, sequence and priorities (sprint planning)",
        "approver_role": "team",
    },
    {
        "id": "build",
        "title": "Implementation",
        "folder": "05-build",
        "skills": ["sdlc-build:task-executor"],
        "artifacts": ["05-build/build-log.md"],
        "gate": "Developers have reviewed every task diff; all tasks done",
        "approver_role": "tech_lead",
    },
    {
        "id": "qa",
        "title": "Testing / QA",
        "folder": "06-qa",
        "skills": ["sdlc-qa:qa-from-acceptance-criteria"],
        "agents": ["sdlc-qa:test-auditor"],
        "artifacts": ["06-qa/test-cases.md", "06-qa/test-report.md"],
        "gate": "QA Lead confirms every acceptance criterion has a passing test",
        "approver_role": "qa_lead",
    },
    {
        "id": "review",
        "title": "Code Review / Security",
        "folder": "07-review",
        "skills": ["sdlc-review:pr-reviewer", "sdlc-review:security-checklist"],
        "agents": ["sdlc-review:code-reviewer", "sdlc-review:security-reviewer"],
        "artifacts": ["07-review/review-report.md"],
        "gate": "Tech Lead signs off the merge; no open high-severity findings",
        "approver_role": "tech_lead",
    },
    {
        "id": "release",
        "title": "Release",
        "folder": "08-release",
        "skills": ["sdlc-release:release-notes", "sdlc-release:pipeline-fixer"],
        "artifacts": ["08-release/release-plan.md", "08-release/release-notes.md"],
        "gate": "Product Owner + stakeholder give go/no-go for rollout",
        "approver_role": "product_owner",
    },
    {
        "id": "operate",
        "title": "Operate / Monitor",
        "folder": "09-operate",
        "skills": ["sdlc-ops:incident-summarizer"],
        "artifacts": ["09-operate/monitoring.md"],
        "optional_artifacts": ["09-operate/"],
        "gate": "Product Owner confirms rollout is stable (SLOs met) or incidents are handled",
        "approver_role": "product_owner",
    },
    {
        "id": "knowledge",
        "title": "Knowledge / Retro",
        "folder": "10-knowledge",
        "skills": ["sdlc-knowledge:retro-capture", "sdlc-knowledge:knowledge-updater"],
        "artifacts": ["10-knowledge/retro.md"],
        "root_artifacts": ["CLAUDE.md"],
        "gate": "Team agrees which lessons become standing rules",
        "approver_role": "team",
    },
]
PHASE_IDS = [p["id"] for p in PHASES]
STATUSES = ["not_started", "draft", "in_review", "approved", "reopened", "needs_revalidation"]

# Work types and the phases each one runs (always in PHASES order).
LANES = {
    "feature": {
        "phases": PHASE_IDS,
        "description": "New capability: the full idea-to-retro flow.",
    },
    "bugfix": {
        "phases": ["requirements", "build", "qa", "review", "release"],
        "description": "Defect fix: expected behaviour as ACs, then fix, test, review, release.",
    },
    "hotfix": {
        "phases": ["build", "review", "release", "operate", "knowledge"],
        "description": "Production emergency: fix first, mandatory review, then RCA and retro.",
    },
    "spike": {
        "phases": ["discovery", "design"],
        "description": "Time-boxed investigation: ends with a design/ADR, no production code.",
    },
    "chore": {
        "phases": ["planning", "build", "review"],
        "description": "Maintenance (dependency bumps, refactors): plan, build, review.",
    },
}

DEFAULT_CODE_PATHS = ["src/", "app/", "lib/", "services/", "packages/", "api/", "web/", "tests/", "test/"]
# Globs matched against the file name; entries ending in "/" match a directory
# anywhere in the path. Patterns with capitals are matched case-sensitively.
DEFAULT_TEST_PATTERNS = [
    "test_*", "*_test.*", "*.test.*", "*.spec.*", "*_spec.*",
    "*Test.java", "*Tests.java", "*Test.kt", "*Tests.cs", "*Test.cs", "*Tests.swift",
    "tests/", "test/", "__tests__/", "spec/",
]
# Commands that change production or shared infrastructure. Deploying is a human action.
DEFAULT_BLOCKED_COMMANDS = [
    r"\bterraform\s+(apply|destroy)\b",
    r"\bkubectl\s+(apply|delete|rollout|scale)\b",
    r"\bhelm\s+(install|upgrade|uninstall|rollback)\b",
    r"\bvercel\b.*\s--prod\b",
    r"\bgit\s+push\b.*\s(--force|-f)\b",
    r"\bgit\s+push\b.*\b(main|master)\b",
]

DEFAULT_SETTINGS = {
    # Code may not be written in these paths until every lane phase before Build is approved.
    "code_paths": DEFAULT_CODE_PATHS,
    # Block `git commit` of code changes that do not include a test change.
    "require_tests_on_commit": True,
    "test_patterns": DEFAULT_TEST_PATTERNS,
    # Warn (not block) when a commit's staged diff is larger than this.
    "max_diff_lines": 400,
    "blocked_commands": DEFAULT_BLOCKED_COMMANDS,
}

ID_PATTERNS = {
    "US": r"US-(\d+)",
    "AC": r"AC-(\d+)\.(\d+)",
    "T": r"T-(\d+)",
    "TC": r"TC-(\d+)",
    "DEF": r"DEF-(\d+)",
}
_BOUND = r"(?<![A-Za-z0-9])"
ID_RE = {k: re.compile(_BOUND + v + r"(?![0-9])") for k, v in ID_PATTERNS.items()}
RESULT_RE = re.compile(r"\b(PASS(?:ED)?|FAIL(?:ED)?|BLOCKED|SKIPPED)\b", re.I)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def now():
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def today():
    return _dt.date.today().isoformat()


def die(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def phase_def(pid):
    for p in PHASES:
        if p["id"] == pid:
            return p
    die(f"Unknown phase '{pid}'. Valid phases: {', '.join(PHASE_IDS)}")


def slugify(name):
    slug = "".join(c.lower() if c.isalnum() else "-" for c in name).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "feature"


def find_root(start=None):
    """Walk up from start (default cwd) to find a directory containing .sdlc/state.json."""
    cur = os.path.abspath(start or os.getcwd())
    if os.path.isfile(cur):
        cur = os.path.dirname(cur)
    while True:
        if os.path.isfile(os.path.join(cur, STATE_DIR, STATE_FILE)):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def state_path(root):
    return os.path.join(root, STATE_DIR, STATE_FILE)


def empty_phase():
    return {"status": "not_started", "artifacts": [], "approved_by": None, "approved_on": None,
            "open_issues": [], "artifact_hashes": {}}


def merged_settings(settings):
    """Fill in settings keys that older state files don't have."""
    out = copy.deepcopy(DEFAULT_SETTINGS)
    out.update(settings or {})
    if "test_markers" in out:  # v1 substring markers matched e.g. 'latest.py'; replaced by globs
        out.pop("test_markers")
    return out


def migrate(state):
    """Upgrade a state dict in place to the current schema. Returns it."""
    if state.get("schema_version", 1) < 2:
        slug = state.get("slug") or slugify(state.get("project", "project"))
        phases = state.pop("phases", {})
        for ph in phases.values():
            ph.setdefault("artifact_hashes", {})
        state.pop("current_phase", None)
        state["features"] = {
            slug: {
                "name": state.get("project", slug),
                "slug": slug,
                "type": "feature",
                "lane": list(PHASE_IDS),
                "docs_root": "docs",
                "created": state.get("created", now()),
                "phases": phases,
            }
        }
        state["active_feature"] = slug
        for h in state.get("history", []):
            h.setdefault("feature", slug)
        state["schema_version"] = SCHEMA_VERSION
    state["settings"] = merged_settings(state.get("settings"))
    for feat in state.get("features", {}).values():
        for pid in feat["lane"]:
            feat["phases"].setdefault(pid, empty_phase())
    return state


def read_state(root):
    """Load and migrate without exiting on error (used by hooks). Returns None on failure."""
    try:
        with open(state_path(root), encoding="utf-8") as f:
            return migrate(json.load(f))
    except Exception:
        return None


def load(root=None):
    root = root or find_root()
    if not root:
        die("No Agentic SDLC project found (no .sdlc/state.json here or in any parent). "
            "Run the init skill first: /sdlc-core:init \"<Project Name>\"")
    with open(state_path(root), encoding="utf-8") as f:
        return root, migrate(json.load(f))


def save(root, state):
    state["updated"] = now()
    path = state_path(root)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def git_identity(root):
    try:
        out = subprocess.run(["git", "config", "user.name"], cwd=root, capture_output=True,
                             text=True, timeout=5)
        return out.stdout.strip() or None
    except Exception:
        return None


def log(state, event, feature=None, phase=None, by=None, note=None, **extra):
    entry = {"ts": now(), "event": event}
    if feature:
        entry["feature"] = feature
    if phase:
        entry["phase"] = phase
    if by:
        entry["by"] = by
    if note:
        entry["note"] = note
    entry.update({k: v for k, v in extra.items() if v is not None})
    state.setdefault("history", []).append(entry)


def get_feature(state, slug=None):
    slug = slug or state.get("active_feature")
    feats = state.get("features", {})
    if slug not in feats:
        die(f"Unknown feature '{slug}'. Features: {', '.join(feats) or '(none)'}")
    return slug, feats[slug]


def lane(feat):
    return feat["lane"]


def prev_in_lane(feat, pid):
    ids = lane(feat)
    if pid not in ids:
        die(f"Phase '{pid}' is not part of this feature's '{feat['type']}' lane "
            f"({', '.join(ids)}).")
    i = ids.index(pid)
    return ids[i - 1] if i > 0 else None


def next_phase(feat):
    """The earliest lane phase that is not approved (reopened phases come first naturally)."""
    for pid in lane(feat):
        if feat["phases"][pid]["status"] != "approved":
            return pid
    return None


def code_unlocked(feat):
    """Code may be written once every lane phase before Build is approved."""
    if "build" not in lane(feat):
        return False
    for pid in lane(feat)[:lane(feat).index("build")]:
        if feat["phases"][pid]["status"] != "approved":
            return False
    return True


def code_lock_reason(feat):
    if "build" not in lane(feat):
        return f"the '{feat['type']}' lane has no Build phase"
    pending = [p for p in lane(feat)[:lane(feat).index("build")]
               if feat["phases"][p]["status"] != "approved"]
    return "waiting on approval of: " + ", ".join(pending)


def open_issues(ph):
    return [i for i in ph.get("open_issues", []) if not i.get("resolved")]


def new_issue_id(pid, ph):
    return f"{pid[:3].upper()}-{len(ph['open_issues']) + 1}"


def docs_path(feat, rel):
    return os.path.join(feat.get("docs_root", "docs"), rel).replace("\\", "/")


def phase_artifacts(feat, pid):
    """Project-relative paths of the phase's expected artifacts."""
    p = phase_def(pid)
    return [docs_path(feat, a) for a in p["artifacts"]] + list(p.get("root_artifacts", []))


# --- matching (shared with the gate hook) -----------------------------------
def is_code(rel, settings):
    rel = rel.replace("\\", "/").removeprefix("./")
    return any(rel.startswith(p) for p in settings.get("code_paths", []))


def is_test(rel, settings):
    rel = rel.replace("\\", "/")
    parts = rel.split("/")
    name, dirs = parts[-1], [d.lower() for d in parts[:-1]]
    for pat in settings.get("test_patterns") or DEFAULT_TEST_PATTERNS:
        if pat.endswith("/"):
            if pat.rstrip("/").lower() in dirs:
                return True
        elif pat != pat.lower():
            if fnmatch.fnmatchcase(name, pat):
                return True
        elif fnmatch.fnmatchcase(name.lower(), pat):
            return True
    return False


# --- hashing (stale-approval detection) --------------------------------------
def hash_path(path):
    if os.path.isfile(path):
        with open(path, "rb") as f:
            return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()
    if os.path.isdir(path):
        h = hashlib.sha256()
        for dirpath, dirnames, filenames in os.walk(path):
            dirnames.sort()
            for fn in sorted(filenames):
                fp = os.path.join(dirpath, fn)
                h.update(os.path.relpath(fp, path).replace("\\", "/").encode())
                h.update(hash_path(fp).encode())
        return h.hexdigest()
    return "missing"


def stale_artifacts(root, ph):
    return [a for a, digest in (ph.get("artifact_hashes") or {}).items()
            if hash_path(os.path.join(root, a)) != digest]


# --- human-intent tokens -----------------------------------------------------
def token_path(root):
    return os.path.join(root, STATE_DIR, TOKEN_FILE)


def write_token(root, scope, prompt=None, session_id=None):
    with open(token_path(root), "w", encoding="utf-8") as f:
        json.dump({"scope": scope, "created": time.time(), "prompt": prompt,
                   "session_id": session_id}, f)


def consume_token(root, scope):
    """True if a fresh token for this scope exists; it is deleted either way once read."""
    path = token_path(root)
    try:
        with open(path, encoding="utf-8") as f:
            tok = json.load(f)
    except Exception:
        return False
    try:
        os.remove(path)
    except OSError:
        pass
    return tok.get("scope") == scope and time.time() - tok.get("created", 0) <= TOKEN_TTL_SECONDS


def require_human(root, scope, confirm_word, what):
    """Proof that a human asked for this: a hook-issued token or an interactive confirmation."""
    if consume_token(root, scope):
        return "slash-command"
    if sys.stdin is not None and sys.stdin.isatty():
        try:
            answer = input(f"Confirm {what} by typing '{confirm_word}': ").strip()
        except EOFError:  # e.g. stdin is the NUL device, which Windows reports as a TTY
            answer = None
        if answer == confirm_word:
            return "terminal"
        if answer is not None:
            die("Confirmation did not match; nothing changed.")
    cmd = "/sdlc-core:approve" if scope == "approve" else "/sdlc-core:settings"
    die(f"{what} must be requested by a human. Type {cmd} in Claude Code (which issues a "
        f"one-time token), or run this command yourself in a terminal.")


# ---------------------------------------------------------------------------
# Traceability
# ---------------------------------------------------------------------------
def norm_id(kind, m):
    if kind == "AC":
        return f"AC-{int(m.group(1))}.{int(m.group(2))}"
    return f"{kind}-{int(m.group(1))}"


def ids_in(text, kind):
    return [norm_id(kind, m) for m in ID_RE[kind].finditer(text)]


def read_text(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def records(text, kind):
    """Split markdown into records that start with an ID of `kind` (table row, heading or bullet).

    A record continues over following plain lines (e.g. bullets under '### T-1') and ends at
    the next heading or table row that doesn't start with such an ID.
    """
    start = re.compile(r"^\s*(?:\|\s*|#{1,6}\s*|[-*]\s+)?(?:\*\*|\[|`)*" + _BOUND + ID_PATTERNS[kind])
    out, cur = {}, None
    for line in text.splitlines():
        m = start.match(line)
        if m:
            cur = norm_id(kind, re.match(ID_PATTERNS[kind], m.group(0)[m.group(0).index(kind):]))
            out.setdefault(cur, []).append(line)
            continue
        s = line.lstrip()
        if s.startswith("#") or s.startswith("|"):
            cur = None
            continue
        if cur:
            out[cur].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def table_rows(text):
    return [l for l in text.splitlines() if l.lstrip().startswith("|")]


def trace(root, feat):
    """Build the US -> AC -> T -> TC -> result matrix and list orphans."""
    def doc(rel):
        return read_text(os.path.join(root, docs_path(feat, rel)))

    req, tasks = doc("02-requirements/requirements.md"), doc("04-planning/tasks.md")
    cases, report = doc("06-qa/test-cases.md"), doc("06-qa/test-report.md")
    review = doc("07-review/review-report.md")

    acs = sorted(set(ids_in(req or "", "AC")), key=_ac_key)
    stories = sorted(set(ids_in(req or "", "US")), key=lambda s: int(s.split("-")[1]))

    # Tasks -> ACs: task records, plus AC-led coverage rows (| AC-1.1 | T-1, T-2 |).
    task_acs = {}
    if tasks:
        for tid, body in records(tasks, "T").items():
            task_acs.setdefault(tid, set()).update(ids_in(body, "AC"))
        for ac, body in records(tasks, "AC").items():
            for tid in ids_in(body.splitlines()[0], "T"):
                task_acs.setdefault(tid, set()).add(ac)
    ac_tasks = {a: sorted({t for t, s in task_acs.items() if a in s}, key=_num_key) for a in acs}

    # Test cases -> ACs, and results (test-report overrides test-cases).
    tc_acs, results = {}, {}
    for text in (cases, report):
        if not text:
            continue
        for tcid, body in records(text, "TC").items():
            tc_acs.setdefault(tcid, set()).update(ids_in(body, "AC"))
        for row in table_rows(text):
            tcs, row_acs = ids_in(row, "TC"), ids_in(row, "AC")
            for tcid in tcs:
                tc_acs.setdefault(tcid, set()).update(row_acs)
    for text in (cases, report):
        if not text:
            continue
        found = {}
        for row in table_rows(text):
            words = [w.upper() for w in RESULT_RE.findall(row)]
            if not words:
                continue
            r = "FAIL" if any(w.startswith("FAIL") for w in words) else (
                "PASS" if any(w.startswith("PASS") for w in words) else words[0])
            for tcid in ids_in(row, "TC"):
                prev = found.get(tcid)
                found[tcid] = "FAIL" if "FAIL" in (prev, r) else r
        results.update(found)

    ac_tcs = {a: sorted({t for t, s in tc_acs.items() if a in s}, key=_num_key) for a in acs}

    issues = []

    def add(check, iid, msg):
        issues.append({"check": check, "id": iid, "message": msg})

    if tasks is not None and req is not None:
        for a in acs:
            if not ac_tasks[a]:
                add("ac_without_task", a, f"{a} is not covered by any task")
    if tasks is not None:
        for t in sorted(task_acs, key=_num_key):
            if not task_acs[t] and req is not None:
                add("task_without_ac", t, f"{t} does not reference any acceptance criterion")
    if cases is not None and req is not None:
        for a in acs:
            if not ac_tcs[a]:
                add("ac_without_tc", a, f"{a} has no test case")
            elif not any(results.get(t) == "PASS" for t in ac_tcs[a]):
                got = ", ".join(t + "=" + results.get(t, "not run") for t in ac_tcs[a])
                add("ac_unverified", a, f"{a} has no passing test case ({got})")
        for t in sorted(tc_acs, key=_num_key):
            if results.get(t) == "FAIL":
                add("tc_failing", t, f"{t} is failing")
            if not tc_acs[t]:
                add("tc_without_ac", t, f"{t} does not reference an acceptance criterion")
    for text, kind_check in ((cases, "open_defect"), (report, "open_defect")):
        for row in table_rows(text or ""):
            if ID_RE["DEF"].search(row) and re.search(r"\b(critical|high|blocker|sev ?1|sev ?2)\b", row, re.I) \
                    and re.search(r"\bopen\b", row, re.I):
                d = ids_in(row, "DEF")[0]
                if not any(i["id"] == d for i in issues):
                    add(kind_check, d, f"{d} is an open high-severity defect")
    for row in table_rows(review or ""):
        if re.search(r"\b(critical|high|blocker|major)\b", row, re.I) and \
                re.search(r"\|\s*open\s*\|", row, re.I):
            add("open_review_finding", row.strip()[:60], "open Critical/High/Blocker/Major review finding: "
                + " ".join(row.split())[:120])

    matrix = [{
        "ac": a,
        "story": f"US-{a.split('-')[1].split('.')[0]}",
        "tasks": ac_tasks[a],
        "test_cases": ac_tcs[a],
        "results": {t: results.get(t, "not run") for t in ac_tcs[a]},
    } for a in acs]
    return {
        "feature": feat["slug"],
        "sources": {
            "requirements": req is not None, "tasks": tasks is not None,
            "test_cases": cases is not None, "test_report": report is not None,
            "review_report": review is not None,
        },
        "counts": {"US": len(stories), "AC": len(acs), "T": len(task_acs), "TC": len(tc_acs)},
        "matrix": matrix,
        "issues": issues,
    }


def _num_key(i):
    return int(i.split("-")[1])


def _ac_key(i):
    a, b = i.split("-")[1].split(".")
    return int(a), int(b)


# Exit checks: which problems block a phase from going to in_review.
PHASE_TRACE_CHECKS = {
    "planning": {"ac_without_task", "task_without_ac"},
    "qa": {"ac_without_tc", "ac_unverified", "tc_failing", "open_defect"},
    "review": {"open_review_finding"},
}
PHASE_HEADING_CHECKS = {
    "discovery": [("01-discovery/problem-brief.md", r"success metric")],
    "design": [("03-design/design.md", r"threat model|security")],
    "release": [("08-release/release-plan.md", r"rollback"),
                ("08-release/release-plan.md", r"go\s*/\s*no-go")],
}


def exit_check_failures(root, feat, pid, extra_artifacts=()):
    fails = []
    for a in phase_artifacts(feat, pid) + [a for a in extra_artifacts]:
        if a.endswith("/"):
            continue
        if not os.path.exists(os.path.join(root, a)):
            fails.append(f"missing artifact {a}")
    if pid == "requirements":
        req = read_text(os.path.join(root, docs_path(feat, "02-requirements/requirements.md"))) or ""
        if not ids_in(req, "US"):
            fails.append("requirements.md has no user stories (US-n)")
        if not ids_in(req, "AC"):
            fails.append("requirements.md has no acceptance criteria (AC-n.m)")
    for rel, pattern in PHASE_HEADING_CHECKS.get(pid, []):
        text = read_text(os.path.join(root, docs_path(feat, rel)))
        if text is not None and not re.search(r"^#+.*(" + pattern + ")", text, re.I | re.M):
            fails.append(f"{docs_path(feat, rel)} has no section matching '{pattern}'")
    checks = PHASE_TRACE_CHECKS.get(pid)
    if checks:
        fails += [i["message"] for i in trace(root, feat)["issues"] if i["check"] in checks]
    return fails


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def make_feature(name, ftype, docs_root):
    if ftype not in LANES:
        die(f"Unknown work type '{ftype}'. Types: {', '.join(LANES)}")
    ids = LANES[ftype]["phases"]
    return {
        "name": name,
        "slug": slugify(name),
        "type": ftype,
        "lane": list(ids),
        "docs_root": docs_root,
        "created": now(),
        "phases": {pid: empty_phase() for pid in ids},
    }


def create_folders(base, feat):
    for pid in lane(feat):
        os.makedirs(os.path.join(base, feat["docs_root"], phase_def(pid)["folder"]), exist_ok=True)
    if "design" in lane(feat):
        os.makedirs(os.path.join(base, feat["docs_root"], "03-design", "adr"), exist_ok=True)


def cmd_init(args):
    base = os.path.abspath(args.dir or os.getcwd())
    os.makedirs(base, exist_ok=True)
    if os.path.isfile(state_path(base)):
        die(f"An SDLC project already exists at {base}. Use `status` to see it, "
            "or `feature new` to start another piece of work.")

    feat = make_feature(args.name, args.type, "docs")
    state = {
        "schema_version": SCHEMA_VERSION,
        "project": args.name,
        "slug": slugify(args.name),
        "created": now(),
        "updated": now(),
        "approvers": {
            "product_owner": args.approver,
            "tech_lead": args.tech_lead or args.approver,
            "qa_lead": args.qa_lead or args.approver,
            "team": args.approver,
        },
        "settings": copy.deepcopy(DEFAULT_SETTINGS),
        "active_feature": feat["slug"],
        "features": {feat["slug"]: feat},
        "history": [],
    }
    log(state, "project_created", by=args.approver, note=args.name)
    log(state, "feature_created", feature=feat["slug"], note=f"{feat['name']} ({feat['type']})")

    os.makedirs(os.path.join(base, STATE_DIR), exist_ok=True)
    create_folders(base, feat)

    # Drop the project CLAUDE.md (or append the SDLC section to an existing one).
    tpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")
    tpl = os.path.join(tpl_dir, "project-CLAUDE.md")
    claude_md = os.path.join(base, "CLAUDE.md")
    if os.path.isfile(tpl):
        with open(tpl, encoding="utf-8") as f:
            body = f.read().replace("{{PROJECT}}", args.name)
        if os.path.isfile(claude_md):
            with open(claude_md, encoding="utf-8") as f:
                existing = f.read()
            if "Agentic SDLC" not in existing:
                with open(claude_md, "a", encoding="utf-8") as f:
                    f.write("\n\n" + body)
        else:
            with open(claude_md, "w", encoding="utf-8") as f:
                f.write(body)

    save(base, state)
    first = lane(feat)[0]
    print(f"Initialized Agentic SDLC project '{args.name}' in {base}")
    print(f"State: {state_path(base)}")
    print(f"Work type: {feat['type']} -> phases: {', '.join(lane(feat))}")
    print(f"Current phase: {first} -> run skill {', '.join(phase_def(first)['skills'])}")


def cmd_feature(args):
    root, state = load()
    if args.action == "list":
        for slug, f in state["features"].items():
            mark = "*" if slug == state["active_feature"] else " "
            nxt = next_phase(f)
            print(f" {mark} {slug:<28} {f['type']:<8} next: {nxt or 'done'}"
                  + (f" ({f['phases'][nxt]['status']})" if nxt else "") + f"  docs: {f['docs_root']}")
        return
    if args.action == "switch":
        if not args.name or args.name not in state["features"]:
            die(f"Unknown feature '{args.name}'. Features: {', '.join(state['features'])}")
        state["active_feature"] = args.name
        log(state, "feature_switched", feature=args.name)
        save(root, state)
        print(f"Active feature: {args.name}")
        return
    # new
    if not args.name:
        die('feature new needs a name, e.g. feature new "Export to CSV" --type feature')
    slug = slugify(args.name)
    if slug in state["features"]:
        die(f"A feature '{slug}' already exists.")
    feat = make_feature(args.name, args.type, args.docs_root or f"docs/features/{slug}")
    state["features"][slug] = feat
    state["active_feature"] = slug
    log(state, "feature_created", feature=slug, note=f"{args.name} ({args.type})")
    create_folders(root, feat)
    save(root, state)
    print(f"Created {args.type} '{args.name}' ({slug}); it is now the active feature.")
    print(f"Phases: {', '.join(lane(feat))}. Docs: {feat['docs_root']}/")


def phase_label(root, ph):
    if ph["status"] == "approved" and stale_artifacts(root, ph):
        return "approved (STALE)"
    return ph["status"]


def render_status(root, state, slug, feat):
    lines = [f"Project: {state['project']}  ({root})",
             f"Feature: {feat['name']} [{slug}]  type: {feat['type']}  docs: {feat['docs_root']}/"]
    nxt = next_phase(feat)
    lines.append(f"Current phase: {nxt or 'ALL PHASES APPROVED'}")
    lines.append(f"Code: {'unlocked' if code_unlocked(feat) else 'locked - ' + code_lock_reason(feat)}")
    lines.append("")
    icon = {"not_started": "  ", "draft": "..", "in_review": "??", "approved": "OK",
            "reopened": "!!", "needs_revalidation": "~~"}
    for p in PHASES:
        if p["id"] not in lane(feat):
            continue
        n = PHASE_IDS.index(p["id"]) + 1
        ph = feat["phases"][p["id"]]
        label = phase_label(root, ph)
        extra = ""
        if ph["status"] == "approved":
            extra = f" by {ph['approved_by']} on {ph['approved_on']}"
        oi = open_issues(ph)
        if oi:
            extra += f"  [{len(oi)} open issue(s)]"
        marker = " <-- next" if p["id"] == nxt else ""
        lines.append(f" [{icon[ph['status']]}] {n:>2}. {p['title']:<24} {label}{extra}{marker}")
    all_issues = [(pid, i) for pid in lane(feat) for i in open_issues(feat["phases"][pid])]
    if all_issues:
        lines.append("")
        lines.append("Open issues needing a decision:")
        for pid, i in all_issues:
            lines.append(f"  - [{pid}] {i['id']}: {i['text']}")
    stale = [pid for pid in lane(feat) if phase_label(root, feat["phases"][pid]).endswith("(STALE)")]
    if stale:
        lines.append("")
        lines.append("Stale approvals (artifact changed after approval): " + ", ".join(stale)
                     + ". Run `verify` for details; reopen the phase if the change matters.")
    others = [s for s in state["features"] if s != slug]
    if others:
        lines.append("")
        lines.append(f"Other features: {', '.join(others)} (feature list / feature switch <slug>)")
    return "\n".join(lines)


def cmd_status(args):
    root, state = load()
    slug, feat = get_feature(state, args.feature)
    if args.json:
        print(json.dumps({"root": root, "feature": slug, "next_phase": next_phase(feat),
                          "code_unlocked": code_unlocked(feat), **state}, indent=2))
    elif args.all:
        for s, f in state["features"].items():
            print(render_status(root, state, s, f))
            print()
    else:
        print(render_status(root, state, slug, feat))


def cmd_next(args):
    root, state = load()
    slug, feat = get_feature(state, args.feature)
    pid = next_phase(feat)
    if not pid:
        out = {"feature": slug, "phase": None,
               "message": "All phases approved. Start new work with `feature new`."}
    else:
        p = phase_def(pid)
        ph = feat["phases"][pid]
        prev = prev_in_lane(feat, pid)
        approver = state["approvers"].get(p["approver_role"])
        if ph["status"] == "in_review":
            action = f"WAIT for human approval. Ask {approver} to review and run /sdlc-core:approve {pid}."
        elif ph["status"] == "reopened":
            action = "Phase was reopened. Resolve its open issues, update the artifacts, then set it to in_review."
        elif ph["status"] == "needs_revalidation":
            action = ("An upstream phase changed after this one was approved. Re-check the artifact "
                      "against the updated inputs, update it if needed, then set it to in_review.")
        else:
            action = "Run the phase skills in order, write the artifacts, then set the phase to in_review."
        inputs = [a for q in lane(feat)[:lane(feat).index(pid)]
                  for a in (feat["phases"][q]["artifacts"] or phase_artifacts(feat, q))]
        out = {
            "feature": slug,
            "type": feat["type"],
            "docs_root": feat["docs_root"],
            "phase": pid,
            "title": p["title"],
            "status": ph["status"],
            "previous_phase": prev,
            "skills": p["skills"],
            "agents": p.get("agents", []),
            "inputs": inputs,
            "artifacts": phase_artifacts(feat, pid),
            "gate": p["gate"],
            "approver": approver,
            "open_issues": open_issues(ph),
            "action": action,
            "project_root": root,
        }
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        for k, v in out.items():
            print(f"{k}: {v}")


def cmd_set_status(args):
    root, state = load()
    slug, feat = get_feature(state, args.feature)
    p = phase_def(args.phase)
    if args.status not in ("draft", "in_review"):
        die("set-status only accepts 'draft' or 'in_review'. Use `approve` or `reopen` for other transitions.")
    prev = prev_in_lane(feat, args.phase)
    if prev and feat["phases"][prev]["status"] != "approved":
        die(f"Cannot work on '{args.phase}': previous phase '{prev}' is not approved yet.")
    ph = feat["phases"][args.phase]
    if ph["status"] == "approved":
        die(f"'{args.phase}' is already approved. Use `reopen` if it needs changes.")
    artifacts = [a.replace("\\", "/") for a in (args.artifact or [])]
    if args.status == "in_review":
        fails = exit_check_failures(root, feat, args.phase, artifacts)
        if fails and not args.force_reason:
            die(f"'{args.phase}' does not meet its exit criteria:\n  - " + "\n  - ".join(fails)
                + "\nFix these, or pass --force-reason \"<why>\" to submit anyway "
                "(this records an open issue the approver must accept).")
        if fails:
            iid = new_issue_id(args.phase, ph)
            ph["open_issues"].append({"id": iid, "raised": today(), "resolved": False,
                                      "text": f"Submitted despite failed exit checks ({args.force_reason}): "
                                              + "; ".join(fails)})
            print(f"WARNING: exit checks overridden; recorded {iid} for the approver.", file=sys.stderr)
        if open_issues(ph):
            ids = ", ".join(i["id"] for i in open_issues(ph))
            print(f"WARNING: '{args.phase}' goes to review with open issues: {ids}. "
                  "The approver must decide them.", file=sys.stderr)
    ph["status"] = args.status
    for a in artifacts:
        if a not in ph["artifacts"]:
            ph["artifacts"].append(a)
    log(state, f"status_{args.status}", feature=slug, phase=args.phase, skill=args.skill)
    save(root, state)
    print(f"{p['title']} -> {args.status}")
    if args.status == "in_review":
        approver = state["approvers"].get(p["approver_role"])
        print(f"Gate: {p['gate']}")
        print(f"Approver: {approver}. Approve with: /sdlc-core:approve {args.phase}")


def cmd_approve(args):
    root, state = load()
    slug, feat = get_feature(state, args.feature)
    p = phase_def(args.phase)
    prev = prev_in_lane(feat, args.phase)
    if prev and feat["phases"][prev]["status"] != "approved":
        die(f"Cannot approve '{args.phase}': previous phase '{prev}' is not approved.")
    ph = feat["phases"][args.phase]
    if ph["status"] == "approved":
        die(f"'{args.phase}' is already approved.")
    if ph["status"] != "in_review":
        die(f"'{args.phase}' is '{ph['status']}'. It must be 'in_review' before it can be approved.")
    if not args.by or not args.by.strip():
        die("An approver name is required (--by NAME). Approvals must be made by a human.")
    if open_issues(ph) and not args.accept_open_issues:
        ids = ", ".join(i["id"] for i in open_issues(ph))
        die(f"'{args.phase}' still has open issues ({ids}). Resolve them first, "
            "or pass --accept-open-issues to approve anyway.")
    via = require_human(root, "approve", args.phase, f"approval of '{args.phase}'")
    paths = ph["artifacts"] or [a for a in phase_artifacts(feat, args.phase)
                                if os.path.exists(os.path.join(root, a))]
    ph["artifact_hashes"] = {a: hash_path(os.path.join(root, a)) for a in paths}
    ph["status"] = "approved"
    ph["approved_by"] = args.by.strip()
    ph["approved_on"] = today()
    log(state, "approved", feature=slug, phase=args.phase, by=args.by.strip(), note=args.note,
        via=via, git_user=git_identity(root),
        accepted_issues=[i["id"] for i in open_issues(ph)] or None)
    save(root, state)
    print(f"{p['title']} APPROVED by {args.by.strip()} on {ph['approved_on']}.")
    nxt = next_phase(feat)
    if nxt:
        np = phase_def(nxt)
        print(f"Next phase: {np['title']} -> skills: {', '.join(np['skills'])}")
    else:
        print(f"All phases of '{slug}' approved.")


def cmd_reopen(args):
    root, state = load()
    slug, feat = get_feature(state, args.feature)
    p = phase_def(args.phase)
    prev_in_lane(feat, args.phase)  # validates the phase is in the lane
    ph = feat["phases"][args.phase]
    if ph["status"] == "not_started":
        die(f"'{args.phase}' has not started; nothing to reopen.")
    iid = new_issue_id(args.phase, ph)
    ph["open_issues"].append({"id": iid, "text": args.reason, "raised": today(), "resolved": False})
    ph["status"] = "reopened"
    # Cascade: work built on the old version of this phase must be re-checked.
    invalidated = []
    for pid in lane(feat)[lane(feat).index(args.phase) + 1:]:
        d = feat["phases"][pid]
        if d["status"] in ("approved", "in_review"):
            if d["status"] == "approved":
                d.setdefault("previous_approvals", []).append(
                    {"by": d["approved_by"], "on": d["approved_on"], "invalidated_by": iid})
            d["status"] = "needs_revalidation"
            d["approved_by"] = d["approved_on"] = None
            invalidated.append(pid)
    log(state, "reopened", feature=slug, phase=args.phase, by=args.by, note=args.reason,
        invalidated=invalidated or None)
    save(root, state)
    print(f"{p['title']} REOPENED ({iid}): {args.reason}")
    if invalidated:
        print(f"Needs revalidation after the fix: {', '.join(invalidated)}.")


def cmd_issue(args):
    root, state = load()
    slug, feat = get_feature(state, args.feature)
    phase_def(args.phase)
    prev_in_lane(feat, args.phase)
    ph = feat["phases"][args.phase]
    if args.action == "add":
        iid = new_issue_id(args.phase, ph)
        ph["open_issues"].append({"id": iid, "text": args.text, "raised": today(), "resolved": False})
        log(state, "issue_added", feature=slug, phase=args.phase, note=f"{iid}: {args.text}")
        print(f"Added {iid} to {args.phase}: {args.text}")
    else:
        for i in ph["open_issues"]:
            if i["id"] == args.text:
                i["resolved"] = True
                i["resolution"] = args.note
                i["resolved_on"] = today()
                log(state, "issue_resolved", feature=slug, phase=args.phase,
                    note=f"{i['id']}: {args.note or ''}")
                print(f"Resolved {i['id']}: {args.note or ''}")
                break
        else:
            die(f"No issue '{args.text}' in phase {args.phase}.")
    save(root, state)


def cmd_verify(args):
    root, state = load()
    slug, feat = get_feature(state, args.feature)
    out = {pid: stale_artifacts(root, feat["phases"][pid]) for pid in lane(feat)
           if feat["phases"][pid]["status"] == "approved"}
    stale = {k: v for k, v in out.items() if v}
    if args.json:
        print(json.dumps({"feature": slug, "stale": stale}, indent=2))
    elif stale:
        for pid, arts in stale.items():
            print(f"STALE {pid}: changed since approval -> {', '.join(arts)}")
        print("If a change alters what was approved, reopen that phase; otherwise ask the approver "
              "to re-approve after review.")
    else:
        print(f"All approvals of '{slug}' match their artifacts.")
    sys.exit(1 if stale else 0)


def cmd_trace(args):
    root, state = load()
    slug, feat = get_feature(state, args.feature)
    t = trace(root, feat)
    if args.json:
        print(json.dumps(t, indent=2))
        return
    c = t["counts"]
    print(f"Trace for '{slug}': {c['US']} stories, {c['AC']} ACs, {c['T']} tasks, {c['TC']} test cases")
    if t["matrix"]:
        print()
        print(f"  {'AC':<9}{'Story':<7}{'Tasks':<18}Test cases (result)")
        for r in t["matrix"]:
            tcs = ", ".join(f"{k}={v}" for k, v in r["results"].items()) or "-"
            print(f"  {r['ac']:<9}{r['story']:<7}{', '.join(r['tasks']) or '-':<18}{tcs}")
    missing = [k for k, v in t["sources"].items() if not v]
    if missing:
        print(f"\n(not written yet: {', '.join(missing)})")
    print()
    if t["issues"]:
        print(f"{len(t['issues'])} traceability issue(s):")
        for i in t["issues"]:
            print(f"  - [{i['check']}] {i['message']}")
    else:
        print("No traceability gaps.")


def _ts(s):
    return _dt.datetime.fromisoformat(s)


def _hours(delta):
    return round(delta.total_seconds() / 3600, 1)


def compute_metrics(state):
    hist = state.get("history", [])
    per_feature = {}
    for slug, feat in state["features"].items():
        ev = [h for h in hist if h.get("feature") == slug]
        phases = {}
        for pid in lane(feat):
            pev = [h for h in ev if h.get("phase") == pid]
            start = next((h for h in pev if h["event"] == "status_draft"), None)
            approved = [h for h in pev if h["event"] == "approved"]
            reviews = [h for h in pev if h["event"] == "status_in_review"]
            m = {}
            if start and approved:
                m["cycle_hours"] = _hours(_ts(approved[-1]["ts"]) - _ts(start["ts"]))
            if approved and reviews:
                last_review = [r for r in reviews if r["ts"] <= approved[-1]["ts"]]
                if last_review:
                    m["approval_wait_hours"] = _hours(_ts(approved[-1]["ts"]) - _ts(last_review[-1]["ts"]))
            m["review_rounds"] = len(reviews)
            m["reopens"] = sum(1 for h in pev if h["event"] == "reopened")
            phases[pid] = m
        created = next((h for h in ev if h["event"] == "feature_created"), None)
        build_start = next((h for h in ev if h.get("phase") == "build" and h["event"] == "status_draft"), None)
        released = next((h for h in ev if h.get("phase") == "release" and h["event"] == "approved"), None)
        f = {"type": feat["type"], "phases": phases,
             "reopens": sum(1 for h in ev if h["event"] == "reopened")}
        if created and released:
            f["idea_to_release_hours"] = _hours(_ts(released["ts"]) - _ts(created["ts"]))
        if build_start and released:
            f["lead_time_for_changes_hours"] = _hours(_ts(released["ts"]) - _ts(build_start["ts"]))
        per_feature[slug] = f

    deploys = [h for h in hist if h["event"] == "deploy"] or \
              [h for h in hist if h.get("phase") == "release" and h["event"] == "approved"]
    incidents = [h for h in hist if h["event"] == "incident"]
    restores = [h for h in hist if h["event"] == "restore"]
    dora = {"deployments": len(deploys), "incidents": len(incidents)}
    if len(deploys) >= 1:
        first = _ts(hist[0]["ts"]) if hist else _ts(deploys[0]["ts"])
        weeks = max((_ts(deploys[-1]["ts"]) - first).total_seconds() / (7 * 86400), 1)
        dora["deploys_per_week"] = round(len(deploys) / weeks, 2)
        dora["change_failure_rate"] = round(len(incidents) / len(deploys), 2)
    lead = [f["lead_time_for_changes_hours"] for f in per_feature.values() if "lead_time_for_changes_hours" in f]
    if lead:
        dora["median_lead_time_hours"] = sorted(lead)[len(lead) // 2]
    ttr = []
    for inc in incidents:
        r = next((x for x in restores if x["ts"] >= inc["ts"] and x.get("ref") in (None, inc.get("ref"))), None)
        if r:
            ttr.append(_hours(_ts(r["ts"]) - _ts(inc["ts"])))
    if ttr:
        dora["mean_time_to_restore_hours"] = round(sum(ttr) / len(ttr), 1)
    return {"dora": dora, "features": per_feature}


def cmd_metrics(args):
    root, state = load()
    m = compute_metrics(state)
    if args.json:
        print(json.dumps(m, indent=2))
        return
    d = m["dora"]
    print("DORA (project-wide)")
    print(f"  Deployments:            {d['deployments']}"
          + ("" if any(h['event'] == 'deploy' for h in state.get('history', []))
             else "  (from release approvals; use `record deploy` for real deploys)"))
    for k, label in (("deploys_per_week", "Deploy frequency/week"),
                     ("median_lead_time_hours", "Lead time (h, median)"),
                     ("change_failure_rate", "Change failure rate"),
                     ("mean_time_to_restore_hours", "Time to restore (h)")):
        print(f"  {label + ':':<24}{d.get(k, 'n/a')}")
    for slug, f in m["features"].items():
        print(f"\nFeature {slug} ({f['type']}): reopens={f['reopens']}"
              + (f", idea->release={f['idea_to_release_hours']}h" if "idea_to_release_hours" in f else ""))
        for pid, pm in f["phases"].items():
            if pm.get("review_rounds") or pm.get("cycle_hours") is not None:
                print(f"  {pid:<13} cycle={pm.get('cycle_hours', '-')}h  waiting-for-approval="
                      f"{pm.get('approval_wait_hours', '-')}h  review rounds={pm['review_rounds']}  "
                      f"reopens={pm['reopens']}")


def cmd_record(args):
    root, state = load()
    slug, _ = get_feature(state, args.feature)
    log(state, args.event, feature=slug, note=args.note, ref=args.ref)
    save(root, state)
    print(f"Recorded {args.event} for '{slug}'" + (f": {args.note}" if args.note else ""))


WEAKENING = {"remove-code-path", "add-test-pattern", "unblock-command"}


def cmd_settings(args):
    root, state = load()
    settings = state["settings"]
    if args.action == "show":
        print(json.dumps(settings, indent=2))
        return
    weakens = args.action in WEAKENING or (args.action == "require-tests" and args.value == "off") \
        or (args.action == "max-diff-lines" and args.value and args.value.isdigit()
            and int(args.value) > settings.get("max_diff_lines", 400))
    if args.action in ("add-code-path", "remove-code-path"):
        if not args.value:
            die(f"settings {args.action} needs a path, e.g. tictactoe/")
        path = args.value.replace("\\", "/").removeprefix("./")
        path = path if path.endswith("/") else path + "/"
        paths = settings.setdefault("code_paths", [])
        if args.action == "add-code-path":
            if path in paths:
                print(f"'{path}' is already a gated code path.")
                return
        elif path not in paths:
            die(f"'{path}' is not a gated code path. Current: {', '.join(paths)}")
        if weakens:
            require_human(root, "settings", path, f"removing gated code path '{path}'")
        paths.append(path) if args.action == "add-code-path" else paths.remove(path)
        note = f"{args.action} {path}"
    elif args.action in ("add-test-pattern", "remove-test-pattern",
                         "block-command", "unblock-command"):
        if not args.value:
            die(f"settings {args.action} needs a value")
        key = "test_patterns" if "test-pattern" in args.action else "blocked_commands"
        items = settings.setdefault(key, [])
        adding = args.action.startswith(("add", "block"))
        if adding and args.value in items:
            print(f"'{args.value}' is already in {key}.")
            return
        if not adding and args.value not in items:
            die(f"'{args.value}' is not in {key}. Current: {items}")
        if key == "blocked_commands" and adding:
            try:
                re.compile(args.value)
            except re.error as e:
                die(f"Not a valid regular expression: {e}")
        if weakens:
            require_human(root, "settings", "yes", f"{args.action} '{args.value}'")
        items.append(args.value) if adding else items.remove(args.value)
        note = f"{args.action} {args.value}"
    elif args.action == "max-diff-lines":
        if not args.value or not args.value.isdigit():
            die("settings max-diff-lines needs a number")
        if weakens:
            require_human(root, "settings", args.value, f"raising max-diff-lines to {args.value}")
        settings["max_diff_lines"] = int(args.value)
        note = f"max_diff_lines={args.value}"
    else:  # require-tests
        if args.value not in ("on", "off"):
            die("settings require-tests needs 'on' or 'off'")
        if weakens:
            require_human(root, "settings", "off", "turning off the test-on-commit rule")
        settings["require_tests_on_commit"] = args.value == "on"
        note = f"require_tests_on_commit={args.value}"
    log(state, "settings_changed", by=args.by, note=note)
    save(root, state)
    print(f"Settings updated: {note}")
    print(f"Gated code paths: {', '.join(settings.get('code_paths', []))}")


def cmd_phases(args):
    if args.json:
        print(json.dumps(PHASES, indent=2))
    else:
        for i, p in enumerate(PHASES, 1):
            print(f"{i:>2}. {p['id']:<13} skills={', '.join(p['skills'])}  gate={p['gate']}")


def cmd_lanes(args):
    if args.json:
        print(json.dumps(LANES, indent=2))
    else:
        for name, l in LANES.items():
            print(f"{name:<8} {' -> '.join(l['phases'])}\n         {l['description']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Agentic SDLC state manager")
    sub = ap.add_subparsers(dest="cmd", required=True)
    feat_opt = argparse.ArgumentParser(add_help=False)
    feat_opt.add_argument("--feature", help="feature slug (default: the active feature)")

    s = sub.add_parser("init")
    s.add_argument("name")
    s.add_argument("--approver", default=os.environ.get("USER") or os.environ.get("USERNAME")
                   or "product-owner")
    s.add_argument("--tech-lead")
    s.add_argument("--qa-lead")
    s.add_argument("--type", default="feature", choices=list(LANES))
    s.add_argument("--dir")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("feature", help="create, list or switch features (work items)")
    s.add_argument("action", choices=["new", "list", "switch"])
    s.add_argument("name", nargs="?", help="feature name (new) or slug (switch)")
    s.add_argument("--type", default="feature", choices=list(LANES))
    s.add_argument("--docs-root")
    s.set_defaults(fn=cmd_feature)

    s = sub.add_parser("status", parents=[feat_opt])
    s.add_argument("--json", action="store_true")
    s.add_argument("--all", action="store_true", help="show every feature")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("next", parents=[feat_opt])
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_next)

    s = sub.add_parser("set-status", parents=[feat_opt])
    s.add_argument("phase")
    s.add_argument("status")
    s.add_argument("--artifact", action="append")
    s.add_argument("--force-reason", help="submit for review despite failed exit checks")
    s.add_argument("--skill", help="skill or agent that produced the work (provenance)")
    s.set_defaults(fn=cmd_set_status)

    s = sub.add_parser("approve", parents=[feat_opt])
    s.add_argument("phase")
    s.add_argument("--by", required=True)
    s.add_argument("--note")
    s.add_argument("--accept-open-issues", action="store_true")
    s.set_defaults(fn=cmd_approve)

    s = sub.add_parser("reopen", parents=[feat_opt])
    s.add_argument("phase")
    s.add_argument("--reason", required=True)
    s.add_argument("--by")
    s.set_defaults(fn=cmd_reopen)

    s = sub.add_parser("issue", parents=[feat_opt])
    s.add_argument("action", choices=["add", "resolve"])
    s.add_argument("phase")
    s.add_argument("text", help="issue text (add) or issue id (resolve)")
    s.add_argument("--note")
    s.set_defaults(fn=cmd_issue)

    s = sub.add_parser("verify", parents=[feat_opt], help="detect approvals whose artifacts changed")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_verify)

    s = sub.add_parser("trace", parents=[feat_opt], help="traceability matrix and orphans")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_trace)

    s = sub.add_parser("metrics", help="DORA and flow metrics from the history")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_metrics)

    s = sub.add_parser("record", parents=[feat_opt], help="record a deploy, incident or restore")
    s.add_argument("event", choices=["deploy", "incident", "restore"])
    s.add_argument("--note")
    s.add_argument("--ref", help="incident or release id, to pair incidents with restores")
    s.set_defaults(fn=cmd_record)

    s = sub.add_parser("settings", help="show or change gate settings")
    s.add_argument("action", choices=["show", "add-code-path", "remove-code-path", "require-tests",
                                      "add-test-pattern", "remove-test-pattern", "block-command",
                                      "unblock-command", "max-diff-lines"])
    s.add_argument("value", nargs="?")
    s.add_argument("--by")
    s.set_defaults(fn=cmd_settings)

    s = sub.add_parser("phases")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_phases)

    s = sub.add_parser("lanes")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_lanes)

    args = ap.parse_args(argv)
    if not hasattr(args, "feature"):
        args.feature = None
    args.fn(args)


if __name__ == "__main__":
    main()
