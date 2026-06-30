---
name: using-aegis
description: Use when starting a turn or checking Aegis skill routing.
---

<SUBAGENT-STOP>Subagents skip this skill.</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
You have Aegis.

Before any response/action, check if an Aegis skill is explicit or relevant.
Load only that skill; otherwise proceed normally.
</EXTREMELY-IMPORTANT>

## Hot Path Rules

1. User and project instructions outrank Aegis.
2. Active codebase question or "what next": check baseline candidates
   (README/ADR/rules/`docs/aegis/baseline`), else bounded index-first scan.
   Create a baseline only with evidence.
3. `/aegis-goal` or `Aegis goal:` loads `goal-framing` before onward routing.
4. Bug, failure, regression, or unexpected behavior routes to `systematic-debugging`; quick bug lane stays compact and owns Change Necessity before source edits.
5. Classify before implementation/start/resume/compaction. Low: concise intent
   + baseline check + TDD Route + verification. Medium/high: baseline read-set + plan. TDD Route: auto=strict/light/skipped; off=no auto, verification
   stays. Spec Brief or Design Spec only for complexity, ambiguity, contracts,
   or cross-module impact. Contract/shared/core/cross-module changes are never
   low without evidence. Source edits: owner workflow surfaces `Change Necessity`.
6. Aegis Reason Note: why Aegis is shaping non-trivial skill/stage work; tiny fast-path may stay implicit; structured trace only for audit/debug/release/long-task review or asked.
7. Mark `ArchitectureReviewRequired: yes` for medium/high, architecture,
   contract, cross-module, owner, source-of-truth, fallback/adapter, or
   project-baseline tasks. Carry it to `verification-before-completion`.
8. Workspace support is lazy. Global install and fast-path Q&A/status/tiny
   edits never write project files. Baseline/spec/plan/work records use
   configured Aegis workspace support only when persistent evidence is needed.
9. Load the smallest needed skill/reference.
10. Tool/log/memory/search outputs are evidence candidates, not prompt payloads: summary first; large inputs use bounded index→window→excerpt.
11. Do not read historical sessions, transcripts, `history.jsonl`,
   `.codex/sessions`, `~/.claude/projects`, or large logs default. Read only
   requested/required direct evidence with scope/time/line bounds.
12. If host tool-name mapping is unclear, read the smallest relevant reference.

Contract when useful: `Route: fast-path`; `Aegis Reason Note`; `Why`; `Next`.
