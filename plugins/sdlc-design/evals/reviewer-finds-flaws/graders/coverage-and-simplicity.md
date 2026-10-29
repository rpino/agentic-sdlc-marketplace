---
type: llm
weight: 2
---

Flags at least two of these: (a) nothing in the design enforces AC-1.2 (once per calendar year); (b) the event bus and broker are heavier than needed for a single-row update and a simpler synchronous design would meet the same ACs; (c) the 2-second NFR and the 202 asynchronous flow are not reconciled, and no SLI, alert, trace or rollback path is described; (d) no STRIDE threat model for the new trust boundaries.
