# Shared Templates

These templates scaffold artifacts for routed specialists. Specialist files
define required outputs. Keep templates and this index aligned with those
contracts.

## Source Of Truth

| Item | Source Of Truth | Update Trigger |
| --- | --- | --- |
| Specialist behavior | `specialists/<specialist-name>.md` | Required outputs, workflow, or checks change. |
| Shared template shape | File listed in the template index below | Artifact fields or review evidence changes. |
| Template ownership | This file | A template is added, removed, renamed, or reassigned. |

Use one canonical template for each reusable artifact. Remove duplicates or
mark them as shared use in this index.

## Template Index

| Template | Owning Specialist Or Shared Use | Artifact | Maintenance Notes |
| --- | --- | --- | --- |
| `accessibility-release-check.md` | `accessibility-gates` | Accessibility release check | Keep conformance target, journey blockers, retest evidence, and release decision fields aligned. |
| `adr.md` | `architecture-decisions` | Architecture decision record | Keep goals/non-goals, constraints, responsibility, reversibility cost, consequences, and reconsideration trigger visible. |
| `agent-pr-review.md` | `agent-pr-review` | Pre-merge review record | Keep intent match, verification evidence, and residual risks visible. |
| `ai-coding-instructions.md` | `ai-coding-governance` | Agent repository rules | Keep protected paths, acceptance checks, ownership, prohibited record fields, retention/disposal, integrity, and volume bounds visible. |
| `api-contract.md` | `api-design-and-compatibility` | API contract | Keep compatibility, same-contract consumer transition, request-surface parity, filtering, item correlation, polling avoidance, error/idempotency, result metadata, and partial-failure semantics aligned. |
| `architecture-review.md` | `architecture-decisions` | Architecture review | Keep options, constraints, tradeoffs, and revisit conditions visible. |
| `backup-recovery-plan.md` | `backup-and-recovery` | Backup and restore plan | Keep RTO/RPO, backup creation-path dependencies, restore evidence, alternate restore targets, client-visible reference repair, restore capacity/quota guardrails, owner, and recovery gaps visible. |
| `bounded-context-map.md` | `architecture-decisions` | Boundary map | Keep ownership, data boundary, dependency, and change trigger fields aligned. |
| `cache-derived-data-plan.md` | `caching-and-derived-data` | Cache and derived data plan | Keep canonical identity, freshness, invalidation, miss behavior, refresh spread, and repair path visible. |
| `cert-lifecycle-plan.md` | `cryptography-and-key-lifecycle` | Certificate and key lifecycle plan | Keep cryptographic material use, activate/overlap/old-decrypt-or-verify/retire/destroy lifecycle, issuance capacity, persisted/queued-state rewrite or reconciliation, rollback or roll-forward limits, emergency revocation, confidentiality exposure, and signature validity aligned. |
| `check-before-moving-on.md` | Shared use | Evidence checkpoint | Keep command, condition, artifact path, owner, checked time, actual result, failure response, and limitation fields reusable. |
| `client-application-security-review.md` | `client-application-security` | Client application security review | Keep trust boundaries, client sinks, local storage, public versus confidential credentials, transport, entry-point hardening, tamper posture, and negative tests visible. |
| `code-readability-for-agents.md` | `code-readability-for-agents` | Code readability review | Keep representative discovery trials, selected authority and verification paths, wrong-file scorecard, canonical paths, misleading names, and search risks visible. |
| `configuration-safety-review.md` | `configuration-and-automation-safety` | Configuration safety review | Keep record safety, bulk row identity/skips/aggregate limits, validation/quarantine, preview, runtime override cleanup, application state, blast radius, recovery protection, and operational levers aligned. |
| `container-runtime-and-orchestration.md` | `container-runtime-and-orchestration` | Runtime posture spec | Keep measured demand, scheduling requests, CPU/memory limit decisions, pressure eviction, fleet floors, drain/probe semantics, and disruption verification visible. |
| `cost-reliability-review.md` | `cost-aware-reliability` | Cost and reliability review | Keep reliability benefit, cost driver, owner, and rollback or cleanup evidence visible. |
| `data-contract.md` | `data-contracts` | Producer and consumer data contract | Keep field meaning, compatibility, consumer checks, and deprecation path aligned. |
| `data-lineage-and-provenance.md` | `data-lineage-and-provenance` | Data lineage and provenance plan | Keep source-of-record, derivation graph, downstream dependencies, boundary-crossing lineage, purpose tags, recompute procedure, and audit record visible. |
| `data-pipeline-reliability.md` | `data-pipeline-reliability` | Data pipeline reliability plan | Keep freshness, validation, lineage, replay, critical-path dependencies, backlog recovery, fairness/rate limits, shared-resource, shed, and recovery fields visible. |
| `database-change-plan.md` | `database-operations` | Database change plan | Keep authoritative state, copy/write-consistency boundary, mixed-version behavior, reconciliation, rollback point, lock risk, throttling, query evidence, and ownership aligned. |
| `dependency-hygiene-plan.md` | `dependency-and-code-hygiene` | Dependency hygiene plan | Keep inventory, batch plan, lockfile safety, and rollback evidence visible. |
| `dependency-matrix.md` | `dependency-resilience` | Dependency resilience matrix | Keep timeout, retry, idempotency, fallback, queue/overload, and terminal-failure disposition aligned. |
| `dev-environment-parity-matrix.md` | `dev-environment-parity` | Environment parity matrix | Keep drift dimensions, safe production evidence, allowed divergence, owner, and action trigger visible. |
| `distributed-data-consistency-plan.md` | `distributed-data-and-consistency` | Distributed data consistency plan | Keep consistency and conflict strategy, replica membership, acknowledgement/durability, quorum assumptions, sloppy/hinted behavior, repair, and verification visible. |
| `documentation-lifecycle.md` | `documentation-lifecycle` | Documentation inventory and freshness plan | Keep primary/secondary documentation modes, operational/architectural tag, source of truth, verification cadence, staleness, and archive rule visible. |
| `edge-traffic-defense-plan.md` | `edge-traffic-and-ddos-defense` | Edge traffic defense plan | Keep origin protection, limit behavior, traffic steering, recovery drain behavior, customer impact, and abort path visible. |
| `engineering-control-evidence-map.md` | `engineering-control-evidence` | Engineering control evidence map | Keep control, evidence, owner, expiry, exception, collection path, and record-safety handling aligned. |
| `eval-harness-spec.md` | `llm-evaluation` | Evaluation harness spec | Keep eval unit, split-access adversarial record, contamination controls, baseline/candidate samples and uncertainty, record safety, thresholds, and triage visible. |
| `event-workflow-contract.md` | `event-workflows` | Event workflow contract | Keep trigger compatibility, replay, ordering, duplicate handling, terminal-failure/quarantine decision, guarantee boundary, side effects, and owner visible. |
| `experiment-guardrail-plan.md` | `experimentation-and-metric-guardrails` | Experiment guardrail plan | Keep decision estimand, assignment-wide impact, valid triggering/complement/translation, MDE, sample size, power, multiplicity control, and guardrails visible. |
| `feature-flag-lifecycle.md` | `feature-flag-lifecycle` | Feature flag lifecycle record | Keep temporary removal expiry distinct from long-lived review, plus owner, fallback, retirement, cleanup, and removal evidence visible. |
| `high-availability-design.md` | `high-availability-design` | High-availability design | Keep fault domains, replica/quorum placement, static capacity, DNS/name resolution, cache/refill load, shared dependencies, operating-envelope mismatches, protective-mode behavior, gray-failure health thresholds, health/control-loop coupling, failover evidence, and return-to-normal fields visible. |
| `identity-and-secrets-review.md` | `identity-and-secrets` | Identity and secrets review | Keep access scope, propagation/freshness/capacity, signer/verifier compatibility, secret lifecycle and deletion safety, protected audit records, break-glass, and traceability aligned. |
| `incident-postmortem.md` | `incident-response-and-postmortems` | Incident timeline and follow-up record | Keep safe timeline, next update time, strategy authority, complete checkpoints, evidence-supported contributing factors, owners, and verified actions visible. |
| `infrastructure-policy-as-code-plan.md` | `infrastructure-and-policy-as-code` | Desired-state and policy plan | Keep secure baselines, drift detection, policy checks, reconciliation, exception, and rollback visible. |
| `input-validation-and-injection-defense.md` | `input-validation-and-injection-defense` | Input validation and injection defense plan | Keep source-to-sink controls, upload count/aggregate and parser-work limits, quarantine, atomic promotion, safe serving, negative tests, and residual risk visible. |
| `internal-service-networking-plan.md` | `internal-service-networking` | Service networking plan | Keep service routing, per-edge peer identity matching, dual-acceptance expiry, retired-identity negative evidence, rollback boundary and procedure, locality, route-state/change safety, and the conditional physical/public operations module visible. |
| `llm-application-security-review.md` | `llm-application-security` | LLM application security review | Keep trust boundaries, tool/data controls, risk-based moderation applicability, prompt confidentiality, red-team scope/skip, severity/retest, protected records, and residual risk aligned. |
| `llm-serving-cost-latency.md` | `llm-serving-cost-and-latency` | LLM serving cost and latency plan | Keep token/latency budgets, authorization-aware cache behavior, safe cost-attribution identifiers and prohibited fields, degradation, and ownership visible. |
| `migration-deprecation-plan.md` | `migration-and-deprecation` | Migration and deprecation plan | Keep caller inventory, traffic-class capacity/backlog validation, migration completion evidence, dependency optionality, reversible domain/DNS transition, no-new-usage checks, rollback, disable-and-observe evidence, and a terminal handoff inventory covering code, config, data, credentials, names, infrastructure, pipelines, monitoring, runbooks, costs, and resurrection paths. |
| `ml-reliability-readiness.md` | `ml-reliability-and-evaluation` | ML reliability readiness plan | Keep eval coverage, skew checks, serving control state, routing-control-plane checks, drift checks, rollback, and production-risk fields aligned. |
| `mobile-release-plan.md` | `mobile-release-engineering` | Mobile release plan | Keep calibrated baseline, sample/confidence, impact rationale, recalibration trigger, staged rollout, client exposure, halt criteria, telemetry, and recovery visible. |
| `multi-region-and-data-residency.md` | `multi-region-and-data-residency` | Multi-region and residency plan | Keep topology, residency, replication-aware affinity, recoverable-point/RPO evidence, missing/divergent-write reconciliation, routing, evacuation, and rehearsal visible. |
| `observability-alerting-spec.md` | `observability-and-alerting` | Observability and alerting spec | Keep urgent-alert basis, metric/gap semantics, applicable correlation identifiers without dummy IDs, record safety, telemetry budgets/pipeline, channel health, runbooks, and ownership visible. |
| `oncall-health-review.md` | `oncall-health` | On-call health review | Keep page cause, noise risk, user-impact guardrail, owner, and fix path visible. |
| `operational-ownership-transfer.md` | `operational-ownership-transfer` | Operational ownership transfer gate | Keep bus-factor inventory, runbook executability, deploy/rollback/failover dry-runs, paging transfer, dependency map, acceptance gate, and handoffs visible. |
| `performance-capacity-plan.md` | `performance-and-capacity` | Performance and capacity plan | Keep load target, headroom, bottleneck, saturation signal, entry-point limits, control-loop input contract and behavior, shared background-work budget, and action trigger visible. |
| `persistent-connection-systems.md` | `persistent-connection-systems` | Persistent connection system plan | Keep authenticated-or-deliberately-anonymous scope, authorization/public bounds, reconnect/resume, backpressure, fanout, capacity, deploy drain, and gap recovery visible. |
| `platform-golden-path-scorecard.md` | `platform-golden-paths` | Platform golden path scorecard | Keep paved-path friction, safety checks, owner, and adoption evidence visible. |
| `privacy-data-lifecycle-plan.md` | `privacy-and-data-lifecycle` | Privacy and data lifecycle plan | Keep minimization, retention, deletion, export, logging, and owner fields aligned. |
| `prr-checklist.md` | `production-readiness-review` | Production readiness checklist | Keep ownership, readiness evidence, rollback, blockers, watch, and dated exceptions visible. |
| `release-build-reproducibility.md` | `release-build-reproducibility` | Release reproducibility plan | Keep artifact identity, pinned inputs, cache hermeticity, promotion path, rollback traceability, and clean install evidence visible. |
| `resilience-requirements.md` | `resilience-requirements` | Resilience requirements contract | Keep outcome, non-functional targets, failure behavior, edge/error behavior, abuse cases, non-goals, and testable acceptance criteria visible. |
| `resilience-experiment-plan.md` | `resilience-experiments` | Resilience experiment plan | Keep hypothesis, blast radius, abort criteria, telemetry, and learning loop visible. |
| `risk-exception-register.md` | Shared use | Risk exception register | Keep risk, compensating control, owner, expiry, acceptance, and review trigger visible. |
| `rollout-plan.md` | `progressive-delivery` | Rollout plan | Keep canary metrics, stop criteria, owner, abort cleanup, rollback, incident-mode automatic rollout queue pause, and promotion pause visible. |
| `scheduled-job-reliability-plan.md` | `scheduled-job-reliability` | Scheduled job reliability plan | Keep run contract, idempotency, overlap/fencing generation, stale-holder test, time basis, missed/stuck detection, safe run records, catch-up, and completion evidence visible. |
| `service-decommission-and-sunset.md` | `service-decommission-and-sunset` | Service decommission and sunset plan | Keep zero-traffic proof, data sanitization and verification, routed credential and cryptographic-material revocation outcomes, namespace retention/reclamation, ordered teardown, monitoring removal, and no-resurrection record visible. |
| `slo-table.md` | `slo-and-error-budgets` | SLO and error-budget table | Keep journey, SLI, target, burn response, and non-urgent follow-up fields aligned. |
| `software-supply-chain-security.md` | `software-supply-chain-security` | Software supply chain security plan | Keep control matrix, pinning/namespace scope, provenance maturity and reader compatibility, signing, inventory, scanning, intake, and exception expiry visible. |
| `state-machine-correctness-plan.md` | `state-machine-correctness` | State machine correctness plan | Keep states, transitions, invariants, fencing generation/stale-holder tests, concurrency risks, exploration/regression seeds, and evidence visible. |
| `support-window-inventory.md` | `fleet-upgrades` | Support window inventory | Keep version support, owners, exceptions, deadline, and cleanup checks visible. |
| `tenant-isolation-review.md` | `tenant-isolation` | Tenant isolation review | Keep context provenance, authentication/membership binding, protected transit, boundary revalidation, conflict rules, shared resources, quarantine, access checks, and audit safety visible. |
| `test-data-engineering-plan.md` | `test-data-engineering` | Test data engineering plan | Keep fixture purpose, source, regeneration path, safety review, and drift signal visible. |
| `testing-quality-gates.md` | `testing-and-quality-gates` | Testing and quality gate plan | Keep historically measured and provisional runtime/flake budgets, feedback objective, sample/confidence, merge/release blockers, infrastructure health, and failure response visible. |
| `threat-model.md` | `secure-sdlc-and-threat-modeling` | Threat model | Keep trust boundaries, abuse cases, controls, audit-store integrity, residual risk, and verification visible. |
| `upgrade-readiness-matrix.md` | `fleet-upgrades` | Upgrade readiness matrix | Keep inventory, update-channel control, skew window, pending-state behavior, startup/reboot/session re-entry checks, remediation reachability, compatibility test, exception, and owner visible. |
| `version-skew-policy.md` | `fleet-upgrades` | Version skew policy | Keep supported combinations, rollout order, tests, exception, and retirement visible. |
| `vulnerability-management-plan.md` | `vulnerability-management` | Vulnerability management plan | Keep exploitability, exposure, owner, patch path, deadline, compensating control, accepted-by decision, and exception expiry visible. |
| `web-release-gates.md` | `web-release-gates` | Web release gate plan | Keep loading, interaction readiness, layout stability, component-state, request-target, client extension/config compatibility, runtime error, and payload checks visible. |

## Maintenance Rules

- Update this index when a template is added, renamed, removed, or reassigned.
- Update the owning template when a specialist changes required output fields.
- Keep each owning specialist's Required Outputs aligned with the template
  output shape.
- Keep shared templates capability-based. Do not add vendor-specific defaults.
- Keep template prose concise enough that agents can copy the structure without
  treating it as generated specialist guidance.
