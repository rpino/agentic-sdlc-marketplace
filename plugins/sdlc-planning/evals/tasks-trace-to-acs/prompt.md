---
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Break this approved design into implementation tasks and show the plan here in chat (don't create files).

Requirements: AC-1.1 a member can freeze for 1-3 months from the app; AC-1.2 a freeze over 3 months is rejected; AC-1.3 billing pauses while frozen; AC-2.1 front-desk screen shows a "Frozen until <date>" badge.
Design: add `frozen_until` column to memberships (migration), POST /memberships/{id}/freeze endpoint with validation, billing job skips memberships whose frozen_until is in the future, front-desk React badge component, feature flag `membership_freeze`.
