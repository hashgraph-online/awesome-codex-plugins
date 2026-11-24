# Telegram's own elements: Stars, grams, gifts, marks

Telegram has a visual vocabulary users already know from the app itself: the Stars sign, gram amounts, gift
cards with their backdrops, rarity, Premium, verification. A Mini App (and a bot's messages) should show these
the way Telegram does, from the data the API returns, and must never fake the ones that signal trust.
Verified against Bot API 10.5 on 2026-11-24. Labels: **[API]** the Bot API page, **[Official]**
core.telegram.org prose, **[Heuristic]** this skill's rendering decision, **[News]** secondary reporting.

Kit: `examples/mini-apps/_kit/tg-values.ts` (formatting, colours) and the "Telegram's own values" block of
`_kit/tma.css`; all of it is shown in the gallery's **Telegram** group. Catalogue: `data/mini-apps/components.json`,
group `telegram`. Payments flow: [payments.md](payments.md); bot side of gifts: [../gifts-and-stories.md](../gifts-and-stories.md);
wallet: [../wallet-and-ton.md](../wallet-and-ton.md).

## Index

| # | Element | Data | Kit | Rule in one line |
|---|---|---|---|---|
| T1 | Stars amount | `XTR`, integer `amount`; `StarAmount` with `nanostar_amount` | `.tma-amount.is-stars` + `.tma-star`, `formatStars`, `starsText` | gold sign before a whole number; never "XTR" |
| T2 | Gram amount | currency `"TON"`, nanograms as a decimal string | `.tma-amount` + `.tma-amount__unit`, `formatGrams`, `gramsText` | exact from nanograms; ticker GRAM after |
| T3 | Fiat amount | ISO currency, minor units | `Intl.NumberFormat` | the provider's currency, the server's number |
| T4 | Gift card | `Gift`: `sticker`, `star_count`, `background`, limits, `is_premium` | `.tma-gifts`, `.tma-gift`, `giftVars`, `limitedLeft` | the gift's own colours and art |
| T5 | Unique gift | `UniqueGift`: model, symbol, backdrop, `number`, rarity | `.tma-gift.is-unique`, `.tma-rarity`, `rarityPercent`, `rarityTier` | "Name #1234", rarity as % |
| T6 | Paid content | `PaidMediaInfo.star_count` | pattern | in chats Telegram draws the lock |
| T7 | Telegram Premium | `initDataUnsafe.user.is_premium` | pattern | say it in words |
| T8 | Verified, Scam, Fake | Telegram, `verifyUser` / `verifyChat` | never | never drawn by the app (lint MA29) |
| T9 | Emoji status | `setEmojiStatus` (8.0) | native | Telegram confirms and shows it |
| T10 | Rating level | `ChatFullInfo.rating` (9.3) | pattern | "Level 5" + progress |
| T11 | Boosts | `t.me/boost/<channel>` | pattern, icon `bolt` | open Telegram's screen |
| T12 | TON wallet card | `ChatFullInfo.ton_wallet_card` (10.4) | native | amounts with `formatGrams` |

## T1. Telegram Stars

- **What Telegram shows.** A gold five-pointed star before the number: `⭐ 250`. Prices are whole Stars; the
  invoice currency is `XTR` **[API]/[Official]**. Balances can carry a fraction: `StarAmount.amount` plus
  `nanostar_amount` (1/10⁹ of a Star, 9.0) **[API]**.
- **Render.**
  - In markup: `<span class="tma-amount is-stars"><svg class="tma-star" aria-hidden="true"><use href="icons.svg#i-stars-gold"/></svg>250<span class="tma-sr-only"> Stars</span></span>`.
    `i-stars-gold` is the kit's own drawing with Telegram's shading (gold gradient, darker edge, a light
    facet); `i-stars` is the flat version for small sizes **[Heuristic]**.
  - **The original artwork.** Telegram's Stars glyph is published in Telegram Web A
    (github.com/Ajaxy/telegram-tt, `src/assets/icons/star/GoldStar.svg`), licensed **GPL-3.0**. It is not
    copied into this skill (MIT). An app owner who accepts GPL-3.0 for that file fetches it with
    `py -3 scripts/fetch_telegram_star.py --out <app>/assets --accept-gpl` (pinned commit, SHA-256 checked,
    a licence notice written next to it) and uses `<img class="tma-star" src="assets/GoldStar.svg" alt="">`.
  - **The price pill** (gifts, paid items, "Unlock" offers), as Telegram's own clients draw it: a translucent
    gold pill (gold at about 13 %), the gold star, the amount in gold, small four-point sparkles drifting out
    of it. `.tma-stars-pill` with `.tma-sparkles` (ten `<i>`); the sparkles stop and stay at half opacity
    under `prefers-reduced-motion` and on weak Android (`data-tma-perf="low"`), as Telegram does with
    animations off. The amount uses `--tma-star-text` (4.5:1 on the pill in both themes). The effect is the
    kit's own CSS; Telegram Web A draws the same idea with "✦" characters, which this skill does not use
    (no emoji, MA13).
  - Never the ⭐ character in markup (headings, rows, prices, footnotes): lint MA13.
  - Where only text fits (MainButton, popups, bot messages): `starsText(250)` → `⭐ 250`; a period:
    `⭐ 250 / month` **[Heuristic]**. The ⭐ before an amount is the one emoji the lint accepts in labels (MA13).
  - A balance: `formatStarBalance(amount, nanostars)` shows at most two decimals and truncates, so it never
    shows more than the user has **[Heuristic]**.
  - In prose: "1 Star", "250 Stars", with a capital S, as in "Telegram Stars" **[Heuristic]**.
- **Never.** "XTR" in front of users; "250 ⭐" or "250 stars ⭐"; a fiat price converted to Stars at a fixed rate
  (prices are set in Stars; [payments.md](payments.md)); the gold colour on text, buttons or a whole theme. The
  gold is the sign's colour only.
- **Rule of goods.** Digital goods and services are paid only in Stars **[Official]**; physical goods go
  through a provider (T3).

## T2. Grams (formerly Toncoin)

- **The name.** The TON blockchain's coin was renamed from Toncoin (TON) to **Gram (GRAM)**, effective
  2026-06-15; the network is still called TON **[News]**: crypto.news, AMBCrypto and The Block, June 2026.
  Check ton.org before relying on details. The Bot API already speaks of "TON grams" and
  "nanograms", and keeps the currency code `"TON"` in `SuggestedPostPrice.currency` and
  `UniqueGiftInfo.last_resale_currency` **[API]**.
- **Data.** Amounts are decimal strings in nanograms (10⁻⁹): `TonWalletCard.amount`, `TonWalletTransfer.amount`
  (negative for outgoing), or integers in nanograms (`SuggestedPostPrice.amount`, 10000000-100000000000)
  **[API]**. Never parse them as floats.
- **Render.**
  - `formatGrams(nano)` uses BigInt, truncates to 4 decimals by default and drops trailing zeros: `12.5034`,
    `-0.0412`. `signed: true` gives `+2.5` for incoming transfers.
  - The unit after the number in `.tma-amount__unit`: `12.5 GRAM` **[Heuristic]**. Plain text: `gramsText()`.
  - Input: `toNanograms("1.25")` → `1250000000n`, or null for anything that is not a plain decimal with at
    most 9 places.
  - One line in help or onboarding, "Grams (formerly Toncoin)", where users may still know the old name
    **[Heuristic]**.
- **Never.** "Toncoin" or "12.5 TON" as a new label (lint MA28); a self-drawn coin or diamond logo: use the
  official mark from the TON or Gram brand page, or the text ticker; rounding a balance up.

## T3. Fiat

Prices for physical goods come from the server in minor units and go through a payment provider
([payments.md](payments.md) §1). Format with `Intl.NumberFormat(locale, {style: 'currency', currency})`; the
number of decimals per currency is the `exp` field of https://core.telegram.org/bots/payments/currencies.json
(`LabeledPrice.amount` is in the smallest units) **[API]**. Never mix currencies
in one invoice; never show a converted Stars amount beside a fiat price as if it were the price.

## T4. Gift cards (regular gifts)

- **Data.** `Gift`: `sticker` (the gift's art), `star_count`, `upgrade_star_count`, `is_premium`
  (Premium-only), `total_count` / `remaining_count` (limited), `background` with `center_color`, `edge_color`,
  `text_color` as RGB integers (9.3) **[API]**.
- **Render.** `.tma-gifts` grid of three, each `.tma-gift`: art (`.tma-gift__art`, the sticker converted to
  an image by your server), title, price pill `.tma-gift__price` with the Stars sign, optional
  `.tma-gift__flag` ("Premium") and `.tma-limited` counter (`limitedLeft()` → "142 of 5,000 left", "Sold out").
  Colours: `giftVars(gift.background)` sets `--gift-center`, `--gift-edge`, `--gift-text`; the card is a
  radial gradient from centre to edge, the text in `text_color`. Without `background` the card falls back to
  the surface with a hairline **[Heuristic]**.
- The gift's colours are Telegram's: they stay the same in light and dark. Do not re-tint them to the theme.

## T5. Unique (collectible) gifts

- **Data.** `UniqueGift`: `base_name` and `number` ("Plant #1042"), `model` (sticker, `rarity_per_mille`, and
  `rarity` uncommon / rare / epic / legendary for crafted models, 9.4), `symbol` (sticker,
  `rarity_per_mille`), `backdrop` (`center_color`, `edge_color`, `symbol_color`, `text_color`), `is_burned`,
  `is_from_blockchain`; the link is `https://t.me/nft/<name>` **[API]**.
- **Render.**
  - `.tma-gift.is-unique` (square), `.is-lg` for a detail screen: `giftVars(backdrop.colors)`;
    `.tma-gift__pattern` repeats the symbol in `symbol_color` through a mask. Set
    `--gift-symbol-image: url("<absolute URL>")`: a relative URL resolves against the stylesheet.
  - The model art in the centre; `.tma-gift__title` "Name #number" in `text_color`.
  - Attributes as a key-value list: Model / Backdrop / Symbol with a `.tma-rarity` chip from
    `rarityPercent(per_mille)` ("1.2%"). A crafted model shows `rarityTier()` ("Rare") instead: its
    `rarity_per_mille` is 0.
  - States in words: "Burned" for `is_burned`; "On the TON blockchain, can't be resold in Telegram" for
    `is_from_blockchain`.
- **Name colours.** A unique gift can colour its owner's name (`UniqueGiftColors`, 9.3): `giftNameColor(c,
  scheme)` picks the light or dark main colour. Use it only for that owner's name.
- **Never.** Invent tier colours, rarity percentages or numbers; draw a "collectible" frame on items that are
  not Telegram gifts.

## T6. Paid content

In chats Telegram draws paid media itself: a blurred preview and an unlock button with the Stars price
(`sendPaidMedia`, `PaidMediaInfo.star_count`) **[API]**. Inside a Mini App, sell content through an invoice
([payments.md](payments.md)): a preview plus "Unlock · ⭐ 50" in the MainButton. Do not copy the chat lock
onto content that is not sold for Stars.

## T7. Telegram Premium

`initDataUnsafe.user.is_premium` (6.2) says whether the user has Premium **[Official]** (unverified until the server
checks `initData`; [security.md](security.md)). Say it in words: "Telegram Premium: two extra saved recipes".
Never draw Telegram's Premium badge next to a name, and never name your own tier "Premium" with a star badge
that can pass for Telegram's **[Heuristic]**.

## T8. Verified, Scam and Fake marks

The verified check, third-party verification by an organisation (`verifyUser`, `verifyChat`, 8.2; formatted
descriptions since 10.4), and the Scam and Fake labels are drawn by Telegram on profiles and chat headers
**[API]**. A Mini App never draws a check mark, shield or "Verified" label next to a person, bot, seller or
channel: users read it as Telegram's word (lint MA29, error). Own trust signals stay in text: "Seller since
2024", "312 orders", a rating.

## T9. Emoji status

`WebApp.setEmojiStatus(custom_emoji_id, {duration})` (8.0) asks the user in a native dialog; Telegram shows the
status. `requestEmojiStatusAccess` (8.0) lets the app set it later **[Official]**. Show the result as text ("Your
status is set for 24 hours"); render the custom emoji only from its sticker file, fetched by the bot.

## T10. User rating level

`ChatFullInfo.rating` (9.3): `level`, `rating`, `current_level_rating`, `next_level_rating`, a reliability
score from Star spendings **[API]**. The bot reads it with `getChat`; the app shows "Level 5" and a
`.tma-progress` towards the next level. Do not call your own loyalty level by Telegram's name.

## T11. Boosts

A boost row: icon `bolt`, "Boost the club channel", `openTelegramLink('https://t.me/boost/<channel>')`.
Telegram shows the boost screen and the count. Boost counts the bot reads (`getUserChatBoosts`) are numbers in
text **[API]/[Heuristic]**.

## T12. TON wallet card

`ChatFullInfo.ton_wallet_card` (10.4): address, `amount` in nanograms, stickers placed by `AreaPosition`, and a
background from one sticker NFT's colours **[API]**. Telegram draws it on the profile. A Mini App shows wallet
data only after the user shares it (widgets, [../wallet-and-ton.md](../wallet-and-ton.md)), with `formatGrams`.

## Bot messages

The same text rules hold in a bot's messages: `⭐ 250` for Stars, `12.5 GRAM` for grams, never `XTR`; a
receipt names the order and the amount ([payments.md](payments.md)). Custom emoji in messages follow
[../custom-emoji.md](../custom-emoji.md).

## Checklist

- [ ] Every amount comes from the server or the API, formatted by the kit; no floats for grams.
- [ ] Stars: gold sign before a whole number; plain `⭐ 250` where no markup; no "XTR".
- [ ] Grams: GRAM after the number; "formerly Toncoin" once where it helps; no drawn logo.
- [ ] Gifts: art and colours from the API; rarity as %, crafted tier in words; "Name #number".
- [ ] No check marks, Premium badges or Scam-like labels drawn by the app.
- [ ] Lint: `py -3 scripts/miniapp_lint.py <app> --strict` (MA13, MA28, MA29).
