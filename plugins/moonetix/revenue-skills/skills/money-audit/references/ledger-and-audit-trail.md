# Ledger and audit trail

**Class id:** `ledger-and-audit-trail`

When a balance is a single number that code overwrites, nobody can say afterwards why it has the value it has. Every other class in this audit becomes harder to detect, to size and to undo. This class rarely loses money by itself; it decides how expensive the other nine are.

## Where to look

The schema: how balances are stored and whether a table of entries exists. Every statement that changes a balance. Manual adjustment tools. Any job that compares the app's records with a provider's.

## Shapes that are bugs

**A balance with no history.**

```sql
UPDATE users SET balance = balance + 100 WHERE id = 42;    -- and no row anywhere says why
```

Some paths may write a history row while others do not. List every balance-changing statement from the money map and mark which ones leave a record. A single unrecorded path means the balance cannot be reconstructed.

**History that cannot be trusted.** Rows that are updated or deleted after the fact. Entries without the source of the change (which payment, which offer, which admin). Entries without a timestamp or with one the client supplied.

**History and balance that can disagree.** The entry and the balance update happen in separate statements with no transaction. After a crash, or a race, the two differ and nothing notices.

**No reference back to the outside world.** A credit that does not store the provider's event or transaction id. A refund then has nothing to look up, and a duplicate has nothing to collide with.

**Manual changes without a name.** Support staff can edit a balance and the system does not record who, when, how much or why.

**No reconciliation.** Nothing ever checks that the balances equal the sum of their entries, or that the payments the app recorded match the provider's settlement reports. A discrepancy can grow for months.

**Retention that erases evidence.** History purged on a short schedule, or deleted along with the user account while financial records are still needed.

## What correct looks like

- An append-only ledger: one row per balance change with account, signed amount, kind, a reference to the source (order id, transaction id, payout id, admin request id), actor and time.
- A unique constraint on (kind, reference). It gives the audit trail and idempotency in one move.
- The balance column, if kept for speed, is written only by the code that inserts the ledger row, in the same transaction.
- A scheduled check that `SUM(ledger.amount)` equals the balance for every account, and a periodic comparison with provider reports.
- Corrections are new entries, never edits.

## How to prove it

This class is proved with a trace, at any severity: the validator does not ask for a live run here. Step one: the schema line that defines the balance. Further steps: each balance-changing statement that writes no record, quoted with file and line. If the app runs, add a demonstration: perform a credit, a promotion and a purchase, then show that the stored records do not add up to the balance.

```bash
node scripts/probe.mjs send promo.json --observe me.json    # balance moves; no table gains a row that explains it
```

## Not a bug

- An event-sourced design where the balance is always computed from entries. That is the strict form of a ledger.
- History kept by the payment provider for money the app never holds, such as a plain subscription with no credits. The class is then not applicable.
- A read-optimized balance cache that is rebuilt from the ledger on demand.

## Severity

This is the one rule for records; the severity table in `SKILL.md` defers to it. No record for some or all balance changes: medium, or high when the app pays out, because losses cannot be traced or recovered. Manual adjustments that do not record who made them, when, how much and why: medium. No reconciliation job: low.
