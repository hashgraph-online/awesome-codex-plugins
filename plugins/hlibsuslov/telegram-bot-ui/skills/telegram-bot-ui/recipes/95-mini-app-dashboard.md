# 95 — Dashboard and portfolio Mini App (dark-fintech style)

Product recipe (no registry row). Verified 2026-11-23. Style: `references/mini-apps/design-system.md` §9
(`fintech`); layout: `references/mini-apps/layout-rules.md` §10; pattern:
`references/mini-apps/screen-patterns.md` §5. Tags: **[API]**, **[official]**, **[heuristic]**.

1. **Request and visible result.** “Show customers their points like a banking app: balance, history,
   bonuses.” — One large balance with its change and a hide toggle, four quick actions, one dismissible
   promo, quiet balance rows, a bonus tab with a hero in the brand colour and a live countdown, an asset
   screen with a one-line chart, a period control, “Redeem” in the MainButton and “Send” as the
   SecondaryButton, and a one-time onboarding sheet.
2. **Why these features.** One figure per screen, fraction and unit smaller in hint colour, direction with
   a sign and an arrow, not colour alone **[heuristic]**; the header follows the hero colour on the bonus tab
   (`setHeaderColor`) **[official]**; the countdown pauses on `deactivated` (8.0) **[official]**; promo and
   onboarding are remembered in `CloudStorage` (6.9) **[official]**; MainButton + SecondaryButton (7.10) for
   the two actions of an asset **[official]**; skeletons first, “—” on error, never 0.00 **[heuristic]**.
3. **Requirements.** SecondaryButton 7.10 (older clients: the kit returns `false`, show the action in the
   content); `activated`/`deactivated` 8.0; any theme (colours are the user's).
4. **Payload.** `examples/payloads/r95-dashboard-portfolio.json`: the bot's alert with
   `startapp=asset-points` (the app opens that asset).
5. **Code.** App: `examples/mini-apps/portfolio/index.html` + `app.ts` (`<html data-tma-style="fintech">`,
   `.tma-figure`, `.tma-delta`, `.tma-actions`, `.tma-banner`, `.tma-hero`, `.tma-chart`, `.tma-segmented`,
   onboarding `.tma-sheet`). Bot: `r90_99_mini_apps.py::r95`, start-param routes checked by an allowlist.
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     [*] --> onboarding: first run (CloudStorage onboarded != 1)
     onboarding --> home: Continue
     home --> asset: tap a balance (BackButton, MainButton + SecondaryButton)
     asset --> home: Back
     home --> bonus: tab (header = brand, countdown runs)
     bonus --> home: tab (countdown stops)
   ```
7. **Result.** Mock preview: `py -3 scripts/preview_miniapp.py examples/mini-apps/portfolio --serve 8790`,
   both themes; switch the Style control to compare `fintech` with `native`.
8. **Typical mistake, limits, alternative.** Neon glows and gradient numbers; a chart on every card; red and
   green without signs; a countdown that keeps ticking in the background; ribbons on cards; a promo that
   comes back after closing. Alternative: a widget for one live number in a private chat (recipe 50).
9. **Run and verify.** `py -3 scripts/miniapp_lint.py examples/mini-apps --strict` ·
   `py -3 scripts/miniapp_style.py show fintech` · `py -3 examples/python/recipes/r90_99_mini_apps.py r95`.
   Evidence: lint, mock preview; no real device.
10. **Adapt.** Keep: one figure, one moment, quiet rows, the header following the top colour. Replace: the
    assets with your data API; the brand colour through a checked profile (`miniapp_style.py check`).
    Related: recipes 07 (wallet), 86 (loyalty points).
