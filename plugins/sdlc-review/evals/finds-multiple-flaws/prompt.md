---
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill, Agent]
---

Use the sdlc-review:code-reviewer agent to review this diff for task T-4 (AC-2.1: WHEN an order is refunded within 30 days of delivery THE SYSTEM SHALL refund the full amount once). Pass it the full diff below, since there is no git repository to read it from. Give me the agent's findings table.

```diff
+@app.post("/orders/<int:order_id>/refund")
+@login_required
+def refund(order_id):
+    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
+    days = (date.today() - order.delivered_on).days
+    if days >= 30:
+        return {"error": "refund window closed"}, 400
+    amount = round(float(order.total) * 1.0, 2)
+    payments.refund(order.payment_id, amount)
+    order.status = "refunded"
+    db.session.commit()
+    return {"refunded": amount}
```
