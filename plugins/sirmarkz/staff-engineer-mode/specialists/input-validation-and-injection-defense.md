---
name: input-validation-and-injection-defense
description: "Use when untrusted input reaches a query, command, template, parser, path, or serializer and needs per-sink defense"
---

# Input Validation And Injection Defense

## Iron Law

```
NO UNTRUSTED INPUT REACHES A SINK WITHOUT BOUNDARY VALIDATION AND SINK-CORRECT ENCODING OR PARAMETERIZATION
```

Validation at the boundary alone does not stop injection. Every sink that interprets data (query engine, shell, template, parser, path resolver, deserializer) needs the defense correct for that sink, or the input is unsafe.

## Overview

Produces a per-sink threat-to-control matrix for conventional, non-model code: each untrusted source mapped to each sink it reaches, the boundary validation applied, the sink-correct defense, and the verification case that proves it. Refuses controls stated as prose without a sink and a test.

**Core principle:** validate untrusted input at the boundary for shape and intent, then neutralize it at each sink with the mechanism that sink requires. Input filtering supports defense; it cannot carry the only barrier.

## When To Use

- Untrusted input such as request fields, headers, uploads, message payloads, imported data, or third-party responses reaches a query, OS command, template, parser, local file path, local redirect response, or deserializer.
- The user asks about query, command, template, markup, path, unsafe deserialization, mass-assignment, or file-upload handling.
- A diff builds a query, command, markup, path, or object graph from data that crossed a trust boundary.
- A review must confirm that conventional application code neutralizes injection at the sink, not only at the edge.

## When Not To Use

- The untrusted source is model output crossing a tool, query, or render sink; use `llm-application-security`.
- The work is trust-boundary mapping, abuse-case enumeration, or control selection at design altitude; use `secure-sdlc-and-threat-modeling`, which routes per-sink implementation here.
- The work is API contract bounds, rate limits, or malformed-request isolation as a contract concern; use `api-design-and-compatibility`.
- The work is server-side request forgery or egress control for outbound fetchers, webhooks, callbacks, imports, link previews, private-address blocking, DNS/IP rebinding checks, or redirect policy for fetched URLs; use `secure-sdlc-and-threat-modeling`.
- The work is remediating an already-deployed known vulnerability by deadline; use `vulnerability-management`.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Untrusted sources reaching the change: request bodies, params, headers, uploads, message payloads, imported files, third-party responses, or stored data later re-emitted.
- Sinks reachable from those sources: query engines, OS or shell calls, markup or template render, expression evaluation, local file-path resolution, local redirect responses, object deserialization, and log sinks.
- Existing defenses: prepared statements, encoders, allowlist validators, schema validators, deserialization config, upload content checks, and where each is enforced.
- Data classification and which sinks cross a privilege or trust boundary.
- Test coverage that exercises malicious input against each sink.

## Workflow

1. **Map sources to sinks.** List every untrusted source in the change and trace which interpreting sinks it can reach. A source with no dangerous sink still needs shape validation.
2. **Validate at the boundary.** Apply allowlist validation for type, length, range, format, and required shape. Reject rather than sanitize where feasible; record why any denylist is used.
3. **Neutralize at each sink with the sink-correct mechanism.** Queries use parameterization or prepared statements with bound values, never string concatenation. Markup uses context-aware output encoding. OS actions avoid the shell or use argument vectors, never interpolated command strings. Templates disable code evaluation on untrusted data. File paths are canonicalized and confined to an allowed root. Local redirect responses validate the target against an allowlist. Deserialization uses safe formats, type allowlists, or schema validation.
4. **Constrain structured inputs.** Validate structured payloads against an explicit schema; bind only expected fields to guard against mass assignment and over-posting.
5. **Handle uploads by content, not by claim.** Validate by verified content type and size, store outside executable paths, and decouple stored name from served path.
6. **Make each control testable.** Define a negative test per sink that feeds malicious input and asserts it is neutralized.
7. **Record residual risk.** Where a sink cannot be fully parameterized or encoded, state the compensating control, expiry, and explicit user acceptance using the shared risk-register and risk-acceptance formats.

## Synthesized Default

Use defense in depth anchored at the sink: allowlist boundary validation plus sink-correct neutralization, each with a negative test. Enforce mechanisms in code; prose rules do not neutralize input. Use input filtering as a supporting layer.

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

- Low-risk internal-only inputs can use lighter source-to-sink maps when no interpreting sink, privilege boundary, or stored re-emission exists.
- Legacy sinks that cannot be parameterized need a compensating control, expiry, and owner; do not normalize the exception as the default.
- Generated validators still need a negative test at the sink, because the generator can validate shape while missing interpretation context.

## Response Quality Bar

- Lead with the source-to-sink gap, control matrix, or negative-test plan requested.
- Cover boundary validation, sink-correct neutralization, structured binding, upload handling, and residual risk before optional security breadth.
- Make recommendations actionable with sink names, control points, tests, and acceptance criteria.
- Name the details to inspect, such as sources, sinks, validators, encoders, query builders, parsers, and negative tests; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside conventional per-sink input defense; route model-output, outbound fetch or egress control, broad threat modeling, and deployed vulnerability remediation away when they dominate.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Source-to-sink map for the change.
- Per-sink threat-to-control matrix: source, sink, boundary validation, sink-correct defense, verification case.
- Structured-input schema and field-binding decision where object payloads exist.
- File-upload handling decision where uploads exist.
- Negative-test plan, one case per high-risk sink.
- Residual-risk register entry for any sink not fully neutralized, with user acceptance and expiry.
- Follow-up checks routed to `secure-sdlc-and-threat-modeling`, `llm-application-security`, `api-design-and-compatibility`, or `vulnerability-management` where central.

## Checks Before Moving On

- `sink_coverage`: every untrusted source is traced to the sinks it reaches; none is unaccounted for.
- `parameterization_check`: every query or command sink uses parameterization or an argument vector, not interpolation.
- `encoding_context`: every render sink encodes for its specific output context.
- `path_safety`: file-path and redirect sinks canonicalize and confine targets to an allowlist.
- `deserialization_safety`: object and markup parsers reject unexpected types and disable code evaluation on untrusted data.
- `structured_binding`: structured payloads validate against a schema and bind only expected fields.
- `negative_tests`: each high-risk sink has a negative test proving malicious input is neutralized.

## Red Flags - Stop And Rework

- A query, command, template, or path is built by concatenating untrusted input.
- Input filtering or escaping is the only barrier, with no sink-correct parameterization or encoding.
- Output is encoded for one context but rendered in another.
- Deserialization accepts arbitrary types or evaluates embedded code.
- A control is stated without a sink and a negative test.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Validate once at the edge, trust everywhere after | Neutralize at each sink with the sink-correct mechanism. |
| Escape strings to stop query injection | Parameterize; bind values, never interpolate. |
| One markup encoder for all output | Encode for the exact context: body, attribute, script, URL, or style. |
| Block known-bad inputs | Allowlist expected shape; reject the rest. |
| Trust upload file extension or declared type | Validate by verified content and serve from a non-executable path. |
