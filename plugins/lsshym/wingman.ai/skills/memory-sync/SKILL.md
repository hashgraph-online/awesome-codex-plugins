---
name: memory-sync
description: Use when progress, decisions, business logic, API contracts, state flow, field mappings, or durable project knowledge should be recorded in Wingman memory.
---

# Wingman Memory Sync

## Core Rule

`memory-sync` writes the smallest useful memory update after meaningful work, while promoting durable knowledge out of hot context when future agents would otherwise re-read old logs or re-debug the same issue.

- Current truth that future agents must obey belongs in `brief.md` or `domains/`.
- `history/` is trace context only; it is not current truth.
- Small isolated changes may write nothing.

## Gate

Apply these gates before reading or writing memory:

1. If the user says "skip update", "不更新", "跳过记录", "这个不用记忆", "局部改动不记录", or equivalent, stop without reading or writing memory.
2. If `.wingman/memory/` is missing, ordinary completion must not invoke `memory-sync`. If sync was explicitly requested, report that repository memory is disabled and `memory-setup` is the explicit enable path.
3. If `.wingman/memory/` exists but `.wingman/memory/brief.md` or `.wingman/memory/context.md` is missing, stop before writing, report the missing core entry files, and suggest `memory-setup` repair. Do not repair from `memory-sync`.
4. Continue only when both `brief.md` and `context.md` exist.

Before reporting meaningful coding, documentation, configuration, product, or operational work as complete in a repository where memory is enabled, run this skill's thresholds. If the work passes a write threshold and memory has not been synced, sync memory before saying done, fixed, completed, or 已完成, unless the user explicitly opted out.

## Promotion Check

Before writing a context log, check whether the new fact or existing same-feature context logs should be promoted to current truth or history.

Prefer promotion when any of these are true:

- The fact defines a stable API path, request body, response field, field meaning, schema, payload, state mapping, enum, route rule, permission rule, payment rule, money rule, quota rule, or lifecycle rule.
- The user corrected a business meaning, field meaning, or workflow interpretation.
- The work fixed a recurring debugging conclusion or a mistake future agents are likely to repeat.
- The behavior crosses files, modules, pages, APIs, or domains.
- The same feature, workflow, or domain already has multiple context logs and those logs now contain long-lived knowledge.
- Future agents would need the fact to avoid re-reading old logs, re-debugging, or choosing a semantically wrong field.

Promotion does not mean every promoted fact needs history. Current truth explains what is binding now; history explains important source events.

## Routing

Route each fact to the destination matching its job:

| Route             | Destination  | Use When                                                                                                                                                   |
| ----------------- | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **IGNORE**        | none         | Too small or too local to remember.                                                                                                                        |
| **CONTEXT_LOG**   | `context.md` | Recent progress, changed files, debugging state, partial work, unresolved follow-ups, or near-term context.                                                |
| **DOMAIN_TRUTH**  | `domains/`   | Stable one-domain business rules, API contract, canonical field, state flow, permission rule, money rule, routing rule, or recurring debugging conclusion. |
| **PROJECT_ADR**   | `brief.md`   | Global or cross-domain architecture decision, repository convention, project-wide agent behavior, or policy.                                               |
| **HISTORY_EVENT** | `history/`   | Past event with lasting trace value beyond hot context.                                                                                                    |

A task may route to more than one destination, but each destination must have a concrete reason. Do not write memory just because this skill was invoked.

## Thresholds

**IGNORE** for typo-only edits, rename-only cleanup, formatting, small copy edits, isolated visual or style tweaks with no behavior/state/data/contract/business impact, behavior-preserving movement or extraction, and one-off failed attempts with no reusable lesson.

**CONTEXT_LOG** when the work may matter in the next few sessions: meaningful progress, changed files and what each one now does, partial work, pending follow-ups, debugging state, recent conclusions, or non-trivial implementation details that are not durable rules.

**DOMAIN_TRUTH** or **PROJECT_ADR** when future agents must obey the result or would otherwise need old logs to avoid re-debugging: stable field meaning, API path/body/response contract, schema, event, config, data model, state or enum mapping, permission, routing, money, quota, lifecycle, product or business invariant, cross-file behavior contract, recurring debugging conclusion with a clear trigger, repository-wide convention, or architecture decision.

**HISTORY_EVENT** defaults to no for small local changes. It defaults to yes when a non-trivial **DOMAIN_TRUTH** or **PROJECT_ADR** was written for a feature milestone, contract decision, field decision, state-flow correction, recurring debugging conclusion, migration, incident, important bug or regression fix, or user-requested historical memory, unless the event has no trace value beyond the current rule.

## Value Funnel

Before writing memory, classify the change by future value:

- **Record** when it changes behavior, contracts, data meaning, workflow, architecture, shared implementation, or a durable debugging conclusion.
- **Skip** when it is local, obvious from the diff, purely mechanical, or has no reusable lesson.
- **Promote** to `domains/` or `brief.md` when it becomes a rule future work must follow.

Every recorded entry must explain why the change was needed and what future mistake it prevents.

## Workflow

1. Apply the Gate.
2. Run Promotion Check before deciding to write a context log.
3. Route facts using the Thresholds.
4. If every fact is **IGNORE**, write nothing and say which threshold blocked the update.
5. For **DOMAIN_TRUTH** or **PROJECT_ADR**, pass the Evidence Gate before writing current truth.
6. Write current truth before history when both are needed.
7. Decide **HISTORY_EVENT** after current truth routing. Write history when the History threshold passes.
8. Write **CONTEXT_LOG** only for hot context. When current truth or history already carries the durable detail, write a short pointer instead of repeating the full event.
9. Report changed memory files, projection indexes, or the threshold that blocked writing.

Current truth comes before history. If a future agent must follow a rule, write it to `brief.md` or `domains/` before writing any history event about it. Do not write history just because `context.md` was updated. Do not create a history event just to fill a `History` backlink. Do not promote guessed thresholds, temporary constants, local workarounds, or one-off implementation details into current rules.

## Write Rules

### Context Log

Open `.wingman/memory/context.md`. Find the recent log section, commonly `## Recent Logs`, `## Current Sprint Logs`, or `## 短期活跃日志 (CURRENT SPRINT LOGS)`.

- Prepend the new log directly below the section heading.
- Update pending tasks only when the task changes pending work.
- If this update corrects a same-day, same-feature, or same-bug log that is now wrong, remove only that obsolete log and keep the corrected truth.
- Do not merge, rewrite, reorder, or delete unrelated history.
- Before using the default context log shape, read `references/templates.md`.
- If **DOMAIN_TRUTH**, **PROJECT_ADR**, or **HISTORY_EVENT** was written for the same fact, use the Context Pointer Template from `references/templates.md` instead of duplicating durable detail in `context.md`.

Before writing a log, internally verify that:

- The implementation used canonical memory fields and did not substitute proxy or heuristic fields for semantic fields.
- The implementation reused an existing component/helper/pattern when the repository already had one.
- Any tiny but high-impact local behavior has an inline invariant comment when code alone would invite accidental cleanup.
- The context log includes the reason for the change and the mistake it prevents.

If this proof fails, report the conflict or missing invariant instead of claiming completion.

Inline invariant comments are for local constraints, not full change history. Use them only when a tiny or odd-looking line would be easy to "simplify" but changing it would alter behavior, data meaning, contract, security, money, routing, permissions, or state flow:

`// @invariant: <constraint>; <why changing it breaks semantics>.`

### Reason Gate

Do not write a context log that only says what changed. Include the reason in one sentence:

`Changed X because Y; prevents Z.`

If the reason is trivial, meaningless, or obvious from the diff, prefer `IGNORE` unless the task is hot context for the next session.

### Current Truth

Before writing **DOMAIN_TRUTH** or **PROJECT_ADR**, verify at least one evidence source:

- The user explicitly stated the rule or decision.
- Existing Wingman memory already implies the rule.
- Product docs, API docs, schema, tests, or accepted specs confirm it.
- The implementation intentionally changed a stable contract or business behavior, not just an incidental implementation detail.

If evidence is weak and the proposed durable rule would constrain future work, ask the user before writing durable memory.

Write current truth with these rules:

- Read `.wingman/memory/brief.md` and use the Domain Registry to route the rule.
- Route one-domain rules to `.wingman/memory/domains/<domain>.md` or that domain folder's focused topic file.
- Route global or cross-domain rules to the architecture decisions section in `brief.md`.
- Create new domain files only for stable business, technical, product, or operational domains. Do not create one domain file per small feature.
- Write new durable truth to the best existing location. If the target already mixes unrelated knowledge clusters, prefer the most specific existing domain or topic file instead of adding another broad entry.
- Write durable rules under `## Current Truths` for English memory or `## 当前业务真理` for Chinese memory.
- Update the Domain Registry when creating, renaming, deprecating, or superseding a domain route. New registry rows use `Domain | Read When | Current File | History Domain Index | History Topics | Aliases | Related Domains | Status`.
- When creating a new domain, choose `.wingman/memory/domains/<domain>.md` for a small domain or `.wingman/memory/domains/<domain>/index.md` plus focused topic files for a large domain.
- Use stable, generic topic names for domain subfiles and history topics. Avoid customer names, project code names, and one-off business labels.
- When replacing a rule, decision, or domain route, mark the old current entry as `superseded` or `deprecated` and point to the replacement. Do not leave conflicting current truths alive.

Before using the default durable truth shape, read `references/templates.md` when the existing memory file has no stronger local format. `History` is optional; write `None` when there is no specific history event. Do not invent a history event just to fill the field. For **PROJECT_ADR**, use ADR lifecycle status values: `proposed | accepted | deprecated | superseded`.

### History Event

Run this section only when **HISTORY_EVENT** passes the threshold.

- Read `references/history-events.md` before writing history.
- Write one event body under `.wingman/memory/history/events/YYYY/MM/YYYY-MM-DD-<event-slug>.md`.
- Update `.wingman/memory/history/index.md`, `.wingman/memory/history/domains/<domain>.md`, `.wingman/memory/history/topics/<topic>.md`, and `.wingman/memory/history/months/YYYY-MM.md`.
- Choose topics from the task's feature, workflow, or problem cluster. Use generic names such as `checkout-flow`, `payment-selection`, `order-status`, `product-detail`, `upload-retry`, or `quota-display`.
- Include `Promoted Truths` links when `brief.md` or `domains/` was updated. Use `None` when no current truth was promoted.
- Do not copy full event bodies into projection indexes.
- Do not treat projection indexes as current rules.
- Projection indexes can be rebuilt from events; do not rewrite event bodies just because an index changes.

## Language And Completion

Memory language: `brief.md` setting when not `auto`; otherwise existing memory language, then user's language, then English. Keep code symbols, paths, API names, config names, and field names unchanged.

Finish by reporting changed memory files, including context, domain truth, history event bodies, and projection indexes. If no history event was written, name the threshold or reason that blocked history. If nothing was written, name the blocking gate or threshold.
