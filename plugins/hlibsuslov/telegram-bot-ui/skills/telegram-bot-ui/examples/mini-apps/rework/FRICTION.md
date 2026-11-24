# Friction log: reworking `tests/fixtures/miniapp_rework/before` with the skill only

Task (user, in Russian): rebuild the gym-booking Mini App in "normal classic Telegram design, like Telegram
itself", keeping the class booking and payment logic. Route followed: `SKILL.md` → `references/mini-apps/README.md`
→ `orchestration.md` §3, then the files §3 and the README route to (anti-slop, design-system, layout-rules,
screen-patterns, telegram-elements, payments, telegram-design-guidelines), the kit and the `catalog` example.

## Results

| Check | Before | After |
|---|---|---|
| `miniapp_lint.py` | 8 errors, 71 warnings (exit 1) | `--strict`: 0 errors, 0 warnings (exit 0) |
| `miniapp_layout.py review` (screens described by me, `review/*.json`) | 15 findings (classes 5, trainers 4, plans 6) | 0 findings on 4 screens |
| `preview_miniapp.py --check` | — | 0 warnings |
| Stand `--serve 8795` + curl | — | stand 200; `/app/rework/index.html`, `dist/*.js`, `_kit/tma.css`, `icons.svg` 200; `POST /api/checkout` 501 |
| `node build.mjs`, `node --check dist/app.js` | — | built, syntax OK |
| `pytest tests/test_mini_apps_*.py` (unchanged files) | — | 75 passed |

Evidence level: static lint, self-described layout review, the stand serves the files. Nothing was rendered
(no browser), no payment path ran end to end (no server), no device.

## Friction points

1. **No rework walkthrough exists; the fixture points to a missing file.** `tests/fixtures/miniapp_rework/before/index.html:13`
   says the app is "the starting point of the rework walkthrough (references/mini-apps/rework.md)". That file
   does not exist; `orchestration.md` §3 is 8 one-line steps. Needed: one worked before → after (which
   defect maps to which kit primitive, what to do with each contract). Did: derived it from §3, design-system
   §9.5, payments.md and the `catalog` example. **Major.**

2. **"Contracts stay frozen" contradicts what the payment rules demand.** `orchestration.md` §3 (last line)
   freezes API routes; but `payments.md` §2 and lint MA26 require a different request body (ids only, no
   `price`, no `user`), `Authorization: tma <initData>`, a response with `order_id`, and a new route
   `GET /orders/<id>` the app never had. The skill does not say how to change a contract in a Mini App
   rework (the bot side has "update every handler in the same change"; nothing for the app/server pair).
   Did: kept the route `/api/checkout`, changed the body to `{classId}` / `{planId}`, expected
   `{order_id, link}`, added `GET /api/orders/<id>`, and wrote it in the `app.ts` header. A server change is
   required and is not part of this folder. **Major.**

3. **`miniapp_layout.py review` only checks what the agent already decided to write down.** `layout-rules.md` §11 /
   `scripts/miniapp_layout.py`: the input JSON has no documented schema (four `example` outputs; keys like
   `unavailable`, `ribbon`, `main_list`, `states.skeleton`, `price.figures`, `form.labels` exist only in
   the source), and it does not validate it: a file with `"primary_action": "main-buton"` and an unknown key
   `foo` gave 1 unrelated finding and exit 0. Rules it cannot see unless you describe them: hover-only
   content, a class card with an image (entity says "no image, time leads"), only 1 feature per plan (rule
   says 3-5; only `> 6` is flagged). My four "after" files returned 0 findings, which proves nothing beyond
   my own description. Needed: a schema (`--schema` or a reference table) and rejection of unknown keys
   and values. **Major.**

4. **The lint misses most of what makes this app "web-like".** `scripts/miniapp_lint.py` has no rule for:
   the own sticky header bar (only a back button with class `back-btn` is caught), the hamburger + drawer,
   cross-hue gradient backgrounds and glows (`box-shadow 0 0 40px` purple), uppercase tracked 9 px labels
   (only the size is caught), a corner ribbon, a 3-column grid on a phone, slop copy ("Unleash Your
   Potential!", "+340% progress!!", "champ"), `innerHTML` built from data, and — the security one —
   **sending `initDataUnsafe.user` from the client as the identity** (`app.js:34`); MA02 only looks at
   server files. Anti-slop §2 and §4 list most of these as tells. Consequence: `--strict` went clean on my
   first build; it would also have been clean for a rework that kept the drawer and the hero. **Major.**

5. **The payment flow the skill prescribes cannot be previewed with the skill's tools.** `payments.md` §8 says
   "Preview each status (`preview_miniapp.py`, `invoice=` parameter)", but an app that follows §2 must first
   get the link from its server: the stand answers `POST /api/checkout` with 501, and `examples/mini-apps/server`
   only verifies `initData` (no checkout or orders route). No example calls `tma.pay` or `tma.watchOrder`.
   Did: wrote the flow from `payments.md` §2-3 and the kit's signatures; it never ran. Needed: a stand
   option or example server that mocks `checkout` + `orders/<id>`, or an example that uses `pay`/`watchOrder`.
   **Major.**

6. **No rule for an existing TON payment option.** The before-app sells a "Wallet" plan for "1.5 TON — Pay
   with Toncoin". `payments.md` §1: digital goods only in Stars, TON is not in `Telegram.WebApp`, out of
   scope; `telegram-elements.md` T2 only says how to name grams. The user asked to keep the payment logic;
   the skill does not say whether to drop, keep as an external TON Connect path, or hand over to the bot.
   Did: dropped the TON plan (it had no handler in `app.js`) and logged it here. **Major.**

7. **Baseline counts under-report.** `miniapp_lint.py` lines ~262-270 report MA28 once per file (`search`, then
   `break` for JS literals), MA29 and MA14 once per file. Not reported: `250 XTR` / `450 XTR` / `1.5 TON` /
   `Pay with Toncoin` (`index.html:48-50`), `${c.price} XTR` in the multi-line template (`app.js:15`, the
   literal regex excludes newlines). §3 step 8 asks for before/after counts; the "before" number is lower
   than the real defect count, and a partial fix re-surfaces the next occurrence. **Minor.**

8. **`miniapp_layout.py show class` prints the wrong markup.** Text: "image none in rows (time leads)", slots
   "time, title, trainer, spots left". Markup: the generic trainer row with `<img class="tma-avatar">` and
   "€30 ★ 4.9". The kit has `.tma-cell__time` for exactly this (tma.css ~line 688), but no reference, data
   file or `show` output mentions it; found by reading the CSS. **Minor.**

9. **L02 contradicts the `class` entity.** `layout-rules.md` §12 L02 fix: "video and class 16:9"; §2 and
   `entities`: group class has no image. Did: no image (the entity wins). **Minor.**

10. **Kit has no disabled row.** L08 wants full classes "dimmed, with the reason in text"; the kit dims
    `.tma-tile[aria-disabled]` only. Did: 1 own CSS rule in `index.html` for `.tma-cell[aria-disabled]`.
    **Minor.**

11. **MainButton hides the tab bar; §3 does not route to where that is said.** `tma.css`:
    `:root[data-tma-main-button="visible"] .tma-tabbar { display: none }`; documented in `components.md` line 46,
    which §3 never sends you to. It decides the structure: Membership as a tab cannot carry
    "Subscribe · ⭐ N / month" (`screen-patterns.md` gym row) without trapping the user. Did: plan rows on the
    tab root, Subscribe on a level-2 plan screen. **Minor.**

12. **§3's defect ranking omits the payment and trust-mark errors.** `orchestration.md` §3 step 3 ranks
    "security (MA01-MA02) → native → states → theme → slop"; the before-app's errors are MA03, MA04, MA25
    (card fields) and MA29 (fake verified badge), which have no place in that order. Did: treated MA25, MA26,
    MA27, MA29 and the `initDataUnsafe` identity as security, first. **Minor.**

13. **§3 does not route a rework to payments.md or telegram-elements.md.** Both were essential here (card
    form, XTR labels, `paid` unlock, verified ticks). Found them via README's route table and the lint
    messages. **Minor.**

14. **Wrong recipe for the gym pattern.** `screen-patterns.md` §2 gym: "Recipes 94, 97"; 97 is
    `97-mini-app-game-fullscreen.md`. **Minor.**

15. **Icon count disagrees.** README: 83; `orchestration.md` §4 and `design-system.md` §10: 81; `icons.svg`
    and `icons.json`: 83. **Minor.**

16. **`design-system.md` §10 import path breaks the build.** The snippet imports `'./_kit/tma.ts'`; `build.mjs`
    rewrites only `../_kit/…` imports. Copying the snippet gives a `dist/app.js` that imports a `.ts` file.
    Did: followed the examples (`'../_kit/tma.ts'`). **Minor.**

17. **Where the stand serves the app is undocumented.** `preview_miniapp.py --help` and the references say
    `--serve PORT`; the app is at `/app/<folder>/index.html` (found in the stand's HTML after `/rework/…` gave
    404). Matters for curl-only checks. **Minor.**

18. **"Classic Telegram" is not a phrase the style table knows.** `design-system.md` §9.2 maps "like Telegram",
    "native" → `native`; that matched. But the kit's look is iOS 27 (floating glass capsule tab bar, 26 px
    inset groups), which is not what "classic Telegram" means to an Android or Desktop user; §6 keeps glass on
    Android too. No guidance on whether "classic" should mean flatter Android/Desktop-like chrome. Did:
    `native` preset, no attribute. **Minor.**

19. **States everywhere vs local data.** `orchestration.md` §2/§3 and design-system §8: skeletons for every
    load. The before-app's lists are constants; the skill does not say what to do when nothing loads. Did:
    empty state for a trainer with no classes, error/pending/timeout states on payment, no skeletons. **Minor.**

20. **Terms footnote needs a URL nobody has.** `payments.md` §4: "By paying you accept the Terms" with
    `openLink` to `/terms`. The app has no terms URL. Did: a footnote without the link. **Minor.**

21. **Kit gaps used by the references.** No DOM helper (every example re-declares `h()`; copied from `catalog`);
    no `requestWriteAccess` in `WebAppLike` although `payments.md` §2.9 recommends it before paying. Did:
    copied `h()`; skipped `requestWriteAccess`. **Minor.**

## Defects of the before-app the tools did not detect

Lint and layout review both silent (or only caught via my own JSON description):
- Own sticky header bar with logo and shadow (`.topbar`); only the `back-btn` was flagged.
- Hamburger button and side drawer (anti-slop §2 lists it; no rule).
- Cross-hue gradient hero and CTA background, purple glows (`box-shadow: 0 0 40px …`).
- Uppercase, letter-spaced labels (only the 9 px size was flagged).
- Corner ribbon "POPULAR" (layout review catches it only if I write `"ribbon": true`).
- 3-column class grid at phone width; side-by-side plans (layout review only if described).
- Class time, trainer and spots hidden behind hover: MA21 caught the hover; nothing said the time must lead.
- Sold-out class (0 spots) selectable and bookable; no availability shown without hover.
- Fake metrics "+340% progress!!", "1,250 XTR balance" with no source; greeting copy, exclamation marks.
- `initDataUnsafe.user` sent to the server as identity; no `Authorization` header; no `Content-Type`.
- `fetch` without `res.ok` or error handling; invoice statuses other than `paid` ignored.
- `innerHTML` built from data (`app.js:11-19`).
- Plans have no purchase action at all (dead end); card form fields not wired to anything.
- Remaining XTR / TON / Toncoin labels after the first one (friction 7).
- `document.body.classList.add('member')` as the result of a payment (MA27 caught the `paid` check only).

## Design decisions I had to invent

- Tabs: Classes · Trainers · Membership · Profile (gym pattern says Trainers · Classes · My bookings
  (· Membership)); no "My bookings" because the app has no bookings API. Classes first, as the old Home.
- Dropped the Home hero and its three stats (fake or sourceless numbers); dropped the Stars "balance".
- Profile instead of SettingsButton for the notifications switch (reachable in a plain browser too).
- Trainer photos: initials in `.tma-avatar`, not `avatar.svg` (its literal purple fill ignores the theme).
  `class.svg` dropped (class rows have no image).
- Trainer detail = their classes today (there is no portrait, bio or schedule data for L11's order).
- Full class: MainButton "Class is full", inactive, with the reason in the content (pattern wants
  "Join the waitlist"; no waitlist API).
- Removed the extra `confirm()` before paying: Telegram's invoice sheet is the confirmation.
- Plans purchasable through the same `/api/checkout` with `{planId}` (new contract; the old app had none).
- Plan "Pro" marked "Most chosen" in text (was a POPULAR ribbon); one feature per plan kept, none invented.
- CloudStorage keys kept as `lastClass` and `notif`; `lastClass` is still only written, as before.
- `startapp` routes `tab-<name>` and `class-<id>` added (the old app had none).
- Copy: all user-visible strings rewritten (no greetings, exclamation marks or emoji).

## Status after the fixes (same branch, after this log)

| # | Fix |
|---|---|
| 1 | `references/mini-apps/rework.md`: the loop, stages, translation table, framework bridge, acceptance score, report; `orchestration.md` §3 routes to it |
| 2 | rework.md §1: stage 1 findings change the contract; app and server change together, the old body is accepted but its price and user are ignored, the report lists every changed route |
| 3 | `miniapp_layout.py schema`; `review` rejects unknown keys and values with exit 2; rework.md §1 step 3 says to describe every key; this folder's `review/*.json` validate and are tested |
| 4 | lint: own top bar (MA19), drawer (MA30), hype copy (MA31), glow and hover scale (MA32), the client's user object sent to the server (MA33, error), tracked caps (MA34); `miniapp_rework.py plan` reports stat cards, nested cards, ribbons, price pills, sticky headers, carousels, modals, toasts |
| 5 | stand `--api mock.json` with the order status following the Invoice control; `rework/mock-api.json`; this app runs checkout, invoice and order status end to end in the stand (paid and failed walked in the browser) |
| 6 | rework.md §1 and §3: a digital good priced in TON becomes Stars; a real TON flow moves to the bot's wallet features |
| 7 | MA28 reports every occurrence (multi-line template literals, `+ ' XTR'`); the baseline is now 9 errors, 89 warnings |
| 8 | `miniapp_layout.py show class` prints the time-led row with `.tma-cell__time`; avatar and thumbnail rows are distinct |
| 9 | L02 no longer lists classes as 16:9 |
| 10 | kit: `.tma-cell[aria-disabled="true"]` dims a row, the chevron stays; the local style here was removed |
| 11 | rework.md §1 step 3: no primary action on a root tab; Subscribe goes on a level-2 screen |
| 12, 13 | rework.md §2 stages: security and payments first, Telegram's values and trust marks third |
| 14 | gym pattern: recipes 94, 96 and this example |
| 15 | icon count 83 everywhere |
| 16 | design-system §10 imports `../_kit/tma.ts` |
| 17 | `preview_miniapp.py` docstring and rework.md: the app lives at `/app/<folder>/index.html` |
| 18 | design-system §9.2: "classic Telegram" = `native`; the platform decides the chrome |
| 19 | rework.md §2: constant data needs no skeleton; empty states and pending / error / success for server actions still do |
| 20 | rework.md §8: missing inputs (terms URL, support handle, waitlist API) go in the report |
| 21 | kit `writeAccess()` (allows_write_to_pm, then `requestWriteAccess` from 6.9), used here before paying. Open: no shared DOM helper; each example keeps its own `h()` |
