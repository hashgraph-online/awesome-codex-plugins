---
name: runtime-evidence-and-tracing
description: Use when connecting observed behavior, logs, metrics, request IDs, run IDs, screenshots, traces, external dependency results, or artifacts into a runtime evidence loop.
---

# Runtime Evidence And Tracing

## Overview

Make runtime validation auditable by tying observed behavior to runtime evidence through stable IDs and artifacts.

Agents should not only say they tested something; they should leave run IDs, request IDs, logs, screenshots, interaction records, or traces. For shared harness terms, see `../../references/harness-patterns.md`; when evidence surfaces are absent, use `references/build-when-missing.md`. For neutral runtime profiles and redaction policy, see `references/runtime-profile-policy.md`.

## When To Use

- The user mentions interactive validation, runtime validation, request IDs, traces, logs, metrics, or artifacts.
- A production or test-environment issue must be traced from observed behavior to runtime evidence.
- A flow with external dependencies needs classification as code failure, dependency blocker, environment issue, or data problem.

## Inputs Needed

- Target flow, entry action, command, or interface.
- Existing logging, request wrapper, headers, and observability endpoints.
- Artifact directory and run ID naming preference.

## Execution Order

- First: Find the request entrypoint and existing request/log/trace propagation points.
- Then: Design run IDs, request IDs, artifact bundles, and collection commands.
- Finally: Output the evidence contract and validation path, including fallback and blocker classification.

## Step-by-Step Process

1. Search request wrappers, service entrypoints, logs, metrics, and trace scripts.
2. Confirm whether the calling surface can generate or propagate `X-Request-ID` and `X-Harness-Run-ID`.
3. If no evidence contract exists, bootstrap the minimum run artifact contract from `references/build-when-missing.md`.
4. Design `artifacts/runs/<run_id>/` with manifest, summary, logs, network, screenshots, and trace files.
5. Define the collection order for the target flow: start, authenticate if needed, operate, wait, read artifacts, and attribute the result.
6. Define blocker categories: code regression, environment unavailable, external dependency unavailable, data missing, and not evaluable.
7. Explain how PRs or ledgers should reference artifacts without committing large temporary files.

## Checks

- Propagation: request ID and run ID remain searchable across caller, service, job, and external dependency evidence.
- Artifact: the directory includes manifest, summary, and reproducible commands.
- Evidence: screenshots, console, network, logs, and metrics cover the failure boundary.
- Attribution: external dependency or environment blockers are not reported as product-quality failures.
- Privacy: artifacts do not contain tokens, phone numbers, real secrets, or sensitive payloads.

## Output Format

```markdown
# Runtime Evidence And Tracing

## Detected Mapping
- runtime-evidence:
- validation:
- ledger:

## ID Contract
- Run ID:
- Request ID:
- Header propagation:

## Artifact Bundle
-

## Collection Flow
1.
2.
3.

## Failure Classification
-

## PR / Ledger Reference
-
```

## Common Mistakes

- Keeping only screenshots with no request ID or runtime evidence.
- Creating traces only in one layer, leaving observed failures disconnected.
- Treating external account or quota issues as product-quality failures.
- Committing large artifacts instead of referencing paths and summaries.

## Example Prompts

- "Connect interactive validation to request IDs."
- "Design artifacts/runs evidence for this runtime workflow."
- "How should this failure be classified: code, environment, or external blocker?"
