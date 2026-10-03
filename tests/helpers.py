"""Shared helpers: run the sdlc-core scripts against throwaway projects."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO, "plugins", "sdlc-core", "scripts")
STATE = os.path.join(SCRIPTS, "sdlc_state.py")
GATE = os.path.join(SCRIPTS, "sdlc_gate.py")
PROMPT = os.path.join(SCRIPTS, "sdlc_prompt.py")
SESSION = os.path.join(SCRIPTS, "sdlc_session.py")

sys.path.insert(0, SCRIPTS)
import sdlc_state  # noqa: E402,F401


class ProjectCase(unittest.TestCase):
    """Each test gets a fresh temp directory; `init_project` creates an SDLC project in it."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sdlc-test-")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    # --- running scripts ---------------------------------------------------
    def run_state(self, *args, ok=True):
        p = subprocess.run([sys.executable, STATE, *args], cwd=self.dir, capture_output=True,
                           text=True, stdin=subprocess.DEVNULL)
        if ok and p.returncode != 0:
            self.fail(f"sdlc_state {' '.join(args)} failed:\n{p.stdout}\n{p.stderr}")
        if ok is False and p.returncode == 0:
            self.fail(f"sdlc_state {' '.join(args)} unexpectedly succeeded:\n{p.stdout}")
        return p

    def hook(self, script, payload):
        payload.setdefault("cwd", self.dir)
        p = subprocess.run([sys.executable, script], input=json.dumps(payload), capture_output=True,
                           text=True, cwd=self.dir)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout) if p.stdout.strip() else None

    def gate(self, tool, **tool_input):
        return self.hook(GATE, {"tool_name": tool, "tool_input": tool_input})

    def assertDenied(self, out, fragment=""):
        self.assertIsNotNone(out, "expected a deny decision, got allow")
        hso = out.get("hookSpecificOutput", {})
        self.assertEqual(hso.get("permissionDecision"), "deny", out)
        self.assertIn(fragment, hso.get("permissionDecisionReason", ""))

    def assertAllowed(self, out):
        if out is not None:
            self.assertNotEqual(out.get("hookSpecificOutput", {}).get("permissionDecision"), "deny", out)

    # --- project helpers ---------------------------------------------------
    def init_project(self, *extra):
        self.run_state("init", "Demo Project", "--approver", "Ana", *extra)

    def state(self):
        with open(os.path.join(self.dir, ".sdlc", "state.json"), encoding="utf-8") as f:
            return json.load(f)

    def write(self, rel, text):
        path = os.path.join(self.dir, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return rel

    def human_approves(self, phase, *extra):
        """Simulate the user typing /sdlc-core:approve, then the skill running the script."""
        self.hook(PROMPT, {"prompt": f"/sdlc-core:approve {phase}"})
        return self.run_state("approve", phase, "--by", "Ana", *extra)

    def pass_phase(self, phase, *artifacts):
        for rel, text in artifacts:
            self.write(rel, text)
        self.run_state("set-status", phase, "draft")
        self.run_state("set-status", phase, "in_review", *sum((["--artifact", r] for r, _ in artifacts), []))
        self.human_approves(phase)


BRIEF = ("docs/01-discovery/problem-brief.md", "# Brief\n## 5. Success metrics\nchurn -5%\n")
REQS = ("docs/02-requirements/requirements.md",
        "# Requirements\n### US-1: Freeze\n- **AC-1.1** WHEN a member freezes THE SYSTEM SHALL pause billing\n"
        "- **AC-1.2** IF the freeze exceeds 3 months THEN THE SYSTEM SHALL reject it\n")
DESIGN = ("docs/03-design/design.md", "# Design\n## 5. Security & threat model\nSTRIDE...\n")
TASKS = ("docs/04-planning/tasks.md",
         "# Plan\n| ID | Title | ACs | Depends on |\n|---|---|---|---|\n"
         "| T-1 | Freeze API | AC-1.1 | - |\n| T-2 | Limit | AC-1.2 | T-1 |\n")
BUILD = ("docs/05-build/build-log.md", "# Build log\n| T-1 | done |\n")
CASES = ("docs/06-qa/test-cases.md",
         "| TC | AC | Level | Result |\n|---|---|---|---|\n| TC-01 | AC-1.1 | API | PASS |\n"
         "| TC-02 | AC-1.2 | unit | PASS |\n")
REPORT = ("docs/06-qa/test-report.md", "# Report\n| AC | TCs | Result |\n|---|---|---|\n"
          "| AC-1.1 | TC-01 | PASS |\n| AC-1.2 | TC-02 | PASS |\n")


def walk_to(case, last_phase):
    """Approve every feature-lane phase up to and including last_phase."""
    order = [("discovery", [BRIEF]), ("requirements", [REQS]), ("design", [DESIGN]),
             ("planning", [TASKS]), ("build", [BUILD]), ("qa", [CASES, REPORT])]
    for phase, arts in order:
        case.pass_phase(phase, *arts)
        if phase == last_phase:
            return
