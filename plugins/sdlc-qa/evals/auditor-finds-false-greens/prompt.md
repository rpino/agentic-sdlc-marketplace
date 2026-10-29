---
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill, Agent]
---

Use the sdlc-qa:test-auditor agent to audit the tests below. There are no files on disk and no test runner, so pass it everything in full and tell it to audit by reading only. Give me the agent's findings table and its verdict.

Acceptance criteria:
- AC-1.1: WHEN a member requests a freeze of 1 to 3 months THE SYSTEM SHALL freeze that member's own membership.
- AC-1.2: IF the requested freeze is shorter than 1 month or longer than 3 months THEN THE SYSTEM SHALL reject the request with a validation error.
- AC-1.3: IF a member requests a freeze of another member's membership THEN THE SYSTEM SHALL reject the request.

test-report.md says: "3 of 3 test cases pass. All ACs verified."

tests/test_freeze.py:

```python
from unittest.mock import patch

def test_ac_1_1_freeze_own_membership(client, member):
    with patch("app.memberships.freeze_membership") as freeze:
        freeze.return_value = {"ok": True}
        resp = client.post(f"/memberships/{member.membership_id}/freeze", json={"months": 2})
        assert freeze.called

def test_ac_1_2_rejects_bad_length(client, member):
    resp = client.post(f"/memberships/{member.membership_id}/freeze", json={"months": 5})
    assert resp is not None

def test_ac_1_3_other_members_membership(client, member, other_member):
    try:
        client.post(f"/memberships/{other_member.membership_id}/freeze", json={"months": 1})
    except Exception:
        pass
```
