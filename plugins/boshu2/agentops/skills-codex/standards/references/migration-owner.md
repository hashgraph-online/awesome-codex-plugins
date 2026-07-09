# Migration-Owner Discipline

One fail-closed **owner** per breaking migration. AgentOps is the verification
membrane: a format change (a retired surface, a renamed command, a schema bump,
a ledger-shape change) must never *silently corrupt* state, and must never
*ambiguously "fix"* it. This reference is the contract every breaking
retirement/migration conforms to.

The recurring pain this closes: "retired-surface debris is a CLASS" — `bd → br`,
skill retirement, registry drift, command renames. Each such break needs exactly
ONE owning check that detects the debris, fixes it atomically, and **refuses to
guess** when the state is ambiguous.

## The four rules

### 1. Version staging: warn → alias → hard-error

A breaking change ships in three staged phases, never as an abrupt cutover:

- [ ] **warn** — the old form still works; the owner emits a deprecation notice
      pointing at the new form.
- [ ] **alias** — the old form resolves to the new one (a hidden/compat alias),
      still warning; consumers migrate.
- [ ] **hard-error** — the old form is removed; using it fails closed with a
      message naming the owner and the new form.

Document which phase the migration is in, in the owner itself. Never jump warn →
hard-error in one release; the alias phase is what makes the cutover recoverable.

### 2. Atomic, format-preserving `--fix`

Detection is paired with a fix, and the fix is:

- [ ] **atomic** — write-temp-then-rename (or an equivalent transaction), never a
      partial in-place edit that a crash can leave half-applied.
- [ ] **format-preserving** — a text-targeted edit that preserves every other
      byte (comments, ordering, trailing newline). Never a lossy round-trip
      (e.g. re-serializing a YAML file drops load-bearing comments).
- [ ] **re-derived from ground truth** — the fixer re-scans current state; it
      never trusts a stale detector snapshot.

### 3. REFUSE ambiguous fixes (both forms present → skip + surface)

The load-bearing rule. When **both** the old form and the new form are present,
the owner **cannot know** which the author meant to keep — a genuine stale usage,
or a deliberate reference (a rename note, an alias doc, a historical example).

- [ ] When old AND new are both present → **skip that unit, surface it, do not
      guess.** A human chooses.
- [ ] Skipped units are reported (not swallowed) and hold the run below "done":
      an ambiguous refusal is *not* a completed fix.
- [ ] Fix only the unambiguous units in the same pass; the refusal is scoped to
      the ambiguous unit, not the whole run.

Silently rewriting an ambiguous unit is the exact failure mode this closes: it
destroys a deliberate reference or double-applies a rename. Refusing is fail-closed.

### 4. Interruptible ledger writes: idempotency-key + marker LAST

Any owner that appends to a ledger (a dedup/consumed/processed marker) must be
crash-safe under interruption. Absorbs `crash-safe-ledger-write-ordering` and the
`idempotent-spawn-epoch` principle.

- [ ] **idempotency-key** — each unit of work carries a stable key; re-processing
      the same key is a no-op, so a re-run after a crash never double-applies.
- [ ] **marker LAST** — write the payload/effect first, then the dedup/consumed
      marker as the *final* write. If the process dies mid-fix, the marker was
      never written, so the re-run re-processes the unit rather than skipping it.
- [ ] **derive-don't-mark, when you can** — the strongest owners skip a marker
      entirely and re-derive "already done" from ground truth (the file no longer
      holds the old form). Then interruption is inherently safe: there is no
      premature skip-marker to strand a half-done unit.

The anti-pattern: writing a "consumed" marker *before* the effect it guards. A
crash between the two strands the work — the marker says done, the effect never
landed, and the re-run skips it. Marker-last inverts that into a safe re-run.

## Worked example (the retrofit)

`bd → br` and skill retirement are the canonical breaks. The live proof in-tree
is the doctor's deprecated-`ao`-command → replacement migration
(`fm-skills-stale-command-refs`, `cli/internal/doctor/fix_skills.go`):

- Atomic + format-preserving: every rewrite flows through `Mutate`
  (temp-then-rename), line-targeted, other bytes preserved (rule 2). Yes.
- Refuse-ambiguous: a file holding **both** a deprecated command and its
  replacement is skipped and surfaced (`FixResult.Skipped`), never guessed
  (rule 3). Yes.
- Interruptible: the fixer re-scans ground truth each run and writes no
  skip-marker, so an interrupted fix is re-processed on re-run (rule 4,
  derive-don't-mark). Yes.

## Checklist for a new migration owner

- [ ] Exactly ONE owning check — not scattered across callers.
- [ ] Fails closed on every ambiguous or untrusted input (never fail-open).
- [ ] Staged warn → alias → hard-error, phase documented in the owner.
- [ ] `--fix` is atomic + format-preserving + re-derived from ground truth.
- [ ] Both-forms-present → skip + surface + hold below "done".
- [ ] Ledger writes: idempotency-key, marker LAST (or derive-don't-mark).
- [ ] A test proves the ambiguous case is refused, not rewritten.
