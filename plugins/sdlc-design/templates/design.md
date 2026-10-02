# Technical Design — <Feature>

| Field | Value |
|---|---|
| Requirements | docs/02-requirements/requirements.md (vX) |
| Tech Lead | |
| Status | Draft / In review / Approved |

## 1. Overview
<What changes, in 3–5 sentences.>

## 2. Current state
<Relevant modules, data, integrations as they exist today — with file paths.>

## 3. Proposed design
### 3.1 Components
```mermaid
flowchart LR
  User --> UI --> API --> Service --> DB[(DB)]
```
### 3.2 Data model
| Entity / table | Change | Migration notes |
|---|---|---|

### 3.3 Interfaces / APIs
| Method & path | Request | Response | Errors |
|---|---|---|---|

### 3.4 Main flow
```mermaid
sequenceDiagram
  participant U as User
  participant A as API
  U->>A: request
  A-->>U: response
```

## 4. Edge cases & failure modes
| Case | Handling | AC |
|---|---|---|

## 5. Security, privacy, audit

## 6. Observability
- Logs:
- Metrics:
- Alerts:

## 7. Rollout & rollback
- Feature flag:
- Migration order:
- Rollback:

## 8. Requirement coverage
| AC / NFR | Component(s) | Notes |
|---|---|---|

## 9. Decisions (ADRs)
- ADR-001 — <title> — Proposed

## 10. Risks & open questions
- [ ]
