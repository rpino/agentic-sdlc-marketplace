---
type: llm
weight: 3
---

Flags both: (a) the Billing call has no retry, timeout, idempotency or compensation, so a Billing error leaves the membership frozen while billing continues, which breaks AC-1.3; and (b) the endpoint only requires login, with no check that the caller owns the membership (IDOR).
