# mini-app: a Mini App, from the decision to the release

**When:** build or restyle a Mini App, `Telegram.WebApp`, `initData`, where the photo, title
and price go, a Figma file to build from, payments or haptics inside the app.

## Read

One route, no hops: `references/mini-apps/orchestration.md` §1 names the file for the request
(decide, launch, API, security, payments, Telegram elements, anatomy, device, accessibility,
forms, materials, Figma, design system, components, layout, rework, anti-slop, testing), §2 is
the order of work to create an app, §3 to rework one. The bot side of the launch and of sent
data: `references/mini-apps-bridge.md`. Recipes 90-99 are the starting points.

## Steps

1. Decide and say why (`references/mini-apps/decide.md`): Mini App, widget or keyboard.
2. Gate every `Telegram.WebApp` call by version: `tgui.py webapp show <Name>`, `webapp gates`.
3. Follow §2 or §3; layout and style with `tgui.py miniapp layout review` and
   `tgui.py miniapp style ...`; a rework starts with `tgui.py miniapp rework plan <app>`.
4. Validate `initData` on the server before trusting any user field
   (`references/mini-apps/security.md`).
5. `tgui.py miniapp lint <app>` and `tgui.py miniapp preview <app>` (`--build` runs the app's own `build.mjs`: trusted projects only; a mock client: it proves
   nothing about real Telegram clients).

## Without scripts

Look names up in the Telegram.WebApp catalog under `data/` and apply the lint rules from
`references/mini-apps/performance-and-testing.md` by hand.

## Done

The floor rules plus version gates, a server-side `initData` check, lint clean, evidence level.

## Next

The bot side (`improve` the launch button and messages) or `build` for payments in the bot.
