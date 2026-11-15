# Case study: btc-tracker (aiogram 3.31, built for Bot API 9.4–10.2)

> Source: github.com/hlibsuslov/btc-tracker at commit `857b8bd` (read 2026-11-12). The owner
> chose the custom emoji by hand. Data used here: `examples/case-studies/btc-tracker/`
> (`icon-map.json` from `CUSTOM_EMOJI_IDS`, `catalog.sample.json` = 39 keys × ua/ru/en).
> Upgrade recipe: [09 tracker bot](../recipes/09-tracker-bot.md).

The bot watches Bitcoin addresses and watch-only public keys, sends transaction and
confirmation alerts, shows balances and statistics, in Ukrainian, Russian and English.

## What it already does well (keep it)

| Practice | Where | Why it is right |
|---|---|---|
| One button builder wraps every `InlineKeyboardButton` | `InlineKeyboardButton()` wrapper in `bot.py` | icons, fallback and kill switch in one place |
| Kill switch for custom emoji (`TELEGRAM_CUSTOM_EMOJI_BUTTONS`) | settings | eligibility can lapse (owner's Premium) |
| Labels stay meaningful without icons; Unicode prefix removed when a custom icon is set | `_BUTTON_ICON_PREFIXES` | no double icons |
| Unicode decoration **removed** where no custom icon exists ("so one keyboard doesn't mix icon systems") | same | exactly the one-system rule |
| `style="primary"` only on the main create action; `danger` on delete + a confirmation screen saying it can't be undone | `kb_wallets`, `kb_wallet_actions`, `wallet_delete_confirm` | hierarchy by meaning |
| Step titles "Step 1 of 2 · Address number", values in `<code>`, hints in `<i>` | strings | clear screen anatomy |
| Stale-state messages ("No. 5 is no longer available. The next available number is No. 6") | `err_btc_position_stale` | server re-checks state |
| Same placeholders and leading symbols in all three languages | `audit_copy.py` on the sample: 0 errors, 0 warnings | consistent localization |
| Private-chat-only middleware, pseudonymous log refs | `log_chat_ref` | privacy |

## What to improve

1. **Seven icon families on one keyboard set.** `audit_icons.py icon-map.json` →
   Telegram iOS/macOS ×5 (tgmacicons + tgiosicons), Unigram ×2, Telegram Android ×1,
   ninecandles ×1, Unigram *animated* ×1 (`rename`), Balticbookworms ×1 (`back`), 2 unknown.
   Different stroke weights, fills and one animated icon in the same rows read as noise.
   **Fix:** choose the iOS/macOS family (already 5/13), rebuild the map from it with
   `build_icon_map.py --set tgmacicons` (+ `tgiosicons` for gaps), leave Back/Cancel label-only
   if the family lacks them, never the animated one on a button.
2. **Two visual languages for one meaning.** Titles use Unicode (`<b>💼 My wallets</b>`) while
   buttons use custom icons; search is 🔍 on buttons and 🔎 in text; back is ← and 🔙.
   **Fix:** `IconSystem.title()` puts the same custom emoji in titles (`<tg-emoji>`); one arrow pair.
3. **Status symbols as decoration.** ✅ is both "Confirmations" (a settings entry) and "success".
   **Fix:** keep ✅/⚠️/❌/⏳ for status only; give settings entries their slot icon.
4. **Four messages per transaction** (new → 1/3 → 2/3 → confirmed). **Fix (10.4):** one
   widget card per transaction in the private chat, silent state edits, caption kept current,
   one real message only for the confirmation the user chose to hear (R09). Fallback: the same
   card as an edited text message.
5. **Address verification as `<code>` lines.** Rows people compare → **compact table**
   (No. · address · path) in a Rich Message; the safety note in an expandable quote.
   Analysis (4 facts) stays short lines — not a table.
6. **Taken address numbers** are explained after the tap. **Fix (10.3):** show them as
   disabled buttons; keep the "type another number" path with `force_reply` on the same keyboard.
7. **Name prompts** ("Send a name…") with a separate Cancel keyboard. **Fix (10.3):** inline
   keyboard (Cancel / suggestions) + `force_reply` in one message.
8. **Live price.** A shared ticker widget (`is_shared`, no queries, `cache_time` 10) re-sent with
   `sendSharedWidget` replaces repeated price lines.
9. **Copy and time.** `copy_text` button for the TXID/address; `date_time` entity for the
   transaction time; explorer as a URL button (already linked in text).

## SDK note

aiogram 3.31.0 implements Bot API 10.3: `disabled`, `force_reply`, `stopped_message_generation`
work natively. Widgets (10.4) need `examples/python/sdk_aiogram/adapter.py` — without it
`widget_query` is dropped. This bot's widgets need no queries (state is pushed), so only the
`SendWidget` method class is required; `editMessageWidgetData` likewise.

## Before → after (one screen)

```
before  <b>💼 My wallets</b>                    [💼 My wallets] uses a tgmacicons icon,
        Every address you track. Choose…        [✏️ Rename] an animated Unigram one,
                                                [← Back] a Balticbookworms one
after   <b><tg-emoji 💼 tgmacicons> My wallets</b>   all buttons from one family;
        Total: 7 · Page 1/2                          Back label-only; no animated icon
```
