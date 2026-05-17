# Context Compaction Guide

When the system auto-compresses prior messages, this defines what MUST be preserved vs what can be safely dropped.

## MUST PRESERVE (loss = workflow failure)

1. **Current phase number and name** — e.g., "Currently in Phase 3 (Implement + Verify)"
2. **Plan file path** — `docs/plans/NNNN__*.md` — this is the **single recovery point**. Reading this file recovers everything.
3. **Language skill in use** — which language skill is active.
4. **User's original task description** — the WHY behind the work.

Everything else is on disk.

## SAFE TO DROP (all recoverable from plan file on disk)

| Information | Where on disk |
|---|---|
| Research findings | Plan file → `Research:` field → research file |
| User clarification Q&A | Plan file → `## Clarifications` |
| HOW-level locks | Plan file → `## Plan` → `### HOW-level locks` |
| Plan details | Plan file body |
| Implementation reasoning | Plan file → `## Implementation Log` |
| Task progress + affected files | Plan file → `## Task Checklist` |
| Verification iteration details | Plan file → `## Verification Results` |
| Review feedback + audit trail | Plan file → `## Review Log` |
| Chronicle content | Plan file → `Chronicle:` field → chronicle file |
| Code file contents | Source files on disk |

## RECOVERY PROTOCOL

1. **Read the plan file** — WORKFLOW STATE has current phase, remaining phases, all file paths.
2. **Read the language skill's configuration** — verification commands, implementation rules.
3. **Re-read `shared/workflow.md`** if the workflow rules themselves were dropped.
4. Read the current phase file from `phases/` for detailed instructions.
