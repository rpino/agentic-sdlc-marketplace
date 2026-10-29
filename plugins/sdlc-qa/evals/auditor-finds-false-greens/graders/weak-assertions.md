---
type: llm
weight: 3
---

Flags both of these: test_ac_1_2 only asserts `resp is not None` and never checks that the request was rejected or that a validation error was returned; and test_ac_1_3 swallows every exception and asserts nothing, so it passes whatever the code does.
