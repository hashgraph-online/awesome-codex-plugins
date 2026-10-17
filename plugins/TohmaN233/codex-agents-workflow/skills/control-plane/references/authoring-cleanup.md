# Finish authoring and remove temporary Workflows

Read when generation finishes or the user requests cleanup of superseded generation Drafts. This is part of authoring completion, using the existing recoverable deletion API.

## Record the task-owned artifacts

Maintain a compact ledger of the exact Workflow IDs created for this task, their source provenance, current revision, authoring Run and role as candidate or superseded Draft. Prefer one Draft and one Run through targeted repairs. Record a necessary replacement explicitly; do not infer ownership from a name, prefix, tag, timestamp or source-family similarity. Existing user Workflows and unrelated Roles are outside this ledger.

## Identify the retained result

Retain exactly the final task Workflow after all required deterministic checks and the complete pinned independent review pass without unresolved findings, the Host records acceptance under the Run-pinned completion policy, and application produces a self-contained executable graph with its complete Workflow-owned resources. Verify the applied revision and resource closure. An import scaffold with `validation.valid: true`, a filename containing "final", or a review of another proposal is insufficient.

Automatic authoring finishes only after cleanup, Ready publication, enablement and `launch_ready` validation. These are shared Host responsibilities for Skill2Workflow and Build Workflow. An explicitly selected manual policy retains an editable Draft. Do not require optional artifact-only dependencies for a route that does not use them.

While a required manual acceptance or a blocked Host completion is pending, retain the exact candidate and evidence needed to resume. State the concrete blocker. A cleanup failure must not publish or enable the result; retry the recorded transaction instead of creating another Workflow or invoking models again.

Preflight the actual deployed resources, conversion certificate and future Ready graph before removing private evidence, including retries of a pending cleanup transaction. A succeeded automatic authoring Run with incomplete completion remains protected from generic age-based Run-history cleanup; the exact authoring cleanup transaction owns its removal. A readiness blocker preserves that Run and its workspace so repairs can resume without another model call.

## Clean and verify

1. After successful application, check the Host's authoring cleanup result. The Host removes eligible private authoring history, managed workspaces, temporary job Workflows and terminal authoring Runs from its exact ownership ledger through the journaled cleanup path. If it fails, report the exact failed stage and use the supported transaction retry. Do not impersonate human acceptance, directly purge storage or fabricate a successful cleanup receipt.
2. Separately clean all superseded task-owned library Drafts in the ledger. The Host's internal cleanup does not delete separately imported library Workflows. Read each exact ID with `workflow_read`; verify current provenance and revision, that it remains the superseded task Draft, and that no unfinished work still needs it. Preserve the retained result, its supporting assets, concurrent edits, system authoring Workflows, user Workflows and Roles.
3. Call `workflow_delete` sequentially with that ID and its exact current `expected_revision`. This moves the Pack to recoverable trash. Do not permanently purge it or create extra backup Workflows. A revision conflict or failed deletion remains visible; reread and reassess before retrying, never substitute a different Workflow.
4. Verify the library afterwards: every selected obsolete ID is absent, the retained result still has the expected revision and resources, and unrelated entries are unchanged. Keep a compact cleanup receipt with exact IDs, revisions and outcomes. Report a remaining ID and failed operation if cleanup is incomplete; do not claim "only the final result remains" until this verification passes.

## Scope of cleanup

Clean temporary Workflow library entries, not original Skills, user task outputs, required scripts/resources, review evidence needed for pending acceptance, or unresolved live effects. Run-history retention follows the Host's separate policy. Do not manually delete Runs to bypass that policy. Once accepted application has completed, keep the final deliverable and a concise verification receipt; redundant generation Workflows must no longer appear as active library entries.
