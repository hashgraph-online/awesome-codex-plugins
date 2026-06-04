---
name: accessibility-gates
description: "Use when designing or releasing user-facing flows needing keyboard, screen-reader, focus, contrast, or assistive checks"
---

# Accessibility Conformance Checks

## Iron Law

```
NO CRITICAL USER FLOW SHIPS WITHOUT A NAMED CONFORMANCE LEVEL, ASSISTIVE-TECH CHECK, AND REGRESSION CHECK
```

Pick the conformance level explicitly for the target surface. Run the critical flow with at least one assistive-technology path before release. Add a regression check so the same defect cannot recur silently. For a solo developer or tiny project, the check can be a keyboard-only and screen-reader walkthrough recorded once per release; the discipline is that the walkthrough happened, not that anyone else performed it.

## Overview

Accessibility is a release quality property, not a post-launch polish pass.

**Core principle:** check critical user journeys on semantic structure, keyboard access, focus behavior, visual contrast, assistive-technology behavior, and regression checks.

## When To Use

- The user is designing, building, changing, or releasing a user-facing flow that needs accessibility, conformance, assistive-technology support, keyboard navigation, focus order, contrast, labels, or release checks.
- A UI change affects forms, navigation, dialogs, errors, media, dynamic updates, or critical journeys.
- Automated checks and manual checks need to be combined into a release decision.
- A regression blocks users from perceiving, operating, or understanding the interface.

## When Not To Use

- The main issue is loading speed, responsiveness, visual stability, or runtime errors; use `web-release-gates` instead.
- The main issue is native crash, startup, offline, or app-store rollout risk; use `mobile-release-engineering` instead.
- The request is brand design or marketing copy without accessibility engineering risk.
- The work is a legal policy discussion without concrete engineering checks.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Critical journeys, user surfaces, target conformance level, supported input modes, and assistive technologies.
- Changed components, labels, roles, focus behavior, keyboard paths, error handling, contrast, and dynamic content.
- Existing automated checks, manual test scripts, defect history, and release-blocking rules.
- Exceptions, expiry, severity, affected users, and compensating path.
- Telemetry or support signals for accessibility regressions where available.

## Workflow

1. **Define the target.** State the conformance expectation and critical journeys before evaluating details.
2. **Map the journey.** Identify every step, control, message, focus transition, and error state a user must complete.
3. **Check semantics and names.** Ensure controls expose meaningful structure, labels, state, and relationships.
4. **Verify operation.** Test keyboard-only paths, assistive-technology paths, and component snapshots for completion.
5. **Check perception.** Review contrast, text resizing, motion, timing, media alternatives, and status updates where relevant.
6. **Combine results.** Use automated checks for broad regressions and manual checks for interaction quality.
7. **Check release.** Block critical journey failures; track lower-risk defects with severity, expiry, and retest date.
8. **Prevent recurrence.** Add component tests, examples, lint rules, or review checks for repeated failure patterns.

## Synthesized Default

Check critical journeys with a named conformance target, automated checks, manual assistive-technology scripts, keyboard completion tests, dated repair plans for accepted deviations, and regression tests for known defects. Accessibility checks should be part of launch readiness for user-facing changes.



## Phase Behavior

- Ideation: identify risks, defaults, unknowns, options, and the next decision before code exists.
- Design: shape the target artifact, tradeoffs, checks, and details to gather.
- Development: guide sequencing, code boundaries, checks, and acceptance criteria.
- Testing: define release-blocking tests, evals, fixtures, and failure probes.
- Release: define rollout, observability, abort, rollback, and readiness details.
- Maintenance: define owners, drift checks, cleanup triggers, and refresh cadence.
- Existing artifact: use current code, docs, telemetry, incidents, or diffs as context for the next engineering decision; do not wait for a finished artifact before guiding design, build, release, or operation.
- Missing details: state assumptions and say what to check next instead of blocking lifecycle guidance.

## Exceptions

- Internal tools may use a narrower journey set only when the affected user group and alternative path are explicit.
- Emergency fixes can ship with a tracked accessibility exception only when delaying is riskier and a repair date exists.
- Automated checks are not enough for complex interactions; manual verification remains required for critical flows.

## Response Quality Bar

- Lead with the accessibility release decision, blocker list, conformance gap, or test plan requested.
- Cover target, critical journeys, semantics, keyboard behavior, focus, assistive-technology checks, contrast, exceptions, and regression checks before optional design advice.
- Name one concrete assistive-technology path for at least one critical journey, such as NVDA, VoiceOver, JAWS, TalkBack, Dragon, or switch control, with a pass/fail criterion for completing that journey.
- Make recommendations actionable with severity, blocking status, retest steps, and release criteria where relevant.
- For recurring defects or launch blockers, make the regression mechanism concrete: name the CI check, lint rule, component test, or recurring manual checklist; include the verification check, the test that would fail without the change, covered environment inventory such as local, CI, staging, or production-like, docs-as-code checklist location, and refresh cadence.
- Name the details to inspect, such as journey list, automated results, manual scripts, screenshots or recordings, defect history, and exception records; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them, explicitly requested tool-specific guidance, or a named assistive technology is needed for test results.
- Stay inside accessibility engineering. Route performance, mobile rollout, or broad legal policy only when those are central.
- Be concise: prefer journey-based check tables over broad accessibility lectures.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Accessibility conformance target and journey inventory.
- Release check matrix: automated checks, manual checks, blocking status, and repair path.
- Critical journey manual test script.
- Exception register with severity, expiry, compensating path, and retest, using the shared risk-acceptance lifecycle plus the shared compensating-control format where a deviation is accepted.
- Regression-prevention plan for recurring defects.
- Follow-up routes for performance or mobile-specific release risk where needed.

## Checks Before Moving On

- `target_defined`: conformance expectation and critical journeys are named.
- `journey_complete`: users can complete critical flows through supported input and assistive paths.
- `mixed_testing`: automated checks and hands-on testing are both used where interaction quality matters.
- `exception_responsibility`: every exception has severity, user-confirmed reason, expiry, and compensating path.
- `regression_check`: known failures have tests or checks to prevent recurrence.

## Red Flags - Stop And Rework

- Automated checks pass, but the critical journey lacks manual test evidence.
- Focus is trapped, lost, or moves unpredictably.
- Controls have visible labels but no reliable accessible names.
- Error messages are visible but not announced or associated with fields.
- Accessibility exceptions have no repair date or verification path.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Component-only checks | Test complete user journeys. |
| Automation as the whole answer | Add manual interaction verification. |
| Treating all defects alike | Block critical journey failures first. |
| Exceptions without expiry | Require compensating path, and retest. |
