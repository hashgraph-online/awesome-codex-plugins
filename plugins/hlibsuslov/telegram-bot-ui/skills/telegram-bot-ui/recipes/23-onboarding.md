# 23 — Onboarding and first run: deep links, language, permissions, empty states, returning users

Product recipe (no registry row of its own). Uses 9.4 button `style`, older deep-link and
reply-keyboard features, and the bot profile texts. Verified 2026-11-15 against Bot API 10.4
(newest release on that date). Background: `references/onboarding-and-first-run.md`.
Tags: **[API]** API requirement · **[official]** official recommendation · **[heuristic]** design
heuristic.

1. **Request and visible result.** “New users open the bot from ads, referral links and product
   links, see a wall of text and leave. Returning users get the same welcome again.” — Before
   Start, the empty chat already says what the bot does (bot description) in the user's language.
   `/start` opens three short steps (language → updates opt-in → optional phone), each with a
   “Not now”/“Skip”; then a home screen whose empty state names one next step. A product link
   leaves the product in the cart; a referral is credited once; returning users get “Welcome
   back” with their latest order and never see onboarding again.
2. **Why these features.**
   - `setMyDescription` (empty-chat text, 0-512), `setMyShortDescription` (profile/share text,
     0-120), `setMyCommands` with `language_code` — per-language texts without code in the
     handler **[API]**. Commands are 1-32 chars of `a-z0-9_` **[API]**; since 10.2 a command can be
     marked `is_ephemeral` (its reply is visible only to the sender) **[API]**.
   - Deep links `t.me/<bot>?start=<param>`: up to 64 chars of `A-Z a-z 0-9 _ -`, base64url for
     anything else **[official, /bots/features#deep-linking]**. Validate and never echo it.
   - Phone only through a reply keyboard button with `request_contact` **[API: inline buttons
     can't request contacts]**; `one_time_keyboard`, `input_field_placeholder` (1-64) and a
     `ReplyKeyboardRemove` afterwards **[API]**. Check `contact.user_id == from.id` — a user can
     also attach someone else's contact **[heuristic]**.
   - `style: "primary"` on the detected language and on the main CTA (9.4) **[heuristic]**.
3. **Requirements.** Any Bot API version with `style` (≥ 9.4) for the styled buttons; everything
   else is older. Production. Private chat. Profile texts are set once per deploy, not per user.
4. **Payload.** Full request sequence: `examples/payloads/r23-onboarding.json`.

   | Screen | Message | Buttons | Leaves to |
   |---|---|---|---|
   | (before Start) | bot description, per language | Start (client) | `/start [param]` |
   | lang | “Hi, Alice! Which language should I use?” | one per language, detected one ✓ + primary | notify |
   | notify | “Step 2 of 3 · Updates … no ads.” | `Notify me` primary · `Not now` | phone |
   | phone (new message) | “Step 3 of 3 · Phone (optional)” | reply keyboard: `Share my phone` (request_contact) · `Skip` | home |
   | home (new message) | empty state or “Welcome back” + latest order; one-time notes (link item, referral) | `Open the catalog` primary · `My orders` `Settings` | product screens |

   Key parts:
   ```json
   {"method": "setMyCommands", "params": {"commands": [{"command": "start", "description": "Відкрити магазин"}, …], "language_code": "uk"}}
   {"method": "sendMessage", "params": {"chat_id": 222222222, "text": "<b>Крок 3 з 3 · Телефон (необовʼязково)</b>…",
     "reply_markup": {"keyboard": [[{"text": "Поділитися номером", "request_contact": true}], ["Пропустити"]],
                      "one_time_keyboard": true, "resize_keyboard": true, "input_field_placeholder": "…"}}}
   ```
5. **Code.** `examples/python/recipes/r23_onboarding.py` (`deploy_setup`, `Onboarding.on_start`,
   `credit_referral`, `ask_phone`, `finish`) on `examples/python/tgkit/flows.py` (`ScreenFlow`,
   `OnceStore`, `UpdateDedup`, `I18n`). TypeScript twin: `examples/ts/usecases/onboarding.ts`.
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     [*] --> parse: /start [param]
     parse --> lang: new user (param: ref_ / item_ / unknown / malformed)
     parse --> home: onboarded user ("Welcome back")
     lang --> notify: language tapped
     notify --> phone: Notify me / Not now
     phone --> home: own contact / Skip
     phone --> phone: someone else's contact (refused)
   ```
   Profile: `{lang, onboarded, notify, phone, orders}`. Payload rules: `item_<key>` → teaser +
   cart; `ref_<code>` → credited once per new user (`OnceStore` key `ref:<user>`), never for the
   inviter themself or an existing user; unknown → logged; malformed → ignored. A redelivered
   `/start` update is dropped by `UpdateDedup`; a tap on a finished step is stale.
7. **Result.** Mock-ups (not client screenshots):
   ```
   Hi, Alice! Which language should I use?    Готово, Богдан
   [ ✓ English ]  (primary)                   Замовлень ще немає. Почніть з каталогу —
   [ Українська ]                             свіже обсмаження щопонеділка.
                                              Alice запросив(-ла) вас: перша доставка безкоштовна.
                                              [ Відкрити каталог ]
                                              [ Мої замовлення ] [ Налаштування ]
   ```
8. **Typical mistake, limits, alternative.** Mistakes: a 15-line welcome; asking for the phone
   before the user has a reason; no way to skip; re-running onboarding on every `/start`; echoing
   the start parameter into HTML; crediting a referral on every click; a reply keyboard that stays
   after the step; one command list for all languages. Limits **[API]**: start parameter ≤ 64,
   description ≤ 512, short description ≤ 120, ≤ 100 commands per scope+language, placeholder
   1-64. Failure paths in the run: duplicate update, someone else's contact, stale onboarding
   button, referral by an existing user, self-referral, malformed payload. Alternative: a Mini App
   onboarding for long sign-up forms; group bots onboard with a deep link to the private chat
   (recipe 24's group entry point).
9. **Run and verify.** `py -3 examples/python/recipes/r23_onboarding.py` (11 self-checks) ·
   `py -3 -m unittest tests/test_usecases.py`. Evidence: offline contract; not rendered in a
   client.
10. **Adapt.** Keep: the payload grammar (`prefix_value`, validated), one-time notes, three steps
    maximum with skip, profile flag `onboarded`. Replace: `COPY` texts, `REF_CODES` and `NAMES`
    with your store, the home actions. Add `/start bizChat<id>` handling for business bots
    (recipe 61) and `?startgroup=` links for group bots. Related: recipe 24 (settings reuse the
    language screen), `references/personalization-and-links.md`,
    `references/localization-and-rtl.md`, `references/reply-keyboards.md`.
