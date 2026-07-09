# Leakage Rules

## Invariant

Only unprotected functional behavior and compatibility requirements should cross into the clean workspace. Source expression, source-shaped design, and contaminated context must stay out.

## Never Cross

Block these from clean artifacts:

- raw source files
- copied source excerpts
- raw diffs
- full `task-manifest.json`
- full `preflight-goal.json`
- `init-config.json`
- source roots, visual roots, contaminated roots, source index refs, visual index refs, coverage ledger refs, and evidence ledger refs
- raw screenshots, `visual-index.json`, visual paths, image hashes, copied visible words, exact palettes, exact iconography, exact spacing/layout reproduction, and distinctive visual expression
- copied comments
- decompiled output
- private package, module, class, helper, method, function, variable, constant, or field names
- source-only file layout
- distinctive internal identifiers
- implementation-shaped pseudocode
- stack traces containing source lines
- unique log messages, UI copy, or strings not needed for compatibility
- formatting, ordering, or naming that mirrors source without public-contract need

## Allowed With Care

Allow these only when needed for compatibility or testing:

- public API names
- command names and flags
- documented config keys
- public protocol fields
- public file formats
- externally visible error codes
- interoperability-relevant strings
- visible UI words only when recorded as public compatibility surface in preflight

When keeping a public name, record why it is compatibility-relevant.

## Identifier Boundary

Treat implementation identifiers as contaminated by default. Package names, namespace names, module paths, class names, method names, function names, variable names, constants, fields, and internal event names must not appear in clean specs unless they are public compatibility surface.

Public compatibility surface means the name is externally documented, required by an existing integration, visible in a public protocol or file format, or explicitly required by the destination scope. If a name is retained, place it in `public_surface` or `public_contracts` with `name`, `kind`, `visibility`, and a concrete compatibility reason. Valid `visibility` values are `public`, `destination`, `protocol`, and `user-required`. Do not mention source-private names in summaries, claims, tests, open questions, skeleton areas, QC findings, or delta tickets.

Task IDs and project names are clean-visible path components: they appear in roots that clean roles read and in paths recorded by clean artifacts. Both must stay neutral. Use generated `task-` plus 8 lowercase hex IDs, and for projects a random neutral word pair or `proj-` plus 8 lowercase hex, matching `[a-z0-9][a-z0-9-]{0,63}`. Never derive a task ID or project name from source folder basenames or meaningful source-name tokens.

The contaminated side should maintain a private identifier denylist for guardrail scanning when practical. The denylist is line-oriented, ignores blank lines and `#` comments, and is bounded to 1,000,000 bytes per file, 20,000 total terms, and 512 characters per term. Keep that list out of clean/source-denied readable roots and do not paste its contents into clean artifacts or model-visible reports.

Agent 1.5 may use the denylist only through hook scanning. Do not include denylist terms in the neutral sanitizer brief, sanitizer prompts, sanitizer reports, clean artifacts, or model-visible feedback.

## Rewrite Pattern

Convert source-adjacent observations into neutral requirements:

- Bad: "Function `parseFooInternal` checks `if x == 7` then calls `retryLater`."
- Good: "When input mode is unsupported, the component rejects the request before persistence and exposes a retryable error."
- Bad: "Copy this loop structure."
- Good: "Process entries in input order and stop after the first validation failure."

## Review Checklist

Before clean handoff, Agent 1.5 confirms from a fresh source-denied context:

- No copied source text remains.
- No source code block remains.
- No private helper or file names remain unless justified as public compatibility.
- No private package, module, class, function, method, variable, constant, or field names remain.
- No algorithm description is more specific than required by observable behavior.
- No formatting, ordering, or naming mirrors source by default.
- Every claim has an evidence status.
- Every retained public name has a compatibility reason.
- Every uncertain behavior is marked as an open question.
- `leakage_review.reviewer_role` is `contaminated-handoff-sanitizer`.
- Clean roles receive `clean-run-context.json` and, when context management is enabled, `role-session-brief.json`; they do not receive `task-manifest.json`, full `preflight-goal.json`, `init-config.json`, `controller-status.json`, source indexes, visual indexes, raw screenshots, or contaminated ledgers.
- Visual fallback handoffs do not include raw screenshots, visual indexes, visual paths, image hashes, copied visible words, exact palettes, exact iconography, or exact layout measurements.
- Agent 0 influences clean roles only through schema-valid durable sanitized artifacts. Direct manager chat, progress feedback, implementation hints, priority changes, and in-progress corrections are contamination risks.
- Agent 3 reports to Agent 0 only after implementation is complete, blocked, or quarantined. Agent 4 reports only through terminal `polish-report.json` after final clean polish review is complete, blocked, or quarantined.

## Contamination Response

If clean work receives blocked material:

1. Stop clean processing for the affected artifact.
2. Mark the artifact contaminated.
3. Remove it from the clean workspace or quarantine it outside the clean artifact set.
4. Regenerate a scrubbed artifact from the contaminated side through Agent 1.5.
5. Record the incident in `qc-report.json` and, when useful, a standalone `contamination-incident.json`.

Do not try to "forget" source material inside the same clean context and continue.

## Guardrail Scripts

Use hook scripts as audit and guardrail support, not as the only boundary:

- `hooks/deny-clean-source-read.py`: denies clean-role and Agent 1.5 reads from `CLEAN_ROOM_SOURCE_ROOTS`, which must include visual evidence roots during visual fallback; clean roles may read only `CLEAN_ROOM_CLEAN_ROOTS`, `CLEAN_ROOM_IMPLEMENTATION_ROOTS`, `CLEAN_ROOM_SCHEMA_DIR`, and `CLEAN_ROOM_ALLOWED_READ_ROOTS`, while Agent 1.5 may read only assigned contaminated artifacts, `CLEAN_ROOM_SCHEMA_DIR`, and `CLEAN_ROOM_ALLOWED_READ_ROOTS`.
- `hooks/deny-contaminated-clean-write.py`: enforces write roots. Agent 2 writes only under `CLEAN_ROOM_CLEAN_ROOTS`, Agent 3 writes reports under `CLEAN_ROOM_CLEAN_ROOTS` and implementation files under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`, Agent 4 writes polish reports under `CLEAN_ROOM_CLEAN_ROOTS` and implementation-root hygiene/commit files under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`, and contaminated roles may write only under `CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS`.
- `hooks/check-artifact-leakage.py`: scans clean artifacts for high-risk leakage markers, obvious source-like identifiers, and terms from optional `CLEAN_ROOM_PRIVATE_IDENTIFIER_DENYLIST` files.
- For Agent 1.5, `hooks/check-artifact-leakage.py` also scans staged contaminated artifacts before promotion to clean handoff.
- `hooks/validate-json-schema.py`: checks JSON syntax and common bundled schema constraints, including the conditional and bounded fields used by these schemas. It is not a full JSON Schema 2020-12 validator.
- `hooks/require-clean-room-env.py`: fails closed when the role, root, or schema environment block is missing.
- `hooks/deny-clean-room-shell.py`: denies shell-style tools for clean-room role sessions except installed Agent 3 verification-runner invocations when `CLEAN_ROOM_ALLOW_AGENT3_SHELL=1` and installed Agent 4 polish-runner invocations when `CLEAN_ROOM_ALLOW_AGENT4_SHELL=1`; both must run with cwd under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`.

Set `CLEAN_ROOM_ROLE`, `CLEAN_ROOM_SOURCE_ROOTS`, `CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS`, `CLEAN_ROOM_CLEAN_ROOTS`, `CLEAN_ROOM_IMPLEMENTATION_ROOTS`, `CLEAN_ROOM_ALLOWED_READ_ROOTS`, and `CLEAN_ROOM_SCHEMA_DIR` explicitly before running hooks. Set `CLEAN_ROOM_PRIVATE_IDENTIFIER_DENYLIST` when the contaminated side has produced a private identifier list for hook-only scanning.
