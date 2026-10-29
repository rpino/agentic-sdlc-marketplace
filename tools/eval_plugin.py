#!/usr/bin/env python3
"""
eval_plugin.py - run `claude plugin eval` on one plugin so that the plugin really loads.

Why: every phase plugin declares a dependency on sdlc-core. The eval sandbox has an empty
home, so that dependency can't be satisfied and the plugin under test is silently skipped
(its skills and agents are missing and the "with plugin" arm is just the bare model).
This script evaluates a throw-away copy of the plugin with the `dependencies` line removed,
which is safe for the reviewer agents because none of them calls into sdlc-core.

It also reports which models did the work, read from each run's trace, because the point of
the model standard is that reviewer subagents run on the model their agent file names.

Usage:
  python tools/eval_plugin.py <plugin> [--inherit-models] [--] [claude plugin eval options]

  --inherit-models   remove `model:` from the copied agents, so subagents inherit the
                     session model. Use it to get a baseline to compare against.
  --save-json PATH   also copy the full result (prompts, per-run answers, grader verdicts)
                     to PATH, so a failing grader can be read against the answer it judged.

Examples:
  python tools/eval_plugin.py sdlc-review --trust-plugin --runs 3
  python tools/eval_plugin.py sdlc-review --inherit-models --trust-plugin --runs 3

The trust flag is passed through on purpose: it says you trust the plugin's code and eval
suite, so you choose to pass it. Standard library only.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv):
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    plugin = argv[0]
    rest = [a for a in argv[1:] if a != "--"]
    inherit = "--inherit-models" in rest
    rest = [a for a in rest if a != "--inherit-models"]
    save_json = None
    if "--save-json" in rest:
        i = rest.index("--save-json")
        save_json = rest[i + 1]
        del rest[i:i + 2]

    src = os.path.join(REPO, "plugins", plugin)
    if not os.path.isfile(os.path.join(src, ".claude-plugin", "plugin.json")):
        print("no such plugin: " + src)
        return 2
    claude = shutil.which("claude")
    if not claude:
        print("the claude CLI is not on PATH")
        return 2

    work = tempfile.mkdtemp(prefix="sdlc-eval-")
    dst = os.path.join(work, plugin)
    try:
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("results"))
        manifest = os.path.join(dst, ".claude-plugin", "plugin.json")
        with open(manifest, encoding="utf-8") as f:
            data = json.load(f)
        data.pop("dependencies", None)
        with open(manifest, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        if inherit:
            for path in glob.glob(os.path.join(dst, "agents", "*.md")):
                with open(path, encoding="utf-8", newline="") as f:
                    text = f.read()
                with open(path, "w", encoding="utf-8", newline="") as f:
                    f.write(re.sub(r"(?m)^model:.*\r?\n", "", text, count=1))

        out_json = os.path.join(work, "result.json")
        cmd = [claude, "plugin", "eval", ".", "--ablation", "none", "--keep-temp",
               "--json", out_json] + rest
        print("running: claude plugin eval . " + " ".join(
            a for a in cmd[4:] if a != out_json) + ("   [agents inherit session model]" if inherit else ""))
        proc = subprocess.run(cmd, cwd=dst)
        if not os.path.isfile(out_json):
            return proc.returncode or 1
        with open(out_json, encoding="utf-8") as f:
            result = json.load(f)
        if save_json:
            shutil.copyfile(out_json, save_json)
        report(result)
        cleanup(result)
        return proc.returncode
    finally:
        shutil.rmtree(work, ignore_errors=True)


def arm_runs(case):
    arms = case["arms"]
    return arms["with"] if isinstance(arms, dict) else arms


def run_models(trace_path):
    """Output tokens per model for one run, from the final `result` event of its trace."""
    try:
        with open(trace_path, encoding="utf-8") as f:
            for line in f:
                if '"modelUsage"' not in line:
                    continue
                usage = json.loads(line).get("modelUsage") or {}
                return {m: u.get("outputTokens", 0) for m, u in usage.items()}
    except (OSError, ValueError):
        pass
    return {}


def report(result):
    print("\n=== Eval summary (mean over runs) ===")
    for case in result["cases"]:
        runs = arm_runs(case)
        scores = [r["score"] for r in runs]
        cost = sum(r.get("costUsd", 0) for r in runs)
        models = {}
        for r in runs:
            for m, tokens in run_models(r.get("tracePath", "")).items():
                models[m] = models.get(m, 0) + tokens
        print("{:<28} score {:.2f}  (runs: {})  cost ${:.2f}".format(
            case["name"], sum(scores) / len(scores), " ".join("%.2f" % s for s in scores), cost))
        for i, r in enumerate(runs, 1):
            if r.get("error"):
                print("    run {} ERROR: {}".format(i, str(r["error"])[:300]))
        print("    output tokens by model: " + (", ".join(
            "{} {}".format(m, t) for m, t in sorted(models.items())) or "unavailable"))
        for i, g in enumerate(case["graders"]):
            votes = [r["graders"][i] for r in runs if i < len(r["graders"])]
            ok = sum(1 for v in votes if v["passed"])
            print("    {:<22} passed {}/{} runs".format(g["name"], ok, len(votes)))


def cleanup(result):
    """--keep-temp leaves each run's sandbox behind. Only out/ was read; remove the rest."""
    for case in result["cases"]:
        for r in arm_runs(case):
            trace = r.get("tracePath")
            if trace:
                shutil.rmtree(os.path.dirname(os.path.dirname(trace)), ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
