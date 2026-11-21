---
name: suede-parity-contract
description: "Suede AI Parity Contract Skills. cross-surface parity contracts generated from live reference constants and asserted through follower behavior. Use when asked \"these app and web thresholds disagree\" or when rules are copied across web, mobile, docs, or services. NOT FOR: choosing the correct shipped value, diff review (suede-code), merge-gate setup (suede-ci-gate), or search audits (suede-seo-audit)."
metadata:
  display-name: "Suede AI Parity Contract Skills"
---

# Suede AI Parity Contract Skills

## Compatibility

Requires source access to one reference and each follower plus their build/test runtimes. Contract generation must import live constants; cross-repository updates require write authority to each repository.

For a concrete input, expected output, recovery path, and validation check, read
[the worked contract](references/worked-contract.md). Use it to check the handoff
before treating the task as complete.

```text
Iron Law: generate the contract from the reference surface's live constants.
A contract you transcribe is a second copy, and second copies drift.
A contract you generate cannot disagree with the code it came from.
```

Silent drift is the failure this prevents. Nothing crashes when a threshold is
copied wrong into a second language. The two surfaces simply start answering the
same question differently, and a user finds out before you do.

## Step 1: Name one reference surface

Exactly one surface is the reference. Every other surface is a follower that
asserts against it. Two references is two sources of truth with extra steps.

Pick the surface where the domain is most complete and most exercised, and write
that choice into the contract's `reference` field so nobody re-litigates it.

## Step 2: Build the contract by importing, never retyping

The builder imports the constants from the modules the application actually runs
on and serializes them. Retyping a value into the builder reintroduces exactly
the copy this skill exists to delete.

When a needed value is private, export it rather than duplicating it. That is a
one-line change and it keeps the count of definitions at one.

Serialize with stable key order and a trailing newline, because followers vendor
the file verbatim and a reformat shows up as a spurious diff.

## Step 3: Make staleness fail on the reference side

One test rebuilds the contract in memory and compares it to the committed file.
Without it the JSON is a snapshot someone took once.

Give it a write mode so regeneration is one command, and put that command in the
contract's README and in the file's own `note` field:

```bash
CONTRACT_WRITE=1 <test runner> <contract test>
```

Compare parsed objects first so the failure names the key that moved, then
compare raw bytes so a reformat is caught too.

## Step 4: Vendor byte-identical to each follower

Followers keep a copy at the same relative path. Prove it matches rather than
assuming:

```bash
shasum -a 256 <reference>/contracts/<name>.json <follower>/contracts/<name>.json
```

Two identical hashes, or the copy is stale. Record the re-sync command in the
follower's README so the next person does not invent one.

## Step 5: Assert through public behavior, not private internals

A follower test that reimplements the reference formula proves only that you can
write the same bug twice.

Assert what a user experiences. For a ladder, feed the contract's rung values to
the public accessor and check the level it returns. For a threshold, check the
boundary **and one step below it**: a threshold asserted only from above still
passes after it moves down.

Start the follower suite with a test that the contract loaded and is non-empty.
A file that fails to load makes every assertion after it vacuously true.

## Step 6: Pin the divergences you already have

You will find existing differences. The contract's job on day one is to make
them visible and hold them still, not to erase them.

Record each under `knownDivergences` with the value on each surface and a
`reason` that survives you leaving. Then add a guard asserting the divergence
list is **exactly** the expected set, so an entry added elsewhere is a failure
rather than a silence.

Each pinned divergence gets two assertions on the follower: that it still
differs by the recorded amount, and that it does **not** equal the reference. The
second one fires when someone closes the divergence and forgets the contract.

### Halt format: a divergence found mid-build

Changing a shipped constant changes behavior for real users, and which surface is
right is a product decision. At the moment you find one, stop and report:

```text
Divergence: <key>. <reference surface> says <a>, <follower> says <b>.
Both shipped. <one line on what a user feels>.
  1. Move <follower> to <a>
  2. Move <reference> to <b>
  3. Record it and decide later
```

Then wait. Do not pick for the user, and do not change either side as a side
effect of writing a contract.

## Step 7: Prove non-vacuity on both sides, in this run

A parity test that cannot fail is worse than none, because it reads as evidence.

Reference side: change one constant, watch the staleness test fail **naming that
key**, restore it, watch it pass. Follower side: edit one value in the vendored
copy, watch exactly the matching assertion fail, restore.

Paste both the failing and the passing output. "The tests pass" is not proof
that they can fail.

## Step 8: Closing a divergence is a two-repo operation

Both halves land or neither does:

1. Change the constant on the surface that is moving.
2. Delete the `knownDivergences` entry and regenerate the contract.
3. Re-sync the vendored copy to every follower.
4. Replace that follower's pinning test with a plain equality assertion.
5. Update the divergence-list guard to the new expected set.

Half of this leaves a red suite that names the missing half, which is the design
working.

## Versioning

Bump `version` only when the **shape** changes: a key added, removed, or
renamed. A changed value is never a version bump. A value is the thing the
contract exists to surface, and a follower should meet it as a failing
assertion rather than as a version it is allowed to skip.

## Done means

Every line proven by a command in this run:

- The staleness test fails on a changed reference constant and names the key.
- Every follower's vendored copy hashes identical to the reference's.
- Every follower suite passes, and its contract-load test proves the file is
  really there.
- Both non-vacuity demonstrations from Step 7 have pasted output.
- The divergence-list guard names the same set the follower tests pin.

## Boundaries

1. Do not decide which surface's value is correct. Record, report, and let the
   user choose.
2. Do not change a shipped constant as a side effect of writing a contract.
3. Do not hand-edit a generated contract or a vendored copy. Edit the source
   constant and regenerate.
4. Do not add a value to the contract that no follower asserts. An unasserted
   key reads as coverage and provides none.
5. Do not put credentials, hostnames, or per-environment configuration in a
   parity contract. It carries domain constants that must agree everywhere.
6. Do not let a follower's contract test reimplement the reference's formula.
   Assert the observable result.

## Routing

- Need the resulting tests wired as required checks or merge gates -> use
  `suede-ci-gate`.
- Need review of the contract diff -> use `suede-code` (`--findings-only` for
  no letter grade).
- Two surfaces behave differently even though the constants match -> the bug
  is in behavior, not canon; debug the follower's code path directly.
- Need to plan a multi-file rollout across surfaces -> use `suede-graph-flo-xr`,
  then return here for the contract itself.
- From `suede-code`: route "these two surfaces hold the same constant twice"
  findings back to `suede-parity-contract`.
