#!/usr/bin/env python3
"""
check_consistency.py - keeps the process definition, the plugins and the docs in sync.

Checks:
  1. Every skill and agent named in sdlc_state.PHASES exists on disk.
  2. Every plugin folder is listed in .claude-plugin/marketplace.json and vice versa.
  3. Each phase row in docs/process.md names that phase's skills and agents.
  4. Every lane in sdlc_state.LANES is documented in docs/process.md.
  5. The README plugin table lists every plugin.

Exit 1 with a list of problems if anything is out of sync. Standard library only.
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "plugins", "sdlc-core", "scripts"))
import sdlc_state  # noqa: E402


def read(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return f.read()


def component_path(ref, kind):
    plugin, name = ref.split(":")
    if kind == "skill":
        return os.path.join(REPO, "plugins", plugin, "skills", name, "SKILL.md")
    return os.path.join(REPO, "plugins", plugin, "agents", name + ".md")


def main():
    problems = []

    for p in sdlc_state.PHASES:
        for ref in p["skills"]:
            if not os.path.isfile(component_path(ref, "skill")):
                problems.append(f"PHASES[{p['id']}] names missing skill {ref}")
        for ref in p.get("agents", []):
            if not os.path.isfile(component_path(ref, "agent")):
                problems.append(f"PHASES[{p['id']}] names missing agent {ref}")

    market = json.loads(read(".claude-plugin/marketplace.json"))
    listed = {pl["name"] for pl in market["plugins"]}
    on_disk = {d for d in os.listdir(os.path.join(REPO, "plugins"))
               if os.path.isfile(os.path.join(REPO, "plugins", d, ".claude-plugin", "plugin.json"))}
    for d in sorted(on_disk - listed):
        problems.append(f"plugin {d} is not listed in marketplace.json")
    for d in sorted(listed - on_disk):
        problems.append(f"marketplace.json lists {d} but plugins/{d} has no plugin.json")

    process = read("docs/process.md")
    rows = {}
    for line in process.splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|", line)
        if m:
            rows.setdefault(int(m.group(1)), line)
    for i, p in enumerate(sdlc_state.PHASES, 1):
        row = rows.get(i)
        if not row:
            problems.append(f"docs/process.md has no phase row {i} ({p['id']})")
            continue
        for ref in p["skills"] + p.get("agents", []):
            if ref.split(":")[1] not in row:
                problems.append(f"docs/process.md row {i} ({p['id']}) does not mention {ref}")
    for lane in sdlc_state.LANES:
        if not re.search(r"\|\s*" + lane + r"\s*\|", process):
            problems.append(f"docs/process.md does not document the '{lane}' lane")

    readme = read("README.md")
    for d in sorted(on_disk):
        if d not in readme:
            problems.append(f"README.md does not mention plugin {d}")

    if problems:
        print("Out of sync:")
        for pr in problems:
            print("  - " + pr)
        sys.exit(1)
    print(f"OK: {len(sdlc_state.PHASES)} phases, {len(sdlc_state.LANES)} lanes, {len(on_disk)} plugins in sync.")


if __name__ == "__main__":
    main()
