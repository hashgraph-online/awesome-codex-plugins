# Build When Missing

Use this when runtime validation is not auditable. Use generic run artifacts, request IDs, interaction evidence, trace scripts, log queries, and external-blocker classification.

## Equivalent Artifacts

- Existing trace exports, test reports, monitoring links, smoke-test artifacts, or run logs may already satisfy the runtime-evidence role.
- Record the chosen artifacts under `Detected Mapping` before creating default run directories.
- Use `templates/runtime-evidence-summary.md` only when no equivalent runtime evidence summary exists.

## Minimum Files

- `artifacts/runs/<run_id>/manifest.json` or an explicitly mapped equivalent manifest.
- `artifacts/runs/<run_id>/summary.md` or a mapped human-readable result and classification summary.
- `scripts/harness/trace_run.py`, `scripts/harness/doctor.py`, or a mapped collection command.
- A request/run ID policy in `RELIABILITY.md`, README, or a runbook.

## Bootstrap Steps

1. Map existing runtime reports, logs, trace exports, and collection commands.
2. Define run ID and request ID names only where the mapped runtime surface can carry them.
3. Create a run directory structure only when no equivalent artifact bundle exists.
4. Add a minimal collection command that writes manifest and summary even when deeper logs are unavailable.
5. Define failure classification: code regression, environment unavailable, external dependency blocker, data missing, not evaluable.
6. Require PR or ledger summaries to reference artifact path and classification.

## Validation

- Run one smoke collection and confirm manifest plus summary are written.
- Confirm the same run ID appears in available caller, service, worker, or external dependency evidence.
- Confirm artifacts are referenced but not committed when large or sensitive.

## Do Not Include

- Tokens, real user identifiers, contact details, dependency keys, or sensitive payloads.
- Claims of runtime validation without evidence of the actual path used.
- Large binary artifacts in normal source commits unless the repository explicitly allows them.
