---
name: money-audit
description: Audit the code paths where an app handles money, credits, points or rewards, and report the bugs that lose money, each with the exact file and line, the quoted code, and a proof (a request, a test or a code trace). Use when the user asks to audit, review or pen-test payments, payment webhooks, postbacks, balances, wallets, credits, coupons, referrals, refunds or payouts, asks whether users can cheat or farm the system, or is about to launch something that charges or pays out. Also use to check one money-handling change before it ships, or one provider integration such as a Stripe, Paddle, Lemon Squeezy, PayPal or RevenueCat webhook, App Store server notifications or Google Play real-time developer notifications.
license: MIT
compatibility: The bundled scripts need Node 20 or newer. Probes are sent only to an app running on the local machine.
metadata:
  author: moonetix
  version: "1.3.6"
---

# Money audit

Find the bugs that let someone create, take or keep value they did not pay for or earn: a webhook nobody verifies, a credit that lands twice, a balance two requests can spend at once, a refund that leaves the goods behind. This is a source-first review of business logic. It is not a general security scan.

A finding counts only when it names the file and line, quotes the code that is there, and carries a proof: a request or a test someone else can rerun, or a step by step code trace. A bundled script rejects a finding whose quote is not at that file and line, or whose proof is missing.

## Two ways to use this skill

- **Focused check.** The user asks about one endpoint, one change or one question ("can this postback be replayed?"). Read the matching reference under `references/`, inspect the code, and answer with file and line evidence. Write no files.
- **Full audit.** The user asks to audit the project, asks for a report, or is preparing a launch. Run the five steps below and write the results to a `money-audit/` folder in the project.

If the request could mean either, ask once which one is wanted.

## Ground rules

1. **Audit first, fix later.** Do not change application code during the audit unless the user asked for fixes in the same request. A report on code you just edited is hard to trust.
2. **Probe only what runs locally.** Start the app on this machine with test configuration. Never send probes to production, staging shared with others, or a third party's API. The probe script refuses any host that is not a loopback address unless that host is named on the command line, and that option is for a test system the user owns and asked you to test.
3. **No real secrets on paper.** Use test keys. If a live secret is found in the code, report where it is and what it opens. Never copy its value into a finding, a command or the report.
4. **Evidence or nothing.** Every finding quotes the code at its location and carries a proof: a live request, a test, or a step by step code trace. A suspicion without one goes in your notes, not in the report.
5. **Say it in money.** For each finding state who can do it (anyone on the internet, any signed-in user, a partner holding a valid key, staff) and what is lost (free credits, a double payout, goods kept after a refund).
6. **Stay on the money path.** Cross-site scripting, missing headers and similar issues belong to a security review. Mention a serious one in a single line at the end and move on.

## Workflow

### 1. Map the money paths

Read [references/map-money-paths.md](references/map-money-paths.md). List every place where value enters the system, moves inside it, or leaves it, with the handler's file and line, who can call it, and what it trusts. Read the database schema as well as the handlers: a unique constraint or its absence decides several classes below. Save the map as `money-audit/money-map.md`.

### 2. Hunt, one class at a time

Work through all ten classes. Read the reference for a class before hunting it; each lists the code shapes to look for, how to prove them, and the cases that look like bugs but are not.

| Class | The question | Reference |
| --- | --- | --- |
| `unverified-events` | Can someone outside make the app believe a payment or conversion happened? | [unverified-events.md](references/unverified-events.md) |
| `duplicate-credit` | Does a genuine event credit more than once when it arrives again? | [duplicate-credit.md](references/duplicate-credit.md) |
| `balance-races` | Can two requests at the same moment spend or withdraw the same funds? | [balance-races.md](references/balance-races.md) |
| `client-trust` | Does the server take a price, amount, plan or account from the request instead of its own records? | [client-trust.md](references/client-trust.md) |
| `money-arithmetic` | Are amounts stored and computed so that rounding, sign and range cannot be bent? | [money-arithmetic.md](references/money-arithmetic.md) |
| `refunds-and-reversals` | When money goes back, does what it bought go back too, exactly once? | [refunds-and-reversals.md](references/refunds-and-reversals.md) |
| `promo-and-referral-abuse` | Can free value be claimed repeatedly, by one person or by a script? | [promo-and-referral-abuse.md](references/promo-and-referral-abuse.md) |
| `payout-controls` | Is every withdrawal limited, held, and paid exactly once? | [payout-controls.md](references/payout-controls.md) |
| `secrets-and-access` | Are the keys and the endpoints that move money out of reach of ordinary users? | [secrets-and-access.md](references/secrets-and-access.md) |
| `ledger-and-audit-trail` | Can every balance be explained from stored records after the fact? | [ledger-and-audit-trail.md](references/ledger-and-audit-trail.md) |

When a flaw fits two classes, file it where its fix lives:

| The flaw | File it under |
| --- | --- |
| A withdrawal that pays twice when requests overlap | `balance-races`. Missing limits and holds go under `payout-controls`. |
| A negative, fractional or malformed amount | `money-arithmetic`. A price or grant the server should have looked up goes under `client-trust`. |
| A signing secret with a working default, or one a client can read | `secrets-and-access`. A check that can be skipped at request time goes under `unverified-events`. |
| An account chosen by the request instead of the session | `secrets-and-access` |
| A reversal that repeats | `refunds-and-reversals`. A credit that repeats goes under `duplicate-credit`. |
| A manual balance change that records no actor or reason | `ledger-and-audit-trail`. An adjustment route an ordinary user can reach goes under `secrets-and-access`. |

When the project integrates a payment provider or an app store, read [references/payment-providers.md](references/payment-providers.md) while hunting `unverified-events`, `duplicate-credit` and `refunds-and-reversals`. It lists the shapes to look for in Stripe, Paddle, Lemon Squeezy, PayPal, RevenueCat, App Store and Google Play integrations.

For each class end with one of three results: at least one candidate finding, **clear** (with the files read and the guard that makes it safe), or **not applicable** (the app has no such feature).

### 3. Prove each candidate

Read [references/proving-findings.md](references/proving-findings.md). Before proving a candidate, try to disprove it: look for the guard in middleware, in the schema, in a queue or gateway in front of the handler. Then prove what survives, in this order of preference:

1. **Probe.** Run the app locally and send the request with `scripts/probe.mjs` (`send`, `replay` for the same request in sequence, `race` for the same request in parallel). Watch a balance before and after with `--observe`.
2. **Test.** Write a failing test in the project's own test framework that shows the loss.
3. **Trace.** When the app cannot be run, walk the code from the point where the value enters to the point where money moves, quoting each step.

### 4. Record and validate

Write `money-audit/findings.json` in the format described in [references/report-format.md](references/report-format.md), then run:

```bash
node <skill directory>/scripts/validate-findings.mjs money-audit/findings.json --root .
```

The validator checks that each quoted snippet is really at the stated file and line, that each finding has a proof, and that all ten classes are accounted for. Fix the report until it prints `VALID`. If a snippet does not match, reread the file and correct the finding, or withdraw it. Never loosen a snippet until it matches something, and never edit the validator.

### 5. Report

```bash
node <skill directory>/scripts/render-report.mjs money-audit/findings.json --root . --out money-audit/REPORT.md
```

Then tell the user, in order of money at risk: what was found, how it was proved, and which classes are clear. Offer to fix the findings. Fix patterns for each class are in its reference; if the companion skills from this collection are installed (`build-ledger`, `build-webhook-endpoint`, `handle-refunds-and-reversals`, `add-payouts` and the others), use them for the larger repairs.

## Severity

| Level | Use it when |
| --- | --- |
| critical | Anyone, or any signed-in user, can create or take value at will, and can repeat it. |
| high | The loss is real but needs a condition: a valid partner key, good timing, an existing balance. Or the loss per attempt is capped. |
| medium | Loss happens only in unusual conditions, or a missing control turns another flaw into a loss. |
| low | Nothing is lost today and nothing else becomes easier to exploit: a timing-unsafe comparison alone, a missing reconciliation job. |

Missing or untrustworthy records, including manual balance changes that do not say who made them, take their level from the rule in [ledger-and-audit-trail.md](references/ledger-and-audit-trail.md#severity), not from this table.

Rate each finding by what it allows by itself. When one finding makes another easier to reach (an unsigned webhook turns a retry-only duplicate into something anyone can trigger), keep both ratings and name the chain in the impact of each.

When the loss depends on how the code is deployed (the database engine or store, the number of workers, timestamps the caller supplies), rate the setups the project ships, documents or uses in its examples, and name the condition in the impact. A setup the documentation warns against does not raise the rating.

A code trace alone can support any level, but the validator warns when a critical or high finding was never run. Run it if the app can be started. Ledger findings are the exception: a missing record is shown by the code, not by a request.

## If the agent can delegate

When sub-agents are available, give each class in step 2 to a separate one along with the money map, and give each candidate in step 3 to a fresh one whose only job is to disprove it. The coordinating agent alone writes `findings.json`. Without sub-agents, for a small app, or on a machine short on resources, do the same work in sequence.

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/probe.mjs` | Send a request once, in sequence or in parallel, edit it on the way, and report statuses and the change in watched numbers. Loopback targets unless a host is named. |
| `scripts/validate-findings.mjs` | Check `findings.json` against the project: quoted code, proofs, coverage. |
| `scripts/render-report.mjs` | Turn a valid `findings.json` into `REPORT.md`. |

All three run with `node`, need no packages, and print usage when called without arguments. The paths above are relative to this skill's folder: call them by their full path from the project directory, so that `--root .` and the request files resolve against the project.
