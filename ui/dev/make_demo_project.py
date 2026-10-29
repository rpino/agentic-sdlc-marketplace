#!/usr/bin/env python3
"""
Creates a demo Agentic SDLC project to point the UI at.

Usage: python ui/dev/make_demo_project.py <target-dir>

It uses the real state script, so the state is exactly what the plugins produce: discovery and
requirements approved, design waiting for approval, plus one open issue. Approvals use the same
one-time token that typing /sdlc-core:approve produces, via the UserPromptSubmit hook script.
Standard library only.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "..", "plugins", "sdlc-core", "scripts")
STATE = os.path.join(SCRIPTS, "sdlc_state.py")
PROMPT = os.path.join(SCRIPTS, "sdlc_prompt.py")


def run(target, *args):
    p = subprocess.run([sys.executable, STATE, *args], cwd=target, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("sdlc_state %s failed:\n%s%s" % (" ".join(args), p.stdout, p.stderr))
    return p.stdout


def write(target, rel, text):
    path = os.path.join(target, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def approve(target, phase):
    payload = json.dumps({"prompt": "/sdlc-core:approve " + phase, "cwd": target})
    subprocess.run([sys.executable, PROMPT], input=payload, capture_output=True, text=True, cwd=target)
    run(target, "approve", phase, "--by", "Ana")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    target = os.path.abspath(sys.argv[1])
    os.makedirs(target, exist_ok=True)
    run(target, "init", "Gym Membership App", "--approver", "Ana")

    write(target, "docs/01-discovery/problem-brief.md",
          "# Problem brief\n\n## Problem\nMembers cancel instead of pausing.\n\n## 5. Success metrics\n"
          "Cancellations for travel or injury drop by half in 6 months.\n")
    run(target, "set-status", "discovery", "draft")
    run(target, "set-status", "discovery", "in_review", "--artifact", "docs/01-discovery/problem-brief.md")
    approve(target, "discovery")

    write(target, "docs/02-requirements/requirements.md",
          "# Requirements\n\n### US-1: Freeze a membership\n"
          "- **AC-1.1** WHEN a member requests a freeze of 1 to 3 months THE SYSTEM SHALL pause billing\n"
          "- **AC-1.2** IF the freeze exceeds 3 months THEN THE SYSTEM SHALL reject it\n")
    run(target, "set-status", "requirements", "draft")
    run(target, "set-status", "requirements", "in_review", "--artifact", "docs/02-requirements/requirements.md")
    approve(target, "requirements")

    write(target, "docs/03-design/design.md",
          "# Design\n\n## Components\nA `POST /memberships/{id}/freeze` endpoint.\n\n"
          "## 5. Security & threat model\nSTRIDE notes.\n")
    run(target, "set-status", "design", "draft")
    run(target, "set-status", "design", "in_review", "--artifact", "docs/03-design/design.md")
    run(target, "issue", "add", "design", "Should a freeze be cancellable early?")
    print("Demo project ready in " + target)


if __name__ == "__main__":
    main()
