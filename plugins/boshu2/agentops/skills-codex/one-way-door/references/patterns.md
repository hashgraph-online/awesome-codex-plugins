# One-way door patterns (layer 3 fallback)

These patterns apply **only** to decisions with no entry in
[`decision-registry.md`](./decision-registry.md). The registry is primary; this
file exists because ad-hoc decisions get raised faster than anyone declares them.

**Calibration rule.** Add a pattern when a false negative would be expensive and
a false positive costs one extra question. Do not add a pattern that fires on
routine work — a gate that asks about everything is a gate the caller learns to
click through, which is the same outcome as no gate.

Matching is case-insensitive substring/regex against the decision summary: read
the `Pattern` column of the tables below and report which row fired, so a
reviewer can re-run the same match by hand.

## Data destruction

| Pattern | Undo cost |
|---|---|
| `rm +-[a-z]*[rf]` | Deleted tree is gone unless a backup predates the decision |
| `\bdrop (table|database|schema|index|column)\b` | Schema and rows gone; restore needs a dump taken before this |
| `\bdelete from\b` | Rows gone; a `WHERE` typo widens the blast radius silently |
| `\btruncate\b` | Table emptied, often without a transaction log to replay |
| `\b(wipe|purge|hard[- ]delete|empty the trash)\b` | Named as permanent by the operation itself |

## Version control

| Pattern | Undo cost |
|---|---|
| `\bforce[- ]push\b\|push +--force\b` | Overwrites remote history; a collaborator's un-fetched work is unrecoverable |
| `\breset +--hard\b` | Discards working tree and index with no reflog entry for uncommitted content |
| `\bbranch +-D\b` | Unmerged commits are only recoverable from reflog, and only locally |
| `\bstash (clear\|drop)\b` | Stash entries are not reachable after clear |
| `\bfilter-(branch\|repo)\b\|\brewrit(e\|ing) history\b` | Every downstream clone diverges |

## Credentials and access

| Pattern | Undo cost |
|---|---|
| `\b(revoke\|rotate\|reset)\b.*\b(key\|token\|secret\|credential\|password)s?\b` | Old value cannot be restored; every consumer must be re-issued |
| `\b(grant\|escalate)\b.*\b(admin\|root\|owner\|write)\b` | Access already used cannot be un-used |
| `\bcommit\b.*\b(secret\|key\|token\|credential)\b` | A pushed secret is compromised even after removal from history |

## Infrastructure

| Pattern | Undo cost |
|---|---|
| `\bterraform destroy\b` | State and resources torn down; recreate is not restore |
| `\bkubectl delete\b` | Persistent volumes and their data may go with the object |
| `\bdrop (namespace\|cluster)\b\|\bdeprovision\b` | Region and identity may not be reclaimable |

## Publication and outward-facing action

| Pattern | Undo cost |
|---|---|
| `\b(publish\|post\|tweet\|announce)\b` | Distribution is not recalled by deletion; caches and indexes persist |
| `\b(send\|reply to)\b.*\b(email\|message\|invite)\b` | Delivered mail cannot be unsent |
| `\b(tag\|cut\|ship) a release\b\|\bpush a tag\b` | Consumers pin the tag; retag breaks their checksums |
| `\bmerge to (main\|master\|trunk)\b\|\bdirect[- ]push\b` | Reverting is a new commit, not an erasure; CI and deploys already fired |
| `\baccept (terms\|agreement)\b\|\bgrant (oauth\|sso)\b` | Consent is recorded on someone else's system |
| `\b(purchase\|buy\|charge\|transfer funds)\b` | Money moved |

## Structural forks

These are reversible with effort rather than impossible, and are listed because
the effort is routinely underestimated by an order of magnitude.

| Pattern | Undo cost |
|---|---|
| `\bschema migration\b` | Down-migrations lose data written under the new shape |
| `\bbreaking change\b\|\bapi (contract\|signature) change\b` | Consumers already adapted; a revert breaks them a second time |
| `\bdata model change\b` | Backfills are one-directional in practice |
| `\barchitectur(e\|al) (change\|fork\|decision)\b` | Every file written after the fork encodes it |

## Deliberately excluded

Patterns considered and rejected, so they are not re-proposed:

- `rollback` — a rollback is usually the *undo*, not the one-way step. Gating it
  makes recovery slower during an incident, which is when the gate hurts most.
- `overwrite`, `replace`, `update` — fire on routine edits. Layer 2 (effect
  class) already covers the cases where these leave the working tree.
- `deploy` — reversible in a repo with a working rollback path; irreversible
  without one. That is a property of the caller's pipeline, so declare it in the
  registry per-repo rather than guessing here.
