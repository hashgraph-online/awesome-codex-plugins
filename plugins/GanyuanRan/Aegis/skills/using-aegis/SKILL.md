---
name: using-aegis
description: "Use when starting a turn or checking Aegis skill routing."
alwaysApply: true
---

<SUBAGENT-STOP>Skip for subagents.</SUBAGENT-STOP>

<EXPLICIT-MODE-GATE>
If activation mode is explicit and this request did not explicitly invoke Aegis or a named skill, stay on the fast path; do not route to any Aegis skill. Explicit invocation proceeds normally.
</EXPLICIT-MODE-GATE>

<EXTREMELY-IMPORTANT>
You have Aegis. Load explicit/relevant Aegis skill before response/action;
otherwise proceed normally.
</EXTREMELY-IMPORTANT>

## Hot Path

1. User/project instructions outrank Aegis.
2. Load only the smallest explicitly requested or clearly relevant skill/reference;
   otherwise stay on the fast path.
3. Active codebase question/"what next": check README/ADR/rules/baseline, else
   bounded index-first scan. Non-trivial work passively use relevant
   `CONTEXT-MAP.md`/`CONTEXT.md`; model semantic conflicts only when found.
4. Primary routes: `grill me`/`grill this plan`/`审问我`/`盘问我`/`拷问我` -> `brainstorming` (literal/explanatory uses do not); `/aegis-goal` or `Aegis goal:` -> `goal-framing`. Bug, failure, regression, or unexpected behavior routes to `systematic-debugging`.
5. Implementation only: Classify before implementation. Low stays owner-local;
   Medium/high: baseline read-set + plan. Spec Brief or Design Spec only for
   ambiguous/contract/cross-module medium/high work. TDD: off=no auto route/load; auto=risk-based strict/light/skipped; explicit strict applies.
   Pure explanation and read-only diagnosis skip implementation/TDD/write gates.
6. For writes, the owner workflow surfaces Change Necessity, records
   `TaskStartSnapshot`, and decides `ArchitectureReviewRequired`; ceremony alone
   never creates a branch/worktree.
7. At the first substantive user-visible stage say why Aegis is shaping
   non-tiny work; do not wait for the user to ask. structured trace is only for audit/debug/release/long-task review/asked and does not route (`Trace Digest`).
8. Workspace support is lazy; use configured Aegis workspace support only when
   records are needed. Q&A/status writes no project files; tiny work writes no
   workspace docs unless its owner requires a durable record.
9. Tool/log/memory/search outputs are evidence candidates, not prompt payloads:
   summary first; large input index->window->excerpt. Bound history/session/
   transcript/log reads by scope/time/lines.
10. Read `references/skill-discipline.md` only when route/order/TDD/workspace/
    context re-entry/host mapping detail is needed.

Contract: only a real fast path emits `Route: fast-path` and an `Aegis Reason Note`; a routed skill owns its next-stage contract.
