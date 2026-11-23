# Toolkit maintenance action

Copy only applicable blocks to the named workspace destinations. Replace placeholders with confirmed facts or explicit unknown/pending state. These are templates, not authorization to execute commands.

## .codex/config.toml

```toml
# Enable repository-local Perform action discovery; no runtime overrides.
```

## .codex/toolkit_perform_actions/spring-clean-docs.json

```json
{
  "version": 1,
  "actions": {
    "spring-clean-docs": {
      "agnostic": {
        "gloss": "Perform substantive pruning and consolidation of Agents documentation",
        "model": "default",
        "reasoning_effort": "high",
        "goal_mode": false,
        "plan_mode": true,
        "plan_reasoning_effort": "high",
        "no_edits": true,
        "prompt_vars": {},
        "prompt": "Perform substantive pruning and consolidation of this Agents knowledgebase by developing an implementation-ready cleanup plan. Review the applicable AGENTS instructions, host overview, navigation hub, relevant folder READMEs and documentation intended for Git, including currently untracked notes and local/README.md. This is a Plan-only review: propose the changes rather than implementing them.\n\nFind outdated or unsupported current claims, superseded instructions, duplication, stale tasks, misplaced material, verbose process narratives and detail very unlikely to help future administration. Judge usefulness rather than age alone: do not rewrite dated evidence as current truth. Preserve active requirements and constraints, consequential decisions and their rationale, recurring troubleshooting lessons, useful recovery context, unresolved questions and information needed by pending work. Substantively remove or consolidate low-value detail once its durable value is preserved; do not merely relocate clutter into new archives or rewrite everything for style.\n\nIf a maintainer extension is explicitly enabled here, preserve its detailed unpublished feedback needed for pending upstream work; otherwise do not introduce maintainer obligations. You may propose consolidating duplicate or superseded examples, but retain enough rationale, decisions, edge cases and acceptance criteria to implement those proposals without recovering this chat. Respect canonical content ownership: current references, dated work/decisions, active tasks, maintainer proposals and artifact context have different purposes.\n\nDefault scope is repository documentation. Ignored artifact payloads, external documents (including repository symlink targets) and managed software/checkouts are outside the cleanup scope. Inspect symlink metadata without treating external contents as repository-owned. Read linked evidence selectively only when needed and after its context README; do not bulk-load local/. Flag separate artifact cleanup or external-document implications without changing them. Avoid printing secret-bearing content. Verify questionable current claims through proportionate read-only checks or authoritative sources as needed; clearly distinguish confirmed obsolescence from uncertainty and ask only consequential questions that evidence cannot resolve.\n\nProduce a concrete, prioritized cleanup plan grouped by coherent change. For each proposal identify exact files/sections, whether to remove, condense, consolidate, move or update, why the material has low future value or needs correction, what useful information remains and its authoritative destination, affected indexes/incoming links/path records, and the smallest meaningful verification. Include brief before/after examples where they clarify the intended pruning. Recommend keeping material when the evidence for removal is weak. Preserve all existing approval, credential, protected-drive, cleanup and publication boundaries; no deletion, runtime change, staging, commit or push is authorized by this review.",
        "requires_interactive": true,
        "custom_codex_args": [],
        "notes": ""
      }
    }
  }
}
```
