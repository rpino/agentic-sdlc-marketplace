---
name: security-checklist
description: Security review of a diff or feature using an OWASP Top 10 / ASVS-based checklist — authorization, input validation, injection, secrets, PII, dependencies, logging and abuse cases. Use during code review, before release, or when asked "is this secure" or for a threat model.
---

# Security Checklist (Phase 7 · Review)

Apply to the diff(s) under review and the feature's design. For each item answer **Pass / Fail / N/A** with evidence (file:line).

## Checklist
1. **Access control** — every new/changed endpoint checks the caller may act on *this* resource (no IDOR). Admin paths protected.
2. **Authentication & session** — no auth bypass; tokens validated; sensible expiry.
3. **Input validation** — server-side validation of type, length, range, format for all inputs.
4. **Injection** — parameterised queries; no string-built SQL/shell/LDAP; output encoding for HTML (XSS).
5. **Secrets** — none in code, config or logs; loaded from the secret store.
6. **Sensitive data / PII** — minimal collection, masked in logs, encrypted at rest/in transit where required; retention honoured.
7. **Dependencies** — new libraries are maintained, licensed acceptably, no known critical CVEs (run the project's scanner if available, e.g. `npm audit`, `pip-audit`, Dependabot/Snyk results).
8. **Error handling** — no stack traces or internals returned to users.
9. **Logging & audit** — security-relevant actions are logged with who/what/when; no sensitive data in logs.
10. **Abuse cases** — rate limiting, replay, mass enumeration, business-logic abuse (e.g. repeated freeze/unfreeze to dodge fees).
11. **Configuration** — secure defaults, CORS, headers, feature flags default off.

## Output
Append a **Security** section to `docs/07-review/review-report.md`: the checklist table plus findings with severity (Critical/High/Medium/Low). Any Critical/High must be fixed or explicitly risk-accepted by a named human before the Review phase is approved.
