#!/usr/bin/env python3
"""
sdlc_state.py - the single source of truth for an Agentic SDLC project.

All reads and writes of .sdlc/state.json go through this script so that
phase transitions and human approvals are deterministic and auditable.

Usage:
  sdlc_state.py init "<Project Name>" [--approver NAME] [--dir PATH]
  sdlc_state.py status [--json]
  sdlc_state.py next [--json]
  sdlc_state.py set-status <phase> <draft|in_review> [--artifact PATH ...]
  sdlc_state.py approve <phase> --by NAME [--note TEXT]
  sdlc_state.py reopen <phase> --reason TEXT [--by NAME]
  sdlc_state.py issue add <phase> "<text>"
  sdlc_state.py issue resolve <phase> <issue-id> [--note TEXT]
  sdlc_state.py phases [--json]

Only the Python standard library is used.
"""
import argparse
import datetime as _dt
import json
import os
import sys

STATE_DIR = ".sdlc"
STATE_FILE = "state.json"
SCHEMA_VERSION = 1

# ---------------------------------------------------------------------------
# Phase map: the process definition. Order matters.
# ---------------------------------------------------------------------------
PHASES = [
    {
        "id": "discovery",
        "title": "Discovery",
        "folder": "docs/01-discovery",
        "skills": ["sdlc-discovery:idea-interviewer"],
        "artifacts": ["docs/01-discovery/problem-brief.md"],
        "gate": "Product Owner + stakeholder agree the problem is worth solving",
        "approver_role": "product_owner",
    },
    {
        "id": "requirements",
        "title": "Requirements",
        "folder": "docs/02-requirements",
        "skills": ["sdlc-requirements:spec-writer", "sdlc-requirements:acceptance-criteria"],
        "agents": ["sdlc-requirements:requirements-reviewer"],
        "artifacts": ["docs/02-requirements/requirements.md"],
        "gate": "Product Owner approves stories and testable acceptance criteria",
        "approver_role": "product_owner",
    },
    {
        "id": "design",
        "title": "Architecture / Design",
        "folder": "docs/03-design",
        "skills": ["sdlc-design:design-drafter"],
        "agents": ["sdlc-design:design-reviewer"],
        "artifacts": ["docs/03-design/design.md", "docs/03-design/adr/"],
        "gate": "Tech Lead approves design and ADRs",
        "approver_role": "tech_lead",
    },
    {
        "id": "planning",
        "title": "Planning",
        "folder": "docs/04-planning",
        "skills": ["sdlc-planning:task-breakdown"],
        "artifacts": ["docs/04-planning/tasks.md"],
        "gate": "Team agrees on tasks, sequence and priorities (sprint planning)",
        "approver_role": "team",
    },
    {
        "id": "build",
        "title": "Implementation",
        "folder": "docs/05-build",
        "skills": ["sdlc-build:task-executor"],
        "artifacts": ["docs/05-build/build-log.md"],
        "gate": "Developers have reviewed every task diff; all tasks done",
        "approver_role": "tech_lead",
    },
    {
        "id": "qa",
        "title": "Testing / QA",
        "folder": "docs/06-qa",
        "skills": ["sdlc-qa:qa-from-acceptance-criteria"],
        "artifacts": ["docs/06-qa/test-cases.md", "docs/06-qa/test-report.md"],
        "gate": "QA Lead confirms every acceptance criterion has a passing test",
        "approver_role": "qa_lead",
    },
    {
        "id": "review",
        "title": "Code Review / Security",
        "folder": "docs/07-review",
        "skills": ["sdlc-review:pr-reviewer", "sdlc-review:security-checklist"],
        "artifacts": ["docs/07-review/review-report.md"],
        "gate": "Tech Lead signs off the merge; no open high-severity findings",
        "approver_role": "tech_lead",
    },
    {
        "id": "release",
        "title": "Release",
        "folder": "docs/08-release",
        "skills": ["sdlc-release:release-notes", "sdlc-release:pipeline-fixer"],
        "artifacts": ["docs/08-release/release-plan.md", "docs/08-release/release-notes.md"],
        "gate": "Product Owner + stakeholder give go/no-go for rollout",
        "approver_role": "product_owner",
    },
    {
        "id": "operate",
        "title": "Operate / Monitor",
        "folder": "docs/09-operate",
        "skills": ["sdlc-ops:incident-summarizer"],
        "artifacts": ["docs/09-operate/"],
        "gate": "Product Owner confirms rollout is stable or incidents are handled",
        "approver_role": "product_owner",
    },
    {
        "id": "knowledge",
        "title": "Knowledge / Retro",
        "folder": "docs/10-knowledge",
        "skills": ["sdlc-knowledge:retro-capture", "sdlc-knowledge:knowledge-updater"],
        "artifacts": ["docs/10-knowledge/retro.md", "CLAUDE.md"],
        "gate": "Team agrees which lessons become standing rules",
        "approver_role": "team",
    },
]
PHASE_IDS = [p["id"] for p in PHASES]
STATUSES = ["not_started", "draft", "in_review", "approved", "reopened"]

DEFAULT_SETTINGS = {
    # Code may not be written in these paths until `planning` is approved.
    "code_paths": ["src/", "app/", "lib/", "services/", "packages/", "api/", "web/", "tests/", "test/"],
    # Block `git commit` of code changes that do not include a test change.
    "require_tests_on_commit": True,
    # Path fragments that identify a test file.
    "test_markers": ["test", "spec", "__tests__"],
}


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


def load(root=None):
    root = root or find_root()
    if not root:
        die("No Agentic SDLC project found (no .sdlc/state.json here or in any parent). "
            "Run the init skill first: /sdlc-core:init \"<Project Name>\"")
    with open(state_path(root), encoding="utf-8") as f:
        return root, json.load(f)


def save(root, state):
    state["updated"] = now()
    path = state_path(root)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def log(state, event, phase=None, by=None, note=None):
    entry = {"ts": now(), "event": event}
    if phase:
        entry["phase"] = phase
    if by:
        entry["by"] = by
    if note:
        entry["note"] = note
    state.setdefault("history", []).append(entry)


def next_phase(state):
    """The earliest phase that is not approved (reopened phases come first naturally)."""
    for pid in PHASE_IDS:
        if state["phases"][pid]["status"] != "approved":
            return pid
    return None


def open_issues(ph):
    return [i for i in ph.get("open_issues", []) if not i.get("resolved")]


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_init(args):
    base = os.path.abspath(args.dir or os.getcwd())
    os.makedirs(base, exist_ok=True)
    if os.path.isfile(state_path(base)):
        die(f"An SDLC project already exists at {base}. Use `status` to see it.")

    slug = "".join(c.lower() if c.isalnum() else "-" for c in args.name).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")

    state = {
        "schema_version": SCHEMA_VERSION,
        "project": args.name,
        "slug": slug,
        "created": now(),
        "updated": now(),
        "approvers": {
            "product_owner": args.approver,
            "tech_lead": args.tech_lead or args.approver,
            "qa_lead": args.qa_lead or args.approver,
            "team": args.approver,
        },
        "settings": DEFAULT_SETTINGS,
        "current_phase": "discovery",
        "phases": {
            p["id"]: {
                "status": "not_started",
                "artifacts": [],
                "approved_by": None,
                "approved_on": None,
                "open_issues": [],
            }
            for p in PHASES
        },
        "history": [],
    }
    log(state, "project_created", by=args.approver, note=args.name)

    os.makedirs(os.path.join(base, STATE_DIR), exist_ok=True)
    for p in PHASES:
        os.makedirs(os.path.join(base, p["folder"]), exist_ok=True)
    os.makedirs(os.path.join(base, "docs/03-design/adr"), exist_ok=True)

    # Drop the project CLAUDE.md (or append the SDLC section to an existing one).
    tpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")
    tpl = os.path.join(tpl_dir, "project-CLAUDE.md")
    claude_md = os.path.join(base, "CLAUDE.md")
    if os.path.isfile(tpl):
        with open(tpl, encoding="utf-8") as f:
            section = f.read().replace("{{PROJECT}}", args.name)
        if os.path.isfile(claude_md):
            with open(claude_md, encoding="utf-8") as f:
                existing = f.read()
            if "Agentic SDLC" not in existing:
                with open(claude_md, "a", encoding="utf-8") as f:
                    f.write("\n\n" + section)
        else:
            with open(claude_md, "w", encoding="utf-8") as f:
                f.write(section)

    save(base, state)
    print(f"Initialized Agentic SDLC project '{args.name}' at {base}")
    print(f"State file: {state_path(base)}")
    print("Current phase: discovery -> run skill sdlc-discovery:idea-interviewer")


def render_status(root, state):
    lines = [f"Project: {state['project']}  ({root})"]
    nxt = next_phase(state)
    lines.append(f"Current phase: {nxt or 'ALL PHASES APPROVED'}")
    lines.append("")
    icon = {"not_started": "  ", "draft": "..", "in_review": "??", "approved": "OK", "reopened": "!!"}
    for i, p in enumerate(PHASES, 1):
        ph = state["phases"][p["id"]]
        extra = ""
        if ph["status"] == "approved":
            extra = f" by {ph['approved_by']} on {ph['approved_on']}"
        oi = open_issues(ph)
        if oi:
            extra += f"  [{len(oi)} open issue(s)]"
        marker = " <-- next" if p["id"] == nxt else ""
        lines.append(f" [{icon[ph['status']]}] {i:>2}. {p['title']:<24} {ph['status']}{extra}{marker}")
    all_issues = [(pid, i) for pid in PHASE_IDS for i in open_issues(state["phases"][pid])]
    if all_issues:
        lines.append("")
        lines.append("Open issues needing a decision:")
        for pid, i in all_issues:
            lines.append(f"  - [{pid}] {i['id']}: {i['text']}")
    return "\n".join(lines)


def cmd_status(args):
    root, state = load()
    if args.json:
        print(json.dumps({"root": root, "next_phase": next_phase(state), **state}, indent=2))
    else:
        print(render_status(root, state))


def cmd_next(args):
    root, state = load()
    pid = next_phase(state)
    if not pid:
        out = {"phase": None, "message": "All phases approved. Start a new iteration or close the project."}
    else:
        p = phase_def(pid)
        ph = state["phases"][pid]
        prev = PHASE_IDS[PHASE_IDS.index(pid) - 1] if PHASE_IDS.index(pid) > 0 else None
        approver = state["approvers"].get(p["approver_role"])
        if ph["status"] == "in_review":
            action = f"WAIT for human approval. Ask {approver} to review and run /sdlc-core:approve {pid}."
        elif ph["status"] == "reopened":
            action = "Phase was reopened. Resolve its open issues, update the artifacts, then set it to in_review."
        else:
            action = "Run the phase skills in order, write the artifacts, then set the phase to in_review."
        out = {
            "phase": pid,
            "title": p["title"],
            "status": ph["status"],
            "previous_phase": prev,
            "skills": p["skills"],
            "agents": p.get("agents", []),
            "artifacts": p["artifacts"],
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
    p = phase_def(args.phase)
    if args.status not in ("draft", "in_review"):
        die("set-status only accepts 'draft' or 'in_review'. Use `approve` or `reopen` for other transitions.")
    idx = PHASE_IDS.index(args.phase)
    if idx > 0 and state["phases"][PHASE_IDS[idx - 1]]["status"] != "approved":
        die(f"Cannot work on '{args.phase}': previous phase '{PHASE_IDS[idx - 1]}' is not approved yet.")
    ph = state["phases"][args.phase]
    if ph["status"] == "approved":
        die(f"'{args.phase}' is already approved. Use `reopen` if it needs changes.")
    if args.status == "in_review" and open_issues(ph):
        ids = ", ".join(i["id"] for i in open_issues(ph))
        print(f"WARNING: '{args.phase}' goes to review with open issues: {ids}. "
              "The approver must decide them.", file=sys.stderr)
    ph["status"] = args.status
    for a in args.artifact or []:
        if a not in ph["artifacts"]:
            ph["artifacts"].append(a)
    state["current_phase"] = next_phase(state)
    log(state, f"status_{args.status}", phase=args.phase)
    save(root, state)
    print(f"{p['title']} -> {args.status}")
    if args.status == "in_review":
        approver = state["approvers"].get(p["approver_role"])
        print(f"Gate: {p['gate']}")
        print(f"Approver: {approver}. Approve with: /sdlc-core:approve {args.phase}")


def cmd_approve(args):
    root, state = load()
    p = phase_def(args.phase)
    idx = PHASE_IDS.index(args.phase)
    if idx > 0 and state["phases"][PHASE_IDS[idx - 1]]["status"] != "approved":
        die(f"Cannot approve '{args.phase}': previous phase '{PHASE_IDS[idx - 1]}' is not approved.")
    ph = state["phases"][args.phase]
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
    ph["status"] = "approved"
    ph["approved_by"] = args.by.strip()
    ph["approved_on"] = today()
    log(state, "approved", phase=args.phase, by=args.by.strip(), note=args.note)
    state["current_phase"] = next_phase(state)
    save(root, state)
    print(f"{p['title']} APPROVED by {args.by.strip()} on {ph['approved_on']}.")
    nxt = state["current_phase"]
    if nxt:
        np = phase_def(nxt)
        print(f"Next phase: {np['title']} -> skills: {', '.join(np['skills'])}")
    else:
        print("All phases approved.")


def cmd_reopen(args):
    root, state = load()
    p = phase_def(args.phase)
    ph = state["phases"][args.phase]
    if ph["status"] == "not_started":
        die(f"'{args.phase}' has not started; nothing to reopen.")
    iid = f"{args.phase[:3].upper()}-{len(ph['open_issues']) + 1}"
    ph["open_issues"].append({"id": iid, "text": args.reason, "raised": today(), "resolved": False})
    ph["status"] = "reopened"
    state["current_phase"] = next_phase(state)
    log(state, "reopened", phase=args.phase, by=args.by, note=args.reason)
    save(root, state)
    print(f"{p['title']} REOPENED ({iid}): {args.reason}")
    print("Downstream phases keep their status; the conductor will route back here first.")


def cmd_issue(args):
    root, state = load()
    phase_def(args.phase)
    ph = state["phases"][args.phase]
    if args.action == "add":
        iid = f"{args.phase[:3].upper()}-{len(ph['open_issues']) + 1}"
        ph["open_issues"].append({"id": iid, "text": args.text, "raised": today(), "resolved": False})
        log(state, "issue_added", phase=args.phase, note=f"{iid}: {args.text}")
        print(f"Added {iid} to {args.phase}: {args.text}")
    else:
        for i in ph["open_issues"]:
            if i["id"] == args.text:
                i["resolved"] = True
                i["resolution"] = args.note
                i["resolved_on"] = today()
                log(state, "issue_resolved", phase=args.phase, note=f"{i['id']}: {args.note or ''}")
                print(f"Resolved {i['id']}: {args.note or ''}")
                break
        else:
            die(f"No issue '{args.text}' in phase {args.phase}.")
    save(root, state)


def cmd_phases(args):
    if args.json:
        print(json.dumps(PHASES, indent=2))
    else:
        for i, p in enumerate(PHASES, 1):
            print(f"{i:>2}. {p['id']:<13} skills={', '.join(p['skills'])}  gate={p['gate']}")


def main():
    ap = argparse.ArgumentParser(description="Agentic SDLC state manager")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init")
    s.add_argument("name")
    s.add_argument("--approver", default=os.environ.get("USER", "product-owner"))
    s.add_argument("--tech-lead")
    s.add_argument("--qa-lead")
    s.add_argument("--dir")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("status")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("next")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_next)

    s = sub.add_parser("set-status")
    s.add_argument("phase")
    s.add_argument("status")
    s.add_argument("--artifact", action="append")
    s.set_defaults(fn=cmd_set_status)

    s = sub.add_parser("approve")
    s.add_argument("phase")
    s.add_argument("--by", required=True)
    s.add_argument("--note")
    s.add_argument("--accept-open-issues", action="store_true")
    s.set_defaults(fn=cmd_approve)

    s = sub.add_parser("reopen")
    s.add_argument("phase")
    s.add_argument("--reason", required=True)
    s.add_argument("--by")
    s.set_defaults(fn=cmd_reopen)

    s = sub.add_parser("issue")
    s.add_argument("action", choices=["add", "resolve"])
    s.add_argument("phase")
    s.add_argument("text", help="issue text (add) or issue id (resolve)")
    s.add_argument("--note")
    s.set_defaults(fn=cmd_issue)

    s = sub.add_parser("phases")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_phases)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
