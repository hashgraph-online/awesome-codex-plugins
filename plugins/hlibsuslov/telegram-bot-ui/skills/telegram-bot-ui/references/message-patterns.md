---
summary: "Notification and message patterns: header formula (icon + 2-5 bold words), body blocks and how they combine, 18 patterns by type, sound and lifecycle, reworking a bot's notifications."
verified: "2026-11-27"
bot_api: "10.5"
---

# Message patterns: the structure of notifications and bot messages

> Verified 2026-11-27 against Bot API 10.5 (HTML tags in `regular-formatting.md`, `disable_notification`
> in `sendMessage`). Catalog: `data/message-patterns.json` (`tgui.py patterns list|find|show|render|check`).
> Renderer: `examples/python/tgkit/notify.py`. Tags: **[API]** API requirement · **[heuristic]** design
> heuristic of this skill.

A message the bot sends on its own (an alert, a status change, a report, a reminder) is read in
a notification preview first, often on a lock screen, and only then in the chat. Its structure
decides whether people read it, act on it or mute the bot. This file gives one grammar for every
such message, a library of patterns by notification type, and the procedure for reworking a
bot's existing notifications. Keyboards and labels live in `buttons-and-styles.md`, tables and
numbers in `data-views.md`, wording in `microcopy-and-labels.md`.

## Do this, in order

Every request that builds or reworks what a bot sends on its own follows these steps, and the
answer shows each one **[heuristic]**:

1. **List and classify.** Every message the bot sends on its own, with its trigger. Give each a
   pattern id from §6 written as the id (`report-kpi`, not "periodic report") and say in one line
   why this pattern and not the nearest other. Put it in a table in the answer: message · pattern
   id · why · sound · lifecycle.
2. **Before/after for two types, then stop.** Rework: rewrite two representative types (an alert
   or an order, and a report) as before/after (§8), with every `{placeholder}`, locale key and
   `callback_data` copied from the source as is (`{id}`, not "1042"). Then stop and ask for a yes
   before rewriting the rest: a rework changes what every user receives. Don't ask about style
   beforehand; the before/after is the question. New bot: one rendered example per pattern, no
   stop.
3. **Fill every slot.** Bold header (one icon + 2-5 words), subject, blank line, one or two body
   blocks, blank line, **italic footer** with the as-of time, the source or the next step. Only a
   one-fact message ("✅ Saved") goes without body and footer.
4. **Render with the skill's renderer, not your own.** Python: `tgkit/notify.py` (copy it into
   the project; `message()` or `payload(spec)` take the slots). Any other stack: write the spec,
   run `tgui.py patterns render <spec.json>`, and port the output keeping its slot order. Don't
   write a second formatter.
5. **Implement sound, lifecycle and grouping; don't leave them as suggestions** (§5).
   `disable_notification` per type. The callback that handles an ask or an alert edits the
   message into its outcome line ("Taken: Igor · 14:05") and removes the buttons. Repeats of one
   event get a cool-down and go into a digest.
6. **Check and name the evidence.** `tgui.py patterns check <payload.json> --pattern <id>` on
   every payload until clean, then `tgui.py check changed`. Say "static checks, not seen in a
   client".

## Contents

- [Do this, in order](#do-this-in-order)
- [1. The grammar](#1-the-grammar)
- [2. The header line](#2-the-header-line)
- [3. Body blocks](#3-body-blocks)
- [4. Combining blocks](#4-combining-blocks)
- [5. Sound, lifecycle and grouping](#5-sound-lifecycle-and-grouping)
- [6. The pattern library](#6-the-pattern-library)
- [7. Choosing a pattern](#7-choosing-a-pattern)
- [8. Reworking a bot's notifications](#8-reworking-a-bots-notifications)
- [9. One grammar per bot](#9-one-grammar-per-bot)
- [10. Self-check and tools](#10-self-check-and-tools)

## 1. The grammar

Every pattern is built from the same five slots, in this order **[heuristic]**:

```
<b>[icon] Header: 2-5 words</b>        ← the news itself; the push preview shows this line
Subject line                            ← optional: which object (name, number, amount, place)
                                        ← blank line
Body: one or two blocks                 ← facts, list, timeline, stats, quote, code … (§3)
                                        ← blank line
<i>Meta or hint</i>                     ← optional: time, as-of, source; or the consequence / next step
[ Primary action ] [ Secondary ]        ← only when the reader can act; §5 says when to remove them
```

- The **header** answers "what happened". The **subject** answers "to what". The **body** gives
  the facts the reader needs to decide. The **footer** says when, from where or what next.
- The blank line after the header group matters: it separates the news from the details, and the
  eye jumps straight to the body. No blank lines inside one block.
- A one-fact message ("✅ Saved") is just a header. Don't pad it to fill the slots.

## 2. The header line

**Formula:** one icon + 2-5 words in bold, ≤ ~40 characters. The whole first line stays ≤ ~80
visible characters, because previews cut there **[heuristic]**. No period, no "!", no greeting.
Leave out the bot's name too: the chat title already shows it.

### The icon slot

- **Exactly one icon.** It is either a **status mark** or a **category mark**:
  - status, the reserved vocabulary of `visual-language.md` §3: ✅ done · ⚠️ needs attention ·
    ❌ failed · ⏳ in progress;
  - category, one per notification type and fixed bot-wide: 📦 order · 💳 payment · 📊 report ·
    🔔 reminder · 💬 message · 🔐 security · 🏷 price · 🧾 receipt · 📈 alert up / 📉 alert down.
- **Status wins when the status is the news**: a failed payment is ❌, not 💳. A delivered order
  is ✅ when "done" matters, 📦 when it's just one step of a tracker.
- **Premium emoji**: write the Unicode icon in the template. An eligible bot upgrades it to the
  same slot's custom emoji (`tgkit/icons.py`: `IconSystem.prepare`; `emoji-packs.md`). Static
  only, one family, and the Unicode alternative keeps the same meaning in pushes and forwards.
  Custom emoji need Fragment usernames or an owner with Premium **[API]**. Never put an icon in
  the header that the bot can't show to everyone.
- No icon at all when the bot's icon system is `none` (style profile). The bold words carry the
  header alone.

### The words

Pick the form by pattern and keep it for every message of that type **[heuristic]**:

| Form | Use for | en | ru | uk |
|---|---|---|---|---|
| Object + state | status change, receipt | Order #1042 shipped | Заказ #1042 отправлен | Замовлення #1042 надіслано |
| Event noun | new message, lead, review | New review | Новый отзыв | Новий відгук |
| The ask | action required | Approval needed | Нужно подтверждение | Потрібне підтвердження |
| Value headline | alert, price drop | BTC above $70,000 | BTC выше 70 000 $ | BTC вище 70 000 $ |
| Period headline | report, digest | Sales this week | Продажи за неделю | Продажі за тиждень |
| Time headline | reminder | Appointment tomorrow at 10:00 | Запись завтра в 10:00 | Запис завтра о 10:00 |
| Problem | failure, incident | Payment failed | Оплата не прошла | Оплата не пройшла |

- **The decisive fact goes into the header** when it fits: the number crossed, the state reached,
  the time. "Order #1042 shipped" beats "Order update".
- **State, not story.** "Order shipped", not "We are happy to inform you that your order has been
  shipped". In Russian and Ukrainian, use the short participle that agrees with the noun
  ("Заказ оплачен", "Оплата получена", "Підписку продовжено") **[heuristic]**.
- A number or code counts as a word. Up to five words means up to five units the eye reads
  before it decides.
- No ALL CAPS, no "Attention", "Important" or "News": the icon and the words already say it.

## 3. Body blocks

A body is made of blocks. Each has a job and a rendered form. Every helper escapes its input
(`tgkit/notify.py`):

| Block | Job | Form (HTML) | Helper |
|---|---|---|---|
| `sentence` | what happened, why, in prose | one or two sentences | `sentence()` |
| `facts` | 2-6 values the reader checks | `Label: <b>value</b>` per line | `facts()` |
| `bullets` | 3-7 items of one kind | `• item` per line | `bullets()` |
| `timeline` | steps of one process | `✓ Paid · 10:02` / `<b>● On the way</b>` / `○ Delivered` | `timeline()` |
| `kpi` | numbers with change | `Revenue: <b>€12,400</b> ▲ 8%` | `dataview.kpi_lines` |
| `progress` | how far a job or a goal is | `▰▰▰▰▱▱▱▱▱▱ 40%` + count | `dataview.progress` |
| `grid` | rows that share columns, few | `<pre>` aligned table (≤ 4 columns, ≤ 10 rows) | `dataview.mono_lines` |
| `quote` | someone's words: a review, a message, an excerpt | `<blockquote>`; `expandable` above 3 lines | `quote()` |
| `details` | logs, the full list, technical detail | `<blockquote expandable>` | `details()` |
| `code` | a value people copy | `Label: <code>value</code>` | `code()` |
| `media` | a product, a place, a chart | a photo with this anatomy as its caption (≤ 1024 **[API]**) | the send method |

Rules per block **[heuristic]**:

- **facts**: labels of 1-2 words, one separator bot-wide (": "). Bold only the values people
  check, not every word. Keep the order the reader decides in: amount before ID.
- **bullets**: one bullet character bot-wide (•). Never bullets for facts that have labels.
- **timeline**: ✓ done, ● current (bold), ○ next. Time after the label. Collapse past steps once
  there are more than five.
- **kpi**: always say what it compares with ("vs last week"). "Down" isn't always bad, so say so
  for latency and refunds (`data-views.md` §2).
- **quote**: the other person's words verbatim and escaped, with the author in the subject line.
  Never the bot's own text in a quote.
- **details**: the main fact stays outside. Expandable is for "if you need it", never for the
  news.
- **code**: one value per line. Use a `copy_text` button for the one value people copy most
  (`buttons-and-styles.md`).
- **Times**: `<tg-time unix="…" format="wDT">fallback</tg-time>` (9.5+ **[API]**) shows the reader's
  time zone and language. Without it, local time with the zone. Never a raw ISO stamp.
- **Lists that need real tables, headings or long text** go to a Rich Message
  (`format-selection.md`, `tables.md`). A notification stays a regular message.

## 4. Combining blocks

**[heuristic]**

- **At most two block types** in one body, plus the footer. The usual pairs are `sentence` +
  `facts`, `facts` + `code`, `kpi` + `bullets`, `timeline` + `facts`, `quote` + `facts`, and
  `facts` + `details`.
- **Order by decision**: the block that decides the action comes first. The quote comes after
  the facts that frame it, and details always go last.
- **Never the same data twice**: if the header says the amount, the facts don't repeat it.
- **Budget**: ≤ 8 body lines (style profile `density.max_body_lines`). Beyond that, the summary
  plus the top 5 and a "Show all" button, a Rich report, or a file (`data-views.md` §4).
- **Emoji**: the header icon plus status marks inside `timeline`, `kpi` or status words, ≤ 1 per
  line, ≤ 3 per message unless the profile allows more. No decorative separators (`━━━━`,
  `➖➖➖`, `=====`): they wrap on phones and read as noise.
- **Formatting**: bold for the header and the checked values, italic for the footer, code for
  copyable values. Underline and strikethrough only when they mean something (an old price).

## 5. Sound, lifecycle and grouping

| Decision | Options | Rule **[heuristic]** |
|---|---|---|
| Sound | `ping` · `silent` (`disable_notification: true` **[API]**: "a notification with no sound") | ping only when the reader must act or wants to know right now. Reports, digests, progress, notices, rewards: silent |
| Lifecycle | `new` · `edit_in_place` · `edit_on_resolve` · `reply_to_first` | progress and trackers edit one message. An ask or an alert, once handled, is edited into its outcome line with the buttons removed. Follow-ups reply to the first message (`reply_parameters`) |
| Grouping | `instant` · `digest` | more than ~3 events of one kind within ~10 minutes become one digest; a lone event stays instant |
| Pinning | rarely | pin only live state the reader keeps returning to (an active order), `pinChatMessage` with `disable_notification` **[API]** |

Edits don't make a sound, so a status change that the reader must notice is a new message (or
a reply to the card), not an edit **[heuristic]**. Group and channel audiences: one ping for many
people, so be stricter about sound and send personal data only in private chats
(`ephemeral-and-personal.md`).

## 6. The pattern library

Every pattern below is in `data/message-patterns.json` with names and search words in en/ru/uk,
the header form and word range, blocks, buttons, sound, lifecycle and a rendered example
(`tgui.py patterns show <id> --lang ru`). The mock-ups show the visible text. The first line is
bold, values in facts are bold, the footer is italic, `>` marks a quote, and "▸" marks an
expandable block. The exact HTML is in the catalog's examples.

### `status-change`: an object moved to a new state
Order shipped, application approved, ticket closed. Header: object + state, 2-5 words. Body:
`facts` (what, where, when) or `timeline` for multi-step objects. Sound: ping when the reader must
act (pickup), else silent. Lifecycle: new message per meaningful step, or one tracker edited in
place plus a ping on the steps that matter (recipe 64).
```
📦 Заказ #1042 отправлен
Новая Почта, отделение № 12

Трек-номер: 20450012345678
Доставка: завтра, до 18:00
[ Отследить ]
```

### `action-required`: the reader must decide
Approve a payout, confirm a booking, answer a question. Header: the ask. Body: `facts` that the
decision needs, then a hint with the deadline and what happens if nobody answers. Buttons:
the forward action `primary` (or `success` when it commits) and the alternative neutral. Sound:
ping. Lifecycle: `edit_on_resolve` ("Approved by you · 14:05", no buttons).
```
⚠️ Нужно подтверждение
Выплата партнёру ООО «Север»

Сумма: 48 000 ₽
Счёт: № 381 от 25.11

Без ответа до 18:00 выплата перенесётся на завтра.
[ Подтвердить ] [ Отклонить ]
```

### `alert-threshold`: a watched value crossed a level
Price, balance, error rate, temperature. Header: value headline with the direction. Body: `facts`
(now, the level, the change over a period) plus meta "as of". Sound: ping. Grouping: one alert
per crossing, a cool-down before the next; repeated crossings go into a digest. Buttons: open the
source, change the level, mute.
```
📈 BTC выше 70 000 $
Ваш уровень: 70 000 $

Сейчас: 70 412 $ ▲ 2,1% за час

данные на 14:05
[ Изменить уровень ] [ Выключить ]
```

### `incident`: something broke
Service down, failed deploy, a stuck queue. Header: ❌ or ⚠️ and the problem. Body: `facts`
(since, impact, scope), `details` for the log. Follow-ups reply to the first message, and the
resolution edits it ("✅ Resolved · 12 min") (recipe 47). Sound: ping on open, silent on updates.
```
❌ API недоступен
eu-west · с 14:02

Затронуто: оплаты и вход
Ошибок: 38% запросов
▸ Подробности (лог, развёрнуть)
[ Открыть мониторинг ]
```

### `report-kpi`: a periodic summary
Daily sales, weekly stats, monthly usage. Header: period headline. Subject: the one-line
conclusion ("Revenue up, refunds normal"). Body: `kpi` (3-6 lines with change and comparison),
optionally `bullets` for the top items. Sound: silent. Lifecycle: new message per period.
Overflow: "Full report" button.
```
📊 Продажи за неделю
Выручка выросла, возвраты в норме

Выручка: 412 000 ₽ ▲ 12%
Заказы: 318 ▲ 4%
Средний чек: 1 296 ₽ ▲ 8%
Возвраты: 6 ▼ 2

по сравнению с прошлой неделей
[ Полный отчёт ]
```

### `product-card`: an item worth a look
New arrival, back in stock, price drop, recommendation. A photo with the anatomy in its caption.
Header: the news about the item ("Back in stock", "Price dropped to €39"). Body: `facts` (price
with the old one struck through, size, stock). Buttons: Buy / Add to cart `primary`, Details.
Sound: silent unless the user asked for this alert. Never more than one card per push; several
go into a digest.
```
[ фото: кроссовки ]
🏷 Цена снижена до 3 990 ₽
Nike Pegasus 41, размер 42

Было: 5 490 ₽
Осталось: 3 пары
[ Купить ] [ Подробнее ]
```

### `receipt`: payment received or order confirmed
Header: ✅ or 🧾 and object + state. Body: `facts` (amount, items, method, number) + `code` for
the order number. Sound: silent if the user just paid in the chat, ping if it arrives later.
Never split a receipt (`data-views.md` §3.7).
```
🧾 Оплата получена
Флет вайт × 2, круассан

Сумма: 255 ₴
Заказ: 1042
Способ: Telegram Stars
[ Мои заказы ]
```

### `payment-problem`: money did not go through, or soon won't
Failed payment, card expiring, subscription not renewed. Header: ❌/⚠️ + problem. Body:
`sentence` (what it means for the user), `facts` (amount, date). Primary: fix it (Pay again,
Update card). Sound: ping. Lifecycle: edited to ✅ when fixed.
```
❌ Оплата не прошла
Подписка Pro не продлена

Сумма: 299 ₽
Доступ сохранится до 30.11
[ Оплатить снова ]
```

### `reminder`: something is coming
Appointment, deadline, event start. Header: time headline, with `<tg-time>`. Body: `facts`
(where, with whom, how long), hint: how to reschedule or cancel and until when. Buttons: Confirm
/ Reschedule. Sound: ping at the right moment, never at night in the reader's time zone.
Cancelled or finished tasks never remind (recipe 22).
```
🔔 Запись завтра в 10:00
Маникюр, мастер Ольга

Адрес: ул. Ленина, 5
Длительность: 1,5 часа

Перенести можно до 20:00 сегодня.
[ Подтвердить ] [ Перенести ]
```

### `message-relay`: someone wrote
An operator's answer, a customer's message, a comment, a mention. Header: 💬 + event noun. The
subject line gives who and where. Body: `quote` with their words (expandable when long).
Buttons: Reply (`force_reply` or open the chat), Open. Sound: ping. Lifecycle: `reply_to_first`
for threads.
```
💬 Новый ответ поддержки
Обращение № 553 · Ирина

> Мы проверили платёж: деньги вернутся на карту
> в течение 3 рабочих дней.
[ Ответить ] [ Закрыть обращение ]
```

### `new-lead`: work arrived for the staff
A new order, lead, application or review for the business side. Header: event noun + the key
number ("New order · 3 400 ₽"). Body: `facts` (who, what, how to reach) + `quote` for the
customer's note. Buttons: Take, Call, Open in CRM. Sound: ping. In a staff group: the first who
taps Take owns it, and the card is edited to show who did (recipe 21).
```
📦 Новый заказ · 3 400 ₽
Анна К. · самовывоз

Состав: 2 позиции
Телефон: +7 900 123-45-67
> Без лука, пожалуйста
[ Взять в работу ] [ Открыть ]
```

### `progress-card`: a long job is running
Export, import, generation, upload. One message edited in place: header ⏳ + the job, `progress`
with the count, `timeline` of stages, Cancel. On finish: edited to ✅ + the result, plus one new
silent or pinging message if the user left (recipe 54, `streaming-and-editing.md`).
```
⏳ Экспорт заказов
Январь–ноябрь 2026

▰▰▰▰▰▰▱▱▱▱ 60%
12 400 из 20 650 строк
[ Отменить ]
```

### `security`: account access changed
New login, password changed, a new device, unusual activity. Header: 🔐 + event. Body: `facts`
(device, place, time) and a sentence on what to do if it wasn't them. Primary: "It wasn't me"
(not `danger`: it protects). Sound: ping always. Never put the secret itself in the message.
```
🔐 Вход с нового устройства
iPhone 15 · Варшава

Время: сегодня в 09:12
Если это были не вы, завершите сеанс.
[ Это не я ] [ Это я ]
```

### `digest`: many small events, batched
Price changes, new comments, task updates collected over a window. Header: period + count ("5
new reviews today"). Body: `bullets` (top 5, one line each) + "and 7 more". Sound: silent. It
replaces separate pushes for the same type, never a single urgent event.
```
💬 7 новых отзывов за день
Средняя оценка: 4,6

• Анна: «Быстро и вкусно» ★5
• Игорь: «Курьер опоздал» ★3
• Мария: «Всё отлично» ★5
и ещё 4
[ Все отзывы ]
```

### `milestone`: the user reached something
Goal reached, streak, level, course finished. Header: ✅ or the category mark + the achievement
(no 🎉 stack). Body: `progress` or `facts` (what it took), the next goal as a hint. Sound:
silent. Buttons: share (`switch_inline_query` or a share link), next step. At most one per day.
```
✅ 30 дней подряд
Испанский · уровень A2

Уроков пройдено: 42
Следующая цель — 60 дней.
[ Продолжить ] [ Поделиться ]
```

### `service-notice`: news from the service
Maintenance, a new feature, a change of terms. Header: the change in 2-5 words. Body:
`sentence` + `facts` (when, what changes for the reader). Sound: silent. Rate: rare, and never
as a disguised ad. A changelog goes to a channel, not to every user's chat.
```
⚠️ Техработы в ночь на субботу
30.11, 02:00–04:00 по Москве

Оплата и вход будут недоступны.
Заказы, оформленные заранее, не пострадают.
```

### `error-blocker`: what the user asked for failed
An upload rejected, a generation failed, a request can't continue. Header: ❌ + what failed (not
"Error"). Body: `sentence` (why, in the reader's words) + one action. `details` holds the
technical part only for technical audiences. Sound: ping when the user is waiting elsewhere,
else silent. Sent at once, not at the end of a long run (`errors-and-fallbacks.md`).
```
❌ Файл не загружен
report.xlsx · 34 МБ

Лимит — 20 МБ. Разделите файл или пришлите CSV.
[ Отправить другой файл ]
```

### `reward`: value credited
A referral bonus, cashback, free month, Stars received. Header: ✅/🎁 + what arrived, with the
number. Body: `facts` (from whom or for what, the new balance), a hint on how to use it. Sound:
silent. Credited once (`OnceStore`), and it says who triggered it only when that person agreed.
```
🎁 +500 бонусов
За приглашение: Алиса

Баланс: 1 250 бонусов
Списать можно при следующем заказе.
[ Потратить ]
```

## 7. Choosing a pattern

Ask the event five questions; the answers pick the pattern, sound and lifecycle **[heuristic]**:

| Question | If yes |
|---|---|
| Must the reader decide something? | `action-required` (ping, edit on resolve) |
| Did something break or fail? | for the user's own request `error-blocker`; for a service `incident`; for money `payment-problem` |
| Is it one object's state? | `status-change`; many steps of one object → a tracker edited in place |
| Is it a number against a level or a period? | crossing a level → `alert-threshold`; a period → `report-kpi` |
| Did a person write or do something? | to the user → `message-relay`; to the business → `new-lead` |

Then: time-bound → `reminder`; money arrived → `receipt` or `reward`; an item → `product-card`;
access → `security`; running work → `progress-card`; many small ones → `digest`; an achievement
→ `milestone`; news from the service → `service-notice`. When an event fits two, pick by what the
reader does next, and never send two messages for one event. `tgui.py patterns find "<what the
message says>"` matches the words in en, ru or uk.

## 8. Reworking a bot's notifications

The procedure for `improve` and `audit` when a bot already sends notifications **[heuristic]**:

1. **Inventory.** Find every message the bot sends on its own: scheduled jobs, webhooks, queue
   consumers, event handlers, admin broadcasts. Grep for send calls outside command and callback
   handlers. For each, note the trigger, frequency, audience, current text and keyboard.
2. **Classify.** Give each a pattern id (§7). A message doing two jobs (a receipt that's also an
   ad) gets split, or keeps the main job. Same type, different shapes across the bot is a
   finding.
3. **Map facts to slots.** The header gets the decisive fact in 2-5 words. The subject gets the
   object. The body gets what the decision needs. Everything else is cut, or moves to details or
   a button. Every placeholder, locale key and `callback_data` stays.
4. **Decide sound, lifecycle, grouping** (§5). Mark which messages become edits, digests or
   replies.
5. **Show, don't ask.** Rewrite two or three representative types (one alert, one report, one
   status) as before/after, then the rest. Render with `tgui.py patterns render` or
   `tgkit.notify`.
6. **Implement** in the project's builders, with icons from the bot's icon system (the Unicode
   mark in code; `IconSystem` upgrades it to the premium pack where eligible).
7. **Check** every new payload: `tgui.py patterns check <payload.json> --pattern <id>`, then
   `tgui.py check changed`. Name the evidence level: static, not seen in a client.

**Before and after.** A Russian monitoring bot:

```
Before                                        After
⚡️⚡️ ВНИМАНИЕ!!! ⚡️⚡️                         📉 BTC ниже 65 000 $
━━━━━━━━━━━━━━━                              Ваш уровень: 65 000 $
Уважаемый пользователь, курс Bitcoin
упал ниже вашего уровня 65000$. Текущая        Сейчас: 64 870 $ ▼ 3,4% за час
цена 64870.12$ (изменение -3.4%).
Время: 2026-11-27T14:05:00Z                   данные на 17:05
━━━━━━━━━━━━━━━                              [ Изменить уровень ] [ Выключить ]
С уважением, команда CryptoBot 🚀
```

What changed: the header is a value headline with one icon. "ВНИМАНИЕ", the greeting, the
sign-off, the decorative rules and the second emoji are gone. The facts are labelled, with the
locale's number format. The ISO time is now local with "as of". Two actions replace none.

## 9. One grammar per bot

Decide once, write it down next to the notification code (a short table), and apply it to every
type **[heuristic]**:

| Decision | Example |
|---|---|
| Icon system and the mark per pattern | Unicode, premium pack "Line" where eligible; 📦 status-change, 📊 report-kpi, … |
| Header form per pattern | object + state for status, value headline for alerts |
| Fact separator, bullet, timeline marks | ": " · "•" · ✓ ● ○ |
| Number, money and time formats per locale | `1 234,5`, `255 ₴`, `<tg-time>` |
| Sound and lifecycle per pattern | §5 table filled in for this bot |
| Footer style | italic, lowercase "as of 14:05" |

The style profile (`bot-style-profile.md`) holds the shared knobs: icon system, body lines,
voice. This table adds the notification-specific decisions.

## 10. Self-check and tools

- [ ] Each bot-initiated message has a pattern id; one shape per type across the bot.
- [ ] Header: one icon (or none bot-wide), 2-5 bold words, the decisive fact. No period, "!",
      greeting or bot name. First line ≤ ~80 characters.
- [ ] A blank line after the header group; one or two body block types; ≤ 8 body lines.
- [ ] Values people check in bold, copyable values in code, times via `<tg-time>` or local with
      the zone, numbers in the locale's format.
- [ ] No decorative separators, no ALL CAPS, ≤ 1 emoji per line, no greeting or sign-off.
- [ ] Sound, lifecycle and grouping set per type. Handled asks and alerts are edited into their
      outcome, with no live buttons left.
- [ ] Custom emoji only where the bot is eligible, with Unicode alternatives of the same meaning.
- [ ] `tgui.py patterns check` clean.

Tools:

- `tgui.py patterns list` shows every pattern with its names.
- `tgui.py patterns find "<text>"` finds the pattern for a message, in en, ru or uk.
- `tgui.py patterns show <id> [--lang ru]` shows the card: header form, blocks, sound, lifecycle,
  the rendered example and its payload.
- `tgui.py patterns render <spec.json>` turns a spec of slots into the HTML message and the
  `sendMessage` payload.
- `tgui.py patterns check <payload.json> [--pattern <id>]` checks the anatomy: header,
  blank line, emoji per line, decorative rules, shouting, greetings and sign-offs, separator mix,
  raw ISO times, body length. With a pattern, it also checks the header word range, sound and
  buttons.

Related: [microcopy-and-labels.md](microcopy-and-labels.md), [visual-language.md](visual-language.md),
[data-views.md](data-views.md), [buttons-and-styles.md](buttons-and-styles.md),
[streaming-and-editing.md](streaming-and-editing.md), [agent-operated-bots.md](agent-operated-bots.md),
[welcome-message.md](welcome-message.md).
