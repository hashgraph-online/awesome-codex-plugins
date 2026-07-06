# Verdict: NOT safe to hand off

This draft must not go to the clean implementation team in its current form. It carries a large amount of contaminated source expression that the leakage rules block from clean artifacts. It also mislabels its own leakage state and skips the required sanitizer. Several fields directly copy source text, identifiers, and pseudocode.

Two process problems first, then the field-by-field scrub list.

## Process problems (independent of content)

1. **It self-approved.** `leakage_review.reviewer_role` is `contaminated-source-analyst` with `status: "approved"`. The source analyst (Agent 1) does not approve its own drafts. Handoff requires Agent 1.5 (the source-denied contaminated-handoff-sanitizer) to review and approve. The valid value is `reviewer_role: "contaminated-handoff-sanitizer"`. As written, this artifact has never passed sanitization.

2. **`leakage_risk` is mislabeled.** It claims `"low"`. The actual content is high risk: copied comments, private identifiers, a literal log string, a hex magic value, and copy-this pseudocode. Do not trust the self-reported risk field.

## What has to be scrubbed (field by field)

### 1. `summary` — multiple violations, rewrite entirely
- `RetryScheduler`, `parseFooInternal`, `retryLater()` are private internal identifiers. Blocked.
- `mode byte equals 7` is a distinctive internal magic value. Blocked unless it is a documented public protocol value (it is not recorded as one here).
- The copied comment `// HACK: keep the 250ms backoff, FLOW-1234 will fix it later` is a copied source comment plus an internal ticket ID. Blocked outright.
- Rewrite to neutral behavior, for example: "The component schedules retries for queued frames. Each entry is validated; entries flagged for retry are rescheduled with a fixed backoff."

### 2. `source_unit_refs` — remove from the handoff artifact
`src/internal/flowpack/retry_scheduler.go` and `src/internal/flowpack/buffer.go` are source paths and source-only file layout. Source paths must never cross into clean artifacts. The clean team gets behavior, not source file locations.

### 3. `evidence_refs` — remove
`coverage-ledger.json#unit-retry` is a coverage ledger reference. Ledger refs are blocked from clean handoff.

### 4. `public_surface` — fix the bogus entry
- `flowpack retry` (kind `command`, documented CLI subcommand) is plausibly legitimate public compatibility surface. Keep only if it is genuinely documented and the reason holds.
- `_flushBuffer` is **not** public. It is a private method (leading underscore, reason given is "used internally during flush", which is the definition of private). Remove it. A name that is "used internally" by definition fails the public-compatibility test.

### 5. `observable_behaviors` — rewrite all three
- "The function `parseFooInternal` iterates entries with `for i := 0; i < len(buf); i++` and breaks on the first invalid mode." This is a private identifier plus a copied source loop. Rewrite to: "Entries are processed in input order, stopping at the first invalid entry."
- The literal log string `"flowpack: dropping malformed frame 0xDEADBEEF"` plus `RetryScheduler.failCount` is a unique log message, a hex magic value, and a private field name. Blocked. Rewrite to: "Rejected entries are not persisted, and a failure counter is incremented." Do not carry the literal string or the hex value unless that exact string is a documented public output the clean team must reproduce (record it as public surface if so; otherwise drop it).
- "Retries use a 250ms fixed backoff." The 250ms value is a behavioral observation, not expression. This one is acceptable as a neutral timing requirement and can stay (state it as a requirement, not as a copied constant tied to the HACK comment).

### 6. `edge_cases` — fix
`mode byte == 7 triggers retryLater()` repeats the magic value and the private identifier. Rewrite to: "an entry flagged for retry is rescheduled rather than committed."

### 7. `outputs` / `error_conditions` — verify, likely keep
`FP_RETRY_EXHAUSTED` is plausibly an externally visible error code. Keep only if it is genuinely part of the public/observable error contract; if it is internal, neutralize it. Record it as public surface with a compatibility reason if retained.

### 8. `compatibility_notes` — delete the contents
`Pseudocode to copy: if x == 7 { retryLater() } else { commit(x) }` is implementation-shaped pseudocode that mirrors source control flow, with the magic value and private identifier again. This is one of the most explicit violations in the file. Remove it. If a constraint is needed, express it abstractly: "Validate each entry before committing; reschedule entries that require retry."

### 9. `test_scenarios` — rename and neutralize
`TestParseFooInternal_Mode7` copies a source test name and private identifier; the `then` clause references `retryLater` and `failCount`. Source test names and fixture structure must not be copied. Rewrite to validate the same observable output without the source names, for example: name "retry-flagged frame is rescheduled and failure count increments", given "a frame flagged for retry", then "the frame is rescheduled and the failure counter increases."

## Summary of blocked items to remove or rewrite

| Location | Problem | Action |
|---|---|---|
| `summary` | private identifiers, magic value, copied `// HACK` comment + ticket ID | rewrite to neutral behavior |
| `source_unit_refs` | source paths / file layout | remove |
| `evidence_refs` | coverage ledger ref | remove |
| `public_surface[_flushBuffer]` | private method posing as public | remove |
| `observable_behaviors[0]` | private identifier + copied loop | rewrite |
| `observable_behaviors[1]` | literal log string, `0xDEADBEEF`, private field | rewrite |
| `edge_cases` | magic value + private identifier | rewrite |
| `compatibility_notes` | copy-this pseudocode mirroring source | delete content |
| `test_scenarios[0]` | copied source test name + private identifiers | rename + neutralize |
| `leakage_review` | self-approved by Agent 1 | re-review through Agent 1.5 |
| `leakage_risk` | mislabeled "low" | reassess after scrub |

## Next step

Do not patch this in the same context that has already seen the source. Send the draft back through Agent 1.5, the source-denied contaminated-handoff-sanitizer, working from a fresh source-denied context with only the neutral brief and this draft. It scrubs the items above, sets `leakage_review.reviewer_role` to `contaminated-handoff-sanitizer`, and either approves the scrubbed artifact or quarantines it. Items that are genuinely public compatibility surface (the documented `flowpack retry` subcommand, `--max-retries`, and any externally visible error code) can be retained, but each must be listed in `public_surface` with a concrete compatibility reason. Everything else gets rewritten to neutral behavior before anything reaches the clean team.
