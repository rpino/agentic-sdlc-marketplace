---
type: llm
weight: 2
---

Also reports at least two of these: (a) the boundary is wrong, `days >= 30` rejects a refund on day 30, which the AC says is within 30 days; (b) money is handled as a float instead of a decimal or integer cents; (c) order.delivered_on may be None for an order that has not been delivered, which raises an error; (d) the payment is refunded before the database commit, so a failed commit leaves the customer refunded but the order not marked refunded; (e) there is no test for the AC in the diff.
