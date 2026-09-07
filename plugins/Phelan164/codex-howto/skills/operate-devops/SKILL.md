---
name: operate-devops
description: Plan and implement infrastructure, CI/CD, container, deployment, observability, and operational configuration changes with least privilege, staged validation, and rollback awareness. Use for pipelines, infrastructure as code, Kubernetes, containers, release automation, monitoring, and production-readiness work; do not use to perform destructive production actions without explicit authorization.
---

# Operate DevOps

## Workflow

1. Read repository and environment guidance before changing configuration.
2. Identify the target environment, current state, owning tool, blast radius, and approval boundary.
3. Separate diagnosis, proposed change, apply, verification, and rollback.
4. Prefer a dry run, plan, diff, render, lint, or local build before any apply step.
5. Make the smallest reversible change.
6. Validate configuration syntax and policy.
7. Test failure behavior and rollback in the safest available environment.
8. Review the diff for secrets, broad permissions, unpinned behavior, and unintended targets.

## Guardrails

- Confirm account, cluster, subscription, region, namespace, and environment before state-changing commands.
- Keep credentials out of code, command output, and generated artifacts.
- Use least-privilege identities and scoped approvals.
- Do not silently apply infrastructure because a plan succeeded.
- Do not delete, force-replace, rotate, deploy, or migrate live resources without explicit authorization.
- Preserve a recovery path for availability, routing, storage, and identity changes.
- Do not weaken security controls merely to make automation pass.
- Treat third-party actions, base images, and pipeline dependencies as supply-chain inputs.

## Change safety

Read [references/change-safety.md](references/change-safety.md) for deployment, infrastructure, CI, secret, permission, or data-path changes.

## Verification

Use repository-native commands in this order:

```text
format/lint → validate/render → plan/diff → policy tests → staged rollout check
```

Report exactly which environment was inspected and which commands were not run.

## Acceptance criteria

- Target and blast radius are explicit.
- A preview or equivalent validation was inspected.
- Credentials and permissions follow least privilege.
- Rollback or roll-forward steps are concrete.
- Monitoring proves success and detects regression.
- The final report separates proposed, executed, and unverified actions.
