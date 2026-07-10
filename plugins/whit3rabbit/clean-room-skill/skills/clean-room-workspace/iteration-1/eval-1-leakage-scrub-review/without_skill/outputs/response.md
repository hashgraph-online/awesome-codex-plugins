No. This draft is **not** safe to pass to the clean implementation team. It is heavily contaminated with source expression and must not cross the wall in its current form.

It also has a process problem: `leakage_review.reviewer_role` is `contaminated-source-analyst` and the analyst self-approved (`status: "approved"`). The analyst cannot clear their own draft. A clean-handoff approval must come from the source-denied sanitizer (Agent 1.5), with `reviewer_role: contaminated-handoff-sanitizer`, reviewing from a fresh source-denied context. The `leakage_risk: "low"` field set by the analyst is also not trustworthy here and is contradicted by the contents below.

Below is everything that has to be scrubbed, by field.

## Blocking leaks (must be removed or rewritten before any handoff)

### 1. Source file paths (`source_unit_refs`)
- `"src/internal/flowpack/retry_scheduler.go"` and `"src/internal/flowpack/buffer.go"` are raw source file paths and source-only file layout. Source roots and source paths never cross into clean artifacts.
- Fix: drop these entirely from the clean handoff. Keep them only on the contaminated side / in the coverage ledger. The clean spec should carry no source path references.

### 2. Contaminated ledger reference (`evidence_refs`)
- `"coverage-ledger.json#unit-retry"` is a coverage-ledger ref. Coverage/evidence ledger refs are blocked from clean artifacts.
- Fix: remove the ledger ref from the clean handoff. Evidence linkage stays on the contaminated side.

### 3. `summary` (multiple leaks)
- Private identifiers: `RetryScheduler`, `parseFooInternal`, `retryLater()`. These are internal class/function/method names, contaminated by default. None are public surface.
- Magic internal detail: "when the mode byte equals 7" describes an internal sentinel value, not observable behavior.
- Copied comment / source excerpt: `// HACK: keep the 250ms backoff, FLOW-1234 will fix it later.` This is a verbatim copied source comment AND it carries an internal ticket ID (`FLOW-1234`). Copied comments and internal tracker IDs never cross.
- Fix: rewrite as neutral behavior, e.g. "The component manages retry timing for a queue. It validates each entry and reschedules entries that are not yet committable; otherwise it commits them." No internal names, no sentinel value, no comment, no ticket ID.

### 4. `public_surface[1]` — `_flushBuffer` is mislabeled public
- `_flushBuffer` is marked `visibility: "public"` with reason "used internally during flush." "Used internally" is by definition **not** public surface. The leading underscore signals private. This is a private method name smuggled in under a public label.
- Fix: remove it. It is not externally documented, not a protocol field, not user-required.
- (`flowpack retry` as a documented CLI subcommand is legitimately retainable public surface, so `public_surface[0]` is fine.)

### 5. `observable_behaviors` (private identifiers + copied algorithm shape + copied string)
- "The function parseFooInternal iterates entries with `for i := 0; i < len(buf); i++` and breaks on the first invalid mode." — private function name (`parseFooInternal`), copied loop structure (source-shaped pseudocode), and an internal buffer variable (`buf`). The algorithm description is more specific than the observable behavior requires.
  - Fix: "Entries are processed in input order, and processing stops at the first entry that fails validation."
- "increments RetryScheduler.failCount" — private class + private field name.
  - Fix: "a failure counter is incremented" (only if that counter is externally observable; otherwise drop).
- The log string `"flowpack: dropping malformed frame 0xDEADBEEF"` — a unique internal log message. Allowed only if it is recorded preflight as required public compatibility surface (e.g. a contract some integration parses). Nothing here establishes that, and the embedded `0xDEADBEEF` looks like a copied literal, not a stable contract.
  - Fix: drop the exact string unless it is confirmed public-compatibility-required and recorded as such. Otherwise: "Malformed entries are rejected and logged."
- "Retries use a 250ms fixed backoff." — a specific internal timing constant tied to the leaked HACK comment. Keep a timing requirement only if it is an externally observable / compatibility-required behavior; if so, state it as a requirement without the source-comment provenance. If it is just an internal implementation detail, drop the exact value.

### 6. `edge_cases`
- "mode byte == 7 triggers retryLater()" — internal sentinel value and private method name.
- Fix: "an entry that is not yet committable is rescheduled for retry." Keep "empty queue" — that one is a legitimate neutral edge case.

### 7. `compatibility_notes` — implementation-shaped pseudocode (clear leak)
- `"Pseudocode to copy: if x == 7 { retryLater() } else { commit(x) }"` — this is explicitly implementation-shaped pseudocode labeled "to copy," plus the private method name. This is exactly the "copy this loop / copy this structure" anti-pattern the wall exists to stop.
- Fix: delete entirely. Replace with a neutral compatibility note only if there is an actual external contract to state.

### 8. `test_scenarios`
- `"name": "TestParseFooInternal_Mode7"`, `"then": "retryLater is invoked and failCount increments"` — the test name embeds the private function name, and the assertion references private method (`retryLater`), private field (`failCount`), and the internal sentinel (mode 7).
- Fix: name and phrase the scenario in terms of observable behavior, e.g. name "RescheduleOnNonCommittableEntry", given "an entry that is not yet committable", then "the entry is rescheduled for retry and the observed failure count increases" (drop the counter if it is not externally observable).

## Fields that are acceptable as-is
- `flowpack retry` CLI subcommand and `--max-retries` flag in `observable_surface` / `public_surface[0]` — legitimate public CLI surface with a stated reason.
- `inputs`, `outputs` (`FP_RETRY_EXHAUSTED` is an externally visible error code, fine), `state_transitions` (`pending -> retrying -> exhausted` is neutral), `error_conditions`, `negative_behaviors`, `timing_or_ordering`, `security_relevant_behavior`, `invariants`, `non_goals` — these are written as neutral behavior and contain no private identifiers. Keep them.

## Bottom line
Do not hand this over. The draft contains, at minimum: source file paths, a coverage-ledger ref, four private identifiers (`RetryScheduler`, `parseFooInternal`, `retryLater`, `_flushBuffer`, plus the `failCount` field and `buf` variable), an internal sentinel value (mode byte 7) repeated across five fields, a copied source comment with an internal ticket ID (`FLOW-1234`), at least one copied literal/log string, and explicit "pseudocode to copy." Route it back to the contaminated side, rewrite the leaking fields into neutral observable-behavior statements as above, and have Agent 1.5 (the source-denied handoff sanitizer) re-review and set `leakage_review.reviewer_role` to `contaminated-handoff-sanitizer` before it goes anywhere near the clean team. If any of this already reached the clean workspace, treat the affected artifact as contaminated, quarantine it, and regenerate a scrubbed version rather than trying to mentally "un-see" it.
