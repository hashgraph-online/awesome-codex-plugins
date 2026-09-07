# Deploy Orchestration Contract

This contract is the entry-visible boundary for the `sealos-deploy` composite skill. The phase modules remain authoritative for commands and provider-specific mechanics. Each phase returns one typed handoff envelope, keeps evidence sanitized, and names the next owner before the following phase starts.

## Phase Order and Ownership

| Phase | Owner | Input | Output and terminal rule |
| --- | --- | --- | --- |
| Preflight | `sealos-deploy/modules/preflight.md` | request, local path or GitHub URL | authenticated workspace, tool canaries, scoped kubeconfig, or `stopped`/`error` |
| Eligibility | `cloud-native-readiness` and `workload-eligibility.mjs` | source tree and bounded detection evidence | eligible workload handoff, or `stopped` before scoring/build |
| Template fast path | `detect-template.mjs` | source identity and config | validated materialized template, or a bounded miss that returns to assessment |
| Mode detection | `sealos-deploy/modules/pipeline.md` | validated state hint and live identity | `DEPLOY` or `UPDATE`, or `stopped` reconciliation |
| Assess and detect | `cloud-native-readiness`, `score-model.mjs`, `detect-image.mjs` | eligibility handoff | `.sealos/analysis.json` and image decision |
| Dockerfile/build or reuse | `dockerfile-skill`, `build-push.mjs` | analysis and source evidence | `.sealos/build/build-result.json` or verified image reuse |
| Template/configure | `docker-to-sealos`, `deploy-template.mjs` | analysis, image, config | `.sealos/template/index.yaml` and validated delivery evidence |
| Deploy or update | `deploy-template.mjs` or scoped kubectl helpers | validated template/state and explicit mutation confirmation | live App identity and rollout evidence, or `stopped`/`error` |
| Runtime Truth | `runtime-truth.md` and read-only helpers | live identity and selected workload matrix | sanitized URL, network, auth, logs, events, readiness, and footprint evidence |
| State and handoff | `sealos-deploy` | successful Runtime Truth report | validated `.sealos/state.json`, terminal `success`, and optional Canvas observation tuple |

The optional template fast path can skip assessment, image detection, Dockerfile generation, and template conversion only after its materialized artifact passes the same artifact validators. No shortcut bypasses preflight, eligibility, mode resolution, deploy/update confirmation, or Runtime Truth.

## Typed Handoff Envelope

Every boundary uses [`../schemas/deploy-handoff.schema.json`](../schemas/deploy-handoff.schema.json). The stable fields are:

- `source`: the module or helper that produced the report.
- `owner`: the phase responsible for correcting a failed precondition.
- `preconditions`: bounded facts required before the next action.
- `inputArtifact`: the repository-relative artifact or live identity consumed once.
- `allowedAction`: the exact read, build, deploy, update, or handoff operation permitted.
- `failureReturn`: the safe `stopped` or `error` result, reason code, and recovery owner.
- `responseOwner`: the module that receives the next action or failure.
- `evidence`: allowlisted observations with timestamps and redaction status.
- `redaction`: an explicit `complete` or `not_applicable` result plus sanitized field names.
- `terminalState`: `success`, `stopped`, or `error`, with a reason code and evidence references.
- `artifactPaths`: repository-relative paths owned by this phase.
- `nextAction`: the single next action or `none` for a terminal success.

Credentials, kubeconfig contents, cookies, bearer tokens, Secret values, environment values, and complete connection strings never enter an envelope. Evidence stores field names, status codes, resource identities, hashes, and sanitized excerpts.

## Artifact Inventory

| Artifact | Owner | Read/write boundary |
| --- | --- | --- |
| `.sealos/config.json` | request/preflight | optional user overrides; validate before read |
| `.sealos/analysis.json` | assess/detect | regenerated analysis snapshot |
| `.sealos/build/build-result.json` | build/reuse | build outcome and image reference |
| `.sealos/template-match.json` | template fast path | deterministic match decision |
| `.sealos/template/index.yaml` | template/configure | final sanitized template |
| `.sealos/delivery-manifest.json` | deploy response | allowlisted API result and resource identity |
| `.sealos/runtime-truth.json` | Runtime Truth | sanitized live evidence, written before state |
| `.sealos/state.json` | state/handoff | validated resume hint plus verified last deploy |
| `~/.sealos/logs/deploy-*.log` | deploy entry | one append-only request log |

Each artifact is validated against its schema or helper contract before downstream trust. A missing, malformed, stale, or mismatched artifact returns `stopped` with the owning phase and reconciliation action. A phase does not rescan the source to replace a failed artifact handoff.

## DEPLOY, UPDATE, and Terminal States

`DEPLOY` creates a distinct instance after eligibility, template, confirmation, and live target checks pass. `UPDATE` requires a validated state record plus a live App/Deployment whose app name, namespace, image, URL, and readiness agree with that record. A missing or unusable kubectl context leaves the request `stopped` for reconciliation and never mutates a guessed target. Update rollback keeps the previous image and state, records rollout and Runtime Truth evidence, and returns `error` when recovery evidence is incomplete.

`success` requires actual App URL/live identity, public route and port agreement when applicable, root and configured-route smoke, required setup or login proof, recent logs and Events, workload convergence, and a complete footprint. Deploy-only output is `stopped` with `runtime_pending` until Runtime Truth completes. `stopped` carries the safe next action for unsupported eligibility, missing auth/tool, unresolved configuration, ambiguous state, or unconfirmed mutation/cleanup. `error` carries the failed owner, reason, sanitized evidence, and recovery action.

## Canvas Boundary

After verified success, deploy may hand Canvas a read-only observation tuple containing sanitized `state.json`, `runtime-truth.json`, the app/namespace identity, and evidence paths. Canvas may inspect topology and status. Deploy owns mutations, cleanup, rollback, and state; Canvas never deploys, updates, deletes, or repairs resources. A missing or unreadable runtime/state handoff keeps Canvas stopped with a diagnostic.

## Main and Preview Branch Boundary

The main-like workflow in this repository includes OAuth/authentication, Template API or scoped kubectl deployment, UPDATE, Runtime Truth, rollback, cleanup, and the Canvas handoff. The branch named `brain-deploy-preview` remains prepare-only: assessment, optional Railpack evidence, Dockerfile preparation, `build-request.json`, sandbox Kaniko or image reuse, template generation, and `delivery-manifest.json`. That branch keeps its own Kaniko flow and excludes OAuth deployment, UPDATE, runtime verification, and Canvas. This contract records the boundary so shared documentation cannot import full-deploy behavior into the preview branch.
