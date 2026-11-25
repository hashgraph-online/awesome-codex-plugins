---
summary: "The baseline per-user record: identity, origin, accepted terms, language, time zone, notification choices, how the profile shapes the interface, storage; read when designing user storage."
verified: "2026-11-24"
bot_api: "10.5"
---

# The baseline user profile

## Contents

- [0. Principles](#0-principles)
- [1. The record](#1-the-record)
- [2. When to write and refresh](#2-when-to-write-and-refresh)
- [3. How the profile changes the interface](#3-how-the-profile-changes-the-interface)
- [4. Optional modules](#4-optional-modules)
- [5. Storage](#5-storage)
- [6. Checklist](#6-checklist)

Every bot built with the skill keeps one record per user from the first contact. The record holds:
- who they are, as Telegram shows them;
- where they came from;
- which terms they accepted;
- their language, time zone and notification choices;
- the profile details that change how the bot talks to them and how its screens look.

This file is the default backend schema and the rules for filling it. The interface side matters most:
the bot uses the user's own Telegram choices (share-screen theme, gift colours, voice-message settings,
usernames) to adapt its messages and personal screens.

Labels:
- **[Official]** the Bot API (`py -3 scripts/tg_api_lookup.py show <Name>`);
- **[Heuristic]** this skill's rule;
- **[Check]** confirm before relying on it.

Code: `examples/python/tgkit/profile.py` (`touch`, `apply_chat_full_info`, `chat_member_update`,
`personal_accent`, `display_handle`, `can_send_voice`, `needs_terms`), tested in
`tests/test_user_profile.py`. Data rules: [user-data.md](user-data.md). Anti-abuse: [user-trust.md](user-trust.md).

## 0. Principles

- **A baseline, not a dossier.** Every field has a purpose a user would recognise: greeting them by name,
  writing in their language, reminding them at a sane hour, not sending voice notes they blocked. Fields
  without a purpose stay out ([user-data.md](user-data.md) §0, §2).
- **Current state, not history.** Keep the current name and usernames, and `profile_updated_at` when they
  last changed. Keep no log of old names or usernames: that is tracking.
- **Disclosed.** The privacy policy lists these fields and why. The record is what `/mydata` returns and
  what `/deletedata` removes.
- **Optional modules are off by default.** Trust signals, external spam lists and MTProto flags are separate
  modules an operator turns on with a reason (§4).

## 1. The record

| Group | Field | Source **[Official]** | Written | Purpose |
|---|---|---|---|---|
| Identity | `user_id` | `User.id` | first contact | the key (64-bit integer) |
| | `first_name`, `last_name`, `username`, `language_code`, `is_premium` | `User` in every update | each update, when changed | greeting, mentions, language, Premium features |
| | `profile_updated_at` | compare on each update | when a public field changes | refresh the snapshot (§2), notice a renamed account in moderation |
| Lifecycle | `first_seen_at`, `last_seen_at` | your clock | first contact; each update | onboarding, re-engagement limits, retention |
| | `blocked_at` | `my_chat_member` in the private chat with status `kicked`; cleared by `member`. A 403 "bot was blocked by the user" confirms it | on the update | stop sending; do not count as an active user |
| Acquisition | `acquisition.kind`, `.value`, `.entry` | the `/start` payload, Mini App `start_param`, `ChatJoinRequest.invite_link`, inline (`chat_type`) | first contact only, never overwritten | which link, ad, channel post or referral brought them. Allowlisted payloads only (`ref_`, `ad_`, `ch_`, `post_`, `qr_`, `item_`, `promo_`) |
| Consent | `terms_version`, `terms_accepted_at` | your terms screen | on acceptance | prove what they agreed to; re-ask when the version changes (`needs_terms`) |
| | `marketing_opt_in` (+ date) | an explicit toggle, off by default | on change | newsletters and promos only with it |
| Locale | `language` | the app's language choice, defaulting to `language_code` | on choice | the interface language ([localization-and-rtl.md](localization-and-rtl.md)) |
| | `timezone` | asked (city), derived from a shared location, or from a Mini App (`Intl…timeZone`) and confirmed | on choice | reminders, digests, quiet hours |
| Notifications | `categories` (orders, reminders, news…), `quiet_from` / `quiet_to`, `can_message` | a settings screen; `allows_write_to_pm`, `requestWriteAccess` | on change | send only what they chose, never at night |
| Labels | `labels` | operator rules (e.g. `customer`, `vip`, `beta`, `support-open`) | by rule, with a reason | segments for the operator's tools. Never sensitive traits (health, religion, politics, ethnicity, sexuality) |
| Profile snapshot | `active_usernames` | `getChat` → `ChatFullInfo.active_usernames` (all active usernames, including collectible ones) | §2 schedule | find and mention the user by any of their usernames |
| | `has_private_forwards` | `ChatFullInfo.has_private_forwards`: `tg://user?id` links work only in chats with the user | §2 | how to point at them in groups (`display_handle`) |
| | `restricts_voice_video` | `ChatFullInfo.has_restricted_voice_and_video_messages` | §2 | no voice or video notes to them (`can_send_voice`) |
| | `share_theme` | `ChatFullInfo.share_theme`: `ChatShareThemeEmoji` (0-6 emoji on a backdrop) or `ChatShareThemeUniqueGift` | §2 | the personal accent (§3) |
| | `unique_gift_colors` | `ChatFullInfo.unique_gift_colors`: light and dark main and other colours | §2 | the personal accent (§3) |
| | `accent_color_id`, `profile_accent_color_id`, `emoji_status_custom_emoji_id` | `ChatFullInfo` | §2 | name colour family, emoji status next to the name in messages |
| | `stars_rating_level` | `ChatFullInfo.rating.level` (a negative level is a concern, per the docs) | §2 | purchase limits, trust ([user-trust.md](user-trust.md)) |
| Community | per chat: `status`, `custom_title`, `tag`, `until_date`, `joined_via` | `getChatMember` / `chat_member` updates (`ChatMemberMember.tag`, `ChatMemberAdministrator.custom_title`); `ChatFullInfo.community` groups chats | on the update, only in chats the bot manages | admin-only buttons, member tags, paid membership expiry |

Not in the baseline (read only for a feature, [user-data.md](user-data.md) §1.2): `birthdate`, `bio`, profile
photos and audios, gifts, `personal_chat`, `ton_wallet_card`, business details.

## 2. When to write and refresh

| Moment | Write |
|---|---|
| First contact (`/start`, a Mini App launch, a join request, an inline query) | create the record with `touch(..., payload, entry)`: identity, `first_seen_at`, acquisition |
| Every update | `touch()`: identity fields if changed, `last_seen_at` |
| Terms screen accepted | `terms_version`, `terms_accepted_at` |
| Settings changed | language, time zone, notifications, marketing opt-in |
| `my_chat_member` in the private chat | `chat_member_update()`: blocked / unblocked |
| `chat_member` in a managed group (needs the bot as admin and `chat_member` in `allowed_updates`) | the community row for that chat |
| Profile snapshot | `getChat(user_id)` → `apply_chat_full_info()`: after the first contact, when `profile_updated_at` moves, before drawing a personal screen if the snapshot is older than 7 days. Never in bulk; mind the rate limits |

## 3. How the profile changes the interface

This is the point of the record for a UI skill **[Heuristic]**.

### 3.1 Personal accent from the user's own theme

People choose a share-screen theme (an emoji theme on a backdrop, or one of their unique gifts) and gift
colours for their name. A bot can use those colours on surfaces that belong to the user:
- a profile card;
- a membership or loyalty card;
- a "your stats" widget header;
- a share card;
- the top of the Mini App's profile screen.

`personal_accent(profile, scheme, backdrops)` resolves them in order:
1. A unique gift as the share theme: its `backdrop.colors` (`center_color`, `edge_color`, `symbol_color`,
   `text_color`, all RGB integers).
2. An emoji share theme: its `background_backdrop_id` looked up in `getChatShareThemeBackdrops()`. Fetch that
   list once and cache it.
3. `unique_gift_colors`: the main and other colours for the current light or dark scheme.
4. Nothing chosen: `None`, and the surface keeps the theme's colours.

Rules:
- **Personal surfaces only.** Never use the user's colours for the app's chrome, buttons, the MainButton,
  links or status colours. Those follow `themeParams` ([mini-apps/design-system.md](mini-apps/design-system.md)).
- **Use the backdrop's own `text_color`** on a backdrop. Use the main colour as a tint or a stripe of
  identity, never as text on the theme background without a contrast check (4.5:1).
- **Light and dark.** Gift colours come in both variants; pick by the current scheme.
- **The gift backdrop component already exists.** In a Mini App, `giftVars()` in `_kit/tg-values.ts` turns
  backdrop colours into the `--gift-center`, `--gift-edge`, `--gift-text` and `--gift-symbol` variables `.tma-gift` reads ([mini-apps/telegram-elements.md](mini-apps/telegram-elements.md)).
- **In messages** the bot cannot colour text. The accent shows in a widget or a Mini App. In chat, show the
  user's emoji status as a custom emoji next to their name where custom emoji are allowed
  ([custom-emoji.md](custom-emoji.md)).
- `accent_color_id` and `profile_accent_color_id` are palette ids that Telegram's clients render with their
  own theme. The Bot API page lists the colours, but they vary by client theme **[Check]**. Do not hard-code
  hex values from them; use them only to pick a matching kit palette (ids 0-6: red, orange, purple, green,
  cyan, blue, pink).

### 3.2 Messages that respect the profile

| Field | Interface rule |
|---|---|
| `restricts_voice_video` | never send a voice or video note; send an audio file with a caption, or text. Sending one fails anyway |
| `has_private_forwards` | in groups, mention by `@username` (any of `active_usernames`) via `display_handle()`, not by an id link |
| `language`, `timezone` | every date, time and number in their language and zone ([localization-and-rtl.md](localization-and-rtl.md)) |
| `notifications` | send only chosen categories, hold non-urgent ones during quiet hours, stop on `blocked_at` |
| `acquisition` | open the thing they came for: `item_42` opens that product, `ref_` shows who invited them, `ch_` thanks the channel ([onboarding-and-first-run.md](onboarding-and-first-run.md)) |
| `terms_version` | a short "what changed" screen with [Accept] when the version moves; nothing else until accepted, if the terms require it |
| `is_premium` | custom emoji in buttons and messages only where they add meaning; never a different price |
| community `status` / `tag` | admin-only actions shown only to admins; the member's tag in member lists |

## 4. Optional modules

| Module | Adds | Turn on when | Notes |
|---|---|---|---|
| Trust | own signals, the id-based age bracket, tiers | the bot moderates groups, pays out, or runs giveaways | [user-trust.md](user-trust.md); never bans on age alone |
| CAS | `cas_listed`, `cas_checked_at` | group moderation at join time | disclosed in the privacy policy, the id only, fail open, no appeal at CAS so your own ([user-trust.md](user-trust.md) §4) |
| MTProto flags | `scam`, `fake`, `verified`, third-party verification (a `bot_verification` field on users) | the bot already runs an MTProto library with its bot token | Telegram's own labels **[Check against core.telegram.org/schema]**; read on contact, not by scanning |
| lols.bot and similar lists | — | not supported | Read 2026-11-24: the operator is not named, the public API has no documentation, and no removal process is described. Sending ids there cannot be disclosed honestly. Revisit when they publish docs and terms |

## 5. Storage

```sql
create table users (
  user_id            bigint primary key,
  first_name         text not null,
  last_name          text,
  username           text,
  language_code      text,
  is_premium         boolean not null default false,
  first_seen_at      timestamptz not null,
  last_seen_at       timestamptz not null,
  profile_updated_at timestamptz,
  blocked_at         timestamptz,
  acq_kind           text not null,               -- organic, ref, ad, ch, post, qr, item, promo, other, ...
  acq_value          text,
  acq_entry          text,
  terms_version      text,
  terms_accepted_at  timestamptz,
  marketing_opt_in   boolean not null default false,
  marketing_opt_in_at timestamptz,
  language           text,
  timezone           text,                        -- IANA name
  notify             jsonb not null default '{"orders":true,"reminders":true,"news":false}',
  quiet_from         time,
  quiet_to           time,
  labels             text[] not null default '{}',
  profile            jsonb,                       -- the §1 snapshot fields only, not the whole ChatFullInfo
  profile_refreshed_at timestamptz
);
create table community_members (
  chat_id bigint, user_id bigint references users on delete cascade,
  status text, custom_title text, tag text, until_date timestamptz, joined_via text,
  updated_at timestamptz, primary key (chat_id, user_id)
);
```

- **Retention:**
  - delete the row on `/deletedata`;
  - remove snapshots and community rows of users not seen for 12 months;
  - keep the consent record (`terms_version`, `terms_accepted_at`) as long as the law needs proof.
- **Logs** carry `user_id` and event names only ([user-data.md](user-data.md) §4).

## 6. Checklist

- [ ] The record is created on first contact with the acquisition and never overwritten.
- [ ] Identity refreshed on each update; no history of names or usernames.
- [ ] Terms version and marketing opt-in recorded; the terms screen re-shown when the version changes.
- [ ] Language, time zone and notification choices drive every message; quiet hours respected; sending stops on block.
- [ ] Profile snapshot from `getChat` on the §2 schedule, only the §1 fields kept.
- [ ] The personal accent only on the user's own surfaces, in the current scheme, with contrast checked.
- [ ] No voice notes to users who restrict them; mentions follow `has_private_forwards`.
- [ ] Optional modules off by default, each disclosed and justified; lols-style undocumented lists not used.
- [ ] Listed in the privacy policy; returned by `/mydata`, removed by `/deletedata`.
