---
name: software-supply-chain-security
description: "Use when source-to-deploy paths need protected source, isolated builds, provenance, signing, inventory, or admission"
---

# Software Supply Chain Security

## Iron Law

```
NO PRODUCTION ARTIFACT WITHOUT SOURCE, BUILD, PROVENANCE, INTEGRITY, AND ADMISSION CHECKS
```

If an artifact cannot be traced back to accepted source and a trusted build path, it should not be trusted for production.

## Overview

Production should run artifacts whose source, build, dependencies, and confirmation path can be verified.

**Core principle:** protect the source-to-deploy chain with traceable changes, isolated builds, provenance, artifact integrity, least-privilege automation, and deployment verification.

## When To Use

- The user asks about build/deploy security, builder isolation, artifact signing, provenance, dependency inventories, deployment admission, secret scanning, or build/deploy integrity.
- A production path lacks a clear record of what source and build produced an artifact.
- Automation credentials can modify source, build, registry, deployment, or infrastructure.
- You need supply-chain controls or records for release integrity.

## When Not To Use

- The work is routine package updates or dead-code cleanup; use `dependency-and-code-hygiene` instead.
- The issue is a deployed vulnerability with patch SLA; use `vulnerability-management` instead.
- The question is runtime authorization or service access; use `identity-and-secrets` instead.
- The request is broad compliance program management; out of scope unless framed as engineering records.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Repositories, branches, change acceptance rules, merge rights, and source protection.
- Build system, workers, isolation, inputs, dependencies, environment, and reproducibility needs.
- Artifact types, registries, signing, checksums, provenance metadata versions, provenance readers or displays, dependency inventories, and retention.
- Deployment path, admission controls, environment promotion, and rollback.
- Automation credentials, token scopes, secret exposure, and third-party integrations.
- Scanning coverage, vulnerability checkpoint, and incident/exception process.
- Vulnerability-reporting or security-policy intake route when external reports or project users can report supply-chain issues.

## Workflow

1. **Map source to deploy.** Draw every step from code change through build, artifact, registry, deployment, and runtime admission.
2. **Protect source.** Require traceable accepted changes, branch protections, responsibility, and tamper-evident history for production paths.
3. **Harden builders.** Use isolated or ephemeral build environments for production artifacts; minimize mutable state and privileged credentials.
4. **Record provenance.** Produce metadata linking artifact identity, source revision, accepted change, build steps, builder identity, dependency inputs, build time, and confirmation path. High-impact paths should make this metadata verifiable at deployment. Treat provenance schema, type, or field changes as compatibility changes: validate old and new readers, displays, policy checks, and audit consumers before removing or deprecating a provenance form.
5. **Protect artifacts.** Sign or otherwise verify integrity; store artifacts in controlled registries with retention and rollback.
6. **Generate inventories.** Produce structured, machine-readable dependency inventories when they support vulnerability response, customer requests, or release checks workflows; name the consumer so the artifact is not ritual.
7. **Decide reproducibility level.** State whether the path needs byte-identical, declared-nondeterminism, or content-equivalent rebuild records, and record any expected differences.
8. **Standardize secure pipelines.** Use reusable pipeline modules for production paths so scanning, integrity checks, dependency inventories, user confirmations, and secure compute are not optional per repository.
9. **Control deployment.** Verify artifact integrity/provenance at admission and keep environment promotion traceable.
10. **Constrain automation.** Use least-privilege, short-lived credentials and secret scanning across source/build paths.
11. **Screen common attack classes.** Check for dependency confusion, typo or name-squatting, compromised package publishing, build-cache poisoning, unchecked install hooks, and compromised automation credentials.
12. **Route vulnerability intake.** Define where security reports about dependencies, build artifacts, or release integrity enter triage, then hand deployed-risk decisions to `vulnerability-management` with artifact, exposure, and provenance details.

## Synthesized Default

Use accepted source, controlled production pipelines, isolated builds, provenance, signed or integrity-verified artifacts, dependency inventory, least-privilege automation, secret scanning, and deployment admission checks for production paths. Keep routine dependency hygiene and deployed vulnerability remediation as adjacent but separate workflows.



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

- Low-risk prototypes may use lighter controls if isolated from production data and deployment.
- Legacy build systems may need staged improvements; record missing provenance/signing as exceptions with expiry and compensating controls using the shared risk-acceptance lifecycle plus the shared compensating-control format.
- Dependency inventories are useful when consumed for vulnerability, customer, or release checks workflows; do not generate unused artifacts as ritual.
- Emergency patches can use expedited paths only with post-facto provenance and acceptance checks.
- Release engineering covers reproducible build mechanics; this skill covers the trust boundary, provenance expectations, artifact integrity, and admission policy.

## Response Quality Bar

- Lead with the source-to-deploy risk, control gap, provenance plan, or exception register requested, using the shared risk-register and compensating-control formats for exception fields.
- Cover source acceptance, builder trust, artifact integrity, provenance, dependency inventory, deployment admission, automation credentials, and secret scanning before optional supply-chain breadth.
- Make recommendations actionable with control locations, validation commands, admission checks, exception expiry, and remediation steps where relevant.
- Name the details to inspect, such as protected branch settings, build identity, isolation model, artifact metadata, signatures or digests, dependency-inventory consumers, deploy policy, and credential scopes; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside supply-chain integrity. Route routine dependency hygiene or deployed vulnerability remediation only when those are the central unresolved risk.
- Be concise: avoid generic framework background and prefer compact control matrices and record maps.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Source-to-deploy supply-chain map.
- Control matrix for source, build, artifact, registry, deployment, and automation.
- Provenance and artifact integrity plan with minimum fields: artifact identity, source revision, accepted change, builder identity, dependency inputs, build time, confirmation path, verification location, and reader compatibility for metadata type or schema changes.
- Structured dependency inventory policy with producer, consumer, retention, and vulnerability checkpoint.
- Build and deployment credential hardening plan.
- Secret scanning and exposure response plan.
- Vulnerability-reporting intake and triage handoff for supply-chain findings.
- Exceptions with expiry and compensating controls using the shared risk-acceptance lifecycle plus the shared compensating-control format.

## Checks Before Moving On

- `source_acceptance`: production source changes require accepted source and protected merge path.
- `builder_trust`: build environment identity, isolation, and credential scope are documented.
- `provenance_check`: production artifacts have source/build provenance or a tracked exception.
- `provenance_compatibility`: provenance metadata changes validate old and new readers, displays, policy checks, and audit consumers before deprecation.
- `integrity_check`: deployment path verifies artifact integrity before promotion/admission.
- `credential_check`: automation credentials are least privilege, short lived where possible, and secret-scanned.

## Red Flags - Stop And Rework

- Anyone with build access can deploy unaccepted code.
- Production artifacts are rebuilt differently per environment without traceability.
- Long-lived automation tokens can modify source, artifacts, and deployment.
- Dependency inventories are generated but never used for vulnerability response or release records.
- Artifact signing exists but deployment never verifies it.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Scanning as the only control | Add provenance, integrity, least privilege, and admission. |
| Trusting the registry blindly | Verify artifact identity and provenance at deployment. |
| Mixing routine updates with supply-chain trust | Route routine dependency hygiene separately. |
| Ignoring build credentials | Treat automation credentials as production access. |
