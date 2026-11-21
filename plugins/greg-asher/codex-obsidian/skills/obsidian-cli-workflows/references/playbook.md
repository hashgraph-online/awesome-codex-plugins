# Obsidian CLI Workflows Playbook

Use this playbook to run named workflow IDs through preview/apply orchestration while preserving domain-skill ownership.

## Invocation shape

```text
workflow_id=<command-id> mode=preview|apply vault=<optional-vault> output=inline|note|json
```

Defaults:
- `mode=preview`
- `output=inline`

## Cited answers, related notes, and handoffs

After explicitly selecting `$obsidian-cli-workflows`, ask in plain language. For example:

- In the Work vault under Projects/Atlas, what did we decide about authentication? Include conflicting evidence and open questions. Exclude Projects/Atlas/Private.
- Find notes related to Projects/Atlas/Decision.md in Work and show what makes each relevant.
- Prepare an Atlas handoff from Work, scoped to Projects/Atlas and tagged #atlas. Preview saving it to Handoffs/Atlas.md.

For a named call that runs retrieval and returns structured evidence without writing:

```text
workflow_id=research.pack mode=apply output=json vault=Work view=answer query="What did we decide about authentication?" scope_path=Projects/Atlas
```

Use [cited retrieval](cited-retrieval.md) for both workflows. Inline and JSON execution are read-only. A save preview includes the actual draft and exact destination. Apply only matching approved changes through the core authoring procedure.

## Preview behavior requirements

Preview must return:
- workflow summary and intent
- required and optional inputs
- ordered step plan with delegated skill per step
- target summary and ambiguity checks
- risk level and apply prerequisites

## Apply behavior requirements

Apply must:
- require explicit confirmation for medium/high risk workflows
- enforce target matching between preview and apply
- execute only approved matching steps
- consume the core authoring/revision contract for every note write, including optional saved reports; retain vault identity/root and path, before/expected state, and per-step verification
- reuse existing matching approval; reconcile uncertain effects before retries and stop dependent steps on conflict
- summarize mutations and side effects clearly
- stop on required capability blockers; for cited retrieval, report unavailable optional evidence and use supported scoped reads

## Global orchestration guardrails

1. Keep direct command execution in domain-skill contracts.
2. Fail closed on ambiguous note/base/workspace targets.
3. Preserve exact-path mutation policies in `obsidian-official-cli`.
4. Preserve capability gating for publish workflows.
5. Preserve runtime-admin/devtools/sync-publish/workspace boundaries.

## Publish capability probe

For `publish.release_gate`:
1. Run `obsidian help publish:status` through delegated sync/publish skill policy.
2. If probe shows unsupported publish commands, return blocker and stop.
3. Only if supported, continue with `publish:status`, `publish:list`, and requested publish mutation commands.

## Delegation map

- `obsidian-official-cli`: note/tasks/properties/history/template/link workflows
- `obsidian-cli-bases-and-bookmarks`: bases and bookmark workflows
- `obsidian-cli-runtime-admin`: runtime plugin/theme/snippet/command/hotkey operations
- `obsidian-cli-devtools`: diagnostics and screenshot/runtime inspection
- `obsidian-cli-sync-and-publish`: sync and publish (capability-gated)
- `obsidian-cli-workspace-and-navigation`: vault/workspace/tab/navigation utilities
