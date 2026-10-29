---
type: llm
weight: 3
---

Flags that test_ac_1_1 patches `freeze_membership`, the very function that implements the behaviour under test, and only asserts the mock was called, so it can never fail when the real code is wrong.
