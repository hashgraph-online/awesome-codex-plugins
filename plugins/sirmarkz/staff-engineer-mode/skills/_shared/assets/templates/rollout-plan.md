# Rollout Plan

## Change

## Source Artifacts

- Deploy workflow:
- Deploy workflow outputs to capture:
  - Artifact identity:
  - Rollout unit identifier:
  - Health gate result:
  - Abort or pause control:
  - Automatic rollout queue pause:
  - Rollback target:
- Metric definitions:
- Artifact or change set:

## Blast Radius

## Rollout Stages

- Preflight:
  - Concurrent canary/config interaction check:
  - Restart or recovery under representative load:
- Small first rollout:
- Next exposure step:

## Compatibility Plan

| Surface | Old/New Compatibility | Skew Risk | Verification |
| --- | --- | --- | --- |

## Feature Flag Or Config Lifecycle

| Temporary Control | Expiry | Removal Condition | Owner |
| --- | --- | --- | --- |

## Canary Metrics

Pull metric names, thresholds, baseline windows, observation windows, and
minimum sample requirements directly from the file or files named in "Metric
definitions:" above. Record the source file and signal name under each
sub-bullet. If no metric definitions file exists yet, fill in the sub-bullets
manually and document that file path once it is created.

- Baseline window:
- Observation window:
- Minimum signal:
  - Sample count or synthetic/manual fallback:
  - Owner who verifies signal quality:
- Metrics scoped to the first rollout slice:
  - User-visible availability or success:
    - Source (metric definitions file and signal name):
    - Stop threshold:
    - Owner:
  - Latency or freshness:
    - Source (metric definitions file and signal name):
    - Stop threshold:
    - Owner:
  - Saturation or backlog:
    - Source (metric definitions file and signal name):
    - Stop threshold:
    - Owner:
  - Correctness invariant:
    - Source (metric definitions file and signal name):
    - Stop threshold:
    - Owner:
  - Business or safety guardrail:
    - Source (metric definitions file and signal name):
    - Stop threshold:
    - Owner:

## Stop Criteria

Before the rollout begins, record the blast radius for each stage: rollout unit
identifier, affected user population and system scope, and maximum impact if
the change fails. Do not begin a stage without these three fields recorded.

For each stop condition below, fill in the owner, exact threshold, abort action,
and rollback action before first exposure. The owner must have authority to halt
promotion without an additional approval step.

| Stop condition | Minimum signal | Threshold | Owner | Abort action | Rollback action |
| --- | --- | --- | --- | --- | --- |
| Canary metric breach | Samples, probes, or manual checks declared in Canary Metrics | Per-signal stop threshold from metric definitions |  | Pause promotion and freeze next exposure step | Roll back the exposed slice to the rollback target or trigger the declared forward-fix path |
| Deploy workflow health gate failure | Workflow result for artifact identity and rollout unit | Any failed, missing, or unverifiable health gate for the exposed slice |  | Abort current stage and block promotion of the rejected artifact | Restore the last known-good artifact or change set for the rollout unit |
| Telemetry quality invalid or unverifiable | Telemetry present and validated against metric definitions | Missing, malformed, unscopeable, or zero samples when the slice is active |  | Hold rollout; do not treat missing data as healthy | Roll back if user impact cannot be ruled out within the response window |
| Minimum signal not reached | Declared sample count or approved synthetic/manual fallback | Minimum signal not reached within the observation window |  | Extend bake time once if fallback is declared; otherwise stop | Keep rollback ready; roll back if impact appears or signal remains unavailable |
| Rollback cannot start immediately | Rollback target, command/procedure, and operator ready | Target unavailable or cannot start within the declared response window |  | Stop before exposure or pause current stage | Use forward-fix only with explicit confirmation and a kill switch or disable path |
| Artifact or rollout unit unidentifiable | Workflow emits artifact identity and rollout unit identifier | Either identity is absent, ambiguous, or mismatched |  | Stop before next promotion step | Roll back only the identified affected unit; if not identifiable, halt promotion globally |

Stop the small first rollout when **any** of the following conditions is met.
Every condition applies to the exposed slice only; fleet-aggregate signals must
not substitute for slice-scoped signals.

- **Canary metric breach (slice-scoped).** Any signal named in the metric
  definitions files listed in Source Artifacts above, scoped to the exposed
  slice, crosses the threshold declared for that signal within the declared
  observation window. Each canary threshold must be set stricter than the
  corresponding internal alert threshold so that the stop fires before the
  alert does.
- **Deploy workflow health gate failure.** The deploy workflow listed in Source
  Artifacts above emits a health gate failure or reports the rollout unit as
  unhealthy for the exposed slice.
- **Telemetry quality invalid or unverifiable.** Telemetry for the exposed slice
  is absent, structurally malformed, or cannot be verified against the metric
  definitions files. Zero samples when the slice is known to be active is a
  stop condition, not a healthy signal.
- **Minimum signal not reached within the observation window.** The exposed
  slice has not produced the minimum sample count declared in the metric
  definitions files within the observation window. Extend bake time or use
  synthetic probes as the declared fallback; stop and investigate if neither is
  available.
- **Rollback cannot be started immediately.** The rollback target - the artifact
  or change set from the point when the harmful change entered, not necessarily
  the immediately previous release - is unavailable or cannot be started within
  the response window declared below.
- **Affected artifact and rollout unit unidentifiable.** The deploy workflow
  output does not emit both the artifact identity and the rollout unit
  identifier. Stop before the next promotion step if either is absent.

**On any stop condition:** pause promotion immediately. The rejected artifact
must not be reintroduced into any slice until: (1) the root cause is identified
and resolved, (2) the metric source, rollback target, and next exposure
threshold are updated with the investigation result, and (3) the blast-radius
declaration for the next stage is recorded.

**Rollback classification (declare before first exposure):**
- *Rollback safe:* change is stateless, flag-gated, or purely additive with no
  schema, data-format, or client-contract dependency. Rollback restores the
  prior artifact without additional remediation.
- *Rollback dangerous / forward-fix required:* a schema migration has run, a
  data format changed and new data is being written, external clients depend on
  the new contract, a stateful workflow is in flight, or a cache holds data in
  the new format. Pre-define a forward-fix path and obtain explicit confirmation
  before first exposure.

## Rollback

- Rollback target:
- New-traffic verification:
- In-flight session/workflow repair:
- Promotion pause:
- Incident-mode automatic rollout queue pause:
- Promotion re-enable criteria:
- Re-enable criteria:

## Abort Cleanup

| State Item | Type | Cleanup Action | Promotion Blocker? | Owner | Verification |
| --- | --- | --- | --- | --- | --- |

## Cleanup

| Cleanup Item | Owner | Trigger | Verification | Due |
| --- | --- | --- | --- | --- |

## Launch Watch

| Watch Signal | Source | Threshold | Owner | Action |
| --- | --- | --- | --- | --- |
