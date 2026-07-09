---
name: django-spike-despike-workflow
description: "Manage Django spikes and de-spiking with tests: branch experiments, exploratory code, learning capture, functional tests against spiked behavior, revert-and-rebuild, custom auth flows, email/token models, and dependency seams. Use when a Django feature was prototyped quickly and needs to be turned into production-quality tested code."
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django Spike De-Spike Workflow
  category: Django
  tags: django,tdd,spikes,auth,testing
---

# Django Spike De-Spike Workflow

Use this skill when exploratory Django code has answered a question but is not yet fit to keep. Preserve the learning, throw away accidental design, and rebuild the feature with tests that express the real behavior.

## Source Traceability

Primary source: Harry Percival, *Test-Driven Development with Python*, 3rd ed. Guidance is transformed and paraphrased from chapters 19 and 20, especially passwordless authentication, branch-based spikes, de-spiking, custom user/token models, email flow tests, and introducing mocks only at external boundaries.

## Workflow

1. Label the spike.
   - Identify what question it answered.
   - Separate facts learned from code to keep.
   - Save notes, screenshots, shell commands, or minimal examples if they matter.

2. Write behavior from the spike.
   - Convert the useful behavior into a functional or integration test.
   - Keep the test user-facing when the spike proved a workflow.
   - Add lower-level tests for token models, forms, views, or email boundaries.

3. Revert or quarantine the spike.
   - Revert the exploratory branch or isolate it from production code.
   - Rebuild in small red/green/refactor steps.
   - Keep commits narrow enough to review.

4. Introduce seams deliberately.
   - Use fakes or mocks only for external email/service boundaries.
   - Keep Django auth and model behavior real unless the test boundary says otherwise.

Read [spike-despike-patterns.md](references/spike-despike-patterns.md) for branch discipline, auth-flow slicing, and de-spiking checklists.

## Decision Rules

- If the spike is mostly UI flow, start de-spiking from a functional test.
- If the spike proved a model or token rule, write model tests before rebuilding views.
- If the spike touched email, test the message boundary without hitting real email services.
- If the spike changed authentication models, keep migration and compatibility risks explicit.
- If the spike's code is messy but behavior is right, prefer rebuild over incremental cleanup.

## Guardrails

- Do not merge spike code just because it works once.
- Do not preserve hardcoded secrets, magic tokens, or one-off settings from the spike.
- Do not mock away Django authentication behavior when auth integration is the point.
- Do not lose the learning when reverting the code.

## Verification

Before finishing, report:

- Spike question and learning.
- Tests that capture intended behavior.
- What spike code was reverted, discarded, or rebuilt.
- External boundaries mocked or faked.
- Focused Django test command and result.
