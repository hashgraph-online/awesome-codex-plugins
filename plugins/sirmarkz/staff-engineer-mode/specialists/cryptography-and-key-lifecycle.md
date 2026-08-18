---
name: cryptography-and-key-lifecycle
description: "Use when certificates, cryptographic keys, algorithms, trust roots, or other cryptographic material need rotation, renewal, revocation, or migration"
---

# Cryptography, Key, And Certificate Lifecycle

## Iron Law

```
EVERY KEY, CERT, AND ALGORITHM HAS AN EXPIRY DATE AND A TESTED REPLACEMENT PATH
```

If a certificate, key, algorithm, or trust root cannot be replaced safely on demand, the system is brittle. "Tested" means the replacement path has been exercised at least once outside an emergency; documentation alone is insufficient.

## Overview

Cryptography fails operationally when keys, certificates, algorithms, and trust roots cannot be inventoried or changed before a deadline.

**Core principle:** keep cryptographic dependencies discoverable, maintained, renewable, replaceable, monitored, and tested before expiry or algorithm transition becomes an incident.

## When To Use

- The user asks about certificate expiry, key rotation, cryptographic algorithm transition, trust-chain changes, renewal automation, or cryptographic agility.
- A service depends on certificates, keys, signing, encryption, trust roots, or cryptographic policies that can expire or become deprecated.
- Rotation, revocation, renewal, or algorithm migration could break clients, jobs, devices, or partner integrations.
- You need checks that cryptographic material is inventoried, expiring, monitored, and replaceable.

## When Not To Use

- The main topic is identity authorization, runtime secret storage or delivery, application secret rotation, or service access policy without a certificate, cryptographic key, trust root, or algorithm lifecycle change; use `identity-and-secrets` instead.
- The main topic is service trust-domain or peer-name matching, internal discovery, or private traffic policy without a cryptographic material lifecycle change; use `internal-service-networking` instead.
- The main topic is artifact provenance or release signing; use `software-supply-chain-security` instead.
- The main topic is secure design broadly; use `secure-sdlc-and-threat-modeling` instead.
- The request is abstract cryptographic research with no engineering lifecycle decision.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Inventory of certificates, keys, algorithms, trust roots, consumers, expiry dates, and renewal paths.
- Usage context: authentication, encryption, signing, verification, storage, transport, or partner integration.
- Rotation process, automation, manual steps, confirmation, access logs, and emergency revocation path.
- Issuance, registration, and renewal pipeline capacity, queue limits, retry behavior, drain rate, and upstream request sources.
- Persisted, queued, or in-flight encrypted state that must be read, rewritten, or recovered during rotation.
- Client and dependency compatibility, trust-store update path, fallback behavior, and rollback or roll-forward limits.
- Monitoring, alert thresholds, test environment coverage, and prior expiry or rotation incidents.
- Deprecation deadline, transition target, exception and compensating controls using the shared risk-acceptance lifecycle plus the shared compensating-control format where a deviation is accepted.

## Workflow

1. **Inventory dependencies.** Find cryptographic material, algorithms, trust roots, consumers, and expiry or deprecation dates.
2. **Classify use.** Separate authentication, confidentiality, integrity, signing, verification, and storage use cases.
3. **Assess agility.** Determine whether each dependency can be renewed, rotated, revoked, or replaced without coordinated outage.
4. **Check compatibility by use.** Test old/new material, algorithm combinations, and component versions for the operation the material performs: signing and verification, encryption and decryption, key establishment, transport identity, message authentication, or trust validation. Include persisted, queued, and in-flight state where material must remain readable or verifiable.
5. **Automate generation, renewal, and activation separately.** Use monitored paths with alerting, audit, and failed-renewal response. Derive renewal lead time from credential lifetime, replacement latency, retry opportunity, and incident-response time rather than treating one fraction as universal. Generating replacement material does not require the current key to be inactive; activation, retirement, revocation, and destruction depend on use-specific compatibility and active-use evidence. Material that requires manual coordination must not auto-activate without that proof.
6. **Protect issuance pipelines.** For certificate or signing-material registration authorities, model renewal bursts, upstream retry storms, queue depth and age, drain rate, request throttling, and capacity isolation so renewal backlog cannot block unrelated provisioning or recovery.
7. **Rotate by use.** For signatures or signed credentials, distribute verifier trust before new signers emit material and retain old verification while valid artifacts remain. For encryption, make readers decrypt old and new material before writers use the new key, then reconcile or re-encrypt retained data before retiring old decryption. For transport identity and trust roots, test both trust paths and mixed-version peers through the overlap. For shared authenticators, prove every producer and verifier follows the selected version. Treat `generate`, `activate for new operations`, `retain for old decrypt or verify`, `retire`, `revoke`, and `destroy` as distinct states.
8. **Plan transitions, including post-quantum.** Define overlap, dual support, rollout order, client migration, and retirement checks for deprecated algorithms or trust roots. Flag long-lived confidentiality and key-establishment material for harvest-now-decrypt-later exposure. Evaluate signing material separately for the period during which authenticity must remain verifiable and for future forgery risk; signatures are not exposed to decryption. Prefer crypto-agile interfaces that can adopt standardized post-quantum or hybrid algorithms without a full redeploy.
9. **Prepare emergency response.** Define a compromise path that can revoke or distrust material without waiting for normal zero-use evidence, then repair encrypted or signed state and recover through a tested roll-forward or rollback where one remains safe.
10. **Close exceptions.** Track unsupported material with expiry, risk, and compensating controls using the shared risk-acceptance lifecycle plus the shared compensating-control format.

## Synthesized Default

Use a cryptographic inventory, expiry monitoring, tested rotation, dual-support transition windows, compatibility checks, emergency revocation plan, and exception register using the shared risk-acceptance lifecycle plus the shared compensating-control format. Prefer designs where cryptographic material can be replaced independently of full application redeploys.



## Exceptions

- Emergency compromise response may skip ordinary rollout windows, but must preserve audit and recovery evidence.
- Legacy clients may require overlap windows; keep them time-bound with usage telemetry and migration checks.
- Low-risk development material can use lighter monitoring if isolated from production trust paths.

## Response Quality Bar

- Lead with the lifecycle risk, rotation plan, transition decision, or expiry blocker requested.
- Cover inventory, responsibility, expiry, rotation, compatibility, monitoring, emergency revocation, transition windows, and exceptions before optional cryptographic detail.
- Make recommendations actionable with dates, checks, alert thresholds, compatibility tests, and retirement criteria where relevant.
- Name the details to inspect, such as inventory, expiry data, consumer list, rotation test output, renewal logs, alert rules, and exception records; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside cryptographic lifecycle. Use identity, supply-chain, or secure-design skills only when those surfaces drive the main decision.
- Be concise: prefer inventory and transition matrices over broad cryptography explanation.
- Scale the artifact to the request: a narrow expiry or rotation question needs the use classification, lifecycle states, compatibility order, monitoring, and emergency path; add issuance-capacity, persisted-state, post-quantum, and exception modules only when relevant.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Cryptographic dependency inventory.
- Consumer, expiry, and renewal map.
- Use-specific lifecycle plan covering generation, activation, overlap, retention for old decrypt or verify, retirement, revocation, and destruction.
- Issuance and renewal pipeline capacity plan with queue, retry, throttle, drain-rate, and isolation behavior.
- Compatibility and dual-support test plan.
- Persisted or queued encrypted-state transition plan with rollback or roll-forward behavior.
- Algorithm, trust-root, and post-quantum transition plan that separates harvest-now-decrypt-later confidentiality exposure from signature authenticity and future-forgery risk.
- Monitoring and alert policy for expiry and failed renewal.
- Emergency revocation and compromise response.
- Exception register with expiry and compensating control using the shared risk-acceptance lifecycle plus the shared compensating-control format.

## Checks Before Moving On

- `inventory_owned`: cryptographic material, algorithms, trust roots, consumers, and expiry dates are visible.
- `rotation_test`: renewal, rotation, or replacement is tested for representative consumers.
- `use_specific_lifecycle`: signing, encryption, key-establishment, transport identity, authenticator, and trust-root material use the compatible activation and retirement order for their operation.
- `issuance_capacity`: issuance and renewal pipelines have queue limits, drain-rate alerts, retry bounds, throttling, and upstream-source visibility.
- `compatibility_window`: old/new compatibility and overlap duration are explicit.
- `encrypted_state_transition`: persisted, queued, or in-flight encrypted state can be read, rewritten, recovered, or safely rolled forward during rotation.
- `expiry_monitoring`: expiry and failed-renewal alerts have a response path.
- `transition_check`: deprecated algorithms or trust roots have migration and retirement criteria.
- `pqc_readiness`: long-lived confidentiality or key-establishment material has a harvest-now-decrypt-later position; long-lived signature validity has a separate post-quantum or hybrid position, or a recorded exception with expiry.

## Red Flags - Stop And Rework

- Certificates are discovered only when expiry alerts fire.
- A key can be created but not rotated or revoked safely.
- Replacement generation is blocked merely because current material remains active, leaving no overlap window.
- Old and new trust paths are never tested together.
- Manual renewal depends on one person remembering a calendar date.
- Deprecated algorithms remain because clients are unknown.
- Long-lived confidentiality, key-establishment, or authenticity guarantees depend on one classical algorithm with no agility or post-quantum migration position.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Inventory only at issuance | Track consumers and expiry throughout the material lifecycle. |
| Ignoring certificate-issuer backlog | Capacity-test issuance and renewal queues, then bound retries and drain rate. |
| Rotation without compatibility | Test old/new overlap before rollout. |
| Rotating keys around queued state only on the happy path | Test queued and in-flight encrypted work through rewrite, retry, rollback, and recovery. |
| Renewal without alerting | Monitor expiry and failed automation. |
| Permanent exceptions | Require a risk record, expiry, and retirement check. |
| Treating quantum migration as future-only | Inventory long-lived confidentiality and key-establishment exposure now, assess signature validity separately, and adopt crypto-agile interfaces. |
