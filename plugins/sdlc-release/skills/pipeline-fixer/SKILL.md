---
name: pipeline-fixer
description: Diagnoses and fixes failing CI/CD pipelines — reads build/test/deploy logs, finds the root cause (code, test flakiness, environment, config, dependency), and proposes or applies the smallest fix. Use when a build, GitHub Actions/Azure DevOps/Jenkins job or deployment fails.
argument-hint: "[pipeline run URL, job name or pasted log]"
---

# Pipeline Fixer (Phase 8 · Release)

Input: `$ARGUMENTS` — a run link, job name, or log text. If nothing is given, ask for the failing run or log.

1. **Get the log.** Use a CI connector/CLI if available (e.g. `gh run view --log-failed`), otherwise ask the user to paste it.
2. **Find the first real error**, not the last line. Classify it:
   - code/test failure (real regression) · flaky test · environment/runner · config/secret missing · dependency/version drift · infrastructure/deploy.
3. **Explain the root cause** in 2–3 sentences with the evidence (log lines).
4. **Fix with the smallest change.** Real regressions go back through the normal build loop (test first). Never "fix" by deleting or skipping tests, lowering coverage thresholds or disabling checks — if that seems necessary, explain and ask a human.
5. **Prevent recurrence:** suggest a guard (pin version, retry for known-flaky infra, add a check) and note it for the retro.

Production deployment changes require explicit human approval.
