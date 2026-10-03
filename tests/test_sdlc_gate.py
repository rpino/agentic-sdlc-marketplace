import json
import os
import subprocess
import sys
import unittest

from helpers import GATE, PROMPT, SESSION, ProjectCase, walk_to


class OutsideProject(ProjectCase):
    def test_everything_allowed_without_state(self):
        self.assertAllowed(self.gate("Write", file_path=os.path.join(self.dir, "src", "a.py")))
        self.assertAllowed(self.gate("Bash", command="echo hi > src/a.py"))

    def test_garbage_payload_is_allowed(self):
        p = subprocess.run([sys.executable, GATE], input="not json", capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)


class StateProtection(ProjectCase):
    def setUp(self):
        super().setUp()
        self.init_project()

    def test_edit_tools_cannot_touch_sdlc_dir(self):
        for rel in (".sdlc/state.json", ".sdlc/approval-token.json"):
            self.assertDenied(self.gate("Write", file_path=os.path.join(self.dir, rel)), ".sdlc/")
            self.assertDenied(self.gate("Edit", file_path=rel), ".sdlc/")

    def test_shell_writes_to_sdlc_are_denied(self):
        for cmd in ("echo {} > .sdlc/state.json",
                    "sdlc_state.py status && echo '{}' > .sdlc/approval-token.json",
                    "cp /tmp/x.json .sdlc/state.json",
                    "sed -i 's/draft/approved/' .sdlc/state.json",
                    "python -c \"open('.sdlc/state.json','w').write('{}')\"",
                    "rm .sdlc/state.json"):
            self.assertDenied(self.gate("Bash", command=cmd))

    def test_powershell_writes_are_denied(self):
        self.assertDenied(self.gate("PowerShell", command="Set-Content .sdlc/state.json '{}'"))
        self.assertDenied(self.gate("PowerShell", command="'x' | Out-File src/app.py"))

    def test_reading_state_is_fine(self):
        for cmd in ("cat .sdlc/state.json", "python plugins/x/sdlc_state.py status --json",
                    "cat .sdlc/state.json > /tmp/copy.json", "ls 2>/dev/null"):
            self.assertAllowed(self.gate("Bash", command=cmd))


class SelfApproval(ProjectCase):
    def test_agent_cannot_run_approve_without_human_prompt(self):
        self.init_project()
        cmd = 'sh run_py.sh "/p/sdlc_state.py" approve discovery --by "Ana"'
        self.assertDenied(self.gate("Bash", command=cmd), "/sdlc-core:approve")
        self.hook(PROMPT, {"prompt": "/sdlc-core:approve discovery"})
        self.assertAllowed(self.gate("Bash", command=cmd))


class CodeLock(ProjectCase):
    def setUp(self):
        super().setUp()
        self.init_project()

    def test_code_locked_before_planning(self):
        self.assertDenied(self.gate("Write", file_path=os.path.join(self.dir, "src", "a.py")), "blocked")
        for cmd in ("echo x > src/a.py", "echo x >> ./src/a.py", "touch tests/test_a.py",
                    "cp /tmp/a.py src/", "tee src/a.py < /dev/null", "sed -i 's/a/b/' lib/x.py",
                    f"echo x > {self.dir}/src/a.py".replace("\\", "/"),
                    "git checkout other -- src/a.py",
                    "python -c \"open('src/a.py','w').write('x')\""):
            self.assertDenied(self.gate("Bash", command=cmd), "")

    def test_reading_and_docs_are_allowed_before_planning(self):
        self.assertAllowed(self.gate("Write", file_path=os.path.join(self.dir, "docs", "x.md")))
        for cmd in ("grep -r freeze src/ 2>/dev/null", "cat src/a.py", "ls src/ > /tmp/listing",
                    "cp src/a.py /tmp/backup.py", "git diff src/", "echo hi > notes.txt"):
            self.assertAllowed(self.gate("Bash", command=cmd))

    def test_code_unlocked_after_planning(self):
        walk_to(self, "planning")
        self.assertAllowed(self.gate("Write", file_path=os.path.join(self.dir, "src", "a.py")))
        self.assertAllowed(self.gate("Bash", command="echo x > src/a.py"))

    def test_hotfix_feature_unlocks_code(self):
        self.run_state("feature", "new", "Prod outage", "--type", "hotfix")
        self.assertAllowed(self.gate("Write", file_path=os.path.join(self.dir, "src", "a.py")))


class BlockedCommands(ProjectCase):
    def test_production_commands_are_denied(self):
        self.init_project()
        for cmd in ("terraform apply -auto-approve", "kubectl apply -f k8s/", "vercel deploy --prod",
                    "git push --force origin feature/x", "git push origin main"):
            self.assertDenied(self.gate("Bash", command=cmd), "human")
        self.assertAllowed(self.gate("Bash", command="git push -u origin feature/T-3-freeze"))
        self.assertAllowed(self.gate("Bash", command="terraform plan"))


class CommitRules(ProjectCase):
    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.dir, check=True, capture_output=True)

    def setUp(self):
        super().setUp()
        self.init_project("--type", "hotfix")
        self.git("init", "-q")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "T")

    def test_commit_without_tests_is_denied(self):
        self.write("src/latest.py", "x = 1\n")  # 'latest' must not count as a test file
        self.git("add", "src/latest.py")
        self.assertDenied(self.gate("Bash", command='git commit -m "fix"'), "no test files")

    def test_commit_with_tests_is_allowed(self):
        self.write("src/freeze.py", "x = 1\n")
        self.write("tests/test_freeze.py", "def test_x(): pass\n")
        self.git("add", ".")
        self.assertAllowed(self.gate("Bash", command='git commit -m "fix(freeze): x"'))

    def test_large_commit_warns(self):
        self.write("src/big.py", "x = 1\n" * 500)
        self.write("tests/test_big.py", "def test_x(): pass\n")
        self.git("add", ".")
        out = self.gate("Bash", command='git commit -m "feat: big"')
        self.assertIn("lines (limit 400)", out.get("systemMessage", ""))


class SessionHook(ProjectCase):
    def test_session_context(self):
        self.init_project()
        out = self.hook(SESSION, {})
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Current phase: discovery", ctx)
        self.assertIn("locked", ctx)

    def test_no_output_outside_project(self):
        self.assertIsNone(self.hook(SESSION, {}))


if __name__ == "__main__":
    unittest.main()
