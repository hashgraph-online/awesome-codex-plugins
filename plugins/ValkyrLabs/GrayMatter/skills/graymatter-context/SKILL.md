---
name: graymatter-context
description: Compile bounded, task-specific GrayMatter context and inspect authorized procedures or retrieval receipts. Use when a task needs grounded prior context, a reusable method, or an explanation of why particular memory was selected.
---

# GrayMatter Context

Compile the smallest useful authorized context for the current task instead of loading broad memory exhaust.

## Workflow

1. For an authorized context request, call `context_compile` with the original user task text unchanged as `task`, preserving all explicit constraints. Do not expand, paraphrase, or add invented evidence checklists, conditions, or exclusions. Set the token budget and procedure/rating controls separately. Scope and secret restrictions still take precedence.
2. Prefer the compiled ContextPage summary, selected items, hydration pointers, policy result, and receipt reference over raw memory dumps.
3. Respect retrieval policy. If the compiled result indicates low confidence, stale context, partial coverage, conflict, retry, clarification, or denial, follow that action before answering confidently.
4. Call `procedure_search` when a repeatable methodology may already exist. Use an authorized high-confidence procedure when it fits the task; do not invent tenant filters.
5. Call `retrieval_receipt_get` when the user asks why context was selected, which sources contributed, or how confidence, freshness, coverage, and policy were evaluated.
6. In that same answer, summarize the selected sources and selection reasons, coverage gaps, source dates/freshness, and answer policy. Disclose disabled or missing evaluator confidence as unavailable, never zero; retrieval, quality, and similarity scores are not evaluator confidence. If a field is missing, say it is unavailable instead of recompiling or inventing it.
7. Cite the receipt ID in the response when provenance or selection rationale materially matters.

## Context discipline

- Keep temporary conversational context in the conversation. Save only durable information through the GrayMatter memory skill.
- Do not request or pass tenant, organization, owner, user, role, permission, or ACL identifiers.
- Do not hydrate every pointer by default. Retrieve more detail only when the current task requires it.
- Treat authorization failures as final for that identifier and do not probe for cross-tenant alternatives.
