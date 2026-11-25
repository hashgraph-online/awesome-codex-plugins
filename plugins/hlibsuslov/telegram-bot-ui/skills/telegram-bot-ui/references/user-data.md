---
summary: "What Telegram gives a bot or Mini App about a user, how to ask for more, and the duties that follow: tiers, data inventory, consent, storage, deletion, review; read before collecting user data."
verified: "2026-11-24"
bot_api: "10.5"
---

# User data: what a bot or Mini App gets, and how to handle it

## Contents

- [0. The rules that come with the data](#0-the-rules-that-come-with-the-data)
- [1. Four tiers of data](#1-four-tiers-of-data)
- [2. Turning "collect everything" into a data inventory](#2-turning-collect-everything-into-a-data-inventory)
- [3. Asking for data the user gives](#3-asking-for-data-the-user-gives)
- [4. Storing, using and deleting](#4-storing-using-and-deleting)
- [5. What the skill does not build](#5-what-the-skill-does-not-build)
- [6. Review checklist](#6-review-checklist)
- [7. Digging deeper](#7-digging-deeper)

What Telegram gives a bot or a Mini App about the person using it, how each piece arrives, how to ask for
more, and what the developer must then do with it. Read it when an operator asks the bot to "collect" or
"know" something about users: a phone number, a location, a birthday, "everything available". Also read it
when designing onboarding, sign-up, delivery, age checks or a CRM sync, and when writing a privacy policy.

Labels:
- **[Official]** the Bot API, the Mini Apps page, or Telegram's terms (Bot Developer Terms §4 and §5,
  Standard Bot Privacy Policy, Mini App Terms §4);
- **[Heuristic]** this skill's rule.

Field list with sensitivity and typical use: `data/user-data.json`, with names checked against the API
catalogs. Look up any field: `py -3 scripts/tg_api_lookup.py show ChatFullInfo`,
`py -3 scripts/webapp_lookup.py show WebAppUser`.

## 0. The rules that come with the data

Telegram's terms bind every bot and Mini App **[Official]**:

1. **A privacy policy.** It states what is stored, how it is collected and why. Set your own in @BotFather;
   without one, the Standard Bot Privacy Policy applies, and you are bound by it. A Mini App also shows a
   Privacy Policy item in its menu.
2. **Only what the service needs.** Collect, store and process only what is essential to the features you
   offer.
3. **Consent for what the user gives.** Data the user submits (a phone number, a location, a form) may be
   used only for the purpose they were told, with explicit, active consent they can withdraw.
4. **No getting around the limits.** Do not mislead users to obtain data Telegram does not give you. Never
   ask for passwords or login codes.
5. **No third parties.** No selling, sharing or passing data to other services (your own other bots
   included) unless the user agreed or the law requires it.
6. **No datasets.** Building large datasets, machine-learning models or AI products from user data or from
   scraped group and channel content is prohibited.
7. **Security.** Encrypt user data at rest with the keys stored apart. Fix leaks quickly and notify users
   where the law requires it.
8. **Deletion.** Delete a user's data without undue delay when they ask, when it is no longer needed, or
   when the service stops. Answer requests within 30 days. Users can also ask for a copy, restrict
   processing and withdraw consent.
9. **Other people's data.** Do not process personal information of people who did not consent, such as
   names or photos of users someone else shared with the bot.

Breaking these rules can get the bot terminated. Business bots that misuse business-message data can be
banned permanently.

## 1. Four tiers of data

| Tier | How it arrives | Examples | What the bot must do |
|---|---|---|---|
| **Automatic** | with every update (`message.from`) or Mini App launch (`initData`) | id, names, username, language, Premium, photo URL, launch chat | use for the current interaction; store only what a feature needs |
| **Readable by API** | the bot asks Telegram about a user it already knows; the user's privacy settings decide what comes back | bio, birthdate, personal channel, profile photos, gifts, rating | read only for a feature the user can see; a missing field means hidden or not set |
| **On request** | the user taps a native prompt or sends something | phone, location, other users or chats, write access, invoice details, Passport | explain first, ask once, work when refused (§3) |
| **Never** | not available to bots | other users' phones, contacts, other chats, last seen, IP of bot users, passwords | the skill does not build workarounds (§5) |

### 1.1 Automatic

From `User` (on every message, callback and inline query) and `WebAppUser` / `WebAppInitData` (Mini Apps):

| Field | Notes **[Official / Heuristic]** |
|---|---|
| `id` | The stable key, up to 52 bits: store it as a 64-bit integer. Never show it to the user. |
| `first_name`, `last_name`, `username` | Changeable. Refresh on each update. `username` is optional: never use it as a key. |
| `language_code` | Telegram's interface language; optional ([localization-and-rtl.md](localization-and-rtl.md)). |
| `is_premium` | Premium features (custom emoji). Never a pricing or targeting signal. |
| `photo_url` (Mini Apps) | Load it to show the avatar. Do not copy the image to your storage. |
| `allows_write_to_pm` (Mini Apps) | False means the bot cannot message the user yet: use `requestWriteAccess()`. |
| `chat`, `chat_type`, `chat_instance`, `receiver` (Mini Apps) | Where the app was opened. `receiver` is the other person in a private chat, someone who did not open the app; use it only for the shared action. |
| `start_param` | The deep-link payload. A route or an id, never personal data (links get forwarded). |
| `ChatJoinRequest.bio`, `user_chat_id` | For bots that moderate join requests. The bot may message the requester for 5 minutes while the request is pending. |

The Mini App's own server also sees the IP address of the requests it receives. That is personal data
under most laws: do not log it longer than security needs.

Always read these on the server from a verified source:
- for bots, the update Telegram sent to your webhook;
- for Mini Apps, the verified `initData`, never `initDataUnsafe` sent by the client
  ([mini-apps/security.md](mini-apps/security.md) §2).

### 1.2 Readable by API

| Method | Returns | Use only when |
|---|---|---|
| `getChat(user_id)` | `ChatFullInfo`: `bio`, `birthdate`, `personal_chat`, `photo`, emoji status, accent colours, `rating` (Stars level), `ton_wallet_card`, `accepted_gift_types`, `first_profile_audio`, business intro, location and hours | a feature shows or needs that field: a birthday greeting the user turned on, gift sending, a business card |
| `getUserProfilePhotos` | up to 100 profile pictures | showing the avatar history the user would expect, rarely |
| `getUserProfileAudios`, `getUserGifts`, `getUserPersonalChatMessages` | what the user put on their profile | a profile or gift feature |
| `getChatMember(chat_id, user_id)` | status in a chat; guaranteed only where the bot is an administrator | membership checks: "join the channel to continue", access to a paid group |
| `getUserChatBoosts` | the user's boosts to a chat the bot administers | boost rewards |

Rules **[Heuristic]**:
- **The user's privacy settings decide.** A missing `birthdate` or `bio` is an answer. Do not retry,
  guess, or ask the user to change their settings for your benefit.
- **Read when needed, not in bulk.** Do not call `getChat` on every user "to have the data". Read at the
  moment a feature needs a field, and keep only that field.
- **Profile data is shown by the user to everyone, not given to you.** A `ton_wallet_card` proves nothing
  about ownership. A `rating` is Telegram's signal about purchases, not a credit score.

### 1.3 On request

| Data | How to ask | What arrives | Notes |
|---|---|---|---|
| Phone number | reply-keyboard button `request_contact: true` (private chats); in a Mini App `requestContact()` (6.9) | a `Contact` message to the bot; the Mini App only gets `contactRequested` with `sent` or `cancelled` | **Check `contact.user_id == message.from.id`.** A user can send someone else's contact card as an ordinary message |
| Location | `request_location: true`; in a Mini App `LocationManager` (8.0) | `Location` with `horizontal_accuracy`; live locations update | round it to what the feature needs; never keep a trail ([mini-apps/haptics-and-device.md](mini-apps/haptics-and-device.md) §3) |
| Other users | `KeyboardButtonRequestUsers` with `request_name`, `request_username`, `request_photo` | `users_shared` with what was asked | those people did not consent: ask only for ids unless names are shown back at once (inviting, splitting a bill) |
| A chat | `KeyboardButtonRequestChat` | `chat_shared` | connecting the bot to the user's group or channel |
| Permission to message | `requestWriteAccess()` (6.9) | a boolean | at the moment it helps: a receipt, a reminder |
| Emoji status | `requestEmojiStatusAccess()` (8.0) | a boolean | only for a feature that sets the status |
| Order details | `sendInvoice` `need_name`, `need_phone_number`, `need_email`, `need_shipping_address` | `OrderInfo` in the pre-checkout and successful-payment updates | provider payments for physical goods only; ignored for Stars ([payments-and-stars.md](payments-and-stars.md)) |
| Identity documents | Telegram Passport | `PassportData`, encrypted to the bot's key | regulated checks only (KYC); decrypt on the server; see core.telegram.org/passport |
| Form input | a Mini App form, `sendData()`, a bot conversation | text the user typed | the rules of [mini-apps/forms-and-data.md](mini-apps/forms-and-data.md) §0: do not ask what Telegram already gave |

## 2. Turning "collect everything" into a data inventory

When an operator asks the bot to collect a phone, a location or "all available information", the agent does
not just add prompts. It produces a **data inventory** first **[Heuristic]**:

| Field | Source (tier) | Feature that needs it | Shown to the user as | Stored where, how long | Who can access it |
|---|---|---|---|---|---|
| phone_number | on request, `request_contact` | courier calls about delivery | "Share your number so the courier can call" | orders table, encrypted, deleted 30 days after delivery | courier app for the active order |
| language_code | automatic | interface language | — | users table, refreshed on each update | the bot |
| … | | | | | |

- **A field with no feature in the "Feature" column is not collected.** Say so to the operator in one line
  with the reason (Bot Developer Terms §4.3), and offer the narrower version that serves their goal.
  For example, "know where users are" can become "ask for the city at checkout".
- **"Everything available" becomes the automatic tier plus what features need.** The API tier is read on
  demand, and the on-request tier is asked for at the moment of the feature.
- The inventory feeds the privacy policy (§4) and the deletion command (§4). Put it in the repository next
  to the bot's code (`docs/data-inventory.md`).

## 3. Asking for data the user gives

The pattern for every prompt (phone, location, other users, Passport) **[Heuristic]**:

1. **At the moment of need**, never at /start. "Share your number" at the first message loses users and
   reads as harvesting.
2. **Say why in the button's message:**
   - "The courier will call this number if they can't find you. We delete it after delivery." with
     [Share my number];
   - next to it, [Type a different number] or [Skip].
3. **Use the native prompt.** Telegram shows exactly what is shared. A text field asking for a phone number
   gets no verification and more typos.
4. **Refusal is a normal path.** Cancelled, or "Skip", leads somewhere useful: pickup instead of delivery,
   a city list instead of location.
5. **Confirm and show what was stored:** "Saved +31 6 ••• 789. Change it in Settings."
6. **Remove the keyboard** after the contact or location arrives (`ReplyKeyboardRemove`).

In a Mini App, the phone goes to the **bot**, not the page. The page learns only `sent`. The server matches
the Contact message to the user by `user_id` and the app asks its server for the result
([mini-apps/forms-and-data.md](mini-apps/forms-and-data.md) §0).

### 3.1 Scenarios: what users tell a bot about themselves, and the easiest way

The best mechanism is the one with the fewest taps and the most certainty: a native prompt beats a typed
answer, and a typed answer in a Mini App field beats one in chat. Look up the details by name with
`tg_api_lookup.py` / `webapp_lookup.py` **[Official names, Heuristic choice]**.

| The user wants to give | Best in a bot | Best in a Mini App | Notes |
|---|---|---|---|
| Who they are (name, language, avatar) | nothing to ask: `message.from` | nothing to ask: verified `initData` | let them edit a display name inside the service if it matters |
| A phone number for a callback or delivery | `request_contact` button | `requestContact()` | arrives as a `Contact` to the bot; check `user_id` |
| A **verified** phone number or email | Telegram Passport `phone_number` / `email` elements: Telegram verified them | the same, opened from the bot | for services that must prove contact details; otherwise the contact button is enough |
| Where they are now | `request_location` | `LocationManager` | round it; one-off |
| Where they are while a courier comes | they share a **live location**: edits arrive with `Location.live_period`, `heading` | — | stop using it when the order ends; never ask for longer than the delivery |
| Location while searching places inline | `InlineQuery.location`, after enabling location requests in @BotFather or `setMySettings` `needs_inline_query_location` | — | nearby results without a chat |
| A delivery address | `sendInvoice` `need_shipping_address` with a `ShippingQuery` for options (provider payments) | a form with `autocomplete="street-address"` … ([forms-and-data.md](mini-apps/forms-and-data.md) §1) | ask once, offer the saved one next time |
| Email for a receipt | `need_email` on a provider invoice | `type="email" autocomplete="email"` | not for Stars purchases: Telegram sends the receipt |
| Birthday (greetings, an age check) | `getChat` → `birthdate` if they show it; else ask day and month with an inline keyboard | `type="date"`, year optional | an age check asks "Are you 18 or older?" rather than the full date when that is enough |
| Time zone (reminders at the right hour) | ask the city, or derive it from a location they shared | `Intl.DateTimeFormat().resolvedOptions().timeZone`, confirmed in settings | store the zone name, not the location |
| Preferences (notifications, units, interests) | inline toggles on a settings screen ([navigation-and-flows.md](navigation-and-flows.md)) | a settings screen saved to the server or CloudStorage | defaults that work; ask at the moment a preference matters |
| Documents (KYC, a licence) | Telegram Passport | the same, opened from the bot | only where regulation requires it; decrypt on the server |
| Photos and files (a receipt, a CV) | send a photo or document; read `file_id` | `<input type="file">`, uploaded to your server | keep files only as long as the case needs them |
| Friends for a split bill or an invite | `request_users`: ids, and names only if shown back | a share link (`switchInlineQuery`, `shareMessage`) | never ask for their contact list |
| A group or channel to connect | `request_chat` with the rights the bot needs | — | the bot gets admin rights the user approves |
| Who referred them | a deep link `?start=ref_…` / `startapp=ref_…` | `start_param` | a code, not the referrer's personal data |
| A rating or feedback | an inline 1-5 row, then an optional comment | `.tma-rating` and a text area | after the task, once |
| Permission to message them | they start the bot, or `requestWriteAccess()` | `requestWriteAccess()` | ask when a receipt or reminder needs it |
| A quick sign-in on this device (step-up) | — | `BiometricManager` (7.2): a token kept on the device, unlocked by Face ID or a fingerprint | biometrics never leave the phone; the server sees only your token |
| A crypto wallet address | — | TON Connect, where the user signs ([wallet-and-ton.md](wallet-and-ton.md)) | a signed proof, never a typed address for payouts |

### 3.2 Beyond the Bot API: MTProto

A bot can also connect over MTProto, the protocol of Telegram's apps, with its bot token, using libraries
such as Telethon, Pyrogram or GramJS. This adds little personal data, because Telegram applies the same bot
limits, but a few things are worth knowing **[Check against core.telegram.org/schema]**:

- User objects carry Telegram's own `scam`, `fake` and `verified` flags. That is useful for anti-abuse
  ([user-trust.md](user-trust.md) §1).
- The bot can resolve a public `@username` to a user. The Bot API's `getChat` accepts usernames only for
  groups and channels. This does not give the bot the right to message that person or process their data.
- Full user info (`users.getFullUser`) returns about what `getChat` returns: bio, birthday and personal
  channel, within the user's privacy settings.
- Bots still cannot read message history, contact lists or other chats, and still see no phone numbers that
  were not shared.

Never use a personal account (a "userbot") on behalf of a bot to collect user data. It breaks the terms
(§5), and the account gets banned.

## 4. Storing, using and deleting

- **Keys and minimal columns.** Store `user.id` as the key. Store a field only if the inventory lists it.
- **Encryption at rest.** Phone numbers, exact locations, emails, addresses and documents go in encrypted
  columns or a secrets store, with keys kept apart **[Official §4.4]**.
- **Logs and analytics:**
  - never log raw `initData`, Contact messages, locations or `OrderInfo`;
  - log `user.id` and the event name only;
  - analytics are anonymous or aggregated.
- **Retention.** Every field has a period in the inventory. A scheduled job deletes what has expired.
- **User commands:**
  - `/privacy` shows the policy;
  - `/mydata` sends a copy of what is stored;
  - `/deletedata` deletes it after a confirmation, and says what is kept for legal reasons, such as tax
    records of payments.

  Answer within 30 days; the bot can answer at once **[Official, Standard Policy §7.3]**.
- **The privacy policy** is written from the inventory, in the user's language, set in @BotFather and
  linked from `/privacy` and the Mini App's menu.
- **No secondary use:**
  - no ads, profiling or selling;
  - no feeding a CRM, an ad network or another bot without the user's agreement;
  - no training models on user data.

## 5. What the skill does not build

The agent declines these and offers the compliant alternative, whoever asks **[Official §4.1, §4.3, §5.2]**:

| Request | Why not | Alternative |
|---|---|---|
| Collect the phone or location without a prompt, or hide the prompt's purpose | consent must be explicit and informed; misleading users to get data is prohibited | the native prompt with a clear reason (§3) |
| Read profiles of every user in groups the bot is in, scrape member lists or channel posts | datasets and scraping are prohibited; those users never used the bot | read only users who interact with the bot, for a feature |
| Combine a Telegram profile with outside sources (search, leaked databases, other platforms) to identify or profile a person | personal data of people who did not consent, use outside the service | none; the bot knows what the user gives it. Anti-abuse checks against a disclosed spam list keyed by the id alone are a different case, with conditions: [user-trust.md](user-trust.md) §4 |
| Keep data after `/deletedata`, or "anonymise" by dropping the name only | deletion on request is mandatory; the id still identifies the person | real deletion; aggregate statistics without ids |
| Share or sell user data to partners or another bot | no third parties without consent | an explicit opt-in screen naming the partner and the purpose |
| Ask for a login code, password or "verify your account" | phishing; prohibited | `initData` already authenticates the user |
| Track a live location in the background | not possible without the user sharing a live location, and not proportionate | a one-time location at the step that needs it |

The default record a bot keeps per user, and how it adapts the interface: [user-profile.md](user-profile.md).

Detecting spammers and risky accounts (account age, Stars rating, spam lists, tiers, appeals): [user-trust.md](user-trust.md).

## 6. Review checklist

- [ ] A data inventory exists; every stored field has a feature, a period and an access list.
- [ ] A privacy policy built from it is set in @BotFather and linked from `/privacy` (and the Mini App menu).
- [ ] Automatic data read from the verified update or verified `initData` only.
- [ ] API data read on demand for a visible feature; missing fields accepted.
- [ ] Every prompt at the moment of need, with the reason and a working refusal; `contact.user_id` checked.
- [ ] Shared users: ids only unless names are shown back at once.
- [ ] Sensitive fields encrypted at rest; raw `initData`, contacts and locations never logged.
- [ ] `/mydata` and `/deletedata` work; expired data is deleted by a job.
- [ ] No third-party sharing, ads, profiling, datasets or outside enrichment.

## 7. Digging deeper

- **Exact fields:**
  - `py -3 scripts/tg_api_lookup.py show User | ChatFullInfo | Contact | KeyboardButtonRequestUsers | OrderInfo`;
  - `py -3 scripts/webapp_lookup.py show WebAppInitData`;
  - after a Bot API release, `py -3 scripts/tg_api_lookup.py diff` lists new fields. Add any user-data field
    to `data/user-data.json` (the test fails until its name exists in the catalog).
- **Terms, re-read when Telegram updates them:**
  - https://telegram.org/tos/bot-developers §4 and §5;
  - https://telegram.org/privacy-tpa (the Standard Bot Privacy Policy);
  - https://telegram.org/tos/mini-apps §4;
  - Telegram's Privacy Policy §6.3, which lists what bots receive.
- **Telegram Passport:** https://core.telegram.org/passport for the request flow, element types and
  decryption.
- **Law:** the GDPR (EU), the UK GDPR, and the user's local law for consent, retention, breach notice and
  children's data. The terms require compliance with the law that applies to your users.
