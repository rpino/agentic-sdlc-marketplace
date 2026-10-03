---
name: release-notes
description: Prepares a release — release plan (feature flag, staged rollout, monitoring, rollback, go/no-go checklist) and audience-specific release notes for business users, support/front-line staff and engineers. Use when shipping, before a deployment, or when asked for release notes or a rollout plan.
---

# Release Notes & Plan (Phase 8 · Release)

Inputs: approved requirements, design (rollout section), review report, merged PRs / build log. Outputs: `docs/08-release/release-plan.md` (template `${CLAUDE_PLUGIN_ROOT}/templates/release-plan.md`) and `docs/08-release/release-notes.md`.

## Release plan
1. **What ships:** stories/ACs included, anything deferred.
2. **Flag & rollout:** feature flag name, default state, staged rollout (e.g. pilot sites/users → 25% → 100%) with criteria to advance each stage.
3. **Pre-flight:** migrations order, config/secrets, dependencies on other teams, support readiness.
4. **Monitoring:** which dashboards/metrics/alerts prove it's healthy (from design §Observability) and the success metric from the brief.
5. **Rollback:** exact steps and who can trigger it; data implications.
6. **Version and changelog:** derive the SemVer bump from the Conventional Commits since the last tag (`feat` → minor, `fix` → patch, `!`/`BREAKING CHANGE` → major). Generate the CHANGELOG entry from those commits, grouped by type, with task and AC refs.
7. **Supply chain:** list the build's SBOM (e.g. `syft . -o cyclonedx-json` or the CI artifact), provenance/attestation (SLSA level reached, e.g. GitHub artifact attestations), and artifact signing (e.g. cosign). If any is missing, say so. Don't invent it.
8. **Go/no-go checklist** for the human decision, including the SLO error budget (don't release into an exhausted budget).

## Release notes (three audiences)
- **Business / customers:** what's new and why it matters, in plain language. No jargon.
- **Support / front-line staff:** how it works, what users will ask, known limitations, how to escalate.
- **Engineering:** changes, migrations, flags, config, links to PRs and ADRs.

Keep each short. Don't promise anything not in the approved scope.

## Human gate
Go/no-go and rollout stage advances are decided by the **Product Owner and stakeholders**. Present the plan; don't flip flags or deploy to production without explicit approval. Deploy commands are blocked by a hook, so the human runs them. After each real deployment, record it with the state script's `record deploy --note "<version> stage <n>"` so the DORA metrics are accurate.

Hand back to `sdlc-core:conductor`.
