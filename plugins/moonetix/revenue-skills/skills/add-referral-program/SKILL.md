---
name: add-referral-program
description: Build a referral program whose rewards are paid once, after a verified qualifying event, and taken back when that event is reversed. Codes and attribution are fixed at sign-up, self-referrals and second accounts of the same person are held back, one reward per referred account is enforced by a unique key, and referrers see what is pending. Covers a one-time bonus and a percentage of earnings, with caps. Covers Next.js with Prisma, Express, Django, Laravel and Rails. Use when the user asks to add referrals, invite a friend, refer and earn, invite codes or an affiliate bonus for users, or to stop referral farming and self-referrals.
license: MIT
compatibility: The verification step needs Node 20 or newer to run the bundled probe script.
metadata:
  author: moonetix
  version: "1.3.6"
---

# Add a referral program

This skill produces a referral program that pays for new customers and not for new rows in the users table: a code per account, an attribution that is written once at sign-up, a reward that waits for activity the server verified, and a take-back when that activity is reversed. It prevents the failures that turn referral programs into the cheapest money in an app. A bonus paid at sign-up, farmed with scripted accounts. A user who invites themselves. A reward that is posted twice, or stays after the friend's purchase was refunded. A referrer who is told nothing and opens a ticket.

## Before writing code

Read the project first, and ask the user only what the code cannot tell you.

- **Stack and database.** Language, framework, database engine, migration tool, test framework, job scheduler, and how the project opens a transaction.
- **Sign-up.** The handler that creates accounts, what it stores about the device and the address, and whether email addresses are verified and normalized.
- **The balance.** A ledger with a posting function, or a bare balance column. Which kinds of entries are verified activity (paid orders, credited conversions) and which are gifts.
- **Verified events and their reversals.** The handlers that post purchases and earnings, and the ones for refunds, chargebacks and reversed conversions. The reward hooks into both.
- **Any existing referral code.** A `referred_by` column, a bonus in the sign-up handler, a coupon used as an invite code. Note where it pays today.
- **What identifies a person.** Device ids, payment fingerprints from the payment provider, payout destinations.
- **Staff tools.** Where admin screens, permissions and the audit log live.

Then settle the decisions that belong to the user. Ask once, in one message, and offer the default.

| Decision | Default |
| --- | --- |
| Reward model | A one-time bonus per referred account. A percentage of earnings suits apps where users earn, and both can run together. |
| Qualifying event | The referred account's first verified payment, or verified earnings that reach a set amount. Never sign-up, email confirmation or a completed profile. |
| Who is rewarded | The referrer. A welcome bonus for the friend, if wanted, is posted at the same moment and not at sign-up. |
| Hold before the reward is posted | The refund or reversal window of the qualifying event, 14 days when unknown. Zero only for a small reward that cannot be withdrawn. |
| Can the reward be withdrawn | No, it is spent in the app. Commission on earnings follows the payout rules. |
| After a reversal | The reward is taken back, also when it is already spent, and that referral never rewards again. |
| Caps | 20 rewards per referrer in 30 days, then a person looks. For a percentage: 12 months and a fixed maximum per referred account. |
| Attribution | Link or typed code, remembered for 30 days, last code wins, written once at sign-up. |
| Same-person signals | Normalized email, device id, payment fingerprint and payout destination hold a referral. The network address only flags it. |
| What the referrer sees of the friend | Join date and state. No email address, no amounts. |

## Build

Use the project's migration tool, database layer and conventions. Do not add a framework to make the patterns fit. Attribution and the reward in Next.js with Prisma, Express, Django, Laravel and Rails are in [references/stacks.md](references/stacks.md).

1. **Make sure balance changes go through a posting function.** Rewards are ledger entries of kind `referral` and `referral_reversal` with the referred account's id as reference, posted through the function built by the `build-ledger` skill or the project's equivalent. If there is no ledger yet, the minimum is a `referrals` row per referred account and a balance change that happens only inside a guarded status change of that row. See [references/rewards-and-reversals.md](references/rewards-and-reversals.md), section "Without a ledger".

2. **Create the schema.** Copy `assets/referrals-schema.sql` into a migration and adapt names and key types. Leave out `referral_commissions` when there is no percentage model.

3. **Give each account a code.** Random, readable, unique, normalized on input. See [references/codes-and-attribution.md](references/codes-and-attribution.md), section "Codes".

4. **Capture and attach.** Store the code from the link in a first-party cookie or the session. Attach it inside the sign-up transaction, as a `pending` row keyed by the referred account. Remove any other code path that sets a referrer. Same reference, section "Attribution happens once, at sign-up".

5. **Record signals and compare both sides.** At sign-up, at the first payment and when a payout destination is set, record the signal and hold unpaid referrals where the other side has the same value. Same reference, section "One person, two accounts".

6. **Settle after every verified event.** Call the settle function in the transaction of each verified credit and of each reversal on a referred account. It moves the referral between `pending`, `qualified`, `rewarded` and `reversed`, and posts or takes back the reward. Remove any reward from the sign-up handler. See [references/rewards-and-reversals.md](references/rewards-and-reversals.md), sections "One function settles a referral" and "Where it is called".

7. **Schedule the job** that pays referrals whose hold has ended. Same reference.

8. **Add the percentage model if it was chosen.** One commission per earning, keyed by the earning's reference, capped per referred account and in time, and reversed with the earning. Same reference, section "Percentage of earnings".

9. **Show the referrer where things stand.** The code, the link, the totals and each referral with its state and the date a reward is due. See [references/visibility-and-staff.md](references/visibility-and-staff.md), section "The referrer's view".

10. **Build the staff view and its three actions:** block, release and revoke, each with a name and a reason. Same reference, section "The staff view".

11. **Schedule the reconcile queries** from the same reference and send a failure to a person.

## Rules that must hold

- Creating an account posts no reward to anyone. Nothing a client can produce for free does.
- The referral row is written once, in the sign-up transaction, keyed by the referred account. No code path changes its referrer.
- The referrer is resolved on the server from a code. The request never carries a referrer id that is trusted.
- An account cannot be its own referrer: a check in code and a constraint in the schema.
- The qualifying activity is computed from verified ledger entries or verified order rows, including their reversals. Never from a flag the client sets.
- The reward is one ledger entry with the referred account's id as reference, under the ledger's unique (kind, reference) key. A second one cannot exist.
- The reward is posted only when the hold has ended, compared with the database clock.
- Every path that reverses qualifying activity calls the settle function in the same transaction. A reversal takes back exactly the amount that was posted, once.
- A commission is keyed by the reference of the earning it came from, and its reversal takes back the stored amount.
- Commission is paid on verified earnings only. Never on bonuses, promo credits, purchases of credits or other commission.
- Caps are checked under a lock, in the transaction that posts.
- A blocked referral posts nothing until a named staff member releases it. Staff cannot decide on referrals of their own account.
- The referrer's view shows states and dates, not the friend's personal data and not the reason for a block.

## Verify

Write these tests in the project's own test framework, against a real database of the kind the project uses:

- Several sign-ups with one code, and no further activity, change no balance.
- A second attach for the same account, an unknown code and the account's own code each change nothing, and the sign-up still succeeds.
- Activity below the threshold leaves the referral `pending`. At the threshold it is `qualified` and nothing is posted.
- After the hold the job posts one reward. The job run again, the qualifying event delivered twice, and a second qualifying purchase post nothing more.
- A reversal during the hold returns the referral to `pending`. A reversal after the reward posts one take-back of the posted amount, also when the referrer has spent it, and a later purchase does not reward again.
- A reversal that leaves the verified activity above the threshold changes nothing.
- A referred account with the referrer's normalized email, device or payment fingerprint ends `blocked` and never pays.
- With the cap reached, the next referral is held, also when two qualify at the same moment.
- If there is a percentage model: one commission per earning reference, rounded down, stopped at the cap and the time limit, reversed once for the stored amount.
- Block, release and revoke each work once and store the staff member. After every test the reconcile queries return no rows.

Then run the app locally with test configuration and probe it. Describe each request in a JSON file as `scripts/probe.mjs` expects (run it without arguments for the format). `referrer.json` reads the referrer's balance, `referrals.json` reads the referrer's list with `"path": "referrals.length"`. `CODE` is the test referrer's code.

`scripts/probe.mjs` is the copy in this skill's folder. Run the commands below from the project directory, so that the request files resolve against the project. Their first line sets `PROBE` to that copy: replace `<skill directory>` with the folder this `SKILL.md` was read from, such as `.agents/skills/add-referral-program`.

```bash
PROBE=<skill directory>/scripts/probe.mjs
# Three sign-ups with the code and nothing else ({{i}} is 1 to 3). Three are a proof, do not script hundreds.
node "$PROBE" replay signup.json --times 3 --set-body 'email=ref-probe-{{i}}@example.test' \
  --set-body ref=$CODE --observe referrer.json --observe referrals.json

# A sign-up that names a referrer directly instead of a code.
node "$PROBE" send signup.json --set-body email=ref-probe-4@example.test \
  --set-body referrer_id=1 --set-body referred_by=1 --observe referrals.json

# The qualifying event for one of the new accounts: a signed test event, twice and at once.
node "$PROBE" replay purchase-event.json --times 2 --observe referrer.json
node "$PROBE" race purchase-event.json --parallel 10 --observe referrer.json

# The reversal of that event, twice.
node "$PROBE" replay refund-event.json --times 2 --observe referrer.json
```

Expected:

- The three sign-ups: each answers 2xx, the list grows by three, and the balance does not move.
- The direct referrer id: the account is created, and the list does not grow.
- The qualifying event: every delivery answers 2xx. With the hold set to zero in test configuration, the balance rises by one reward in total. With a hold, the balance does not move and the referral shows as qualified with a date.
- The reversal: both deliveries answer 2xx. The balance falls by one reward in total, or the referral returns to waiting if the reward was not posted yet.

Done when:

- the tests pass in the project's test run,
- the probes give the expected results three times in a row,
- a search of the sign-up and email confirmation handlers finds no call that posts to a balance,
- every refund, chargeback and reversal handler for a qualifying kind calls the settle function,
- the pay job and the reconcile queries are scheduled, and their failures reach a person,
- the rules of the program are stated where the code is shared: the condition, the wait, the cap, and that a refund takes the reward back.

## Out of scope / do not

- This skill does not build the ledger, verify payment or network events, or build the refund paths themselves. Those are the `build-ledger`, `build-webhook-endpoint` and `handle-refunds-and-reversals` skills. General protection of sign-up bonuses and trials is the `guard-signups` skill, and whether a reward can leave as money is decided in the `add-payouts` skill.
- It is not a multi-level scheme. Rewards for the referrals of referrals raise legal questions in many countries: raise that with the owner before building it.
- Do not pay at sign-up "just a small amount". Small times a script is large.
- Do not use the user id, the username or a counter as the code.
- Do not let an existing account add or change its referrer.
- Do not compute the reward from the current configuration when taking it back. Read the amount that was posted.
- Do not delete a referral row when an account is closed or banned. Block it, and keep the entries.
- Do not show the referrer why a referral was held, and do not show the friend's email address or purchases.
- Do not treat a matching network address as proof. Households share one.
- An optional starting point is the open-source library https://github.com/moonetix/referral-engine (JavaScript and PHP, MIT): readable codes, attribution with guard checks, flat, percentage and tiered commission plans with caps, and its own append-only commission ledger with holds and clawbacks.
