---
name: release-build-reproducibility
description: "Use when cutting releases, tags, versions, builds, packages, artifact identity, or promotion"
---

# Release Engineering And Build Reproducibility

## Iron Law

```
NO RELEASE WITHOUT PINNED INPUTS, REPRODUCIBLE BUILD, IMMUTABLE ARTIFACT, AND TRACEABLE PROMOTION
```

If you cannot tell exactly what was built, how it was built, and where it was promoted, the release is not reliable.

## Overview

Release engineering turns source changes into trustworthy artifacts.

**Core principle:** build from pinned inputs in a controlled environment, identify the artifact precisely, and promote that artifact through validation and release.

## When To Use

- The user asks about build systems, release engineering, release trains, release branches, release candidates, packaging, versioning, or artifact promotion.
- The user is making a release and needs release-cut steps, branch or candidate handling, versioning, packaging, artifact identity, or promotion checks.
- The agent is about to create a tag, bump a version, publish a hosted release record, build a release package, publish an artifact, or promote an artifact.
- Builds are slow, flaky, non-hermetic, non-reproducible, cache-sensitive, or dependent on local developer machines.
- A release process needs build-once promotion, release cut criteria, release branch policy, or artifact identity.
- You need to separate build, deploy, and release responsibilities.

## When Not To Use

- The main topic is rollout stages, canaries, feature flags, rollback, or production exposure; use `progressive-delivery` instead.
- The main topic is artifact signing, provenance maturity, dependency inventory, builder trust, or deploy admission; use `software-supply-chain-security` instead.
- The main topic is generic code review latency or developer workflow policy, with no build or release artifact risk.
- The main topic is an actively vulnerable deployed artifact; use `vulnerability-management` instead.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Source revision, branch/release-line model, release cadence, and supported versions.
- Build graph, test graph, generated code, packaging steps, and artifact outputs.
- Pinned dependencies, lockfiles, toolchains, build images, environment variables, and network access.
- Cache strategy, cache keys, invalidation rules, remote/local differences, and flaky build examples.
- Evidence that cache hits are hermetic and cannot let stale build or test output satisfy changed inputs.
- Release checks: tests, static checks, compatibility checks, security checks, and confirmation requirements.
- Artifact identity, metadata, storage, promotion path, deployment consumers, and rollback path.
- Inflight release behavior: promotion ordering, supersession, stalled stage handling, and environment-specific deployment history.
- Deploy or scale dependencies on live artifact sources, mirrored or cached artifacts, and behavior when artifact sources are unavailable.

## Workflow

1. **Separate concerns.** Distinguish developer build feedback, CI validation, artifact creation, deployment, and user-facing release.
2. **Pin every input.** Record source revision, dependencies, toolchains, build image, generators, and configuration needed to recreate the artifact.
3. **Make builds hermetic.** Remove undeclared local files, ambient credentials, network fetches, clock-sensitive output, and machine-specific behavior.
4. **Stabilize the graph.** Define build/test targets, cache keys, generated-output responsibility, and invalidation rules so cache hits cannot hide missing dependencies or stale behavior.
5. **Build once, promote many.** Create an immutable artifact once and move the same artifact through validation, staging, and production; deploy and scale paths should use pinned, available artifacts rather than live resolution during an emergency where feasible.
6. **Coordinate inflight releases.** If more than one release can be active, define promotion order, supersession rules, stalled-stage behavior, and how each environment records exactly which artifact it accepted.
7. **Define release lines.** Choose trunk release, release branch, train, or candidate flow based on support window and rollback needs. Emergency release branches should be short-lived, minimal, and reviewed with higher scrutiny because they bypass normal flow.
8. **Keep main recoverable.** Prefer short-lived topic branches, protected main, and release branches with explicit cherry-pick/backport policy so hotfixes do not disappear from the next release.
9. **Check releases deliberately.** Keep checks fast and signal-rich; quarantine flaky checks, but do not let flakes silently weaken the release signal.
10. **Record traceability.** Link artifact, source, build logs, checks, release decision, deployment, and rollback target, including rollback to an older known-good artifact when the harmful change is latent rather than the immediately previous release.
11. **Pair release cuts with readiness.** For a new release, run `production-readiness-review` before the first release command so ownership, rollback, watch, and operator impact are reviewed alongside build reproducibility.

## Synthesized Default

Use hermetic, reproducible, build-once promotion with pinned inputs, explicit artifact identity, fast automated checks, and traceable release metadata. Prefer trunk-compatible releases with short-lived topic branches and maintained release branches only when support windows require maintained release lines.



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

- Emergency fixes may use a shortened check path, but artifact identity, pinned inputs, and rollback target still apply.
- Long-lived support branches are appropriate when customers, platforms, or compliance commitments require maintained versions.
- Some generated artifacts cannot be byte-identical across platforms; require semantic reproducibility and record the allowed nondeterminism.
- Experimental internal tools may use lighter packaging if they do not create production artifacts.

## Response Quality Bar

- Lead with the release pipeline decision, reproducibility gap, flaky-build diagnosis, or release-cut plan requested.
- Cover pinned inputs, hermeticity, artifact identity, cache safety, release checks, promotion, and rollback traceability before optional release topics.
- Make recommendations actionable with build metadata, validation commands, checks, stop criteria, and rollback artifact references where relevant.
- Name the details to inspect, such as source revision, lockfiles, toolchain versions, build images, cache keys, build logs, artifact metadata, and promotion records; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside build and release engineering. Route rollout/canary behavior or supply-chain signing only when those are the central unresolved risk.
- Be concise: avoid generic release-process background and prefer compact pipeline maps, hermeticity checklists, and traceability tables.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Build and release pipeline map.
- Pinned-input and hermeticity checklist.
- Artifact identity and metadata standard.
- Inflight release ordering and supersession policy.
- Deploy/scale artifact dependency table with source, pinning, availability, mirror/cache, and unavailable-source behavior.
- Release branch/train/candidate policy.
- Build cache and invalidation policy.
- Cache hermeticity evidence: inputs covered by keys, stale-output detection, and a miss-path check for release-trust gates.
- Release check list with required versus advisory checks.
- Promotion and rollback traceability plan, including rollback-target selection when a harmful change is latent.
- Emergency branch policy with expiry, scope, and reviewer escalation when bypassing normal flow.

## Checks Before Moving On

- `input_pinning`: source, dependencies, toolchains, generated inputs, and build environment are pinned or explicitly exempted.
- `hermeticity_check`: build does not depend on undeclared local files, ambient network, machine state, or unscoped credentials.
- `artifact_identity`: artifact has immutable identifier, source revision, build metadata, and storage location.
- `inflight_order`: concurrent releases have ordering, supersession, stalled-stage, and per-environment deployment-history rules.
- `artifact_availability`: deploy and scale paths use pinned artifacts with availability behavior defined for missing artifact sources.
- `cache_safety`: cache keys and invalidation rules show stale output cannot satisfy changed inputs.
- `cache_hermeticity`: cache hits are trusted only when all behavior-changing inputs are declared and miss-path checks are exercised for release evidence.
- `release_record`: promotion and rollback path link artifact, checks, deployment, verification results, and rollback-target selection when the harmful change may be older than the previous deployment.
- `emergency_branch_bounds`: emergency release branches have documented expiry, scope, and reviewer escalation.

## Red Flags - Stop And Rework

- Release artifacts are rebuilt separately for each environment.
- Multiple inflight releases can overtake, supersede, or stall without a recorded ordering policy.
- A build passes only on one developer machine or one CI worker.
- Cache misses are slow, but cache hits are not trusted.
- Cache hits can produce release artifacts or test results without proving all behavior-changing inputs were declared.
- Release branches exist indefinitely with no support window, or merge policy.
- Rollback target is "whatever was previously deployed" with no artifact identity or latent-change check.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating deploy as release | Build and deploy artifacts separately from user exposure. |
| Chasing speed before determinism | Make the build correct and reproducible, then optimize graph and cache. |
| Ignoring generated code | Treat generators and generated outputs as declared build inputs. |
| Letting flakes erode checks | Quarantine, assign, and fix flakes with expiry. |
| Treating cache speed as release evidence | Prove cache hermeticity and stale-output behavior before trusting a green gate. |
