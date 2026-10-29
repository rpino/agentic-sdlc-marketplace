---
type: llm
weight: 3
---

Reports, as Blocker or Major severity, that the endpoint can refund the same order more than once: it never checks that the order is already refunded (or uses an idempotency key), so a repeated request calls payments.refund again. AC-2.1's "once" is violated.
