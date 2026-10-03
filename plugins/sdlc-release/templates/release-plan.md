# Release Plan — <Feature> <version>

| Field | Value |
|---|---|
| Target date | |
| Feature flag | `<flag_name>` (default OFF) |
| Release owner | |
| Go/no-go approver | |

## Scope
| Included | Deferred |
|---|---|
| US-1 (AC-1.1–1.4) | |

## Rollout stages
| Stage | Audience | Advance when | Owner |
|---|---|---|---|
| 1 | Pilot | No Sev1/2 for N days, metric trending | |
| 2 | 25% | | |
| 3 | 100% | | |

## Pre-flight checklist
- [ ] Migrations applied in order
- [ ] Config / secrets in place
- [ ] Support briefed (release notes sent)
- [ ] Dashboards and alerts live

## Version & supply chain
- Version: <x.y.z> (SemVer bump from Conventional Commits: major / minor / patch)
- CHANGELOG entry: <link>
- SBOM: <path or CI artifact> (CycloneDX / SPDX)
- Provenance / attestation: <SLSA level, attestation link>
- Signed artifacts: <cosign / registry signature>
- Open dependency vulnerabilities accepted: <none / list + approver>

## Monitoring
- Health (SLIs from requirements):
- SLO error budget remaining at go/no-go:
- Success metric:

## Rollback
1.

## Go / No-go
- Decision: ____ by ____ on ____
