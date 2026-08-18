---
name: client-application-security
description: "Use when securing a browser or mobile client against client-side injection, insecure storage, tampering, or unsafe deep links and webviews"
---

# Client Application Security

## Iron Law

```
NO CLIENT TRUST WITHOUT SERVER-SIDE ENFORCEMENT, SAFE STORAGE, AND OUTPUT-SINK DEFENSE ON THE DEVICE
```

The client runs in an attacker-observable environment. Treat shipped static credentials and client-side checks as recoverable or bypassable. Short-lived tokens and device-bound, non-exportable keys can still reduce risk when protected by the platform and backed by server-side authorization.

## Overview

Client application security covers the attacker-controlled execution surface of a browser or mobile app: client-side injection sinks, local data storage, transport trust, tamper and reverse-engineering exposure, and unsafe entry points such as deep links and embedded web views. Server-side input defense, identity issuance, and model-output handling are owned elsewhere; this file owns what runs on the user's device.

**Core principle:** never trust the client for authorization, do not embed reusable credentials that rely on client secrecy, use protected storage for necessary tokens or device-bound keys, neutralize client-side sinks, and harden attacker-driven entry points.

## When To Use

- Securing a browser or native mobile client surface against client-side injection, insecure local storage, or tampering.
- Hardening deep links, intents, custom URL schemes, or embedded web views that accept external input.
- Deciding transport trust on the device, such as certificate or key pinning and downgrade resistance.
- Assessing what a client may hold or decide locally versus what must be enforced server-side.

## When Not To Use

- The sink is server-side (query, shell, server template, server file path); use `input-validation-and-injection-defense`.
- The risk is an LLM prompt, tool, retrieval, or unsafe model output; use `llm-application-security`.
- The concern is client performance, crash rate, or release rollout; use `web-release-gates` or `mobile-release-engineering`.
- The work is credential issuance, session/token policy, or workload identity; use `identity-and-secrets`.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Client type, platform(s), supported versions, and rendered surfaces that show untrusted content.
- Client-side sinks: dynamic markup/DOM, eval-like execution, web views, file/scheme handlers.
- Local data stored on device, its sensitivity, and the storage protection used.
- Transport posture: TLS expectations, pinning, and downgrade/mixed-content handling.
- Entry points: deep links, intents, URL schemes, inter-app messaging, and clipboard/share targets.
- Any authorization or pricing/limit logic currently enforced only on the client.
- Tamper, rooting/jailbreak, and reverse-engineering exposure relevant to the threat model.

## Workflow

1. **Set the client trust boundary.** List every decision the client currently makes and move authorization, pricing, and limits to server-side enforcement; keep only UX hints on the client.
2. **Neutralize client sinks.** Prefer APIs that place untrusted values into text or typed properties instead of parsing them as code or markup. Apply context-correct encoding at remaining render boundaries; when the product permits untrusted rich markup, use a maintained allowlist sanitizer and keep it out of script, style, event-handler, and executable URL contexts. Avoid eval-like execution. Use a restrictive content-security policy or platform equivalent as defense in depth, not as a substitute for safe sinks.
3. **Secure local storage.** Store only what is necessary; keep short-lived tokens, sensitive data, and device-bound or non-exportable keys in platform-protected storage, never in plaintext or world-readable locations. Do not embed reusable service credentials, private signing material, or shared API secrets in the shipped binary.
4. **Harden transport.** Require TLS, resist downgrade and mixed content, and apply certificate or key pinning where the threat model and update cadence justify it, with a recovery path for rotation.
5. **Harden entry points.** Validate and authorize deep links, intents, URL schemes, and inter-app messages; treat externally supplied parameters as untrusted; constrain embedded web views (disable unsafe bridges, restrict navigation and file access).
6. **Plan for tampering.** Assume the binary can be inspected and modified; do not rely on client-side checks for security, and add tamper/root signals only as defense-in-depth, not as a control.
7. **Protect data at rest and in display.** Apply privacy rules to caches, logs, screenshots, and clipboard; redact sensitive fields the device renders or persists.
8. **Verify with negative tests.** Test injection into client sinks, malicious deep links, downgraded transport, and tampered builds; prove the server rejects what a modified client would send.

## Synthesized Default

Treat the client as untrusted: enforce authorization server-side, use safe render sinks and maintained sanitization where markup is allowed, keep reusable static credentials out of the binary, protect necessary short-lived tokens or device-bound keys, harden transport and external entry points, and use tamper signals only as defense in depth. Verify with negative tests that a modified client cannot exceed server-enforced limits.

## Exceptions

- Certificate pinning may be deferred when rapid certificate rotation outweighs the pinning benefit, with the residual risk recorded.
- Low-sensitivity client caches may use lighter storage protection if classification confirms no sensitive data.
- Tamper/root detection may be omitted when the threat model does not justify its cost and server-side enforcement is complete.

## Response Quality Bar

- Lead with the client trust-boundary, sink-defense, storage, or entry-point decision requested.
- Cover server-side enforcement, client sinks, local storage, transport, entry points, and tamper posture before optional client-security breadth.
- Make recommendations actionable with concrete sinks, storage locations, pinning decisions, and negative tests.
- Name the details to inspect, such as rendered surfaces, storage, manifests, deep-link handlers, web-view config, and transport settings; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside client-side application security. Route server-side input defense, LLM-output risk, identity issuance, and client performance when those are central.
- Be concise: prefer a sink/entry-point matrix over generic mobile or web security background.
- Scale the artifact to the request: a narrow sink, storage, or entry-point question needs the trust decision, control, and negative test; add the full client posture only when the request spans those surfaces.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Client trust-boundary map: client hints versus server-enforced decisions.
- Client-side sink inventory with neutralization per sink.
- Local-storage classification and protection plan, distinguishing recoverable embedded credentials from protected short-lived tokens and device-bound or non-exportable keys.
- Transport-trust and pinning decision with rotation/recovery path.
- Entry-point hardening for deep links, schemes, intents, and web views.
- Tamper/reverse-engineering posture as defense-in-depth.
- Negative-test plan proving server rejection of modified-client requests.

## Checks Before Moving On

- `server_enforced`: authorization, pricing, and limits are enforced server-side; the client holds only hints.
- `client_sinks`: untrusted values use text or typed-property sinks where possible; permitted markup has context-correct encoding or maintained sanitization; executable contexts are excluded; policy controls remain defense in depth.
- `local_storage`: sensitive data and necessary tokens or device-bound keys use protected storage; no reusable credential that relies on client secrecy ships in the binary.
- `transport_trust`: TLS is required, downgrade is resisted, and pinning (if used) has a rotation/recovery path.
- `entry_points`: deep links, schemes, intents, and web views validate and authorize external input.
- `tamper_posture`: client checks are defense-in-depth only; security does not depend on them.
- `negative_tests`: tests prove a modified client cannot exceed server-enforced limits.

## Red Flags - Stop And Rework

- Authorization, pricing, or feature limits are enforced only on the client.
- A reusable service credential, shared API secret, or private signing key is shipped in the client binary, or sensitive material is stored in plaintext.
- Untrusted content reaches an interpreting client sink without a safe API, context-correct encoding, or maintained sanitization.
- A deep link, scheme, or web view accepts external input without validation or authorization.
- Security relies on tamper or root detection the attacker can disable.
- Sensitive data is written to logs, caches, screenshots, or clipboard without redaction.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Trusting client checks | Enforce authorization and limits server-side; client checks are hints. |
| Credentials in the binary | Do not ship reusable credentials that depend on client secrecy; issue scoped, short-lived tokens or device-bound keys where needed. |
| Plaintext local storage | Use platform-protected storage and classify what is stored. |
| Open entry points | Validate and authorize deep links, schemes, intents, and web views. |
| Pinning with no recovery | Pair pinning with a rotation/recovery path to avoid lockout. |
