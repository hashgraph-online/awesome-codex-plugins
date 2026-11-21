---
name: add-offerwall
description: Add an offerwall to a website, app, game, bot or community so users earn the app's own currency. Builds the wall link or iframe URL on the server for the signed-in user, a postback endpoint that verifies the network's hash, credits each transaction id once, computes the reward on the server and takes it back once on a reversal, and a hold before fresh earnings can be withdrawn. Covers Next.js with Prisma, Express, Django, Laravel and Rails. Use when the user asks to add or integrate an offerwall, survey wall or rewarded offers, to handle or fix a postback or S2S callback, or reports double credits, fake credits or chargebacks from an offer network.
license: MIT
compatibility: The verification step needs Node 20 or newer to run the bundled probe script.
metadata:
  author: moonetix
  version: "1.3.6"
---

# Add an offerwall

This skill produces the four pieces an offerwall needs: a wall link built on the server for the signed-in user, a postback endpoint that credits each conversion exactly once, a reversal path that takes each credit back exactly once, and a hold that keeps fresh earnings from being withdrawn. It prevents the failures that drain rewards apps: a postback anyone can forge, a retry that credits twice, an amount taken from a field nobody signed, a chargeback that is acknowledged and ignored, and coins that are paid out before the network takes them back.

**Which of the three skills.** Use this one for an offerwall or survey wall: the wall link, the postback that credits, the reversal postbacks and the hold. For payment webhooks and app store notifications, use `build-webhook-endpoint`. For refunds and chargebacks of payments, and for taking back what other rewards a credit caused, use `handle-refunds-and-reversals`.

## Before writing code

Read the project first.

- **Stack.** Language, framework, database, migration tool, test framework, and how the project opens a transaction.
- **Accounts and sessions.** How a request is tied to a user, and the type and format of the account id.
- **The balance.** A ledger with a posting function, or a bare balance column. Every existing place that credits a user.
- **Existing integrations.** Postback or webhook handlers already in the code, and how they verify, deduplicate and reverse. Other networks must keep working.
- **Where coins leave.** A cash-out, gift cards, transfers, or spending inside the app only.
- **What sits in front of the app.** Proxies, CDNs, bot protection and rate limits that could block a server-to-server call, and how the client address is read.
- **The rate.** Where coins per dollar and the user share are defined today, if anywhere.

Then settle the decisions that belong to the user. Ask once, in one message, with the default.

| Decision | Default |
| --- | --- |
| Network | The one the user has an account with. If none yet: AdGem, ayeT-Studios, BitLabs, Lootably, Moonetix or another from [references/network-facts.md](references/network-facts.md). |
| Where the wall appears | An "Earn" page for signed-in users: an iframe on the web, a web view or the network's SDK in an app, a private link from a bot. |
| User id sent to the network | The account's own stable id. Never an email address or a username. |
| Rate and user share | The values the app already uses. If there are none, ask; the `design-reward-economy` skill sets them. |
| Rounding | Down, once, to whole units of the currency. |
| A reversal after the coins are spent | The balance goes below zero. Spending and payouts are refused until it is back above. |
| Hold before cash-out | 30 days on offer earnings, then resized from the app's own reversal data. Spending inside the app is not held. |
| What can be cashed out | Offer earnings past the hold. Bonuses only if the owner says so. |
| A postback for an unknown user | Logged, answered with 2xx, not credited. |
| Test postbacks in production | Verified and logged, not credited to real accounts. |

## Build

Follow the project's stack and conventions. Do not add a framework to make the patterns fit. The postback route and handler in Next.js with Prisma, Express, Django, Laravel and Rails are in [references/stacks.md](references/stacks.md).

1. **Read the network's documentation** and write down, in the code as comments or in the project's docs: the postback parameters, the signature scheme and exactly which fields it covers, how a reversal is signaled, the answer the network expects, and its retry schedule. [references/network-facts.md](references/network-facts.md) has these for 30 networks as a starting point. The network's dashboard is the authority.

2. **Configuration.** The link secret, the postback secret and any API key come from the environment, are required at start-up and have no default. The rate, the share and the hold come from one configuration module.

3. **The wall link.** A server function that takes the user from the session and returns the signed URL, and a page or an authenticated endpoint that serves it. Nothing secret reaches the client, and a user id in the request is ignored. Patterns for web pages, single-page front ends, mobile apps, games and bots are in [references/wall-link.md](references/wall-link.md).

4. **The conversion record.** A table with one row per network transaction, keyed by network and transaction id, holding the account, the payout, the coins credited and the status. Schema in [references/postback-endpoint.md](references/postback-endpoint.md).

5. **The postback route.** Outside session, CSRF and rate-limit middleware. It authenticates first, in constant time, over the values exactly as they arrived. Then it validates shapes and decides the amount on the server from fields the signature covers and the app's own rate. Sections "The route", "Authenticate first" and "Deciding the amount" in [references/postback-endpoint.md](references/postback-endpoint.md).

6. **The credit.** One transaction: insert the conversion row, and only when a row was inserted post the ledger entry through the posting function that the `build-ledger` skill builds, with kind `offer` and a reference made of the network and the transaction id. Section "The handler" of the same reference.

7. **The reversal.** One transaction: flip the conversion from credited to reversed, and only when a row changed post the opposite entry, for the stored amount, to the stored account, with the flag that allows debt. A reversal with no credit is recorded so that a late credit pays nothing. Map the network's way of signaling reversals onto this with "Reversal shapes" in [references/network-facts.md](references/network-facts.md).

8. **If the project has no ledger yet,** the minimum is a unique key on the transaction id: the conversion table's primary key, with the balance update in the same transaction and only after the insert created a row. Section "Without a ledger: the minimum" of [references/postback-endpoint.md](references/postback-endpoint.md). Say to the user that this closes double credits but gives no history, and that the `build-ledger` skill is the next step.

9. **The answer.** 2xx only after the commit, also for duplicates and ignored events. 4xx for a bad signature. 5xx when storing failed, so the network retries. An exact body where the network requires one. Section "What to answer" of the same reference.

10. **The hold.** A function that returns what an account may withdraw: offer earnings older than the hold, minus reversals and payouts, capped by the balance. Every cash-out path calls it inside the transaction that takes the funds (the `add-payouts` skill), and the interface shows held coins as pending. Section "The hold" of the same reference.

11. **Around it.** A log line per postback with the raw query string and the answer, the address allowlist as a second layer where the network publishes addresses, notifications after the commit, and referral commissions posted and reversed with the credit (the `add-referral-program` skill). Section "Around the handler" of the same reference.

## Rules that must hold

- The wall link is built on the server. The user id in it comes from the session, and a user id in the request changes nothing.
- No secret, key or signing function exists in client code, in a page, in an API response or in the repository.
- The postback is authenticated before anything else runs, unconditionally, with a constant-time comparison. There is no debug or test switch a caller can set.
- Secrets have no default value, and the app does not start without them.
- Every value the handler acts on (account, amount, status, transaction id) is covered by the signature, or the handler does not act on it.
- The credited amount is computed on the server from authenticated fields and the app's own rate. It never comes from an unsigned parameter or from the client.
- A transaction id is credited once. The guarantee is a unique key in the schema, not a lookup in code.
- The balance changes only when the insert reported a new row, in the same transaction.
- A reversal takes back the stored amount from the stored account, once. The amount and the user in the reversal request are not used.
- A reversal for an unknown transaction changes no balance, and a later credit for that id pays nothing.
- The rule for a reversal after the coins are gone is explicit. With the default, only the reversal path may take a balance below zero.
- The answer is 2xx only after the change is committed. A failed write answers 5xx.
- Fresh offer earnings cannot be withdrawn before the hold has passed, and a reversal reduces what can be withdrawn at once.
- Client callbacks from a wall or an SDK never credit anything. They only refresh what the server says.

## Verify

Write these tests in the project's own test framework, against a real database of the kind the project uses:

- The link endpoint returns a link for the session's user, ignores a `user_id` in the request, refuses a guest, and its response contains no secret.
- A correctly signed credit raises the balance by the amount the server computes from the payout and the configured rate.
- The same postback twice in a row, and ten times at once, credits once.
- A missing signature, a wrong signature, a tampered amount, user or status, and a repeated parameter are each refused and change nothing.
- A reversal lowers the balance by the stored credit. A second reversal changes nothing.
- A reversal for an unknown transaction changes nothing, and the credit that arrives afterwards pays nothing.
- A reversal after the coins were spent leaves a negative balance, and a spend or payout is then refused.
- A forced database failure in the middle of a credit answers 5xx and stores nothing. The retry credits once.
- A fresh earning is not withdrawable. The same earning is withdrawable once the clock is past the hold.

Then start the app locally with test configuration (`test_postback_key_not_secret` as the postback secret) and probe it. `postback.json` holds the postback URL with `{{TX}}`, `{{STATUS}}` and `{{HASH}}` in place of the values, `me.json` reads the test user's balance, `link.json` requests the wall link. Run `node "$PROBE"` without arguments for the file format. The `sign` helper below fits a hash over `tx:user:payout:status`; sign the way the network signs.

`scripts/probe.mjs` is the copy in this skill's folder. Run the commands below from the project directory, so that the request files resolve against the project. Their first line sets `PROBE` to that copy: replace `<skill directory>` with the folder this `SKILL.md` was read from, such as `.agents/skills/add-offerwall`.

```bash
PROBE=<skill directory>/scripts/probe.mjs
export KEY=test_postback_key_not_secret
sign() { node -e 'console.log(require("node:crypto").createHmac("sha256", process.env.KEY).update(process.argv[1]).digest("hex"))' "$1"; }
CREDIT=$(sign "tx_local_1:42:0.85:1"); REVERSAL=$(sign "tx_local_1:42:0.85:2")
RACE=$(sign "tx_local_2:42:0.85:1"); FRESH=$(sign "tx_local_3:42:0.85:1")
ME="--observe me.json --var SESSION=$SESSION"

# A genuine credit, then retries of it, then a new one ten times at once.
node "$PROBE" send   postback.json --var TX=tx_local_1 --var STATUS=1 --var HASH=$CREDIT $ME
node "$PROBE" replay postback.json --var TX=tx_local_1 --var STATUS=1 --var HASH=$CREDIT --times 3 $ME
node "$PROBE" race   postback.json --var TX=tx_local_2 --var STATUS=1 --var HASH=$RACE --parallel 10 $ME

# Forged, on an id that was never credited: no signature, a changed amount, a changed user.
node "$PROBE" send postback.json --var TX=tx_local_3 --var STATUS=1 --var HASH=$FRESH --drop-query hash $ME
node "$PROBE" send postback.json --var TX=tx_local_3 --var STATUS=1 --var HASH=$FRESH --set-query payout=999 $ME
node "$PROBE" send postback.json --var TX=tx_local_3 --var STATUS=1 --var HASH=$FRESH --set-query user=43 $ME

# The reversal, delivered twice.
node "$PROBE" replay postback.json --var TX=tx_local_1 --var STATUS=2 --var HASH=$REVERSAL --times 2 $ME

# The wall link for the session's user, with another id in the request.
node "$PROBE" send link.json --var SESSION=$SESSION --set-query user_id=43 --extract url
```

Expected:

- `send`: 2xx, and the balance rises by one reward. `replay`: every answer is 2xx and the balance does not move. `race`: every answer is 2xx and the balance rises by one reward.
- The three forged requests: 4xx each, and the balance does not move.
- The reversal: both answers are 2xx, and the balance falls by one reward, not two.
- The link: it carries the session user's id, not 43, and the response contains no secret.
- Request a payout or read the withdrawable amount right after the credit: the fresh coins are not in it.

Done when:

- the tests above pass in the project's test run,
- the probes give the expected results three times in a row,
- a search of client code, pages and the repository finds no secret,
- a test postback from the network's dashboard reaches the deployed endpoint and is answered with 2xx, and the dashboard's log shows it.

## Out of scope / do not

- This skill does not build the ledger, the cash-out or sign-up screening, and it does not choose the rate. Those are the `build-ledger`, `add-payouts`, `guard-signups` and `design-reward-economy` skills. It is the fix for forged, repeated and unreversed postbacks that the `money-audit` skill reports.
- For networks and details not in the reference, check the network's documentation. Do not guess a parameter name or a hash formula.
- Do not credit from the browser, from an SDK callback or from a "reward earned" event in the app.
- Do not check for the transaction id and then insert. Insert, and let the unique key decide.
- Do not subtract the amount named in a reversal request. Look up what was credited.
- Do not answer 2xx before the commit, and do not answer 4xx or 5xx to a duplicate: the network would keep retrying.
- Do not rely on an address allowlist alone where the network offers a signature, and do not read the address from a header the caller controls.
- Do not put the postback route behind login, CSRF checks, a redirect or bot protection.
- Do not reformat values before hashing, and do not rebuild a URL that the network signed as a whole.
- Do not clamp a balance at zero on a reversal without recording the shortfall, and do not let a reversal fail because the balance is too low.
- Do not send email addresses, names or other personal data to the network as the user id or in sub ids.
