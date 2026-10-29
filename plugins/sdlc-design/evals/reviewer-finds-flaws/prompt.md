---
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill, Agent]
---

Use the sdlc-design:design-reviewer agent to review the design below against the requirements. There are no files on disk, so pass it both texts in full. Give me the agent's findings table and its decisions for the Tech Lead.

requirements (summary): AC-1.1 a member can freeze their own membership for 1 to 3 months. AC-1.2 a member can freeze only once per calendar year. AC-1.3 WHEN a freeze starts THE SYSTEM SHALL stop billing until it ends. NFR-1 99.9% of freeze requests succeed within 2 seconds.

design.md:

Components: a new `POST /memberships/{id}/freeze` endpoint in the Members service, a new `FreezeEventBus` that publishes `FreezeRequested` events to a message broker, a `FreezeConsumer` that updates the membership, and a call from the consumer to the Billing service's `PUT /subscriptions/{id}/pause`.

Data: migration 0042 drops the column `memberships.plan_type` and adds `memberships.frozen_until` (date, nullable). The old version of the Members service, which still reads `plan_type`, keeps running during the rollout.

Flow: the endpoint validates months is 1 to 3, publishes the event and returns 202. The consumer sets `frozen_until`, then calls Billing to pause the subscription. If Billing returns an error the consumer logs it.

Security: the endpoint requires login.

Operability: logs for each step.
