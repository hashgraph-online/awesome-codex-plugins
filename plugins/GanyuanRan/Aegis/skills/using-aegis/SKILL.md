---
name: using-aegis
description: Use when starting a turn or checking Aegis skill routing.
---

<SUBAGENT-STOP>Skip for subagents.</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
You have Aegis. Load explicit/relevant Aegis skill before response/action;
otherwise proceed normally.
</EXTREMELY-IMPORTANT>

## Hot Path

1. User/project instructions outrank Aegis.
2. Active codebase question/"what next": check README/ADR/rules/baseline, else
   bounded index-first scan. Non-trivial owners passively use relevant `CONTEXT-MAP.md`/`CONTEXT.md`;
   compose `establishing-project-context` only on semantic delta/conflict.
   Create baselines only with evidence.
3. Direct grilling or plan/design pressure-tests (`grill me`, `grill this plan`, `审问我`, `盘问我`, `拷问我`) route to `brainstorming`; literal/explanatory uses do not.
4. `/aegis-goal` or `Aegis goal:` loads `goal-framing` before routing.
5. Bug, failure, regression, or unexpected behavior routes to `systematic-debugging`; quick bug lane owns Change Necessity before source edits.
6. Classify before implementation/start/resume/compaction. Low: intent, baseline, verification. Medium/high: baseline read-set + plan. TDD: off=no auto route/load; auto=strict/light/skipped; explicit request applies. Spec Brief or Design Spec only for complex, ambiguous, contract, cross-module work; shared/core/contract/cross-module never low without evidence. Source edits/new paths: owner workflow surfaces Change Necessity.
7. Non-tiny loaded skill: at the first substantive user-visible stage say why Aegis is shaping work/risk; do not wait for the user to ask. structured trace only for audit/debug/release/long-task review/asked; `Trace Digest` does not route. Tiny stays implicit.
8. ArchitectureReviewRequired: yes for medium/high architecture/contract/
   cross-module/owner/source-of-truth/fallback/adapter/baseline; carry to
   verification.
9. Workspace support is lazy; use configured Aegis workspace support only when records needed. Fast Q&A/status/tiny edits write no files.
10. Load smallest needed skill/reference.
11. Tool/log/memory/search outputs are evidence candidates, not prompt payloads;
   summary first, large input index->window->excerpt.
12. No history/sessions/transcripts/large logs by default; bound requested
   evidence by scope/time/lines.
13. Unclear host tool-name mapping: read smallest relevant reference.

Contract: `Route: fast-path`; `Aegis Reason Note`.
