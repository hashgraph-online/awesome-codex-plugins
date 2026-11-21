# Worked contract: Suede Graph Flo XR

This is an illustrative application, not a claim of measured customer results.

## Input

A request supplies an absolute repo, a bounded multi-file change, protected paths and agentBudget=light. The host is Codex without Claude Workflow registration.

## Expected output

Read the orchestration contract, explain that the bundled runtime did not execute, and route to direct implementation with isolated file ownership and evidence. On a supported Claude Code macOS host, derive agentNamespace and helperDir from the actual install before launching.

## Failure and validation

A missing budget is missing input, not permission to infer standard. A failed sandbox probe halts before setup mutation; never rerun the acceptance command outside it. A returned run key requires the documented handoff file and actual existence check; no local result proves deployment.

## Inspect saved run evidence

A completed workflow assembles its handoff directly from the run record. It
does not spend an additional worker call or convert a held result into a pass.

From a developer checkout of the skill repository, save the **structured
workflow return value** as a private JSON artifact, then run:

```sh
npm run --silent audit:graph-flo -- /path/to/private-run.json
```

This offline check validates the evidence format and graph and budget
consistency. A valid report is not an execution receipt, permission to
resume a run, or a release approval. Do not publish raw run evidence.

## Reading a bundled Claude search halt

An empty search used to report `no safe graph winner` however it ended, so an
infrastructure flake and a genuine evidence conflict printed the same line. The
halt output now names which happened, and `haltDetail` carries the counts behind it:

| Reason | What it means |
|---|---|
| `every candidate lost its score to an agent failure` | No thought in the run was ever scored. Infrastructure, not evidence: offer an authorized rerun. |
| `no candidate reached Select` | The search emptied upstream for some other reason; read `graph.dropped`. |
| `every finalist lost its score before Select` | Finalists existed and were pruned as unscored. |
| `every finalist was pruned before Select` | Finalists were pruned for a non-score reason. |
| `every finalist carries a degraded or missing score` | Finalists reached Select without a valid score. |
| `every finalist failed deterministic plan eligibility` | Real rejection. `haltDetail.eligibilityRejections` lists every reason. |
| `no safe graph winner` | None of the above fits: read the graph. |

`haltDetail.infrastructureDegraded` is independent of the reason: both can be
true at once. Read the reason for what stopped Select and that flag for what
degraded the pool feeding it.

Score calls are read-only and idempotent, so a transport-level death is retried:
twice per call, capped run-wide at 5% of the agent ceiling, and refused entirely
once the remaining budget falls to the reserved floor (20% of the ceiling). A
malformed score is never retried: the schema is enforced at the tool layer, so
an invalid score is a judgment to keep, not a connection to redial. Every
attempt and every refused retry lands in `graph.scoreRetries`, and
`scoreReliability` rides out in the result on every run, halted or not: a flake
that costs two finalists still degrades a run that goes on to ship.

Claude's registered agent profiles enforce tool separation: local readers have
no shell, write, or web tools; public-web readers have no local-file or shell
tools; patch authors have no mutation tools; and appliers/verifiers have only
Bash plus structured output. Patch authors return unified diffs, one clamped
applier applies them, and a separately budget-reserved clamped verifier compares
the exact path set and diff digest immediately after every Build or Fix Apply,
before any reader or Gate call. Patch validation rejects symlinks, gitlinks,
binary patches, renames, copies, and file-type transitions before Apply. Gate
runs only allowlisted local validation
commands under macOS `sandbox-exec`, with no network, host reads limited to
runtime/system roots, the worktree, its `.git` common directory derived again
inside the exact Gate clamp, and the run's private temp root. The model-reported
common directory is never interpolated into sandbox permissions. Writes are limited to known generated artifacts
and that private temp root. The allowlist includes bounded project-local checks
for Node, Python, Go, Rust, Make, Swift Package Manager, Xcode simulator builds
with derived data under the private temp root, and offline Gradle validation.
Nested module `build` roots are derived only from selected files under that
module's `src` tree and are rejected if a symlink or realpath can escape the
worktree. A second diff attestation runs after Gate and hashes
the binary Git diff plus every reported file's mode, size, and bytes, including
untracked additions.

Gate removes credential-like and interpreter-injection environment variables,
then redirects home, temporary, and cache paths before an acceptance command
starts. If a check depends on removed credentials, report it as unverified;
never rerun it outside the sandbox merely to obtain a pass.

A transport failure with no required Research, Gaps, Review, Gate, or Release
report halts instead of counting as clean evidence. An explicit empty findings
array from a responding reviewer is a valid report.

A successfully applied blocker patch is not treated as semantically cleared.
The original blocker remains in `fixedBlockersPendingVerification`. The Gate
attempt records its exact command set and reported output, but it cannot prove
those commands ran because the Workflow API exposes no trusted required-tool
execution receipt. The workflow therefore sets `claimedPassed` from the agent
report, forces `passed:false`, sets `gateVerified:false`, and keeps the verdict
and handoff status at `hold`. Only a trusted outer runner with immutable
execution receipts can promote that evidence.

These controls have a precise trust boundary. `bashCommandClamp` constrains a
Bash command when an agent invokes it; Claude Workflow does not provide a
required-tool-call receipt, so a structured verifier response remains a model
attestation rather than cryptographic proof that Bash ran. Likewise,
`authority`, `allowedRepo`, `allowedFiles`, and `allowedCommands` are audit
metadata, not filesystem permissions. Local reader tools are separated from web
tools but are not path-sandboxed by the Workflow API. Report these facts in any
security-sensitive handoff and do not describe the result as host-certified.
