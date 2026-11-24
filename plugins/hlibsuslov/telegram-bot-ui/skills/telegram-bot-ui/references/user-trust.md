# User trust and anti-abuse

How a bot decides how much friction to put in front of a user: new accounts in a group, a first order in a
shop, a referral payout, a giveaway entry. It covers:
- the signals Telegram really gives;
- the signals your own records give;
- what an account's id says about its age, and what it does not;
- optional external anti-spam lists;
- a policy that keeps honest users in and gives everyone an appeal.

Read it when an operator asks to "detect suspicious users", "check account age", "score trust" or "use a
spam database". It is optional: most bots need none of it.

Labels:
- **[Official]** the Bot API, or a service's own documentation;
- **[Heuristic]** this skill's rule;
- **[Check]** confirm before relying on it.

Code: `examples/python/tgkit/trust.py`, with `IdAgeEstimator` and `assess()`, tested in
`tests/test_user_trust.py`. Data rules: [user-data.md](user-data.md).

## 0. What trust is for, and what it is not

- **It sets friction for an action, it does not judge a person.** The output is a tier with reasons that
  decides one of: let through, add a check, hold for review, or restrict in this bot's own space.
- **It never identifies who someone is.** No looking up the real person behind an account, no phone
  lookups, no joining Telegram data with outside profiles (§6).
- **It degrades gracefully.** Unknown signals count as unknown, not as suspicious. A new or private
  account is normal, not guilty.
- **It is disclosed.** The privacy policy says which signals are used, and whether any leave the bot, such
  as an id sent to a blocklist (§4).

## 1. What Telegram gives a bot

The Bot API has **no account creation date, no report count and no scam or fake label** **[Official]**:
`py -3 scripts/tg_api_lookup.py search scam` finds nothing. What it does give:

| Signal | Where | Weight **[Heuristic]** |
|---|---|---|
| Stars rating level | `getChat` → `ChatFullInfo.rating` (`UserRating.level`); the docs call it an indication of reliability when buying digital goods | a positive signal for purchases; absence means nothing |
| Premium | `User.is_premium` | weak positive at most; never a price or access gate |
| Username, profile photos | `User.username`; `getUserProfilePhotos` → `total_count` | adds weight to another signal only; many honest people have neither |
| Join requests | `ChatJoinRequest` (with `bio`), and `query_id` for bots assigned to process join requests: `sendChatJoinRequestWebApp` or `answerChatJoinRequestQuery` within 10 s | the place for a check before someone enters a group |
| Telegram's own anti-spam | `ChatFullInfo.has_aggressive_anti_spam_enabled` (admins turn it on) | prefer it in groups before building your own |

Through MTProto, the protocol behind third-party clients, which bots can also use with their token, user
objects carry `scam`, `fake` and `verified` flags that Telegram sets **[Check]**. If the bot already runs
on an MTProto library, these are Telegram's own labels and the strongest signal available. Never use a
personal account ("userbot") to collect data for a bot: that is scraping.

## 2. Your own records: the best signals

What the bot has seen itself is specific, current and fair, because it describes behaviour in your service:

| Signal | Example |
|---|---|
| First seen by the bot | known for 6 months |
| Completed orders, paid and not disputed | 3 completed orders |
| Refunds, chargebacks, disputes | 2 disputes in 30 days |
| Reports upheld by your moderators | 2 upheld reports (not raw reports: anyone can report anyone) |
| Behaviour at entry | a link in the first message, posting within seconds of joining, the same text in several chats |
| Moderator decisions | cleared on appeal; restricted on 2026-11-02 |

Keep them with dates and expire them (§7). An old upheld report should not follow someone forever.

## 3. Account age from the id

**What is true.** Telegram assigns user ids that grow over time on average, and does not publish
creation dates **[Official]**. Third-party "account age" tools fit a curve through ids with known dates and
all label their output as estimates **[Check]**. Their maintainers note that ids are handed out in blocks,
so two accounts registered at the same moment can be millions apart and the order is not strict. No tool
publishes a measured accuracy. Treat any answer as a bracket of months.

**How to estimate honestly.** `IdAgeEstimator` builds the bracket from your own anchors, never from tables
copied from the internet:

- **kind `created`:** accounts whose registration day you know, such as accounts your team registered and
  test accounts. These give the **lower bound**: an id above one created on day D was probably created
  after D.
- **kind `seen`:** the first day your bot saw an id. That is an **upper bound** only: the account existed
  then.

```python
from datetime import date
from tgkit.trust import AgeAnchor, IdAgeEstimator, Signals, assess

est = IdAgeEstimator(load_anchors())             # your own records
after, before = est.bracket(user.id)             # (None, None) when nothing supports either side
a = assess(Signals(created_after=after, has_username=bool(user.username)), date.today())
```

**Rules [Heuristic]:**
- Only a lower bound can say "new". A recent upper bound says nothing about newness.
- The estimate is a reason for **a check, never for a ban**. People register new accounts every day: new
  users, a lost phone, a fresh start. `assess()` never moves anyone past `watch` on age.
- Say "probably created recently (estimate)" in moderator tools, never a date.

## 4. External anti-spam lists (optional)

A shared list of accounts banned for spam across many groups catches spammers on their first message. It
also sends an identifier to a third party, so it needs conditions.

**CAS, Combot Anti-Spam** **[Official, cas.chat/api, read 2026-11-24]:**
- `GET https://api.cas.chat/check?user_id=<id>`, with an API key from a Combot account, as `api_key=` or
  `Authorization: Bearer <key>`;
- the answer has `ok`, `result`, and `description` / `error_code` on errors. The shape of `result` is not
  documented: parse it defensively and treat any listing as a hit;
- commercial bots must credit it ("Powered by CAS" with a link);
- bans are tied to the user id, expire automatically after a while, and have **no appeal**: Combot does
  not remove them on request.

Other lists exist (SpamWatch-style services, lols.bot and others). Their APIs, terms and appeal routes were
not verified here. Read each one's own documentation before using it.

**Conditions for any external list [Heuristic, from the Bot Developer Terms §4]:**
1. **Disclosed.** The privacy policy names the service and says the Telegram id is checked against it for
   abuse prevention. Without that, sending ids to a third party breaks the Standard Bot Privacy Policy.
2. **The id only.** Never names, messages, phone numbers or anything else.
3. **At the moment of risk:** a join, a first message, a first order. Not a sweep of every user.
4. **Fail open.** A timeout or an error means no signal, not a hit. Cache an answer for hours, not
   forever.
5. **Your own appeal.** Because a list like CAS has none, your moderators can clear a user
   (`Signals.manual_allow`) and that wins in your bot.
6. **No feeding back without due process.** Do not report users to shared lists from automatic decisions.

## 5. The policy: tiers and actions

`assess()` returns one of four tiers with reasons. Defaults to tune per bot:

| Tier | When (defaults) | Group | Shop / payouts / giveaways |
|---|---|---|---|
| `trusted` | two of: 3+ completed orders, Stars rating level 3+, known 6+ months; or cleared by a moderator | no checks | instant payouts, higher limits |
| `normal` | no signal either way | the group's usual rules | the usual flow |
| `watch` | 1 upheld report; or the account is probably new (age adds weight to a thin profile, never alone) | a check at the join request (a Mini App question, not a puzzle), links held for the first day, slow mode on first messages | a lower first-order limit, payouts after a holding period, one entry per giveaway with manual review of winners |
| `restricted` | a blocklist hit, or 2+ upheld reports | muted or read-only, messages to moderators; **a ban only after a human looks** | orders held for review; no payouts until reviewed |

**Rules [Heuristic]:**
- **Graduated and reversible.** Every action has an end date or a review. Nothing permanent is decided by
  code alone.
- **A human for anything that matters:** bans, frozen money, closed accounts. Under the GDPR (Art. 22),
  decisions with significant effects need human involvement and a way to contest them.
- **Tell the user what happens and how to appeal, in neutral words.** For example: "New members can post
  links after their first day." Or: "We're reviewing this order; it usually takes a few hours.
  [Contact support]." Never write "you are suspicious" or "you are on a spam list".
- **The bot never bans on age alone, a missing photo, a missing username or one raw report.**
- **Measure the cost.** Count honest users caught (appeals won) as well as spammers stopped, and loosen the
  thresholds when appeals succeed often.

## 6. What the skill declines

| Request | Why not | Instead |
|---|---|---|
| Find out who the person behind an account is, their phone or other profiles | identifying people from outside data; not allowed by Telegram's terms and privacy law | trust tiers about behaviour in your bot |
| Scrape a "spam score" or profile from websites, leaked databases or userbots | scraping and datasets are prohibited (Bot Developer Terms §4.3) | documented APIs used with the conditions in §4 |
| Ban automatically on account age or "looks fake" | catches honest new users; no due process | `watch` friction and human review |
| Share your own block decisions with other bots or a public list automatically | other people's data to third parties without consent or due process | keep decisions in your bot; report through a list's own process only after review |
| Use trust tiers for prices, discounts or access to essential services | discrimination; profiling beyond abuse prevention | tiers only gate risky actions |
| Keep reports and tiers forever | data minimisation and retention | expire them (§7) |

## 7. Storing, logging, expiring

- **Store per user:**
  - `first_seen`;
  - counters of completed orders and disputes;
  - upheld reports with dates;
  - moderator decisions with the moderator and the reason;
  - the last blocklist check with its date.

  Store no raw messages beyond what moderation needs.
- **Log every automatic action** with the tier and the reasons from `assess()`, so a moderator can explain
  it on appeal.
- **Expire:**
  - upheld reports after 12 months;
  - blocklist answers after 24 hours;
  - "new account" stops mattering once the bot has known the user for a month.

  These are defaults to fit your policy.
- `/deletedata` ([user-data.md](user-data.md) §4) also deletes trust records. The exceptions are records you
  must keep for a legal claim or fraud case; say which in the privacy policy.

## 8. Checklist and digging deeper

- [ ] Telegram's own tools first: aggressive anti-spam in groups, join requests with a check.
- [ ] Your own records as the main signals, dated and expiring.
- [ ] Age from the id only as a bracket from your own anchors; it never bans.
- [ ] External lists disclosed in the privacy policy, the id only, at the moment of risk, fail open, cached briefly.
- [ ] Tiers graduated and reversible; a human for bans and frozen money; the user told how to appeal.
- [ ] Appeals counted; thresholds loosened when honest users are caught.
- [ ] Nothing that identifies the person, scrapes, shares decisions or prices by trust.

Digging deeper:
- `py -3 scripts/tg_api_lookup.py show ChatJoinRequest | UserRating | sendChatJoinRequestWebApp`, and after
  each Bot API release `tg_api_lookup.py diff`, in case Telegram starts exposing new trust signals.
- CAS documentation: https://cas.chat/api, https://cas.chat/banned_faq.
- MTProto user flags: core.telegram.org, the `user` constructor in the schema.
- GDPR Art. 22 (automated decisions) and recital 47 (fraud prevention as a legitimate interest), for the
  legal basis your policy states.
