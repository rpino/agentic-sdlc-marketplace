---
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill, Agent]
---

Use the sdlc-requirements:requirements-reviewer agent to review the requirements below against the problem brief. There are no files on disk, so pass it both texts in full. Give me the agent's findings table and its list of decisions for the Product Owner.

Problem brief, "Membership Freeze": Members who travel or get injured cancel instead of pausing, and we lose about 4% of members a year. Members should be able to freeze their membership from the app for 1 to 3 months, once per year, with no fee while frozen. Front-desk staff must be able to see that a membership is frozen. Success metric: cancellations for travel or injury drop by half within 6 months. Out of scope: freezing family plans.

requirements.md:

US-1: As a member, I want to freeze my membership so that I am not charged while I travel.
- AC-1.1: WHEN a member requests a freeze of 1 to 3 months THE SYSTEM SHALL freeze the membership.
- AC-1.2: The freeze screen should load quickly and be easy to use.
- AC-1.2: WHEN a member has already frozen this year THE SYSTEM SHALL reject the request.

US-2: As front-desk staff, I want to see which memberships are frozen so that I do not turn away members by mistake.
- AC-2.1: WHILE a membership is frozen THE SYSTEM SHALL show a "Frozen" badge on the member record.

US-3: As a family-plan owner, I want to freeze the whole family plan so that nobody is charged.
- AC-3.1: WHEN the owner of a family plan requests a freeze THE SYSTEM SHALL freeze every member on the plan.

NFR-1: The system should be secure and fast.
