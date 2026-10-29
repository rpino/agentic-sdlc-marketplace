---
type: llm
weight: 3
---

Flags that migration 0042 drops `plan_type` while the old service version still reads it during rollout (not backward compatible, and not safely reversible), and recommends an expand-and-contract approach (add first, remove only after all code stops using it).
