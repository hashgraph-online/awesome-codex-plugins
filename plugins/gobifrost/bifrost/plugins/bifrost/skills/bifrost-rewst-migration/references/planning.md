# Planning and verification

## Build an execution record

Use the user's existing migration record when available; otherwise start with
[the plan template](../assets/migration-plan.md). Keep it in a private project,
not the public skill repository. Store secret references rather than values.
Keep raw exports in restricted storage, including exports of apparently harmless
workflow definitions: parameters and templates may contain embedded credentials.

Separate facts by provenance: current live observation, dated export, verified
test, vendor documentation, and proposed design. Historical dashboard counts
are a starting point for reconciliation, not current completion evidence.

## Inventory and contracts

Capture a row for each source object, including objects without active triggers.
For each resource record its type, source ID and organization, name, capture
version/hash, owner, references, consumers, enabled state, and disposition.
Record coverage per resource class and organization. Resolve inherited resources
and org-variable precedence; duplicate names are not stable identities.

For each business feature capture:

| Contract | Evidence to recover |
| --- | --- |
| Trigger | Form, manual, cron, webhook, completion listener; enabled state, conditions, timezone, tenant scope, concurrency, deduplication and backfill behavior |
| Identity | Initiator versus execution identity, run-as organization, integration overrides, roles and customer authorization |
| Inputs | Types, defaults, required fields, validation, dynamic option generators, hidden and computed fields |
| Execution | Task DAG, branches, loops, joins, task retries/timeouts, error transitions, completion handlers, subworkflow inputs and outputs |
| Output | Return schema, status, templates, notifications, external state changes and the evidence that confirms them |
| State | Azure Tables/SQL, caches, correlation IDs, checkpoints, pending approvals, deduplication records, scheduled or suspended work |
| Consumers | External callback senders, bookmarks, portal links, PSA runbooks, scripts, apps, agent tools and downstream jobs |

Integrations require a separate readiness matrix: authentication method and
credential owner, API scopes, tenant mappings, parent/customer overrides,
service accounts, permissions, IP allowlists, endpoints, rate limits, pagination,
webhook subscriptions and renewals. Recover custom action definitions as well as
their invocation parameters. A pack name is insufficient to implement an action.
Reconnect OAuth through the provider's supported flow; do not assume Rewst can
export its integration credentials.

## Choose the target design

Build the dependency graph before sequencing features. Implement highly shared
adapters first, then their consumers; do not assume the historic number of
workflows equals the number of target features. Match on outcomes and contracts.
Document which source operations are consolidated and why no behavior is lost.

Reuse an existing Bifrost module when it owns the domain. Preserve the access
tuple across workflow, form/app/agent, table and file policies, integration scope,
and any Solution boundary. Follow `bifrost:build` for exact current authoring and
deployment commands. Local previews can still write to connected systems.

Use deterministic code for rules, transformations, arithmetic, and state
transitions. If a source action uses AI, preserve or explicitly change its
decision authority, prompt contract, tool restrictions and evaluation criteria.
Do not replace ordinary DAG logic with an agent merely because the migration is
being performed by one.

Decide how to migrate operational state separately from definitions. Identify
deduplication keys, in-flight tasks and approvals, scheduled future work,
watermarks, and audit requirements. Choose drain, replay, explicit reconstruction,
or authorized retirement for each class. Include a final delta capture and
change-freeze or source-version check before cutover.

## Sequence and gate the work

| Stage | Work | Exit evidence |
| --- | --- | --- |
| Intake | Resolve source/destination, access, scope, policies and automatic authority | Consolidated answers, exceptions, authorization and stop rules |
| Extract | Bounded credential validation, fresh snapshots and external consumer discovery | Resource coverage, checksums, pagination, dependencies and explicit gaps |
| Reconcile | Compare source with existing Bifrost capabilities and prior migration work | Every object classified; parity contracts and ownership agreed |
| Foundation | Integrations, scopes/mappings, shared modules, secret references, operational state and access | Readiness tests and recovery path for each dependency |
| Implement | Thin workflows plus forms/apps, event sources and operational tooling | Source reviewed and deployment status recorded; triggers remain controlled |
| Verify | Offline replay, sandbox lifecycle, permissions, recovery, shadow comparison | Passing feature matrix and reviewed intentional differences |
| Canary | Transfer a bounded cohort to one active writer | Downstream reconciliation, no duplicate effects, monitors and rollback verified |
| Expand | Move dependent cohorts in order; repeat gates | Coverage ledger and observation thresholds pass for each cohort |
| Retire | Resolve old links, pending work, retention, credentials and contract cancellation | Final disposition of all resources and explicit retirement acceptance |

Estimate effort after inventory. Separate shared foundations, feature complexity,
vendor consent, test-data preparation, and observation time; use ranges and name
uncertainties. A renewal date is a constraint, not proof that testing fits.

## Verification

Create cases from real historical outcomes where authorized, independently
reviewed expectations, and synthetic edge cases. Historical executions can
contain defects; preserve intended behavior rather than treating every old
result as correct. Redact replay inputs and remove credentials before sharing.

| Layer | Required evidence |
| --- | --- |
| Extraction | Auth denial, GraphQL errors with HTTP 200, schema mismatch, empty inventory, pagination boundary, duplicates, partial capture and resume rules |
| Semantics | Undefined/null/false/empty/defaults, strings versus numbers, list ordering, timezone/DST, date formatting, loop/join behavior and error transitions |
| Integration | Correct tenant and object mapping, scope and credential expiry, pagination, throttling, transient errors and ambiguous writes |
| Business outcome | Expected records and values in every affected system, matching output contracts, required notifications and audit trail |
| Access | Intended staff and customer roles succeed; wrong tenant, missing role and external user are denied; admin success alone is insufficient |
| Reliability | Duplicate, concurrent, out-of-order and delayed events; retries after partial writes; timeout/cancel, offline targets, crash recovery and exhausted retries |
| UI and entry points | Form validation, option generators, user context, permissions, loading/error/empty states, file attachments and submitted workflow result |
| Cutover | In-flight drain/replay, one writer, activation watermark, no unintended backfill, sender URL/auth switch, schedule timezone and rollback rehearsal |
| Operations | Useful alerts, named exception owner, visible failed or stalled work, reconciliation report, runbook and credential renewal process |

A dry run must block side effects at the adapter boundary, including email,
chat, tickets, purchases and device operations; a flag that only skips the final
write is insufficient. Use separate test tenants and sink recipients for tests
that exercise real writes. Shadow mode compares proposed effects against Rewst
while only one system commits them. An API timeout after a write requires
reconciliation before retrying.

Define feature-specific acceptance limits before production: required cases,
critical failures allowed, reconciliation mismatch tolerance, latency and error
budgets, duplicate/missed-event tolerance, observation duration and business-cycle
coverage. Use synthetic time/replay for infrequent jobs, then monitor the next
real occurrence or record the owner's explicit acceptance of that remaining
uncertainty. Do not silently replace monthly/quarterly coverage with a short soak.

## Cutover and rollback

Maintain a per-feature cutover transaction: source version, cohort, start time,
previous and new trigger configuration, last processed watermark, in-flight IDs,
deduplication namespace, verification queries, and exact rollback owner/actions.
Cross-platform exactly-once delivery cannot be assumed; deduplication and
reconciliation close the gap.

- **Schedules:** disable the old writer, settle in-flight runs, then enable the
  new schedule under the chosen overlap/catch-up policy. Verify the next run and
  downstream state; elapsed time alone is insufficient.
- **Webhooks:** prepare and test the new authenticated receiver, switch the
  sender, verify delivery and acknowledgements, drain the old receiver, and
  handle retries around the handoff with correlation keys.
- **Forms and apps:** verify all user roles and generators, update launchers and
  links, perform the authorized communication, and retain the old entry point
  according to the transition policy.
- **Manual and child workflows:** update callers and runbooks, including
  completion listeners and indirect dynamic references, before retiring the old
  callable.

On a gate failure, pause the affected cohort and execute only the authorized
recovery. Stop the new writer before restarting the old one. Reconcile effects
already committed by either system; rollback of code or triggers does not undo
an email, purchase, user deletion, or vendor-side write. Use compensating actions
only where defined and authorized. Preserve evidence and the last known state.

## Handoff and retirement

Deliver the final resource/feature map, source and deployed versions, test and
reconciliation evidence, operational dashboards/alerts, exception ownership,
credential renewal instructions, rollback records and remaining limitations.
Verify no required caller still reaches Rewst and no pending/scheduled work is
lost. Archive exports and audit records under the agreed retention policy.
Revoke migration session credentials; distinguish them from vendor credentials
still shared with other systems. Delete resources or cancel the subscription
only within the user's recorded authority.
