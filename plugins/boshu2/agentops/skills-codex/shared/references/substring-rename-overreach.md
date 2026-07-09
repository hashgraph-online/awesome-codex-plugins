# Substring Rename Overreach

When a bulk rename uses substring matching (`sed -i 's/Old/New/g'` over
many files), it catches identifiers from concepts that share a prefix with
the target but are semantically different. The build passes (symbols are
just identifiers — the compiler doesn't care what concept they encode) and
tests pass, but the post-rename code has semantic mismatches that surface
later as confused APIs and misnamed errors.

Mirror of `docs/learnings/2026-05-13-substring-sed-rename-overreach.md`
(authored from `/evolve` cycle 126). Copied here per CI's no-symlinks rule
so any skill (`/evolve`, `/crank`, `/refactor`, `/standards`) can reference
the rule.

## Worked Example (Cycle 126)

`daemon.QueueClaim → daemon.QueueLease` shipped via
`find ... -name '*.go' | xargs sed -i 's/QueueClaim/QueueLease/g'`.

The sed pattern caught identifiers from **two different concepts**:

1. **Intended:** `daemon.QueueClaim` (struct, lease semantics — has fields
   `ClaimToken`, `LeaseEpoch`, `LeaseExpiresAt`). Correctly renamed to
   `QueueLease`.
2. **Over-reach:** `rpi.ErrQueueClaimConflict`, `rpi.RequireQueueClaimOwner`,
   and the `cli/cmd/ao` wrappers `errQueueClaimConflict` /
   `requireQueueClaimOwner`. These are about **work-item claim coordination
   in `.agents/rpi/next-work.jsonl`** — when two workers race to claim the
   same harvested work item. That IS a Claim concept (per the BC2 contract:
   Claim = public assertion of a work slot), not a Lease.

Caught by the `PreToolUse:Bash` post-commit diff hook:

```go
func EnsureQueueItemClaimable(...) error {
    ...
    return ErrQueueLeaseConflict   // ← Claim API, Lease error name
}
```

`EnsureQueueItemClaimable` kept Claim-language (sed only matched
`QueueClaim`, not `Claimable`), but the error it returned was renamed to
`ErrQueueLeaseConflict`. The semantic mismatch was visible at a glance.

## The Rule (Pre-Rename Checklist)

Before any bulk sed rename across packages:

1. **Find the type definition** — `grep -rn 'type <OldName>\b'`.
2. **Enumerate every identifier that contains the substring** — not just
   the type itself. Use:
   ```bash
   grep -roE '\w*<OldName>\w*' cli/ scripts/ docs/ --exclude-dir=testdata \
     | sort -u
   ```
3. **Classify each identifier** by concept: the type-def concept vs.
   sibling concepts that share the prefix incidentally.
4. **Sed only on identifiers matching the target concept.** Use file
   restrictions, line-number restrictions, or per-concept regexes.
5. **After commit, re-read the diff.** Look for semantic inconsistencies —
   APIs that kept old language returning errors that took new language,
   or vice versa.

## Worked Pattern

```bash
# Step 1: type def
grep -rn 'type QueueClaim\b' cli/

# Step 2: enumerate ALL identifiers containing "QueueClaim"
grep -roE '\w*QueueClaim\w*' cli/ scripts/ docs/ \
  --exclude-dir=testdata | sort -u

# What you SHOULD see (with classification):
#   QueueClaim                 (the struct — daemon, rename)
#   ErrQueueClaimConflict      (rpi, WORK-ITEM claim — KEEP)
#   RequireQueueClaimOwner     (rpi, WORK-ITEM claim — KEEP)
#   errQueueClaimConflict      (ao wrapper — KEEP)
#   requireQueueClaimOwner     (ao wrapper — KEEP)

# Step 3: classify (above)
# Step 4: sed only on the struct + its method-receiver params
# Step 5: post-commit diff re-read
```

## Anti-Pattern Signal

If a single sed across N files moves a counter from `K → 0` **and** N is
large enough you can't diff-review the changes by eye, the rename almost
certainly over-reached. Lower N by restricting the file set, or use
`gopls rename` / IDE refactoring tooling that knows about identifier scope.

## When This Matters Most

Renames where the substring is a noun that has BOTH a domain concept
(BC1/2/etc.) AND an incidental code identifier:

- **Gate vs Validator:** `cli/internal/flywheel.Validator` has nothing to do
  with `scripts/check-*.sh` validators. Mass `Validator → Gate` sed would
  break it.
- **Run vs Cycle:** `CIRun` (BC2 port), `RPIRun` (rpi package),
  `ContextVariantRun` (eval) — all legitimate "Run" identifiers. Narrow
  renames only.
- **Session:** already-prefixed Sessions (`AgentSession`, `GCSession`,
  `GasCitySession`, `CLIFallbackSession`) are unaffected. Only the bare
  `type Session struct` declarations need the rename.

## See Also

- `docs/learnings/2026-05-13-substring-sed-rename-overreach.md` — the
  promoted canonical version (this is a skill-side mirror).
- `docs/contracts/ubiquitous-language.md` — the source-of-truth for which
  identifiers map to which concept.
- `skills/standards/references/go.md` — Go-specific rename conventions.
