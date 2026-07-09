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
2. Active codebase question/"what next": check baselines
   (README/ADR/rules/`docs/aegis/baseline`), else bounded index-first scan.
   Create baselines only with evidence.
3. `/aegis-goal` or `Aegis goal:` loads `goal-framing` before routing.
4. Bug, failure, regression, or unexpected behavior routes to `systematic-debugging`; quick bug lane owns Change Necessity before source edits.
5. Classify before implementation/start/resume/compaction. Low: intent + baseline check + TDD Route + verification. Medium/high: baseline read-set + plan. TDD default off; auto/explicit => strict/light/skipped; off=no auto, verify.
   Spec Brief or Design Spec only for complexity, ambiguity, contracts, or
   cross-module impact. Contract/shared/core/cross-module changes are never low
   without evidence. Source edits/any new source-code path: owner workflow surfaces Change Necessity.
6. Aegis Reason Note / Visibility Non-Omission: if Aegis skill is loaded and not tiny fast-path, first substantive user-visible stage gives one natural sentence: why Aegis is shaping the task + quality risk reduced; do not wait for user to ask where Aegis was used. Tiny fast-path may stay implicit. structured trace only for audit/debug/release/long-task review/asked; Trace Digest on-demand. Trace does not route; behavior/owner skill route first.
7. Mark ArchitectureReviewRequired: yes for medium/high architecture, contract, cross-module, owner, source-of-truth, fallback/adapter, or project-baseline tasks; carry to verification-before-completion.
8. Workspace support is lazy; use configured Aegis workspace support only when records needed. Fast Q&A/status/tiny edits write no files.
9. Load smallest needed skill/reference.
10. Tool/log/memory/search outputs are evidence candidates, not prompt payloads; summary first; large inputs use bounded index->window->excerpt.
11. No historical sessions/transcripts/history.jsonl/.codex/sessions/~/.claude/projects/large logs by default; read requested evidence with scope/time/line bounds.
12. Unclear host tool-name mapping: read smallest relevant reference.

Contract: `Route: fast-path`; `Aegis Reason Note`.
