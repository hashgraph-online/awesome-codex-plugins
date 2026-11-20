---
name: guard-signups
description: Build sign-up screening and once-only redemption rules that keep sign-up bonuses, free trials, promo codes and referral rewards from being farmed by fake and duplicate accounts. Covers normalized emails, disposable domains, datacenter and Tor addresses, velocity limits, an explainable allow, review or block score, and atomic promo caps. Covers Next.js with Prisma, Express, Django, Laravel and Rails. Use when the user wants to stop fake sign-ups, multi-accounting, bonus or trial abuse, promo code farming, or duplicate accounts made with Gmail dots and plus tags.
license: MIT
compatibility: The verification step needs Node 20 or newer to run the bundled probe script.
metadata:
  author: moonetix
  version: "1.3.6"
---

# Guard sign-ups

Build the checks that decide what a new account may claim: a normalized email as the uniqueness key, a risk score in which every point has a written reason, three outcomes (allow, review, block), and redemption rules that hand out each bonus, promo code and trial once. The failure it prevents is the cheapest loss an app can have: free value collected many times by one person with many email strings.

Two halves, and both are needed. Screening lowers the number of fake accounts. The once-only rules remove the reason to create them. A score alone is a filter that a patient abuser tunes against. Unique keys alone do nothing about ten thousand scripted sign-ups.

## Before writing code

Read the project first:

- **Stack and storage.** Language, framework, database, test framework, and whether a shared store such as Redis is already in use.
- **The users table.** How email uniqueness is enforced today (often a unique index on the address as typed) and whether email verification exists.
- **Every way an account is created.** The sign-up handler, social login, invitations, admin tools, imports, and the change-email flow. Each one needs the same key.
- **How the client address is read.** Find the reverse proxy, load balancer or CDN in front of the app and the header it sets. This decides whether the address checks see visitors or the proxy.
- **The free value.** Every bonus, trial, promo code and referral reward: where it is granted, and whether it can be withdrawn or transferred.
- **The balance.** A ledger with unique references, or a bare balance column.

Then ask the user once. State the defaults; if the user has no preference, proceed with them.

| Decision | Default |
| --- | --- |
| Thresholds | Review from 30 points, block from 70. |
| What blocks alone | An invalid or disposable email. No network signal blocks alone. |
| What review means | The account is created and usable. The bonus is held until the email is verified and one more proof is given. |
| The second proof | A verified phone number, or the first verified payment or earning. |
| Velocity limits | Per address 5 an hour and 20 a day, per network prefix 50 a day, per normalized email 5 a day. |
| Tor exits and privacy relays | Tor is 40 points (review). Relays are 0 points, recorded only. |
| Trial identity | Normalized email, plus the card fingerprint when a card is collected. One trial per identity, ever. |
| Promo eligibility | A verified email. |
| Existing accounts that collide once normalized | Keep them. The oldest keeps the key; the others are flagged and get no further bonuses. |
| Data refresh | Lists stored with the app, refreshed weekly by a scheduled job. No network calls during sign-up. |
| Retention | Assessments 90 days. Unclaimed held bonuses void after 30 days. |

## Build

Follow the project's stack, naming and test framework. The references show Node, Python and PHP; translate, do not import a new framework. Table definitions are in `assets/signup-guard-schema.sql`. Promo redemption and bonus release in Next.js with Prisma, Express, Django, Laravel and Rails are in [references/stacks.md](references/stacks.md).

1. **Normalize the email and key uniqueness on it.** Add `email_normalized` with a unique index, write it on every path that creates an account or changes an address, and backfill existing rows without merging anyone. Rules per provider, code and the backfill are in [references/identity-and-signals.md](references/identity-and-signals.md).
2. **Check disposable domains.** Store the list with the app, match the domain and its parents, keep an allow list. Same reference.
3. **Read the client address correctly, then classify it.** Trust forwarding headers only from the project's own proxies. Classify the address as datacenter, Tor, privacy relay or CDN from the providers' published ranges, and compute the network prefix (IPv4 /24, IPv6 /64). Same reference.
4. **Count attempts.** One counter per rule and window, for the address, the network prefix and the normalized email. Count before deciding, outside the sign-up transaction. See [references/score-and-outcomes.md](references/score-and-outcomes.md).
5. **Score, decide, record.** The score is the sum of the reasons' points. Store one assessment row per attempt with the reasons, including refused attempts. Same reference.
6. **Wire the three outcomes.** Allow: create the account. Review: create the account, keep it usable, hold the bonus, ask for verification. Block: create nothing, show hints, give a contact path. Same reference, including the rules that protect users on shared networks.
7. **Hold and release bonuses.** A bonus is a `held` grant under a unique key, moved into the balance by a conditional update when its conditions are met. See [references/bonuses-promos-trials.md](references/bonuses-promos-trials.md).
8. **Make promo codes once per account with an atomic global cap.** A redemption row under a unique key and a conditional counter update, in one transaction, with attempt limits around it. Same reference.
9. **Stop trial restarts.** Claim the trial under a keyed hash of each identity (normalized email, card fingerprint, phone), in a table that outlives the account. Same reference. The keyed hashes here and in the counters need a server-side secret; if the project has none suitable, adding one is a new required setting, so name it as the first deploy step and make the app refuse to start without it.
10. **Pay referral rewards for verified activity.** Never at sign-up, once per invited user, reversed when the activity is. Same reference.
11. **Schedule the upkeep.** A job that refreshes the lists and refuses a failed or shrunken download, and a job that deletes expired counters and old assessments.

## Rules that must hold

- The unique index is on the normalized email. Mail goes to the address as typed.
- A normalization rule exists only where the provider documents it. Unknown domains are lowercased and nothing else.
- Every account-creating and email-changing path writes the normalized key in the same statement as the address.
- The client address comes from the socket, or from a forwarding header only when the socket peer is a trusted proxy.
- A non-public client address is never counted or scored.
- The score equals the sum of the stored reasons' points. Weights and thresholds are configuration, not code branches.
- No network signal or velocity rule blocks alone. Privacy relay addresses score zero.
- Every attempt is counted before the decision, and refused attempts still count.
- Review never disables the account. It holds the bonus and asks for verification.
- A block shows hints only: no score, threshold, list name or limit.
- A bonus enters the balance through one conditional transition from `held`, and its key makes a second grant impossible.
- A promo redemption inserts under a unique `(code, account)` key and takes the cap with a conditional update, in one transaction. The amount comes from the code's row.
- A trial claim is keyed by identity, not by account, and survives account deletion.
- A referral reward is created by verified activity of the invited user, once.
- Lists are read from local storage during a request. Nothing is fetched at sign-up time.

## Verify

Write these tests in the project's test framework:

- Normalization vectors, run against every implementation in the project: the Gmail variants collapse to one key, an Outlook plus tag and a custom-domain dot are kept, malformed addresses are rejected.
- A second sign-up with a dot or plus variant of an existing Gmail address is refused, and one user row exists.
- A disposable address is refused with a hint and leaves an assessment row with no account.
- An address inside a fixture datacenter range gives `review`: the account exists, the grant is `held`, the balance is zero. Use a fixture range list in tests so that data refreshes cannot break them.
- Thirty sign-ups with different emails from one residential address are all created, and none is blocked.
- Releasing a bonus twice credits once.
- One account redeeming a code twice gets it once. A code capped at N is redeemed N times across N + 1 accounts.
- A second trial is refused for the same normalized email with a new account, and for a new email with the same card fingerprint.

Then run the app locally with test configuration and probe it. In the local configuration, list `127.0.0.1` as a trusted proxy so the probe can present a client address. `signup.json`, `promo.json` and `me.json` are request files as described by `node "$PROBE"` with no arguments; `me.json` reads the balance of the account that `promo.json` signs in as.

`scripts/probe.mjs` is the copy in this skill's folder. Run the commands below from the project directory, so that the request files resolve against the project. Their first line sets `PROBE` to that copy: replace `<skill directory>` with the folder this `SKILL.md` was read from, such as `.agents/skills/guard-signups`.

```bash
PROBE=<skill directory>/scripts/probe.mjs
node "$PROBE" send signup.json --set-body email=jane.doe@gmail.com
node "$PROBE" send signup.json --set-body email=janedoe+1@gmail.com
node "$PROBE" send signup.json --set-body email=x@mailinator.com
node "$PROBE" send signup.json --set-body email=pat@example.org --set-header x-forwarded-for=<address in a datacenter range>
node "$PROBE" replay signup.json --times 8 --set-body email=repeat@example.org --set-header x-forwarded-for=203.0.113.9
node "$PROBE" replay promo.json --times 3 --observe me.json
node "$PROBE" race promo.json --parallel 10 --observe me.json
```

Expected, in order: the first answers 2xx; the second answers 4xx as a duplicate; the third answers 4xx with a hint; the fourth answers 2xx and the new account's balance is zero with the bonus held; in the fifth the first attempt answers 2xx, the next ones answer 4xx as duplicates, and the last ones answer 4xx with the too-many-attempts hint; in the sixth one request answers 2xx, two answer 4xx, and the balance rises by one redemption; the last, on a fresh account, shows one 2xx, nine 4xx and a balance that rises by one redemption.

Done when:

- All tests pass, and the probes show the results above.
- The backfill has run, and the collision report has been shown to the user.
- A support person can answer "why was this account held" from the stored reasons alone.
- The user has confirmed the thresholds, the second proof and the retention period.

## Out of scope, and what not to do

- **No device fingerprinting, no machine learning, no paid IP reputation service.** Add them later as more reasons in the same score if the volume justifies it.
- **No bot challenge implementation.** Use an existing challenge service, verified on the server, as a proof in the review path.
- **Residential proxies are not detected.** They exit through home connections. The once-only rules and payout checks are what bound that loss.
- **Do not block on a datacenter, Tor or velocity signal alone.** Real users arrive from cloud desktops, company gateways and shared addresses.
- **Do not strip dots or plus tags for every domain.** It merges different people on providers that treat those characters as significant.
- **Do not send mail to the normalized address.** It is a key, not an address.
- **Do not enforce "once" in application code alone.** A check followed by an insert loses to two requests that arrive together. The unique key is the control.
- **Do not count redemptions with `SELECT COUNT(*)` before inserting.** Use the conditional counter update.
- **Do not apply address lists to webhook or postback endpoints.** Their callers are servers by design; verify signatures there.
- **Do not show users the score or the rule they tripped.**

Related work in this collection: the `build-ledger` skill for the balance these grants credit, the `add-payouts` skill for keeping bonus value out of withdrawals, and the `add-subscriptions` skill for the subscription a trial starts.

## Further reading

- Ready-made Node and PHP checks for the screening half: https://github.com/moonetix/signup-guard
- Cloud, CDN, Tor and privacy relay ranges collected from the providers' feeds: https://github.com/moonetix/datacenter-ip-ranges
