---
summary: "Onboarding and first run: before Start, reading /start, first-run steps, empty states, returning users, groups; read when designing a bot's first minute."
verified: "2026-11-15"
bot_api: "10.4"
---

# Onboarding and first run

> Verified 2026-11-15 against Bot API 10.4 (newest release on that date) and
> https://core.telegram.org/bots/features. Runnable model: [recipe 23](../recipes/23-onboarding.md)
> (`examples/python/recipes/r23_onboarding.py`). Tags: **[API]** API requirement ·
> **[official]** official recommendation · **[heuristic]** design heuristic of this skill.

The first minute decides whether a bot is used again. A good first run answers three questions in
this order: *what is this*, *what do I do now*, *what will it send me*. Everything else waits.

## Before the user presses Start

The empty chat is a screen you design. It shows the bot description, and the profile / share card
shows the short description.

| Surface | Method | Limit | Note |
|---|---|---|---|
| Empty chat text | `setMyDescription` | 0-512 chars **[API]** | One sentence of value + one of how. Per `language_code`. |
| Profile and link-share text | `setMyShortDescription` | 0-120 chars **[API]** | Shown with the link when people share the bot. |
| Command menu | `setMyCommands` | ≤ 100 commands; `command` 1-32 of `a-z0-9_`; description 1-256 **[API]** | Per scope and `language_code`. A list without `language_code` is the fallback for languages without their own list **[API]**. |
| Ephemeral commands | `BotCommand.is_ephemeral` (10.2) | — | Marks a command whose reply only its sender sees **[API]**; good for `/mybalance` in groups. |
| Menu button | `setChatMenuButton` | — | Commands list or a Mini App. |

Set these once per deploy and per language, never inside the `/start` handler **[heuristic]**.
The same goes for the bot's switches (topics, inline placeholder, privacy): `setMySettings`
(10.5, `bot-settings.md`).

Users the owner invited with `t.me/botinvite/<bot>` (10.5) skip this screen and `/start`: their
chat opens with a `write_access_allowed` message carrying `inviter`. Treat that message as their
first run: name the inviter, offer one first action **[heuristic]**.

## Reading `/start`

- `t.me/<bot>?start=<param>` delivers `/start <param>` **[official]**; the parameter is up to
  64 characters of `A-Z a-z 0-9 _ -`, base64url recommended for anything else **[official]**.
- Treat it as untrusted input: validate against that alphabet, map it through a small grammar
  (`item_<key>`, `ref_<code>`, `promo_<code>`, `panel_<token>`), log unknown values, **never echo
  it** into HTML **[heuristic + security-and-escaping.md]**.
- One-time tokens (a private panel, a login) are bound to the user they were issued to: someone
  else's `/start panel_<token>` must not burn it (`tgkit/ephemeral.py::PersonalPanels.redeem_start`).
- Business bots receive `/start bizChat<user_chat_id>` when the owner taps “Manage Bot” in a
  managed chat **[official, features page]** — route it to that chat's panel (recipe 61).
- A referral counts once per new user, never for the inviter themself (`OnceStore` key
  `ref:<user>`) **[heuristic]**.

## The first-run steps

At most three steps, each with a visible way out **[heuristic]**:

1. **Language** — pre-select `from.language_code` (✓ + `style: "primary"`), names in their own
   language (“Українська”, not “Ukrainian”). Skip this step if you support only one language.
2. **What you'll receive** — say exactly what notifications mean (“when your order ships, no
   ads”), `Notify me` / `Not now`. Users who say no still get transactional messages they caused.
3. **Optional data** — a phone or location only through a reply keyboard button with
   `request_contact` / `request_location` (inline buttons can't ask for them **[API]**), with
   `one_time_keyboard`, an `input_field_placeholder` (1-64) and a text `Skip` button; remove the
   keyboard afterwards with `ReplyKeyboardRemove` **[API]**. Verify `contact.user_id == from.id`:
   users can attach someone else's contact **[heuristic]**.

Show progress as text (“Step 2 of 3”), not as decoration. Retire the buttons of a finished step —
an old tap must be refused as stale, not re-run the step (`ScreenFlow` versions).

## Empty states

An empty list is a screen with a job: say what's missing and offer the one action that fills it
(“You have no orders yet. Start with the catalog” + a primary `Open the catalog`) **[heuristic]**.
Never “No data”, never an empty message, never a bare “0 results”.

| Situation | Message | Primary action |
|---|---|---|
| No orders / bookings / items | what will appear here | create the first one |
| Search with no results | why (filters) | remove a filter (recipe 63) |
| Feature not available yet | when it will be | notify me |
| Permission not granted | what the bot can't do without it | how to grant it |

## Returning users

- Keep an `onboarded` flag; a returning `/start` goes to home with “Welcome back” and the most
  relevant live object (latest order, open ticket, next booking) **[heuristic]**.
- Do not repeat one-time notes (the referral bonus, the deep-linked product) after they were shown.
- A redelivered `/start` update (webhook retry) must not open a second menu: deduplicate by
  `update_id` (`tgkit/flows.py::UpdateDedup`).
- A user who blocked and unblocked the bot is a returning user: their data is still yours to show.

## Groups

Personal onboarding never runs in a group. A group `/start` or `/settings` answers with a URL button
to `t.me/<bot>?start=<context>`, or with an ephemeral reply to a button tap (recipe 04, 24)
**[heuristic: personal content keeps its audience]**. Group-level setup (rules, roles) belongs to
admins and is in recipe 29.

## Checklist

- [ ] Description, short description and commands set for every supported language.
- [ ] `/start` parameter validated, mapped, never echoed; unknown values logged.
- [ ] ≤ 3 first-run steps, each skippable, progress as text.
- [ ] Contact/location only via reply keyboard; keyboard removed afterwards; own contact checked.
- [ ] Every empty state names one next action.
- [ ] Returning users skip onboarding; one-time notes shown once; duplicate updates dropped.
- [ ] Copy exists in every language (`I18n.missing()` is empty; `scripts/audit_copy.py` passes).

Related: [personalization-and-links.md](personalization-and-links.md#deep-links),
[localization-and-rtl.md](localization-and-rtl.md), [reply-keyboards.md](reply-keyboards.md),
[navigation-and-flows.md](navigation-and-flows.md), `references/use-case-playbooks.md`.
