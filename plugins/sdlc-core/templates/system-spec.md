# {{PROJECT}}: living specification

This file describes how the system behaves **today**. It is the starting point for every enhancement, bug fix and hotfix.

- `adopt` drafts the first version from the code, for a human to approve.
- Each feature updates it at release (`sdlc-release:spec-updater`), and the Release gate approves the change.
- Don't edit it by hand outside a feature. Every entry says which feature last changed it.

Entry IDs (`CAP-n`) are stable. Never renumber them, because other documents refer to them.

## Capabilities

### CAP-1: <capability name>
- **Behaviour:** what the system does, in plain words.
- **Rules:** limits, eligibility, fees, validations and other business rules.
- **Source:** the feature and ACs that define it (for example `freeze-membership`, AC-1.1), or `adopted` if it was reverse-engineered.
- **Evidence:** `path/to/file:line` where the behaviour is implemented.
- **Last changed:** date, by feature `<slug>`.

## Non-functional and operational facts
SLOs, performance limits, security controls, data retention, integrations and anything operators need to know.

## Unconfirmed
Statements inferred from the code that no human has confirmed. Move each one up into a capability when someone confirms it, or delete it.
