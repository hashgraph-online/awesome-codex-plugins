---
name: build-ledger
description: Build an append-only ledger with a cached balance for points, credits, coins or wallet money. One row per balance change, a unique (kind, reference) key that makes a repeated event harmless, debits that cannot overdraw, and a scheduled reconciliation check. Covers Next.js with Prisma, Express, Django, Laravel and Rails. Use when the user asks to add a balance, wallet, credits or points system, wants transaction history or an audit trail, needs to stop double credits or double spending, or has an app with only a balance column and wants to migrate it to a ledger.
license: MIT
compatibility: The verification step needs Node 20 or newer to run the bundled probe script.
metadata:
  author: moonetix
  version: "1.3.5"
---

# Build a ledger

This skill produces the one place in an app where balances change: a ledger table with one row per change, a cached balance that only one function writes, and a check that the two agree. It prevents three failures. A balance nobody can explain after the fact. An event that credits twice because it was delivered twice. Two requests that spend the same funds because both read the balance before either wrote it.

## Before writing code

Read the project first, and ask the user only what the code cannot tell you.

- **Stack and database.** Language, framework, database engine and version, the migration tool, the test framework. How the project opens a transaction, and whether the framework already wraps each request in one.
- **Where the balance lives today.** A column on the user row, a wallet table, a value computed from a history table, a counter in a cache. Note the type of the account key.
- **Every statement that changes a balance.** Search for writes to the column in handlers, jobs, admin tools, database triggers and scripts. This list is the scope of the work.
- **What identifies each change.** For each writer, the id that names the event: an order id, a provider transaction id, a payout id, an idempotency key from the client. A writer with no such id is not idempotent today, and step 4 has to give it one.

Then settle the decisions that belong to the user. Ask once, in one message, and offer the default.

| Decision | Default |
| --- | --- |
| Unit and precision | Whole numbers in the smallest unit (cents, coins, points). No fractions, no floating point. |
| What an account is | One balance per user. One row per owner and unit when users hold several (coins and gems, USD and EUR). |
| Cached balance | Keep one, written only together with the ledger row. Compute from entries instead only for low volumes. |
| Balance below zero | Only a reversal may cause it. While it is below zero, spending and payouts are refused. |
| Manual adjustments | A named staff permission, a written reason, a cap per adjustment. Staff cannot adjust their own account. |
| History before the ledger | One opening-balance entry per account. Old history tables stay read-only. |
| Retention | Entries are kept as long as financial records must be kept, also after the user account is closed. |
| Reconciliation | Nightly, with an alert to the people on call when any account disagrees. |

## Build

Use the project's migration tool, database layer and conventions. Do not add a framework or an ORM to make the patterns below fit. The posting function in Next.js with Prisma, Express, Django, Laravel and Rails, with the transaction, lock and unique key in each, is in [references/stacks.md](references/stacks.md).

1. **Create the schema.** Copy the template for the project's database from `assets/` (`ledger.postgres.sql`, `ledger.mysql.sql`, `ledger.sqlite.sql`) into a migration. Adapt names and key types to the project. If the balance already sits on an existing table, keep it there and point the ledger at that table. The columns and the reason for each are in [references/schema-and-posting.md](references/schema-and-posting.md).

2. **Write one posting function.** It runs inside a transaction that the caller opened. It inserts the ledger row under the unique (kind, reference) key, and only when a row was inserted does it update the cached balance. It returns whether the entry was posted. A repeated event returns "not posted" and changes nothing. Patterns for PostgreSQL, MySQL and SQLite are in [references/schema-and-posting.md](references/schema-and-posting.md).

3. **Make debits conditional.** A debit is one statement that subtracts only if the balance covers it, and the function fails when no row changed. The failure rolls the transaction back. Where a debit pays for something outside the database (a delivery, a payout, an API call), take the funds first, act second, and post a give-back entry if the action fails. Same reference, section "Debits and the order of work".

4. **Route every balance change through the function.** Each caller chooses a kind and a reference that is the same every time the same event arrives. Use the table of kinds and references in the reference file. Apply the negative-balance rule: only reversal callers pass the flag that allows debt.

5. **Add manual adjustments** if staff need them: an authenticated endpoint or command that posts an entry with the staff member as actor, a reason, a request id as reference and a cap. See [references/reconciliation-and-adjustments.md](references/reconciliation-and-adjustments.md).

6. **Add the reconciliation check.** One query that lists every account whose cached balance differs from the sum of its entries, wrapped in a command that exits with an error when the list is not empty. Schedule it with whatever the project already uses for jobs. Same reference.

7. **Expose history read-only.** The balance is read from the cache. The history is read from the ledger, newest first, paged by id. Nothing in the read path writes.

8. **If the app already has a balance column,** follow [references/migrating-a-balance-column.md](references/migrating-a-balance-column.md): opening-balance entries, then every writer moved behind the function, then a search that proves no direct write is left.

## Rules that must hold

A reviewer should be able to check each of these against the diff.

- Every change to a balance has exactly one ledger row, written in the same transaction as the balance update.
- The balance column is written in one function and nowhere else. A search of the code base for writes to it finds only that function.
- The ledger has a unique constraint on (kind, reference) in the schema, not only a check in code.
- The balance update runs only when the insert reported one new row.
- The reference comes from the event (order id, transaction id, request id). It is never a random value created at posting time for an event that can arrive twice.
- A debit is a single conditional statement, or runs under a row lock, and the code checks how many rows changed.
- Only reversal code paths may push a balance below zero. Spending, transfers and payouts never do.
- Amounts are integers, validated as non-zero and within range before posting. Amounts from a client are validated as greater than zero before they are negated.
- Ledger rows are never updated or deleted. A correction is a new entry that points at the entry it corrects.
- Every entry made by a person carries that person's identity from the session, and a reason.
- Funds are taken before an external effect, and given back by a new entry when the effect fails.
- The reconciliation command exists, is scheduled, and fails loudly.

## Verify

Write these tests in the project's own test framework, against a real database of the kind the project uses, not a mock:

- Posting the same (kind, reference) twice returns "posted" once, and the balance moves once.
- Posting the same (kind, reference) from ten concurrent calls moves the balance once.
- A debit larger than the balance fails, leaves the balance unchanged and leaves no ledger row.
- Concurrent debits that together exceed the balance: only as many succeed as the balance covers, and it never goes below zero.
- A reversal with the debt flag can take the balance below zero. A spend then fails.
- A failed delivery returns the funds once.
- Zero, fractional, non-numeric and out-of-range amounts are refused.
- Updating or deleting a ledger row fails.
- After every test above, the reconciliation query returns no rows. After a direct write to the balance in a test, it returns that account.

Then run the app locally with test configuration and probe the endpoints that use the ledger. Describe each request in a JSON file as `scripts/probe.mjs` expects (run it without arguments for the format). `me.json` reads the signed-in test user's balance.

`scripts/probe.mjs` is the copy in this skill's folder. Run the commands below from the project directory, so that the request files resolve against the project. Their first line sets `PROBE` to that copy: replace `<skill directory>` with the folder this `SKILL.md` was read from, such as `.agents/skills/build-ledger`.

```bash
PROBE=<skill directory>/scripts/probe.mjs
# A credit that arrives twice, in sequence and at the same moment.
node "$PROBE" replay credit.json --times 2 --observe me.json
node "$PROBE" race credit.json --parallel 10 --observe me.json

# A spend, sent ten times at once by a user whose balance covers two.
node "$PROBE" race spend.json --parallel 10 --observe me.json

# A negative amount on an endpoint that takes one.
node "$PROBE" send transfer.json --set-body amount=-400 --observe me.json
```

Expected:

- `replay` and `race` on the credit: every request answers 2xx, and the balance rises by the value of one credit.
- `race` on the spend: two requests answer 2xx and eight are refused with a 4xx, the balance falls by two prices and ends at zero or above. If the request carries an idempotency key, all ten are one purchase: the balance falls by one price.
- The negative amount: a 4xx, and the balance does not move.
- Run the reconciliation command after the probes. It reports no mismatch.

Done when:

- the tests above pass in the project's test run,
- the probes give the expected results three times in a row,
- a search for writes to the balance column finds only the posting function,
- the reconciliation command is scheduled and its failure reaches a person.

## Out of scope / do not

- This skill does not verify inbound events, handle refunds or build payouts. Those are the `build-webhook-endpoint`, `handle-refunds-and-reversals` and `add-payouts` skills. Each of them posts entries through the function built here.
- It is not double-entry bookkeeping for a company's accounts. It tracks what the app owes each user.
- Do not check for an existing row and then insert. Two deliveries at the same moment both pass the check. Insert, and let the unique constraint decide.
- Do not read the balance, compute in the application and write the result back. Not in SQL, and not through an ORM's `save()`.
- Do not catch the insufficient-funds error inside the transaction and continue. The ledger row of the failed debit is already inserted and must be rolled back.
- Do not fix a wrong balance with an `UPDATE`. Post a correcting entry, with a name and a reason.
- Do not keep processed event ids in a cache or in process memory as a replacement for the unique constraint. They expire and restart; the constraint does not.
- Do not put a `CHECK (balance >= 0)` on the cached balance if reversals may create debt. The conditional debit is the guard.
- Do not delete ledger rows when a user account is deleted. Detach the personal data and keep the entries.
