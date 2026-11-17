# Map the money paths

The audit is only as complete as this map. A handler that is not on it will not be checked.

## What to list

Value does three things in an app. List every place where it does any of them.

| Direction | Typical entry points |
| --- | --- |
| **In** | Payment provider webhooks, checkout return URLs, app store receipts and server notifications, offerwall and affiliate postbacks, ad reward callbacks, promo and gift codes, sign-up and referral bonuses, admin grants, data imports |
| **Moves** | Spending credits or points, purchases of in-app items, transfers and gifts between users, currency conversion, subscription upgrades and downgrades, usage metering |
| **Out** | Withdrawals, gift card and crypto payouts, refunds the app issues, affiliate commissions paid, prize draws |

Also list the **rules** these depend on: price tables, exchange rates, plan definitions, limits, hold periods. A rule the client can influence is a finding in itself.

## How to find them

Search the code, then read the schema. Useful terms:

```
balance  credit  coins  points  wallet  amount  price  total  reward  bonus
payout  withdraw  redeem  cashout  refund  chargeback  dispute  reversal
webhook  postback  callback  ipn  notify  signature  hmac  secret
coupon  promo  voucher  referral  invite  trial  plan  subscription  entitlement  quota
stripe  paddle  paypal  lemonsqueezy  revenuecat  receipt  purchaseToken
```

Do not stop at HTTP routes. Check:

- **Background work:** queues, cron jobs, scheduled functions. A nightly "grant daily bonus" job is a money path.
- **Admin and support tools:** anything that edits a balance by hand.
- **Database rules:** with Firebase, Supabase and similar backends, the security rules or row-level policies are the server. A rule that lets a client write its own `balance` or `plan` field is an entry point.
- **Client code:** it shows which endpoints exist and which values the client sends to them.
- **Migrations and schema files:** column types for amounts, unique constraints, foreign keys, whether a ledger table exists.

## What to record for each path

| Field | Why it matters |
| --- | --- |
| Handler file and line | The finding will need it |
| Caller | Anonymous, signed-in user, partner server, staff, scheduler |
| How the caller is verified | Session, signature, shared key, IP list, nothing |
| Inputs it trusts | Every value that reaches a balance change or a price |
| What it writes | Tables and columns, external calls |
| Repeat protection | Unique key, state check, idempotency key, none |
| Atomicity | One statement, a transaction, or separate steps with I/O in between |

## A library instead of an app

When the target is a library (a ledger, a referral engine, a payment client), there are no routes. Each public function that credits, debits, pays or reverses is a row of the map, and the caller is the application that integrates the library. Fill the Caller and Trusts columns with what the library assumes about that caller: which values it accepts unchecked (account ids, amounts, timestamps), whether calls must be serialized, which store or connection it is given. Read the README and the type definitions for the duties the library hands to its caller. A duty that is documented and that the library's own stores and examples meet is not a finding; note it if it is easy to miss. A duty that is not documented, or that a shipped store or example breaks, is a finding. Prove findings with a failing test in the library's own test runner, or with a small script under `money-audit/evidence/`, since there is no app to probe. Use `environment` to say which runtime and versions the proofs ran on, which stores they used, and what could not be run, such as a database server.

## Also note, once

- **How balances are stored:** one mutable column, a ledger of entries, or both.
- **Amount types:** integer minor units, decimal, or floating point.
- **Concurrency:** one process, several workers, serverless functions. Several workers make every check-then-write a race.
- **The database's default isolation level** and whether handlers use transactions at all.

## Output

Write `money-audit/money-map.md`:

```markdown
# Money map: <project>

Storage: users.balance (REAL column), no ledger table.
Concurrency: Node cluster, 4 workers, PostgreSQL at READ COMMITTED.

| # | Direction | Path | Handler | Caller | Verified by | Trusts | Writes | Repeat protection | Atomicity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | in | POST /webhooks/pay | routes/webhooks.js:12 | provider | signature header | event.data.order_id | orders.status, users.balance | none | two statements, no transaction |
| 2 | moves | POST /api/spend | routes/wallet.js:9 | user | session | body.item | users.balance, purchases | none | read, await, write |
| 3 | out | POST /api/payouts | routes/payouts.js:7 | user | session | body.amount | users.balance, payouts, provider call | none | check, provider call, then deduct |
```

Every row is then checked against the ten classes. A row can produce findings in several of them.
