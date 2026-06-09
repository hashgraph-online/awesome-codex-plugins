---
name: privacy-and-data-lifecycle
description: "Use when personal data needs minimization, classification, retention, erasure, export, or privacy-safe telemetry"
---

# Privacy Engineering And Data Lifecycle

## Iron Law

```
NO PERSONAL DATA FLOW WITHOUT PURPOSE, CLASSIFICATION, MINIMIZATION, RETENTION, DELETION, AND AUDIT
```

If you cannot find and delete or justify every copy, you do not control the data lifecycle.

## Overview

Privacy controls fail when personal data is collected, copied, logged, retained, or derived without a lifecycle.

**Core principle:** collect the least sensitive data that satisfies the purpose, propagate classification through every copy, and make retention, deletion, export, and audit behavior testable.

## When To Use

- The user asks about data minimization, retention, deletion, privacy-safe telemetry, sensitive-data lifecycle, anonymization, pseudonymization, or privacy engineering controls.
- A service copies personal or sensitive data into logs, traces, metrics, caches, search indexes, analytics, ML features, exports, backups, or support tools.
- A system needs engineering support for erasure, export, data subject requests, consent/purpose enforcement, or retention schedules.
- A design needs to prevent privacy regressions in release, observability, or data pipelines.

## When Not To Use

- The main issue is tenant boundary enforcement or noisy-neighbor isolation; use `tenant-isolation` instead.
- The main issue is authentication, authorization, secrets, or cryptography; use `identity-and-secrets` instead.
- The request is broad legal privacy statements, notice drafting, or regulator/auditor liaison; out of scope unless converted to concrete engineering controls.
- The work is only control mapping; use `engineering-control-evidence` instead.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Data inventory: fields, classifications, purpose, source, users, and downstream copies.
- Collection points, transformations, derived data, logs, telemetry, exports, backups, caches, and support views.
- Log, trace, and metric fields that may contain sensitive or stale data, with retention and cleanup path.
- Retention requirements, deletion triggers, legal holds if any, archival behavior, and backup expiration model.
- Data residency, cross-border transfer constraints, third-party processors, and subprocessors that store or receive personal data.
- Consent or purpose constraints that must be enforced by code, configuration, policy, or workflow.
- Access paths, activity logs, break-glass behavior, and privacy incident history.
- Data-subject request intake path, identity/account scope, response SLA, export format, erasure trigger, verification method, and exception handling.
- Validation approach for minimization, redaction, deletion, export correctness, and regression prevention.

## Workflow

1. **Inventory the flow.** Map personal data from collection through storage, processing, telemetry, derived data, export, support, backup, and deletion.
2. **Classify fields.** Mark sensitivity, purpose, allowed uses, residency, retention, protection level, and whether the field can be tokenized, redacted, aggregated, or omitted; make the classification drive access, telemetry, sharing, retention, and deletion behavior.
3. **Minimize collection.** Remove fields that are not needed; prefer derived, aggregated, tokenized, or on-device/local processing when it satisfies the purpose.
4. **Constrain use.** Enforce purpose, consent, and access constraints in code, data jobs, schemas, policy, or workflow checks.
5. **Control copies.** Apply privacy rules to logs, traces, metrics labels, crash reports, caches, search indexes, analytics, ML features, support tools, and third-party processors; remove stale telemetry fields and classify sensitive ones.
6. **Engineer deletion and retention.** Define retention classes, delete propagation, deletion markers for asynchronous cleanup, derived-copy repair, backup expiry, restore-time cleanup, audit trail, holds/exclusions, and failure handling. Model deletion as typed edges over a personal-data catalog so every downstream and derived asset is reachable and deletion completeness is countable; make deletion bounded by an SLA, idempotent, and restartable so a crash resumes rather than silently drops it. For retired media or destroyed keys, state the sanitization level (clear, purge, cryptographic-erase, or destroy) and how it is verified.
7. **Define the data-subject-rights workflow.** Specify how access, export, erasure, and portability requests are received, authenticated, scoped to stores and processors, completed within an SLA, verified for completeness, and closed with an audit record.
8. **Assess anonymization labels.** Do not call data anonymized unless reidentification risk has been assessed with an explicit method such as equivalence-class thresholds, diversity checks, noise-based aggregation, motivated-intruder assessment, or equivalent domain assessment; otherwise call it pseudonymized, aggregated, or tokenized.
9. **Verify export and erasure.** Test that subject, tenant, or account-scoped export/deletion finds expected copies, includes required third-party paths, uses a defined output format, and reports known exclusions.
10. **Prevent regressions.** Add schema checks, telemetry redaction tests, data-lineage alerts, and release checks for new sensitive fields.

## Synthesized Default

Use privacy-by-design as engineering controls: data inventory, classification, minimization, purpose enforcement, privacy-safe telemetry, retention/deletion automation, data-subject-rights workflow with SLA, export/erasure verification, and audit. Make user/control-plane deletion and retention behavior explicit across primary, derived, and archived copies. Keep legal interpretation outside the skill; make the agreed control enforceable and testable.



## Phase Behavior

- Ideation: identify risks, defaults, unknowns, options, and the next decision before code exists.
- Design: shape the target artifact, tradeoffs, checks, and details to gather.
- Development: guide sequencing, code boundaries, checks, and acceptance criteria.
- Testing: define release-blocking tests, evals, fixtures, and failure probes.
- Release: define rollout, observability, abort, rollback, and readiness details.
- Maintenance: define owners, drift checks, cleanup triggers, and refresh cadence.
- Existing artifact: use current code, docs, telemetry, incidents, or diffs as context for the next engineering decision; do not wait for a finished artifact before guiding design, build, release, or operation.
- Missing details: state assumptions and say what to check next instead of blocking lifecycle guidance.

## Exceptions

- Legal hold, fraud, security investigation, or financial record retention may override normal deletion; record scope, and expiry.
- Some backup media cannot delete individual records immediately; require bounded expiry, restore-time deletion, and documented risk.
- Aggregated or anonymized data can have different retention only when reidentification risk is assessed.
- Low-risk internal telemetry may use lighter controls if it contains no personal or sensitive data by classification.

## Response Quality Bar

- Lead with the data-flow finding, privacy control design, retention/deletion plan, data-subject-rights workflow, or blocker list requested.
- Cover inventory, classification, minimization, purpose/access enforcement, telemetry/support controls, retention/deletion propagation, and verification before optional privacy breadth.
- For access, erasure, export, or portability requests, state the request workflow, responsible control points, SLA, store coverage, exception list, verification method, and closure notes.
- Make recommendations actionable with field-level decisions, control points, test checks, failure handling, and retention or exception expiry where relevant.
- Name the details to inspect, such as field inventories, data stores, logs, caches, derived copies, consent/purpose rules, deletion traces, export tests, and backup behavior; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside engineering controls for data lifecycle. Leave legal interpretation out unless the user supplies a requirement to implement.
- Be concise: avoid generic privacy principles and prefer compact field inventories, flow maps, and verification plans.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Personal-data flow inventory.
- Field classification and minimization plan.
- Purpose/consent/access enforcement plan.
- Privacy-safe telemetry and support-tool controls.
- Telemetry data review table for sensitive or stale log, trace, and metric fields.
- Retention, deletion, backup, and derived-data propagation design with typed deletion edges, a deletion SLA, restartability, completeness accounting, third-party propagation, and the media-sanitization level.
- Data-subject-rights workflow for access, erasure, export, and portability with intake, scope, SLA, verification, exclusions, and audit closure.
- Anonymization or pseudonymization risk assessment when those labels are used.
- Export/erasure verification plan with store coverage, third-party coverage, output format, exclusion list, and completeness checks.
- Regression checks and activity logs.

## Checks Before Moving On

- `data_inventory`: personal and sensitive fields are mapped through primary and derived copies.
- `minimization_check`: every collected field has purpose, and keep/remove/tokenize decision.
- `copy_control`: logs, metrics, traces, caches, exports, support tools, and analytics have privacy handling.
- `telemetry_data_review`: log, trace, and metric fields are reviewed for sensitive data, stale fields, retention, and minimization.
- `deletion_path`: retention, deletion trigger, propagation, backup behavior, and failure handling are defined.
- `deletion_completeness`: deletion is modeled as typed edges over the data catalog, bounded by an SLA, restartable, and accounted for to completion across downstream, derived, backup, and third-party copies.
- `dsr_workflow`: access, erasure, export, or portability requests have intake, SLA, scope, verification, exclusions, and closure notes.
- `anonymization_check`: anonymized or pseudonymized outputs state reidentification-risk method and residual limits.
- `verification_plan`: export, erasure, redaction, or minimization controls have tests or review results.

## Red Flags - Stop And Rework

- Sensitive fields appear in logs or metric labels because they are useful for debugging.
- Retention is "forever" because no deletion trigger, expiry, or verification path exists.
- Delete requests remove primary rows but leave caches, search indexes, analytics, or ML features.
- Consent or purpose is documented but not enforced by the system.
- Data is labeled anonymized without reidentification risk review.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating privacy as legal text | Convert privacy decisions into code, config, checks, and records. |
| Mapping only primary storage | Include telemetry, derived data, backups, exports, and support tools. |
| Redacting after collection | Minimize or tokenize before broad propagation. |
| Trusting manual deletion | Automate propagation and verify with checks. |
| Best-effort, uncountable deletion | Model typed deletion edges with an SLA, restartability, and completeness accounting. |
