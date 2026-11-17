# Network facts

What 30 offerwall and survey networks send in a postback, how they sign it, how they signal a reversal and what answer they expect. Use it to pick the scheme and the reversal shape before writing the handler.

Read this first:

- **The network's dashboard and documentation are the authority.** Parameter names, macros and schemes change. This file records what the networks documented in November 2026. Check every row you rely on against the current documentation.
- **n/d** means not documented on the pages that were read. The feature may exist. For anything not listed here, check the network's documentation.
- Macros are shown with each network's own delimiters. Bare names are parameters the network fixes.

## Parameters

| Network | User id | Transaction id | Reward (your currency) | Payout to you | Status |
| --- | --- | --- | --- | --- | --- |
| AdBreak Media | `[YOUR_USER_ID]` | `[TXID]` | `[REWARD_VALUE]` | `[PAYOUT]` | `[STATUS]` |
| AdGate Media | `{s1}` | `{conversion_id}` | `{points}` | `{payout}` | `{state}` |
| AdGem | `{player_id}` | `{transaction_id}` | `{amount}` | `{payout}` | n/d |
| adjoe | `{user_uuid}` | `{trans_uuid}` | `{coin_amount}` | n/d | n/d |
| AppsPrize (AppSamurai) | `user_id` | `trans_id` | `event_coin_amount`, `coin_amount` | `cpi_bid` | n/d |
| ayeT-Studios | `{external_identifier}` | `{transaction_id}` | `{currency_amount}` | `{payout_usd}` | `{is_chargeback}` |
| Besitos | `user_id` | `transaction_id` | `reward_local_currency` | `payout` | `reverse` |
| BitcoTasks | `subId` | `transId` | `reward` | `payout` | `status` |
| BitLabs | `[%USER:UID%]` | `[%TX%]` | `[%VALUE:CURRENCY%]` | `[%VALUE:USD%]` | `[%ACTIVITY:TYPE%]` |
| Cherries | `{pid}` | `{transaction_id}` | `{user_reward}` | `{earned}` | `{status}`, `{subcode}` |
| CPAlead | `{subid}` | `{lead_id}` | `{virtual_currency}` | `{payout}` | n/d |
| Digital Turbine (DT Offer Wall) | `uid` | `_trans_id_` | `amount` | `payout_net` | n/d |
| inBrain.ai | `PanelistId` | `RewardId` | `Reward` | `RevenueAmount` | `RewardType` |
| Lootably | `{userID}` | `{transactionID}` | `{currencyReward}` | `{revenue}` | `{status}` |
| MM Wall | `{user_id}` | `{transaction_id}` | `{amount}` | `{payout}` | n/d |
| Monlix | `{{userId}}` | `{{transactionId}}` | `{{rewardValue}}` | `{{payout}}` | `{{status}}` |
| Moonetix | `{user_id}` | `{transaction_id}` | `{reward}` | `{payout}` | `{status}` |
| MyChips (LoyaltyPlay) | `{user_id}` | n/d | `{user_payout_in_vc}` | `{payout}` | n/d |
| Offery | `subId` | `transId` | `reward` | `payout` | `status` |
| Playfull | `{uid}` | `{transaction_id}` | `{payout}` | `{payout_usd}` | n/d |
| Prime Earn | `{user}` | `{tx_id}` | `{reward}` | `{payout}` | `{type}`, `{status}` |
| PubScale | `user_id` | `token` | `value` | `payout_usd` | n/d |
| RapidoReach | `endUserId` | `transactionId` | `currencyAmt` | `amt` | `status` |
| Tapjoy (Unity) | `snuid` | `id` | `currency` | `rev` | n/d |
| TapResearch | `uid` | `cpid` | `payout_amount` | `revenue` | `status` |
| TheoremReach | `{user_id}` | `{tx_id}` | `{reward}` | `{reward_amount_in_dollars}` | `reversal` |
| Unity LevelPlay (ironSource) | `[USER_ID]` | `[EVENT_ID]` | `[REWARDS]` | n/d | n/d |
| UPWALL | `{userid}` | `{transactionID}` | `{user_amount}` | `{payout}` | n/d |
| Wannads | `{user_id}` | `{transaction_id}` | `{reward}` | `{payout}` | `{status}` |
| YourSurveys | `[MEMBERID]` | `[ROUTEID]` | n/d | `[RPI]` | `[PYTHON-STATUS]` |

## Signatures

"Amount covered" says which amount the signature protects, and so which amount the handler may use: see "Deciding the amount" in postback-endpoint.md. "Everything": the signature covers the whole URL or body. "None": there is a signature, but no amount is inside it. "Nothing": no signature is documented, or the request carries only a shared secret.

| Network | Scheme | Signed input | Sent in | Amount covered |
| --- | --- | --- | --- | --- |
| AdBreak Media | SHA-256, secret appended | user id + offer id + transaction id + secret | `[HASH]` | None |
| AdGate Media | None documented | | | Nothing |
| AdGem | HMAC-SHA256 | v2: the full URL without `verifier`. v3: the request body | `verifier` parameter (v2), `Signature` header (v3) | Everything |
| adjoe | SHA-1, token appended | `trans_uuid` + `user_uuid` + `currency` + `coin_amount` + `device_id` + `sdk_app_id` + token | `sid`, hex | Reward |
| AppsPrize (AppSamurai) | SHA-256, token appended | `trans_id`, `user_id`, `coin_amount`, `coin_currency`, app token, S2S token | `sig` | Reward |
| ayeT-Studios | HMAC-SHA256, optional | All request parameters sorted by key, joined as a query string | `X-Ayetstudios-Security-Hash` header, hex | Everything |
| Besitos | HMAC-SHA256 | The URL as received, without `verifier` | `verifier`, last in the URL | Everything |
| BitcoTasks | MD5, secret appended | `subId` + `transId` + `reward` + secret | `signature` | Reward |
| BitLabs | HMAC-SHA1 | The whole callback URL without the trailing `&hash=` value | `hash`, hex | Everything |
| Cherries | HMAC-SHA256 | The entire URL without `hash` | `hash`, last, URL-safe Base64 without padding | Everything |
| CPAlead | Shared secret in the URL | Nothing is signed | `{password}` | Nothing |
| Digital Turbine (DT Offer Wall) | SHA-1, token first | token + `uid` + `amount` + `_trans_id_` + the `pub0` to `pub9` that are present | `sid`, hex | Reward |
| inBrain.ai | MD5, secret appended | `PanelistId` + `RewardId` + secret | `Sig` in the JSON body | None |
| Lootably | SHA-256, secret appended | `userID` + `ip` + `revenue` + `currencyReward` + secret | `{hash}` | Reward and payout, not the transaction id |
| MM Wall | HMAC-SHA1, optional | The entire URL before `&hash=` | `hash`, hex | Everything |
| Monlix | Shared secret in the URL | Nothing is signed | `{{secretKey}}` | Nothing |
| Moonetix | HMAC-SHA256 | `transaction_id:user_id:reward:status`, values as they arrive | `{hash}`, lowercase hex | Reward |
| MyChips (LoyaltyPlay) | HMAC-SHA256, opt-in | The raw query string without the signature, pairs sorted | `{signature}`, lowercase hex | Everything |
| Offery | MD5, secret appended | `subId` + `transId` + `reward` + secret | `signature` | Reward |
| Playfull | SHA-1, key appended | All parameters except `hash_key`, sorted by name, joined as a query string, then the key | `{hash_key}` | Everything |
| Prime Earn | SHA-1, salt appended | The full URL without `hash` and `shash`, then the salt | `hash` | Everything |
| PubScale | MD5, secret first | `secret.user_id.value.token`, with `value` as an integer | `signature`, hex | Reward |
| RapidoReach | MD5, secret appended | `transactionId` + secret | `txnHash`, lowercase hex | None |
| Tapjoy (Unity) | MD5 (standard), HMAC-SHA256 (improved) | Standard: `id:snuid:currency:secret`. Improved: the request body | `verifier` parameter, `X-Tapjoy-Signature` header | Reward, or everything |
| TapResearch | HMAC-MD5 | The query string before `&sig=`, as received | `sig`, last, lowercase hex | Everything |
| TheoremReach | SHA-1 based | Not documented publicly for the reward callback | `hash` | n/d |
| Unity LevelPlay (ironSource) | MD5, key appended | timestamp + event id + user id + rewards + key | `signature` | Reward |
| UPWALL | Shared secret in the URL | Nothing is signed | `{password}` | Nothing |
| Wannads | MD5, secret appended | `user_id` + `transaction_id` + `reward` + secret | `{signature}` | Reward |
| YourSurveys | HMAC-SHA256 | The full URL without the signature parameter | `[HMACSIGN]` | Everything |

Where the amount is not covered, or nothing is signed, the amount in the request proves nothing by itself. Add the address allowlist, and where the network offers an API to look a transaction up, ask it before crediting.

## Reversals, answers and sender addresses

| Network | Reversal signal | Expected answer | Sender addresses |
| --- | --- | --- | --- |
| AdBreak Media | Status `rejected`, same transaction id, amounts stay absolute | 200. The body must not contain `fail` or `error` | Published |
| AdGate Media | Sent only when `{state}` is in the URL | 200 | Published |
| AdGem | n/d | Any 2xx | On request |
| adjoe | n/d | 200, or 401 for a wrong `sid` | Published |
| AppsPrize (AppSamurai) | n/d | 200 | n/d |
| ayeT-Studios | `is_chargeback=1`, the original id with an `r-` prefix, negative amounts. Must be enabled | Always 200 | n/d |
| Besitos | The same transaction id again with `reverse=1` | 200 | On request |
| BitcoTasks | `status=2`, same `transId`, amounts stay absolute | The body `ok`, exactly | Published |
| BitLabs | Activity type `RECONCILIATION`, with `[%REF%]` naming the original. Values may be negative, positive or 0 | 200 | Published |
| Cherries | Negative `earned` and `user_reward`. Subcodes 201, 301 and 401 are reversals, 101 an adjustment | n/d | n/d |
| CPAlead | None on this callback | 2xx, no redirects | Published |
| Digital Turbine (DT Offer Wall) | n/d | 200 with an empty body, also for duplicates | Published |
| inBrain.ai | `RewardType` of `offer_completion_reversed` on offer callbacks | n/d | n/d |
| Lootably | `status=0`, though the documentation says only status 1 is sent today | The body `1` | n/d |
| MM Wall | n/d | 200 | Published |
| Monlix | `{{status}}` of 2 | n/d | n/d |
| Moonetix | `status=2`, the same transaction id, the same positive reward and payout | Any 2xx within 6 seconds. Redirects are not followed. Up to 5 retries | Published |
| MyChips (LoyaltyPlay) | A separate deduction postback URL, payout as a positive value | n/d | Published |
| Offery | `status=2`, amounts stay absolute | The body `ok` | n/d |
| Playfull | n/d | n/d | Given during onboarding |
| Prime Earn | Surveys: `type=4`, negative amounts, its own `tx_id`, and `reconciled_tx_id` naming the original | 200 or 201 | Published |
| PubScale | n/d | Any 2xx | Published |
| RapidoReach | Status `R`. `currencyAmt` can be negative | 200, only after processing | Shown in the dashboard |
| Tapjoy (Unity) | n/d | 200. A 403 stops retries | n/d |
| TapResearch | A second postback with the same `cpid` and status `Rejected` | Any 2xx within 5 seconds | Published |
| TheoremReach | A separate webhook: POST JSON with event type `reversal` or `ban` | n/d for the reward callback | n/d |
| Unity LevelPlay (ironSource) | n/d | 200 with `<event id>:OK` in the body | Published |
| UPWALL | A negative `{payout}`. No status macro | n/d | n/d |
| Wannads | The same transaction id with status `rejected` and a negative reward. Migrated accounts get a positive reward with status 2 | The body `OK` or `1` | Published |
| YourSurveys | A separate reconciliation callback | n/d | No static list |

Published address lists change. Load them from the network's documentation into configuration, not into code.

## Reversal shapes

Map each shape to "which original transaction, credit or reversal" before the handler in postback-endpoint.md runs.

- **The same transaction id with a reversal status.** The handler as written.
- **A new id that points at the original:** a prefix on the original id, or a separate reference field. Look the original up by that reference and record the reversal under the original's id.
- **A negative amount with no status.** Treat the sign as the status and ignore the magnitude. Take back what was stored.
- **A separate reversal URL or webhook.** Authenticate it by its own rules, then run the same reversal.
- **Adjustments** that raise or lower a reward without cancelling it. Post each as its own ledger entry under the adjustment's id, and cap the total taken back at what was credited.
- **No reversal signal at all.** The network still deducts reversed conversions from what it pays you. Reconcile against its reports every month and post the reversals yourself.

## Moonetix in detail

The same sources document this network beyond the postback. Wall links and SDK flows of the other networks are not in the source data: check the network's documentation.

- **Postback URL template:** `https://yoursite.com/postback?user={user_id}&tx={transaction_id}&event={event_id}&status={status}&reward={reward}&payout={payout}&hash={hash}`
- **Statuses:** 1 credited, 2 reversed. Reward and payout are never negative; the status says add or take back.
- **Unsigned macros:** `{payout}`, `{event_id}`, `{offer_id}`, `{offer_name}`, `{country}`, `{ip}`, `{sub1}` to `{sub5}`. Use them for logs and reports, never for the amount.
- **The reward** arrives in your currency, computed from the rate and share set for the offerwall. Credit it as received. Do not reformat it before hashing: `150` and `150.00` give different hashes. If it carries a fraction, such as `12.75`, round it down once to whole units after the hash check and accept it, because a refusal would cost the user the whole reward.
- **Wall link:** `https://wall.moonetix.com/<app id>?user_id=<id>&hash=<hex HMAC-SHA256 of the user id, keyed with the link hash salt>`. User ids are 1 to 100 characters from `A-Z a-z 0-9 . _ @ : + -`. `sub1` to `sub5` are optional and not signed. The link hash salt and the postback secret key are different values.
- **Mobile SDKs** open the wall with a single-use session token that your server requests with its API key. The token expires after 10 minutes. The app never holds the key or the salt.
- **Test postbacks** from the dashboard have a transaction id that starts with `test_` and offer id 0.
- **Delivery:** GET, user agent `Moonetix-Postback/1.0`, retries after about 1 minute, 5 minutes, 30 minutes, 2 hours and 6 hours.

Further reading: [offerwall-postback-handlers](https://github.com/moonetix/offerwall-postback-handlers) has tested handlers in PHP, Node.js, Python and Java, and [affiliate-postback-macros](https://github.com/moonetix/affiliate-postback-macros) is the source of the tables above, with a link to each network's documentation.
