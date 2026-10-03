import json
import os
import unittest

from helpers import (BRIEF, CASES, DESIGN, PROMPT, REPORT, REQS, TASKS, ProjectCase, sdlc_state,
                     walk_to)


class InitAndLifecycle(ProjectCase):
    def test_init_creates_state_folders_and_claude_md(self):
        self.init_project()
        st = self.state()
        self.assertEqual(st["schema_version"], 2)
        feat = st["features"][st["active_feature"]]
        self.assertEqual(feat["type"], "feature")
        self.assertEqual(len(feat["lane"]), 10)
        self.assertTrue(os.path.isdir(os.path.join(self.dir, "docs", "03-design", "adr")))
        self.assertTrue(os.path.isfile(os.path.join(self.dir, "CLAUDE.md")))

    def test_init_twice_fails(self):
        self.init_project()
        self.run_state("init", "Again", ok=False)

    def test_cannot_skip_a_phase(self):
        self.init_project()
        p = self.run_state("set-status", "requirements", "draft", ok=False)
        self.assertIn("previous phase 'discovery'", p.stderr)

    def test_full_walk_records_approvals_and_hashes(self):
        self.init_project()
        walk_to(self, "qa")
        st = self.state()
        feat = st["features"][st["active_feature"]]
        self.assertEqual(feat["phases"]["qa"]["status"], "approved")
        self.assertEqual(feat["phases"]["design"]["approved_by"], "Ana")
        self.assertIn("docs/03-design/design.md", feat["phases"]["design"]["artifact_hashes"])
        nxt = json.loads(self.run_state("next", "--json").stdout)
        self.assertEqual(nxt["phase"], "review")
        self.assertIn("docs/02-requirements/requirements.md", nxt["inputs"])

    def test_open_issues_block_approval_unless_accepted(self):
        self.init_project()
        self.write(*BRIEF)
        self.run_state("set-status", "discovery", "draft")
        self.run_state("issue", "add", "discovery", "Which gyms are in the pilot?")
        self.run_state("set-status", "discovery", "in_review")
        self.hook(PROMPT, {"prompt": "/sdlc-core:approve discovery"})
        self.run_state("approve", "discovery", "--by", "Ana", ok=False)
        self.human_approves("discovery", "--accept-open-issues")
        hist = self.state()["history"][-1]
        self.assertEqual(hist["accepted_issues"], ["DIS-1"])


class HumanOnlyApproval(ProjectCase):
    def setUp(self):
        super().setUp()
        self.init_project()
        self.write(*BRIEF)
        self.run_state("set-status", "discovery", "draft")
        self.run_state("set-status", "discovery", "in_review")

    def test_approve_without_token_or_tty_is_refused(self):
        p = self.run_state("approve", "discovery", "--by", "Ana", ok=False)
        self.assertIn("must be requested by a human", p.stderr)

    def test_token_from_prompt_hook_allows_one_approval(self):
        self.hook(PROMPT, {"prompt": "/sdlc-core:approve"})
        self.run_state("approve", "discovery", "--by", "Ana")
        self.assertFalse(os.path.exists(os.path.join(self.dir, ".sdlc", "approval-token.json")))
        self.assertEqual(self.state()["history"][-1]["via"], "slash-command")

    def test_other_prompts_do_not_issue_tokens(self):
        for prompt in ("please approve discovery", "/sdlc-core:next", "/approvex"):
            self.hook(PROMPT, {"prompt": prompt})
        self.run_state("approve", "discovery", "--by", "Ana", ok=False)

    def test_settings_token_does_not_approve(self):
        self.hook(PROMPT, {"prompt": "/sdlc-core:settings require-tests off"})
        self.run_state("approve", "discovery", "--by", "Ana", ok=False)

    def test_expired_token_is_refused(self):
        sdlc_state.write_token(self.dir, "approve")
        path = os.path.join(self.dir, ".sdlc", "approval-token.json")
        with open(path) as f:
            tok = json.load(f)
        tok["created"] -= sdlc_state.TOKEN_TTL_SECONDS + 1
        with open(path, "w") as f:
            json.dump(tok, f)
        self.run_state("approve", "discovery", "--by", "Ana", ok=False)


class StaleApprovals(ProjectCase):
    def test_editing_an_approved_artifact_marks_it_stale(self):
        self.init_project()
        walk_to(self, "requirements")
        self.run_state("verify")
        self.write(REQS[0], REQS[1] + "- **AC-1.3** WHEN sneaky THE SYSTEM SHALL change\n")
        p = self.run_state("verify", ok=False)
        self.assertIn("STALE requirements", p.stdout)
        self.assertIn("approved (STALE)", self.run_state("status").stdout)

    def test_crlf_only_changes_are_not_stale(self):
        self.init_project()
        walk_to(self, "discovery")
        with open(os.path.join(self.dir, BRIEF[0]), "w", encoding="utf-8", newline="\r\n") as f:
            f.write(BRIEF[1])
        self.run_state("verify")


class ReopenCascade(ProjectCase):
    def test_reopen_invalidates_downstream_approvals(self):
        self.init_project()
        walk_to(self, "planning")
        self.run_state("reopen", "requirements", "--reason", "Missing rule for check-in while frozen")
        feat = list(self.state()["features"].values())[0]
        self.assertEqual(feat["phases"]["requirements"]["status"], "reopened")
        for pid in ("design", "planning"):
            self.assertEqual(feat["phases"][pid]["status"], "needs_revalidation")
            self.assertEqual(feat["phases"][pid]["previous_approvals"][0]["by"], "Ana")
        self.assertEqual(feat["phases"]["discovery"]["status"], "approved")
        # Design cannot be revalidated before requirements is re-approved.
        self.run_state("set-status", "design", "in_review", ok=False)
        self.run_state("issue", "resolve", "requirements", "REQ-1", "--note", "Deny check-in")
        self.run_state("set-status", "requirements", "in_review")
        self.human_approves("requirements")
        self.run_state("set-status", "design", "in_review")
        self.human_approves("design")
        self.assertEqual(json.loads(self.run_state("next", "--json").stdout)["phase"], "planning")


class ExitChecks(ProjectCase):
    def test_missing_artifact_blocks_review(self):
        self.init_project()
        self.run_state("set-status", "discovery", "draft")
        p = self.run_state("set-status", "discovery", "in_review", ok=False)
        self.assertIn("missing artifact docs/01-discovery/problem-brief.md", p.stderr)

    def test_planning_with_uncovered_ac_is_blocked(self):
        self.init_project()
        walk_to(self, "design")
        self.write(TASKS[0], "| ID | Title | ACs |\n|---|---|---|\n| T-1 | Freeze | AC-1.1 |\n| T-2 | Docs | |\n")
        self.run_state("set-status", "planning", "draft")
        p = self.run_state("set-status", "planning", "in_review", ok=False)
        self.assertIn("AC-1.2 is not covered by any task", p.stderr)
        self.assertIn("T-2 does not reference any acceptance criterion", p.stderr)

    def test_force_reason_records_an_issue_for_the_approver(self):
        self.init_project()
        walk_to(self, "design")
        self.write(TASKS[0], "| T-1 | Freeze | AC-1.1 |\n")
        self.run_state("set-status", "planning", "draft")
        self.run_state("set-status", "planning", "in_review", "--force-reason", "AC-1.2 deferred")
        feat = list(self.state()["features"].values())[0]
        issue = feat["phases"]["planning"]["open_issues"][0]
        self.assertIn("AC-1.2 deferred", issue["text"])
        self.hook(PROMPT, {"prompt": "/sdlc-core:approve planning"})
        self.run_state("approve", "planning", "--by", "Ana", ok=False)

    def test_qa_with_failing_test_is_blocked(self):
        self.init_project()
        walk_to(self, "build")
        self.write(CASES[0], CASES[1].replace("| TC-02 | AC-1.2 | unit | PASS |", "| TC-02 | AC-1.2 | unit | FAIL |"))
        self.write(REPORT[0], "# Report\n")
        self.run_state("set-status", "qa", "draft")
        p = self.run_state("set-status", "qa", "in_review", ok=False)
        self.assertIn("TC-2 is failing", p.stderr)
        self.assertIn("AC-1.2 has no passing test case", p.stderr)

    def test_review_with_open_high_finding_is_blocked(self):
        self.init_project()
        walk_to(self, "qa")
        self.write("docs/07-review/review-report.md",
                   "## Findings\n| File:line | Severity | Finding | Fix | Status |\n|---|---|---|---|---|\n"
                   "| api.py:12 | High | IDOR on freeze | check owner | Open |\n")
        self.run_state("set-status", "review", "draft")
        p = self.run_state("set-status", "review", "in_review", ok=False)
        self.assertIn("IDOR", p.stderr)

    def test_design_needs_a_threat_model_section(self):
        self.init_project()
        walk_to(self, "requirements")
        self.write(DESIGN[0], "# Design\n## Overview\n")
        self.run_state("set-status", "design", "draft")
        self.run_state("set-status", "design", "in_review", ok=False)


class Trace(ProjectCase):
    def test_matrix_and_orphans(self):
        self.init_project()
        for rel, text in (REQS, TASKS):
            self.write(rel, text)
        self.write(CASES[0], "| TC | AC | Result |\n|---|---|---|\n| TC-01 | AC-1.1 | PASS |\n| TC-07 | | |\n")
        t = json.loads(self.run_state("trace", "--json").stdout)
        self.assertEqual(t["counts"], {"US": 1, "AC": 2, "T": 2, "TC": 2})
        row = {r["ac"]: r for r in t["matrix"]}
        self.assertEqual(row["AC-1.1"]["tasks"], ["T-1"])
        self.assertEqual(row["AC-1.1"]["results"], {"TC-1": "PASS"})
        checks = {(i["check"], i["id"]) for i in t["issues"]}
        self.assertIn(("ac_without_tc", "AC-1.2"), checks)
        self.assertIn(("tc_without_ac", "TC-7"), checks)
        self.assertNotIn(("ac_without_task", "AC-1.1"), checks)

    def test_task_sections_and_coverage_rows_count(self):
        self.init_project()
        self.write(*REQS)
        self.write(TASKS[0], "### T-1: Freeze\n- **Satisfies:** AC-1.1\n\n## Coverage check\n| AC | Tasks |\n"
                             "|---|---|\n| AC-1.2 | T-3 |\n")
        t = json.loads(self.run_state("trace", "--json").stdout)
        row = {r["ac"]: r for r in t["matrix"]}
        self.assertEqual(row["AC-1.1"]["tasks"], ["T-1"])
        self.assertEqual(row["AC-1.2"]["tasks"], ["T-3"])

    def test_ids_do_not_overlap(self):
        self.assertEqual(sdlc_state.ids_in("TC-01 T-2 AC-1.10 DEF-3 NFR-1 ST-9", "T"), ["T-2"])
        self.assertEqual(sdlc_state.ids_in("AC-1.10, AC-01.2", "AC"), ["AC-1.10", "AC-1.2"])


class LanesAndFeatures(ProjectCase):
    def test_hotfix_lane_unlocks_code_immediately(self):
        self.init_project("--type", "hotfix")
        feat = list(self.state()["features"].values())[0]
        self.assertEqual(feat["lane"], ["build", "review", "release", "operate", "knowledge"])
        self.assertTrue(sdlc_state.code_unlocked(feat))

    def test_bugfix_lane_skips_discovery(self):
        self.init_project("--type", "bugfix")
        self.pass_phase("requirements", REQS)
        nxt = json.loads(self.run_state("next", "--json").stdout)
        self.assertEqual(nxt["phase"], "build")
        self.run_state("set-status", "design", "draft", ok=False)

    def test_second_feature_has_its_own_docs_and_state(self):
        self.init_project()
        walk_to(self, "discovery")
        self.run_state("feature", "new", "Export CSV", "--type", "chore")
        st = self.state()
        self.assertEqual(st["active_feature"], "export-csv")
        self.assertEqual(st["features"]["export-csv"]["docs_root"], "docs/features/export-csv")
        self.assertTrue(os.path.isdir(os.path.join(self.dir, "docs", "features", "export-csv", "04-planning")))
        self.assertIn("export-csv", self.run_state("feature", "list").stdout)
        nxt = json.loads(self.run_state("next", "--json", "--feature", "demo-project").stdout)
        self.assertEqual(nxt["phase"], "requirements")
        self.run_state("feature", "switch", "demo-project")
        self.assertEqual(self.state()["active_feature"], "demo-project")


class Migration(ProjectCase):
    def test_v1_state_is_migrated(self):
        v1 = {
            "schema_version": 1, "project": "Old", "slug": "old", "created": "2026-01-01T00:00:00+00:00",
            "approvers": {"product_owner": "Ana", "tech_lead": "Ana", "qa_lead": "Ana", "team": "Ana"},
            "settings": {"code_paths": ["src/"], "require_tests_on_commit": True, "test_markers": ["test"]},
            "current_phase": "requirements",
            "phases": {p: {"status": "approved" if p == "discovery" else "not_started",
                           "artifacts": ["docs/01-discovery/problem-brief.md"] if p == "discovery" else [],
                           "approved_by": "Ana" if p == "discovery" else None, "approved_on": None,
                           "open_issues": []} for p in sdlc_state.PHASE_IDS},
            "history": [{"ts": "2026-01-01T00:00:00+00:00", "event": "project_created"}],
        }
        self.write(".sdlc/state.json", json.dumps(v1))
        nxt = json.loads(self.run_state("next", "--json").stdout)
        self.assertEqual(nxt["phase"], "requirements")
        self.run_state("issue", "add", "requirements", "q?")  # forces a save in v2 format
        st = self.state()
        self.assertEqual(st["schema_version"], 2)
        self.assertNotIn("test_markers", st["settings"])
        self.assertEqual(st["settings"]["code_paths"], ["src/"])
        self.assertEqual(st["features"]["old"]["phases"]["discovery"]["artifacts"],
                         ["docs/01-discovery/problem-brief.md"])


class SettingsAndMetrics(ProjectCase):
    def test_weakening_settings_needs_a_human(self):
        self.init_project()
        self.run_state("settings", "add-code-path", "game/")
        self.run_state("settings", "require-tests", "on")
        self.run_state("settings", "require-tests", "off", ok=False)
        self.run_state("settings", "remove-code-path", "game/", ok=False)
        self.hook(PROMPT, {"prompt": "/sdlc-core:settings remove-code-path game/"})
        self.run_state("settings", "remove-code-path", "game/")
        self.assertNotIn("game/", self.state()["settings"]["code_paths"])

    def test_metrics_from_history(self):
        self.init_project()
        walk_to(self, "requirements")
        self.run_state("record", "deploy")
        self.run_state("record", "incident", "--ref", "INC-1")
        self.run_state("record", "restore", "--ref", "INC-1")
        m = json.loads(self.run_state("metrics", "--json").stdout)
        self.assertEqual(m["dora"]["deployments"], 1)
        self.assertEqual(m["dora"]["change_failure_rate"], 1.0)
        self.assertIn("mean_time_to_restore_hours", m["dora"])
        self.assertEqual(m["features"]["demo-project"]["phases"]["requirements"]["review_rounds"], 1)


class TestPatterns(unittest.TestCase):
    def test_globs(self):
        s = {"test_patterns": sdlc_state.DEFAULT_TEST_PATTERNS}
        for path in ("tests/test_api.py", "src/api_test.go", "web/app.spec.ts", "web/Button.test.tsx",
                     "src/__tests__/x.js", "src/main/java/FreezeTest.java", "spec/models/user_spec.rb"):
            self.assertTrue(sdlc_state.is_test(path, s), path)
        for path in ("src/latest.py", "src/contest/rules.py", "src/attestation.go", "src/Latest.java",
                     "src/specification.md"):
            self.assertFalse(sdlc_state.is_test(path, s), path)


if __name__ == "__main__":
    unittest.main()
