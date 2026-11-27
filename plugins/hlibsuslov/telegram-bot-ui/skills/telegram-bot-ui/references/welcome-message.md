---
summary: "The first message after /start, designed per scenario: welcome brief, entry points, language first or not, media, greeting, how-it-works lines, buttons, edits, failures, the welcome spec check."
verified: "2026-11-27"
bot_api: "10.5"
---

# The welcome message: the first message after /start

> Verified 2026-11-27 against Bot API 10.5 (`tgui.py lookup show sendPhoto|editMessageMedia|editMessageText`)
> and https://core.telegram.org/bots/features. Steps around it (description, deep-link grammar,
> opt-ins, empty states, returning users): [onboarding-and-first-run.md](onboarding-and-first-run.md).
> Check a design with `tgui.py check welcome <spec.json>` (§10). Tags: **[API]** API requirement ·
> **[official]** official recommendation · **[heuristic]** design heuristic of this skill.

Every user sees this message, usually once, and it decides whether the bot gets used again. It
is a designed screen, not a greeting. The empty chat (the bot description) has already said what
the bot is. The welcome says what to do now, and gets the user to the first useful result in one
tap. Design it per scenario: who arrives, from where, wanting what. Never write one generic
"Welcome!" for every case.

## Contents

- [1. Think first: the welcome brief](#1-think-first-the-welcome-brief)
- [2. Entry scenarios](#2-entry-scenarios)
- [3. Language first, or straight to the welcome](#3-language-first-or-straight-to-the-welcome)
- [4. Anatomy of the welcome](#4-anatomy-of-the-welcome)
- [5. Variants by bot type](#5-variants-by-bot-type)
- [6. After the welcome: edits and navigation](#6-after-the-welcome-edits-and-navigation)
- [7. Failure paths](#7-failure-paths)
- [8. Worked examples](#8-worked-examples)
- [9. Self-check](#9-self-check)
- [10. The welcome spec and `check welcome`](#10-the-welcome-spec-and-check-welcome)

## 1. Think first: the welcome brief

Before writing a word, answer these seven questions and show the answers to the user as a short
brief, above the copy. If the project doesn't answer one, say what you assumed **[heuristic]**.

1. **Who arrives, and from where?** List every entry the bot really has (§2): plain `/start` from
   search or a shared profile, deep links (ads, referrals, products, QR codes on packaging), an
   owner invite, a group, a business chat, a Mini App, a returning user. Each one gets its own
   first message.
2. **What did they come for?** Name the one job of their first minute: order a coffee, ask a
   question, track a parcel, book a slot. Not the bot's ten features: the one job.
3. **What is the first useful result, and how many taps away is it?** Aim for one tap, or zero
   when a deep link already names it. If it takes three steps, the welcome's primary button
   starts step one.
4. **What does the bot already know?** `from.first_name`, `from.language_code`, the start
   parameter, a stored profile. Write down what it must **not** assume. `language_code` is the
   app's UI language, not a promise. The name is user-controlled text.
5. **What must they know to trust it?** Is it free, what does it cost, what will it send them and
   how often, who is behind it. Only the line that removes the real doubt for this product.
6. **Does a picture earn its place?** What would it show (§4.2)? "Our logo" doesn't count.
7. **What does the second `/start` show?** The returning variant (§2), written now, not later.

Brief format (keep it to the facts, then write the message):

```
Welcome brief
Arrives:      new user, plain /start (60%) · product QR on the cup (30%) · referral (10%)
Came for:     order coffee to pick up
First result: a drink in the cart, 1 tap (Order) · 0 taps from the QR (drink preselected)
Knows:        first_name, language_code (en/uk supported) · item key from the QR
Trust line:   ready in 10 minutes, pay on pickup
Picture:      yes, the counter with today's drinks (16:9), no text in the image
Second /start: home with the open order's status, no intro, no picture
```

## 2. Entry scenarios

The same `/start` handler serves very different people. Route first, then design each branch
**[heuristic]**.

| Entry | How it arrives | First message | Trap |
|---|---|---|---|
| Plain `/start`, new user | `/start` without a parameter, no profile | the full welcome (§4) | a menu dump; "Choose an option below 👇" |
| Product or object link (`item_<key>`, QR) | `/start item_<key>` **[official: ≤ 64 chars of `A-Z a-z 0-9 _ -`]** | **the object itself** (card, photo, price) with one line saying who you are above it; primary = the action on the object; "Open the catalog" secondary | a generic welcome, then the object as a second message; the payload lost behind a language picker |
| Referral (`ref_<code>`) | `/start ref_<code>` | the full welcome plus one line about the real benefit ("Alice invited you: first delivery is free"); credit once per new user | crediting on every `/start`; an unescaped inviter name; a bonus line for an existing user |
| Ad or campaign (`c_<id>`) | `/start c_<id>` | the full welcome; the first line keeps the ad's promise ("7 days free" if the ad said so); campaign logged | the ad promises something the welcome never mentions |
| Login, panel or one-time token | `/start login_<token>` | **no welcome**: the confirmation ("Signed in on the website as …") and one button; token bound to its user | marketing on a security step; someone else's token burnt |
| Owner invite (`t.me/botinvite/<bot>`, 10.5) | no `/start`: a `write_access_allowed` service message with `inviter` **[API]** | name the inviter and offer one first action | waiting for a `/start` that never comes |
| Mini App opened first (`startapp`, menu button) | no `/start`; maybe `write_access_allowed` with `web_app_name` **[API]** | the Mini App is the first screen; the chat welcome (when they do send `/start`) is short and its primary is a `web_app` button | a long chat onboarding that repeats the app's |
| Group: `/start@bot` or the bot added | a group message, or `my_chat_member` | **no personal welcome in the group.** Added: one short note for admins (rights it needs, one `Set up` URL button to `t.me/<bot>?start=setup_<id>`). A member's `/start`: a URL button to the private chat, or an ephemeral reply to a button tap | onboarding, names or personal data posted to the group |
| Business chat (`/start bizChat<user_chat_id>`) | the owner tapped "Manage Bot" **[official]** | that chat's panel (recipe 61), no welcome | the consumer welcome shown to the business owner |
| Returning user | `/start`, profile has `onboarded` | **home, not welcome**: the bot's name as the title, then the most relevant live object (open order, next booking, unread answer) and the same main actions. No intro, no picture unless home itself is a media screen | the same welcome again; "Welcome back! 👋" with nothing behind it |
| Blocked, then came back | `my_chat_member` back to `member`, then `/start` | returning user: their data is still there | treating them as new and re-crediting a referral |
| Language unknown or unsupported | `language_code` missing or not one the bot supports | the language picker first (§3), then the welcome in place of the picker | the welcome in a language they didn't choose |
| Tapped Start twice, or a retried webhook | two `/start` updates (two `update_id`s for a double tap, one repeated id for a retry) | one live welcome: drop duplicate `update_id`s; for a second `/start` within seconds, don't send another | two identical welcomes stacked |

Unknown or malformed parameters fall back to the plain welcome and are logged. They are never
echoed into the text **[heuristic + security-and-escaping.md]**.

## 3. Language first, or straight to the welcome

| Situation | Do |
|---|---|
| The bot speaks one language | no picker |
| Several languages and `language_code` is one of them | the welcome in that language right away; the switch lives in Settings and in `/language` |
| Several languages and `language_code` is missing or unsupported | the picker first, then the welcome replaces it |
| The language decides content or law (bilingual markets, region-specific catalogs) | the picker always, with the detected language preselected (✓ + `style: "primary"`) |

**The picker message** **[heuristic]**: text only (it must arrive instantly), one short line in
the default language, optionally repeated in the audience's most likely second language. Then
one button per language, each named in its own language ("Українська", "English"), and no flags:
a flag is a country, not a language (`visual-language.md` §3). On the tap, **replace the picker
with the welcome** so the chat holds one message. `editMessageMedia` can replace a text message
with a photo (7.11+, **[API]**: "replace a text or a rich message with a media"), and
`editMessageText` handles a text-only welcome. A deep-link payload that arrived with the
`/start` waits in the user's state (not in `callback_data`, which is ≤ 64 bytes **[API]**).
After the pick, go to the payload's screen, not to the generic welcome.

## 4. Anatomy of the welcome

```
[ picture: the product or the result, 16:9, no text baked in ]      ← optional, §4.2
<b>Title</b>                                  ← name or greeting, ≤ ~40 chars
Value line: what you get, concrete, a number if there is one
How it works: 2-3 short lines, each naming a button or a gesture visible right here
Promise or one-time note (trust line, referral bonus, the linked item)  ← optional
[ Primary action ]                            ← style primary, the first useful result
[ Secondary ] [ Secondary ]                   ← 1-3, neutral
```

### 4.1 One message

Media, text and buttons travel in **one** message, not three (a photo, then text, then "Choose an
option" with the keyboard). The notification, the chat list and the user's eye get one thing, and
navigation has one anchor to edit **[heuristic]**. A message carries a single `reply_markup`
**[API]**: inline buttons **or** a reply keyboard, never both (§4.6). An album
(`sendMediaGroup`) can't carry buttons at all **[API]**, so never open with one. `sendVideoNote`
has no caption **[API]**, so a round video needs a second message and is rarely worth it.

### 4.2 Media: when, what, how

**When a picture earns its place** **[heuristic]**: shops, food, booking, travel and services (the
product or the place), learning and content (the course cover), image-generating AI (a real
example output), games (the board), Mini App-first products (a real screen of the app), consumer
brands. **When it doesn't**: utilities, monitoring for professionals, support desks, group admin
bots, agent and ops bots, B2B tools. There, a text welcome is faster and more honest. A logo on
a gradient costs a slower first message and a smaller text budget and tells the user nothing.

**What it shows:** the product or the result the user will get, not the logo. It reads at phone
width (~360 pt). It has **no text baked in**: that text isn't translated, searched or read aloud,
and it duplicates the caption. The brand is present but small, and the image holds up in light
and dark themes. Telegram re-compresses photos, so fine text and thin lines don't survive
**[heuristic]**.

**Shape and weight** **[heuristic]**: landscape 16:9 to 4:3, or square. A tall image (9:16) pushes
the text and buttons below the fold on a phone. About 1280 px on the long side is enough. Keep
the JPEG light, a few hundred KB, so the first message isn't waiting on a download. API limits
for `sendPhoto` **[API]**: ≤ 10 MB, width + height ≤ 10000, ratio ≤ 20.

**How to send it:** upload once (at deploy, or on the first send), store the returned `file_id`
and send by `file_id` from then on. A `file_id` is per bot **[API: "pass a file_id … (recommended)"]**.
Sending by URL makes Telegram fetch the file every time, and uploading on every `/start` is
slower still. No `sendChatAction` before the welcome: it has to be instant **[heuristic]**.

**Other carriers:**

- `sendAnimation` (silent MP4 or GIF) when the value is motion: a 3-5 s loop of the flow,
  ≤ ~1 MB **[heuristic]**. Not a video with sound: it won't autoplay with sound.
- `show_caption_above_media: true` puts the text above the picture **[API]**. Use it when the text
  is the point and the picture only illustrates it.
- A text welcome with a large link preview (`link_preview_options`: `url`, `prefer_large_media`,
  `show_above_text` **[API]**) gives a 4096-character body and a picture from the site's preview
  image. Use it only when the product page is stable: the preview depends on the site and can be
  cached stale.
- A Rich Message with a photo block (10.2+, `sendRichMessage` + `InputRichMessageMedia`,
  `rich-media.md`) suits a document-like intro for a knowledge-base bot. It's still short.
- The **description picture** (photo or video, in the empty chat above "What can this bot do?")
  is set in @BotFather (*Edit Description Picture*). The Bot API has no method for it
  **[official]**. It is the "before Start" picture. Don't send the same image again as the
  welcome.
- `message_effect_id` works in private chats only **[API]**. The Bot API publishes no list of
  effect ids, so use only an id read from a real message's `effect_id`, test it, and keep it to
  playful consumer bots. Never invent one.

### 4.3 Text: four parts, at most seven lines

1. **Title** (bold, one line, ≤ ~40 chars). The product's name and what it is ("BrewBot · coffee
   to go"), or a greeting: "Welcome to X" when X is a brand people know, "Hi, Alice" when the
   name is clean (below). One greeting, no "!!!", no 👋🎉 stack.
2. **Value line**: what the user gets, concretely, with a number when there is one ("Coffee from
   3 shops in Kyiv, ready in 10 minutes"). Say it in different words from the description the
   user just read in the empty chat.
3. **How it works**: 2-3 short lines. Each one names an element the user can see **right
   here**: a button on this message, the menu button, a command, or "just write …". Use the
   button's exact label in bold, so the eye links the line to the button. Never describe a
   button, command or menu that isn't there. This is the "short description of the interface",
   not a feature list.
4. **Promise or one-time note** (optional, one line): the trust line (free, pay on pickup, no ads,
   what notifications they'll get), or the referral bonus or linked item, shown once.

**Budget** **[heuristic]**: ≤ 7 non-empty lines, ≤ ~500 visible characters. The first line stays
≤ ~80 visible characters, because notification and chat-list previews cut there. Hard limits
**[API]**: caption 0-1024 and text 1-4096 characters, both after entity parsing.

**Formatting**: bold the title and the button names, nothing else. No headings, no bullet wall,
no ALL CAPS. At most 1-2 emoji, used as anchors and never as decoration (`visual-language.md`
§3). In a text welcome, a privacy or terms link needs `link_preview_options.is_disabled`, or its
preview will take over the message.

**The user's name** (`from.first_name`) **[heuristic]**: it's user-controlled. Escape it with the
one escaping function for the format, cap it at ~32 characters, and skip it when it's empty
after trimming or is only symbols. Isolate a right-to-left name in left-to-right text
(`localization-and-rtl.md`). Use it in the greeting only, never as the whole title. Never use
`username` or `last_name`, and never write "Dear user". In languages that inflect names in
address (Ukrainian vocative "Богдане", Polish "Anno"), greet without the name unless the
project has a reliable inflection. The nominative there reads like a form letter.

**Voice**: the bot's voice from its style profile (`bot-style-profile.md`). Formal or informal
address ("вы" or "ты", "ви" or "ти") is decided once per language and kept everywhere.

**Never on the welcome** **[heuristic]**:

- "I'm a bot that can: 1) … 10) …": list jobs as buttons, not as a manual;
- "Choose an option below 👇", "Press /help for help": the buttons explain themselves;
- the description text repeated word for word;
- asking for a phone, email or location before any value (`user-data.md`: at the moment of need);
- a forced "subscribe to our channel to continue" before the first result. If the business
  insists, deliver the first result first, then ask and say why;
- a terms wall. One line with a link is enough where data or payments require it;
- "Loading…", fake progress, or a timer before the welcome.

### 4.4 Buttons

- **One primary**, the first useful result, with `style: "primary"` **[heuristic, floor.md]**. Then
  1-3 neutral secondaries: 2-4 buttons, ≤ 3 rows, ≤ 2 per row so long translations fit
  (`buttons-and-styles.md`).
- **Order**: primary on top and full width; secondaries in pairs below; Help or About last.
  Settings stays in the menu and commands unless the first-run decision lives there.
- **Only actions that have something behind them for a new user.** "My orders" with no orders
  waits until the first order; "Continue the lesson" waits until there is a lesson
  **[heuristic]**. Every button that does appear works for a brand-new user.
- **Labels are the verbs the text used.** If the text says "tap **Order**", the button says
  "Order".
- **Mini App products**: the primary is a `web_app` button "Open <app>", and the menu button
  opens the same app (`setChatMenuButton`, set at deploy).
- **AI and typing-first bots**: the primary action is typing, so the buttons are 2-3 example
  requests that run on tap ("Summarize a link", "Plan my week"). The text ends with "or just
  write your question".
- Every tap gets `answerCallbackQuery` first **[floor.md]**. `callback_data` is versioned so a
  welcome scrolled back to weeks later still answers.

### 4.5 Chat chrome around it

Set the description (empty-chat text, 0-512), the short description (profile and share card,
0-120), the commands and the menu button once per deploy and per language, never inside the
`/start` handler **[API limits; heuristic placement]**. The `/start` command's own description
says what it does now ("Main menu"). The welcome's "how it works" may point at the menu button
only if it is set. Don't pin the welcome: pins are for state the user comes back to (an active
order, a subscription), not for the introduction.

### 4.6 Inline buttons or a reply keyboard

Inline buttons on the welcome suit most bots. A persistent reply keyboard (`is_persistent`,
`resize_keyboard` **[API]**) only fits bots whose users repeat 2-4 actions all day: cashier
tools, quick logging, support agents (`reply-keyboards.md`). Then the welcome itself carries it
as its `reply_markup`, with no inline buttons on that message, and the text names the buttons
"below the input field". Never put `request_contact` or `request_location` on the welcome.

## 5. Variants by bot type

Pick the closest row. Most bots combine two, so take the first useful result from the main job
**[heuristic]**. The archetypes are in `bot-archetypes.md`.

| Bot type | First useful result | Picture | Primary | Secondary | The line that must be there | Avoid |
|---|---|---|---|---|---|---|
| Shop, food, ordering | an item in the cart | yes: the product or counter | Order / Open the catalog | Today's offer · Help | price or delivery or pickup promise | a category dump of 8 buttons |
| Booking, services | a free slot chosen | yes: the place or the specialist | Book a time | Prices · Address | when the next free slot is, how to cancel | asking for the phone first |
| AI assistant | the first good answer | no, or one real example output | (typing) + 2-3 example requests | Modes or Settings last | what it's good at, in one line; limits if any ("10 free questions a day") | "I'm an AI language model…" |
| Image or media AI | the first generated result | yes: a real output | Try an example | My images (later) · Plans | what to send, with an example | a gallery of 10 samples |
| Learning, courses | the first lesson started | yes: the course cover | Start lesson 1 | How it works · Plans | length and pace ("5 minutes a day") | a syllabus in the welcome |
| Content, knowledge base | the first answer found | optional | Search / Browse topics | Popular · About | what's covered and how fresh it is | the whole table of contents |
| Monitoring, alerts | the first thing watched | no | Add <thing> to watch | Example alert · Help | what an alert looks like and how often they come | three demo alerts sent at once |
| Wallet, crypto, payments | wallet linked or first balance shown | optional | Connect wallet / Show balance | Fees · Security | what it can and can't do with funds | asking for a seed phrase (never) or keys |
| Support desk | the question sent | no | (typing) "Describe the problem" or Choose a topic | My tickets (later) · Hours | when a human answers ("replies within 2 hours on weekdays") | a FAQ wall before the user can write |
| Community or group helper (private chat) | the group set up or rules accepted | no | Add to a group (`startgroup` URL) / Set up | How it works | which rights it needs and why | personal onboarding in the group |
| Mini App-first | the app opened | yes: a real screen of the app | `web_app` Open <app> | Help | what the app does, in one line | repeating the app's own onboarding in chat |
| Subscription, paywall | the free part used | optional | Try it free / Start | Plans | price and trial in plain words, how to cancel | the paywall as the first screen |
| Games | the first round | yes: the board | Play | Rules · Leaderboard | how long a round takes | a rules essay |
| Utility, one-shot tool (converter, downloader) | the first conversion | no | (send input) "Send me a link" with an example in `<code>` | Formats · Help | what input works and the limits | a menu for a tool with one job |
| Agent or ops bot (the owner's own) | the first notification set up | no | Connect / Test notification | Settings | who can use it (operator only) | anything public; tokens in the text |
| Business account bot | the owner's panel | no | Open the panel | Help | what it does on the owner's behalf | the consumer welcome |

## 6. After the welcome: edits and navigation

Decide this when designing the welcome. A photo welcome changes what the next tap can do
**[API]**:

- `editMessageText` edits **text, rich and game messages** only. On a photo welcome it fails
  ("there is no text in the message to edit"). The caption changes through `editMessageCaption`,
  and the picture through `editMessageMedia`.
- `editMessageMedia` can turn a text message into a media message (7.11+), but nothing turns a
  media message back into text. Going from a photo screen to a text screen means a new message.

So pick one model per bot **[heuristic]**:

| Model | Use when | Mechanics |
|---|---|---|
| **The welcome stays; deeper screens are new messages** | a photo welcome in a text-first bot | the first tap sends the next screen as a new message; the welcome's buttons keep working; "Home" sends home again |
| **Edit in place, all media** | every main screen has a picture (catalog, gallery) | each screen is `editMessageMedia` with its own photo, caption and keyboard |
| **Edit in place, all text** | a text welcome | `editMessageText` from screen to screen (`navigation-and-flows.md`) |

**One live home** **[heuristic]**: store `home_message_id`. On a new `/start`, send the home, then
remove the old home's buttons (`editMessageReplyMarkup` without a keyboard) or delete it. Bots
can delete their own messages in private chats, within 48 hours of sending **[API]**. Old
messages never keep a second set of live main-menu buttons.

## 7. Failure paths

| Failure | Behaviour |
|---|---|
| The photo fails (bad `file_id` after moving to a new bot, the URL is down) | send the text welcome right away, log it; no retry loop. The user never gets nothing |
| The user blocked the bot before the welcome arrived (403) | stop and mark the user; no retries |
| The parameter has expired or is unknown | the plain welcome. Add one line ("This link has expired") only when the user clearly expected something (a product, a promo) |
| A string is missing in their language | the fallback language, logged (`I18n.missing()`) |
| Slow work on `/start` (CRM sync, analytics) | send the welcome first, do the work after; the welcome never waits on a third party |
| A long, empty or right-to-left name | escaped, capped, isolated, or dropped from the greeting (§4.3) |
| Duplicate `/start` | §2, last row |

## 8. Worked examples

Mock-ups, not client screenshots. Full requests: `examples/welcome/coffee-shop.json`, checked by
`tgui.py check welcome`.

**A. Coffee shop, new user, Ukrainian, photo** (`sendPhoto` by `file_id`):

```
[ photo: the counter with today's drinks, 16:9 ]
BrewBot · кава з собою                            (bold)
Кава з 3 кавʼярень Києва, готова за 10 хвилин.
Натисніть «Замовити», оберіть напій і точку — напишемо, коли все готово.
Оплата при отриманні, без реєстрації.
[ Замовити ]                    (primary)
[ Адреси й години ] [ Допомога ]
```

No name in the title: Ukrainian addresses people in the vocative ("Богдане"), and a name the
bot can't inflect reliably reads wrong. No "My orders" either: a new user has none yet.

Variants. **QR on the cup** (`/start item_flatwhite`): the flat white's photo and price with
"BrewBot · кава з собою" above it, primary "Додати в замовлення". **Returning**: "BrewBot" in
bold, then "Замовлення #1042 готується, буде о 12:40" and the same buttons plus "Мої
замовлення", no photo. **`language_code` de**: the picker (below), then the welcome replaces it.

**B. AI assistant, new user, Russian, text only:**

```
Привет, Алиса                                      (bold)
Отвечаю на вопросы по вашим документам и ссылкам и показываю, откуда ответ.
10 вопросов в день — бесплатно.
Напишите вопрос, пришлите файл или нажмите пример:
[ Кратко пересказать ссылку ]   (primary)
[ Разобрать PDF ] [ Что ты умеешь? ]
```

The example buttons run a real sample request. Each answer streams with Stop
(`dynamic-feedback-and-streaming.md`).

**C. Price alerts, text only, the first job is the setup:**

```
PriceWatch                                         (bold)
Сообщу, когда цена монеты пересечёт ваш уровень, — без спама, только по событию.
Нажмите «Добавить монету» или напишите, например: <code>BTC 70000</code>
[ Добавить монету ]             (primary)
[ Как выглядит уведомление ]
```

**D. The language picker, then the welcome in its place** (booking bot, `language_code` missing):

```
Choose a language · Оберіть мову                   (text message, instant)
[ Українська ] [ English ]
[ Русский ]
        ↓ tap "Українська": editMessageMedia replaces this message
[ photo: the studio ]
Студія «Лінія» · запис на манікюр                   (bold)
Найближчий вільний час — сьогодні о 16:30.
Натисніть «Записатися», оберіть майстра й час. Скасувати можна за 3 години.
[ Записатися ]                  (primary)
[ Ціни ] [ Адреса ]
```

## 9. Self-check

Before showing the welcome to the user, every line must hold:

- [ ] The brief (§1) is written. Each real entry (§2) has its own first message, and the
      returning one is among them.
- [ ] One message: media, text and buttons together. No album, no "Choose an option" follow-up.
- [ ] The language rule (§3) is applied. The picker, if any, is replaced by the welcome, and a
      deep-link payload survives the pick.
- [ ] The picture shows the product or the result, has no baked-in text, is landscape or square,
      and is sent by `file_id`. Or there is no picture, and that is the right call for this bot.
- [ ] Title, value, how-it-works and an optional promise: ≤ 7 lines, the first ≤ ~80 visible
      characters, the caption ≤ 1024.
- [ ] Every button named in the text exists, with the same label. No dead or empty actions for
      a new user.
- [ ] One primary, 2-4 buttons, ≤ 2 per row, Help last. Nothing asks for personal data.
- [ ] The name is escaped, capped and isolated, or not used. The start parameter is never echoed.
- [ ] Next-tap mechanics fit the media type (§6). One live home on a repeated `/start`.
      Duplicates are dropped.
- [ ] The text fallback for a failed photo exists. Every language has the strings.
- [ ] `tgui.py check welcome <spec.json>` is clean. The evidence level is named (static or
      offline contract, not seen in a client).

## 10. The welcome spec and `check welcome`

Write the design as a spec file, `bot-ui/welcome.json` or next to the handler: one scenario per
entry, each with the requests the bot sends. A step with `"on"` runs after a user action, and
steps without it run right after the entry **[heuristic format of this skill]**.

```json
{
  "kind": "welcome-spec",
  "bot": "BrewBot",
  "archetype": "shop",
  "languages": ["en", "uk"],
  "scenarios": [
    {"id": "new", "entry": "/start", "user": "new", "language_code": "uk",
     "steps": [{"method": "sendPhoto", "params": {"chat_id": 111, "photo": "<file_id>", "caption": "…",
                "parse_mode": "HTML", "reply_markup": {"inline_keyboard": [[…]]}}}]},
    {"id": "returning", "entry": "/start", "user": "returning", "steps": […]},
    {"id": "unknown-language", "entry": "/start", "user": "new", "language_code": "de",
     "steps": [{"method": "sendMessage", "params": {…picker…}},
               {"on": "tap lang:uk", "method": "editMessageMedia", "params": {…welcome…}}]}
  ]
}
```

`py -3 <skill>/scripts/tgui.py check welcome bot-ui/welcome.json` (or `--json`) checks every
request against the catalog and every keyboard with the keyboard validator. It adds the welcome
rules: one message before the first tap (`WELCOME_SPLIT`), no album (`WELCOME_ALBUM`),
caption and text limits, no data request on the first message (`WELCOME_ASKS_DATA`), a next
action (`WELCOME_NO_ACTION`), one primary and at most 6 buttons, line and first-line budgets,
greeting filler (`WELCOME_FILLER`), a stray link preview, setup calls inside `/start`, a text edit
of a media welcome (`EDIT_TEXT_ON_MEDIA`), and coverage: a returning scenario, an
unsupported-language scenario when there are several languages, and a returning message that
differs from the new one. `tgui.py check changed` runs it on changed spec files.

Related: [onboarding-and-first-run.md](onboarding-and-first-run.md),
[microcopy-and-labels.md](microcopy-and-labels.md), [visual-language.md](visual-language.md),
[media-and-files.md](media-and-files.md), [navigation-and-flows.md](navigation-and-flows.md),
[localization-and-rtl.md](localization-and-rtl.md), [bot-archetypes.md](bot-archetypes.md).
