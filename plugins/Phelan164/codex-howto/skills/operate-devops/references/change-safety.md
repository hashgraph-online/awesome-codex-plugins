# Operational change safety

## Preflight

- Confirm environment and identity.
- Inspect current state and drift.
- Identify dependencies, consumers, and maintenance windows.
- Estimate blast radius and failure modes.
- Capture a recoverable baseline where the platform supports it.

## CI/CD

- Pin trusted actions and dependencies according to repository policy.
- Minimize token permissions and secret exposure.
- Keep untrusted pull-request code away from privileged credentials.
- Make retries safe and deployment concurrency explicit.
- Preserve useful logs without leaking secrets.

## Infrastructure as code

- Format and validate.
- Render templates.
- Inspect plans for replacement, deletion, permission expansion, and target drift.
- Apply only to the reviewed target.
- Reconcile out-of-band changes deliberately.

## Containers and runtime

- Use approved, maintained base images.
- Avoid running as root unless required and justified.
- Keep build-time and runtime secrets out of layers.
- Define health, readiness, resource, and shutdown behavior.

## Rollout

- Choose canary, blue/green, rolling, or maintenance rollout based on failure cost.
- Define abort thresholds before starting.
- Monitor service-level and business-level signals.
- Confirm rollback compatibility with schema and state changes.

## Handoff

Record the target, executed commands, changed resources, evidence, monitoring window, recovery procedure, and unresolved operational risk.

## Fillable change plan

Complete this before an apply or deployment:

```text
Change:
Owner:
Approval authority:
Target account/subscription:
Target region/cluster/namespace:
Observed current state and drift:
Intended resources and explicit exclusions:
Blast radius:
Dependencies and compatibility constraints:

PLAN
Preview/render commands:
Expected diff:
Replacement/deletion/permission-expansion checks:
Go/no-go criteria:

APPLY
Exact command:
Required identity and scoped permissions:
Staging/canary sequence:
Abort thresholds:

VERIFY
Configuration and runtime checks:
Service-level signals:
Business-level signals:
Observation window:
Post-apply drift/reconciliation check:

ROLLBACK OR ROLL-FORWARD
Trigger:
Exact recovery steps:
Data/schema compatibility:
Recovery verification:

HANDOFF
Executed versus proposed actions:
Evidence locations:
Unresolved risks and owner:
```

Do not fill unknown target or recovery details by guessing. Keep the change in
the plan stage until the missing authority or evidence is available.
