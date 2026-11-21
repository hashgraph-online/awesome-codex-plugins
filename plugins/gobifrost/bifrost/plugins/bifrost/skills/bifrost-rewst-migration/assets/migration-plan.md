# Rewst to Bifrost migration plan

Status: discovery. Record a fresh capture date and responsible owner. Store this
working record and raw exports privately; the distributed skill contains no
installation state.

## Scope and intake

Resolve discoverable facts first, then send one consolidated question set. Record
each answer, evidence source and owner; mark unresolved decisions explicitly.

| Topic | Decisions to record |
| --- | --- |
| Source | Rewst region and verified API endpoint; parent/customer organizations; authorized account and secret reference |
| Destination | Bifrost instance, intended organizations and users, authorized account/role and source repository, existing capabilities, Workspace/App/Solution ownership |
| Coverage | All active/disabled workflows, shared dependencies, Crates and customizations, forms, apps, integrations, scripts/templates, state stores, roles and external callers; explicit exclusions |
| Outcomes | Business-critical features, known defects, required parity, accepted redesigns and retirement candidates |
| Constraints | Renewal/cancellation and notice dates, sequencing, blackout windows, allowable outage/missed events and spending limit |
| Testing | Test tenants/devices/users, sink recipients, allowed production reads and writes, representative cases and who accepts them |
| Authority | Actions permitted without another prompt; protected actions; cutover/cancellation authority; handling of new discoveries and cost overruns |
| Operations | Source change freeze, rollback triggers, exception owner/contact, notification policy, observation periods and retention |
| Private storage | Location and owner of the plan, raw snapshots and derived evidence; access controls, encryption and deletion/retention rules |

## Execution authority

For each action record allowed scope, prerequisites, automatic gate, stop
condition and owner. An unanswered field is unresolved, not implicit approval.
Carry already granted authorization forward.

| Action | Scope and authority | Gate and stop condition | Owner |
| --- | --- | --- | --- |
| Read and extract source | Unresolved | Unresolved | Unresolved |
| Prepare local source and tests | Unresolved | Unresolved | Unresolved |
| Create/deploy Bifrost resources | Unresolved | Unresolved | Unresolved |
| Configure integrations and permissions | Unresolved | Unresolved | Unresolved |
| Run sandbox/production writes | Unresolved | Unresolved | Unresolved |
| Send user/customer communications | Unresolved | Unresolved | Unresolved |
| Transfer triggers and operational state | Unresolved | Unresolved | Unresolved |
| Disable/delete old automations | Unresolved | Unresolved | Unresolved |
| Revoke credentials and cancel Rewst | Unresolved | Unresolved | Unresolved |

## Source evidence and coverage

Track each resource class for every in-scope organization. Link its private
snapshot and manifest, capture time, query/schema evidence, counts, pagination
termination, checksums, and gap status. Distinguish source absence, permission
denial, unsupported extraction and successful empty capture.

Coverage classes: organizations and inheritance; workflows and full task bodies;
triggers/listeners; forms and option generators; templates/scripts; integration
packs/actions/custom definitions and overrides; variables/mappings; Crates and
unsynced customizations; App Builder resources; roles/access; history fixtures;
external callers and operational state.

## Resource register

Maintain one row per source object with: type, stable source ID, organization,
name, hash/version, dependencies, callers, enabled state, disposition, target
resource(s), ownership/access, implementation status and evidence links.

Allowed dispositions: migrate, reuse existing, consolidate, retire with recorded
authority, or blocked with owner. A missing dependency blocks its consumers.

## Feature contracts and target design

For each feature record:

1. Trigger, intended business outcome and completion owner.
2. Inputs, defaults, Jinja transformations, branch/error/completion semantics.
3. Execution identity, run-as scope, roles and integration overrides.
4. External reads/writes, state stores, outputs and consumer contracts.
5. Reused Bifrost modules/workflows; new artifacts and deployment ownership.
6. State migration and idempotency; retry and partial-failure recovery.
7. Test cases and expected downstream evidence; intentional differences.
8. Cutover cohort, exact activation/rollback steps and observation gates.

## Integration readiness

For every provider record the API/auth method, secret reference and renewal
owner, required scopes and user consent, parent/customer mapping, custom actions,
rate limits/pagination, network prerequisites, webhook lifecycle, test target,
verification results and remaining gaps. Keep credential values out of this plan.

## Work sequence and estimates

Order dependencies before consumers. Track intake, extraction, reconciliation,
shared foundation, implementation, verification, canary, expansion and retirement.
For every work item record owner, prerequisites, effort range, external waits,
exit evidence and unresolved blockers. Estimate from the recovered inventory.

## Test and acceptance register

Each case records feature/source contract, fixture provenance, setup/cleanup,
identity/tenant, expected result, observed result, downstream state, failure
handling, test execution link, artifact version and acceptance status.

Cover semantic replay, integration contracts, the complete business lifecycle,
allowed/denied access, UI entry points, duplicate/concurrent/out-of-order events,
timeouts and partial writes, recovery, cutover and operations.

Record feature-specific thresholds for required cases, critical errors,
duplicates/missed events, reconciliation mismatches, latency, observation period
and infrequent business-cycle coverage. Every exception needs scope and owner.

## Cutover and rollback register

For every cohort record source version, change freeze/final delta, previous/new
trigger configuration, in-flight drain or replay, watermark, correlation and
deduplication strategy, one active writer, communication/entry-point updates,
verification queries, rollback trigger, compensation limits and recovery owner.

Feature progression: discovered → classified → dependencies ready → implemented
→ deployed inactive → verified → canary → live observed → source disabled →
retired. Record blockers separately; deployment alone does not imply live.

## Completion and ongoing operation

Account for every source object and external consumer. Attach the final parity
map, passing evidence, exceptions, runbooks, monitors, renewal instructions,
rollback records and archive/retention location. Record separate outcomes for
trigger disablement, deletion, credential revocation and subscription
cancellation. List required user actions and the condition that unblocks each.
