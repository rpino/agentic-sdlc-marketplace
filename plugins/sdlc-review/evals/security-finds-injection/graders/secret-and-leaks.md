---
type: llm
weight: 2
---

Also reports at least two of these: (a) a live payment API secret (PAYMENT_API_SECRET) is hard-coded in source; (b) the 500 response returns a full stack trace to the client; (c) card_number (sensitive payment data) is selected and returned in the response when staff only need names; (d) the endpoint only checks login, not that the caller is front-desk staff.
