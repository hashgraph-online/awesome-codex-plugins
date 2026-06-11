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
| `accessibility-release-check.md` | `accessibility-gates` | Accessibility release check | Keep journey blockers, retest evidence, and release decision fields aligned. |
| `adr.md` | `architecture-decisions` | Architecture decision record | Keep context, decision, tradeoffs, consequences, and revisit trigger visible. |
| `agent-pr-review.md` | `agent-pr-review` | Pre-merge review record | Keep intent match, verification evidence, and residual risks visible. |
| `ai-coding-instructions.md` | `ai-coding-governance` | Agent repository rules | Keep protected paths, data boundaries, acceptance checks, and ownership visible. |
| `api-contract.md` | `api-design-and-compatibility` | API contract | Keep compatibility, request-surface parity, low-traffic or embedded-runtime paths, header/metadata/callback preservation, error shape, idempotency, result-metadata invariants, fanout partial-failure semantics, and rollout fields aligned. |
| `architecture-review.md` | `architecture-decisions` | Architecture review | Keep options, constraints, tradeoffs, and revisit conditions visible. |
| `backup-recovery-plan.md` | `backup-and-recovery` | Backup and restore plan | Keep RTO/RPO, backup creation-path dependencies, restore evidence, alternate restore targets, client-visible reference repair, restore capacity/quota guardrails, owner, and recovery gaps visible. |
| `bounded-context-map.md` | `architecture-decisions` | Boundary map | Keep ownership, data boundary, dependency, and change trigger fields aligned. |
| `cache-derived-data-plan.md` | `caching-and-derived-data` | Cache and derived data plan | Keep canonical identity, freshness, invalidation, miss behavior, refresh spread, and repair path visible. |
| `cert-lifecycle-plan.md` | `cryptography-and-key-lifecycle` | Certificate and key lifecycle plan | Keep owner, expiry, rotation mode, active-use signal, issuance-pipeline capacity, component-version compatibility, queued encrypted state, overlap, verification, and rollback fields aligned. |
| `check-before-moving-on.md` | Shared use | Evidence checkpoint | Keep command, condition, artifact path, owner, checked time, actual result, failure response, and limitation fields reusable. |
| `client-application-security-review.md` | `client-application-security` | Client application security review | Keep trust boundary, client sinks, local storage, transport pinning, entry-point hardening, tamper posture, and negative tests visible. |
| `code-readability-for-agents.md` | `code-readability-for-agents` | Code readability review | Keep canonical paths, misleading names, size limits, and search risks visible. |
| `configuration-safety-review.md` | `configuration-and-automation-safety` | Configuration safety review | Keep required/non-empty inputs, validation, rejected-change quarantine, dormant-feature guards, generated-config boundary, preview, tracking/shadow mode, application state, fanout controls, priority/scheduling class, blast radius, rollback, operational lever gates, derived-state cleanup, owner, and expiry fields aligned. |
| `container-runtime-and-orchestration.md` | `container-runtime-and-orchestration` | Runtime posture spec | Keep resource bounds, drain contract, probe semantics, lifecycle ordering, host lifecycle, image posture, and disruption verification visible. |
| `cost-reliability-review.md` | `cost-aware-reliability` | Cost and reliability review | Keep reliability benefit, cost driver, owner, and rollback or cleanup evidence visible. |
| `data-contract.md` | `data-contracts` | Producer and consumer data contract | Keep field meaning, compatibility, consumer checks, and deprecation path aligned. |
| `data-lineage-and-provenance.md` | `data-lineage-and-provenance` | Data lineage and provenance plan | Keep source-of-record, derivation graph, downstream dependencies, boundary-crossing lineage, purpose tags, recompute procedure, and audit record visible. |
| `data-pipeline-reliability.md` | `data-pipeline-reliability` | Data pipeline reliability plan | Keep freshness, validation, lineage, replay, critical-path dependencies, backlog recovery, fairness/rate limits, shared-resource, shed, and recovery fields visible. |
| `database-change-plan.md` | `database-operations` | Database change plan | Keep lock risk, rollback, throttling, bounded-value headroom, replica/site dependency behavior, query evidence, and owner fields aligned. |
| `dependency-hygiene-plan.md` | `dependency-and-code-hygiene` | Dependency hygiene plan | Keep inventory, batch plan, lockfile safety, and rollback evidence visible. |
| `dependency-matrix.md` | `dependency-resilience` | Dependency resilience matrix | Keep timeout, retry, idempotency, fallback, queue, and overload fields aligned. |
| `dev-environment-parity-matrix.md` | `dev-environment-parity` | Environment parity matrix | Keep drift dimensions, allowed divergence, owner, and action trigger visible. |
| `distributed-data-consistency-plan.md` | `distributed-data-and-consistency` | Distributed data consistency plan | Keep consistency model, repair path, split-brain risk, time/clock ordering including leap/DST behavior, at-rest quality controls, and verification visible. |
| `documentation-lifecycle.md` | `documentation-lifecycle` | Documentation inventory and freshness plan | Keep source of truth, current-state verification, cadence, staleness signal, archive rule, and no-duplication rule visible. |
| `edge-traffic-defense-plan.md` | `edge-traffic-and-ddos-defense` | Edge traffic defense plan | Keep origin protection, limit behavior, traffic steering, recovery drain behavior, customer impact, and abort path visible. |
| `engineering-control-evidence-map.md` | `engineering-control-evidence` | Engineering control evidence map | Keep control, evidence, owner, expiry, exception, and collection path aligned. |
| `eval-harness-spec.md` | `llm-evaluation` | Evaluation harness spec | Keep eval unit, case coverage, trace or final-state checks, grader, threshold, regression history, and triage fields visible. |
| `event-workflow-contract.md` | `event-workflows` | Event workflow contract | Keep trigger compatibility, replay, ordering, duplicate handling, failed-message behavior, side-effect acceptance, and owner visible. |
| `experiment-guardrail-plan.md` | `experimentation-and-metric-guardrails` | Experiment guardrail plan | Keep assignment, exposure, guardrails, sample balance, and readout validity visible. |
| `feature-flag-lifecycle.md` | `feature-flag-lifecycle` | Feature flag lifecycle record | Keep owner, expiry, fallback, cleanup, and removal evidence visible. |
| `high-availability-design.md` | `high-availability-design` | High-availability design | Keep fault domains, replica/quorum placement, static capacity, DNS/name resolution, cache/refill load, shared dependencies, operating-envelope mismatches, protective-mode behavior, gray-failure health thresholds, health/control-loop coupling, failover evidence, and return-to-normal fields visible. |
| `identity-and-secrets-review.md` | `identity-and-secrets` | Identity and secrets review | Keep scope, permission propagation, authorization freshness recovery, authorization decision capacity, authentication dependency-cycle checks, signer/verifier compatibility, lifetime, rotation, secret-bearing resource deletion safety, audit-store integrity, break-glass path, and traceability fields aligned. |
| `incident-postmortem.md` | `incident-response-and-postmortems` | Incident timeline and follow-up record | Keep timeline, impact, contributing factors, owners, and verification actions visible. |
| `infrastructure-policy-as-code-plan.md` | `infrastructure-and-policy-as-code` | Desired-state and policy plan | Keep secure baselines, drift detection, policy checks, reconciliation, exception, and rollback visible. |
| `input-validation-and-injection-defense.md` | `input-validation-and-injection-defense` | Input validation and injection defense plan | Keep source-to-sink map, per-sink controls, structured binding, upload handling, negative tests, and residual risk visible. |
| `internal-service-networking-plan.md` | `internal-service-networking` | Service networking plan | Keep discovery, identity, locality, topology input checks, asset lifecycle state, workflow/device compatibility, isolation/rejoin gates, control-plane or fail-open state, route-state freshness, stale route/boot/client artifact checks, external or partner failover signaling, observer-path safety, routing-change safety, planned-work safety with automation or manual-path checks, degraded-path emergency tooling, access boundary, and fallback behavior visible. |
| `llm-application-security-review.md` | `llm-application-security` | LLM application security review | Keep prompt injection, tool access, data exposure, and residual risk fields aligned. |
| `llm-serving-cost-latency.md` | `llm-serving-cost-and-latency` | LLM serving cost and latency plan | Keep token budget, latency budget, cache behavior, degradation path, and owner visible. |
| `migration-deprecation-plan.md` | `migration-and-deprecation` | Migration and deprecation plan | Keep caller inventory, traffic-class capacity/backlog validation, migration completion evidence, dependency optionality, domain/DNS retirement evidence, no-new-usage check, batches, rollback, and removal evidence visible. |
| `ml-reliability-readiness.md` | `ml-reliability-and-evaluation` | ML reliability readiness plan | Keep eval coverage, skew checks, serving control state, routing-control-plane checks, drift checks, rollback, and production-risk fields aligned. |
| `mobile-release-plan.md` | `mobile-release-engineering` | Mobile release plan | Keep staged rollout, client-exposure load, halt criteria, telemetry, environment target, server-client state, rollback or forward-fix path visible. |
| `multi-region-and-data-residency.md` | `multi-region-and-data-residency` | Multi-region and residency plan | Keep topology, residency placement, replication-aware affinity, geo-routing, evacuation runbook, residency-under-failover, and rehearsal fields visible. |
| `observability-alerting-spec.md` | `observability-and-alerting` | Observability and alerting spec | Keep metric definitions, telemetry consumers, missing-signal behavior, backfill/gap semantics, maintenance suppression guard, telemetry volume and quota budget, operational channel health, runbook, and owner visible. |
| `oncall-health-review.md` | `oncall-health` | On-call health review | Keep page cause, noise risk, user-impact guardrail, owner, and fix path visible. |
| `operational-ownership-transfer.md` | `operational-ownership-transfer` | Operational ownership transfer gate | Keep bus-factor inventory, runbook executability, deploy/rollback/failover dry-runs, paging transfer, dependency map, acceptance gate, and handoffs visible. |
| `performance-capacity-plan.md` | `performance-and-capacity` | Performance and capacity plan | Keep load target, headroom, bottleneck, saturation signal, entry-point limits, control-loop input contract and behavior, shared background-work budget, and action trigger visible. |
| `persistent-connection-systems.md` | `persistent-connection-systems` | Persistent connection system plan | Keep connection protocol, reconnect/resume, backpressure, presence/fanout, protocol-tied capacity, deploy drain, and gap detection visible. |
| `platform-golden-path-scorecard.md` | `platform-golden-paths` | Platform golden path scorecard | Keep paved-path friction, safety checks, owner, and adoption evidence visible. |
| `privacy-data-lifecycle-plan.md` | `privacy-and-data-lifecycle` | Privacy and data lifecycle plan | Keep minimization, retention, deletion, export, logging, and owner fields aligned. |
| `prr-checklist.md` | `production-readiness-review` | Production readiness checklist | Keep ownership, readiness evidence, rollback, blockers, watch, and dated exceptions visible. |
| `release-build-reproducibility.md` | `release-build-reproducibility` | Release reproducibility plan | Keep artifact identity, pinned inputs, cache hermeticity, promotion path, rollback traceability, and clean install evidence visible. |
| `resilience-requirements.md` | `resilience-requirements` | Resilience requirements contract | Keep outcome, non-functional targets, failure behavior, edge/error behavior, abuse cases, non-goals, and testable acceptance criteria visible. |
| `resilience-experiment-plan.md` | `resilience-experiments` | Resilience experiment plan | Keep hypothesis, blast radius, abort criteria, telemetry, and learning loop visible. |
| `risk-exception-register.md` | Shared use | Risk exception register | Keep risk, compensating control, owner, expiry, acceptance, and review trigger visible. |
| `rollout-plan.md` | `progressive-delivery` | Rollout plan | Keep canary metrics, stop criteria, owner, abort cleanup, rollback, incident-mode automatic rollout queue pause, and promotion pause visible. |
| `scheduled-job-reliability-plan.md` | `scheduled-job-reliability` | Scheduled job reliability plan | Keep run contract, idempotency, overlap policy, time basis, deadline, missed/stuck detection, catch-up, and completion evidence visible. |
| `service-decommission-and-sunset.md` | `service-decommission-and-sunset` | Service decommission and sunset plan | Keep zero-traffic proof, data disposition, credential/cert revocation, name reclamation, ordered teardown, monitoring removal, and no-resurrection record visible. |
| `slo-table.md` | `slo-and-error-budgets` | SLO and error-budget table | Keep journey, SLI, target, burn response, and non-urgent follow-up fields aligned. |
| `software-supply-chain-security.md` | `software-supply-chain-security` | Software supply chain security plan | Keep provenance, provenance-reader compatibility, signing, dependency inventory, secret scan, vulnerability intake, and exception expiry visible. |
| `state-machine-correctness-plan.md` | `state-machine-correctness` | State machine correctness plan | Keep states, transitions, invariants, concurrency risks, and test evidence visible. |
| `support-window-inventory.md` | `fleet-upgrades` | Support window inventory | Keep version support, owners, exceptions, deadline, and cleanup checks visible. |
| `tenant-isolation-review.md` | `tenant-isolation` | Tenant isolation review | Keep boundary, shared resource, tenant-controlled config quarantine, fallback path, access check, and residual risk visible. |
| `test-data-engineering-plan.md` | `test-data-engineering` | Test data engineering plan | Keep fixture purpose, source, regeneration path, safety review, and drift signal visible. |
| `testing-quality-gates.md` | `testing-and-quality-gates` | Testing and quality gate plan | Keep merge blocker, release blocker, test-infrastructure health, later signal, owner, and failure response visible. |
| `threat-model.md` | `secure-sdlc-and-threat-modeling` | Threat model | Keep trust boundaries, abuse cases, controls, audit-store integrity, residual risk, and verification visible. |
| `upgrade-readiness-matrix.md` | `fleet-upgrades` | Upgrade readiness matrix | Keep inventory, update-channel control, skew window, pending-state behavior, startup/reboot/session re-entry checks, remediation reachability, compatibility test, exception, and owner visible. |
| `version-skew-policy.md` | `fleet-upgrades` | Version skew policy | Keep supported combinations, rollout order, tests, exception, and retirement visible. |
| `vulnerability-management-plan.md` | `vulnerability-management` | Vulnerability management plan | Keep exploitability, exposure, owner, patch path, deadline, and exception expiry visible. |
| `web-release-gates.md` | `web-release-gates` | Web release gate plan | Keep loading, interaction readiness, layout stability, component-state, request-target, client extension/config compatibility, runtime error, and payload checks visible. |

## Maintenance Rules

- Update this index when a template is added, renamed, removed, or reassigned.
- Update the owning template when a specialist changes required output fields.
- Keep each owning specialist's Required Outputs aligned with the template
  output shape.
- Keep shared templates capability-based. Do not add vendor-specific defaults.
- Keep template prose concise enough that agents can copy the structure without
  treating it as generated specialist guidance.
