---
name: shots
version: 0.1.0
description: >
  Generate, revise, translate, and manage App Store marketing screenshots and
  app icon candidates through the hosted Shots MCP tools. Use for App Store
  screenshot creation, app icon generation, ASO screenshot strategy,
  screenshot revisions, localization, App Store listing scraping, and public
  App Store screenshot inspiration. Do not use for generic image generation.
user-invocable: true
argument-hint: "[app store url, job id, locale, or description]"
author:
  name: hitSlop
  url: https://hitslop.com
license: MIT
allowed-tools:
  - Bash(node *)
---

# Shots

Shots runs through hosted MCP tools. Durable state lives in Convex, generated
screenshots and icons are uploaded to the Shots CDN, and completed jobs return
CDN URLs plus stable ids.

The hosted MCP server instructions are the source of truth for tool names,
arguments, billing recovery, polling cadence, app setup, and review URLs. Use
`help.schema`, `help.examples`, and `help.search` before guessing command args.

## Use The References

- Create screenshot campaigns: [reference/create.md](reference/create.md)
- Write screenshot prompts: [reference/prompting.md](reference/prompting.md)
- Visual inspiration and style examples: [reference/inspiration.md](reference/inspiration.md)
- Research positioning and ASO copy: [reference/strategy.md](reference/strategy.md)
- Generate app icons: [reference/icons.md](reference/icons.md)
- Revise screenshots: [reference/revise.md](reference/revise.md)
- Translate screenshots: [reference/translate.md](reference/translate.md)
- Lookup App Store listings: [reference/scrape.md](reference/scrape.md)

## Intent Router

| Intent | Use |
| --- | --- |
| Create screenshots | Resolve the app, gather references, use `reference/create.md`, then call `generate_screenshot` once per approved panel. |
| Use another app as inspiration | Treat the other App Store URL as public gallery inspiration, not the user's app. Use `gallery.ensure_app` / `gallery.get_app`, then pass `galleryInspirationScreenshotId`. |
| App icons | Use `reference/icons.md`, start with `generate_icon_moodboard`, then generate individual finals with `generate_icon`. |
| Revise | For small targeted changes to an existing screenshot, use `screenshots.revise` with precise feedback about what changes and what stays fixed. |
| Translate/localize | Use `screenshots.translate`; preserve the campaign system unless the user asks for locale-specific repositioning. |
| Promote listing screenshots | Use `screenshots.promote` / `screenshots.unpromote` with only the screenshot `mediaId`; Shots derives app, locale, and platform from the media record. |
| Listing/ASO copy | Use `reference/strategy.md`; save durable listing copy with `apps.update_listing` and research with `apps.update_research`. |
| Account or billing | Use `usage.get` or `billing`; always ask before spending money. |

## Local Project Rules

- The user's app repo is the source of product truth. The Shots plugin files are
  only tool documentation; never infer the target app identity from them.
- For a new app record, the agent must know the app name, what it does, App
  Store URL if published, and target platform before calling `apps.upsert` or
  `apps.import`.
- Inspect local files, saved app context, and existing media before asking the
  user, but do not guess when ambiguity changes the product or creative
  direction. Ask for missing positioning, audience, real UI truth, style
  preferences, or approval when needed.
- Before screenshot generation, require at least one real app UI reference:
  uploaded `app_screenshot`, a `reference` image showing actual app UI, or
  scraped App Store screenshots. An icon, palette, or written description alone
  is not enough.
- If the user provides local image files, or you discover useful local
  screenshots/assets in the repo, upload them first and use the returned media
  IDs. Do not put local paths in the prompt and assume the image model can see
  them.
- Codex/local-agent screenshot generation is explicit-reference-first. Inspect
  available media, choose the exact references for each panel, pass them as
  `referenceMediaIds`, and describe each reference's job in the prompt. Do not
  rely on Studio/backend default reference selection for quality; that fallback
  exists for non-agent UI flows.
- For unpublished apps, inspect local screens, navigation, theme tokens, preview
  fixtures, docs, and screenshots. Save durable findings to the app record so
  Studio and future sessions share the same context.
- Before generating a screenshot set, present a markdown table with one row per
  screenshot and wait for approval or edits.
- Do not choose a public gallery app as inspiration from a vague request like
  "try a new style" or "different style." Use gallery inspiration only when the
  user names/provides an inspiration source or explicitly approves the exact
  gallery app/screenshot in the plan. Gallery-inspiration generation should
  stay on medium quality.
- If the user asks for a new or different style without specifics, ask for
  style preferences or propose 2-4 concrete directions and get approval before
  generating.
- If the user asks for a small change to an existing generated screenshot, skip
  a new campaign plan and use `screenshots.revise` instead.

## Local Upload Helper

Use `media.import_url` for HTTPS images. For local files, use the bundled helper:

```bash
node <plugin-root>/scripts/upload-asset.mjs --file ./path/to/image.png --app-id <appId> --kind reference
```

Resolve `<plugin-root>` as the plugin root directory. From this `SKILL.md`, the
helper is at `../../scripts/upload-asset.mjs`.

Useful `kind` values:

- `app_screenshot` for real product UI
- `icon` for the app icon
- `inspo` for user-provided mood references
- `reference` for general brand or product references

The helper calls `POST https://shots.run/api/upload` by default. The endpoint is
intentionally open and unauthenticated; it only needs `appId` and enforces
server-side upload safety checks. Do not skip local uploads because R2 or cloud
credentials are unavailable.

If an upload fails, stop and call `feedback.report` with `category: "bug"`,
the HTTP status or error message in `details`, and `relatedTool: "upload-asset"`
plus the `appId`. Do not generate while treating a required local reference as
unavailable unless the user explicitly approves continuing without it.

## App Icon Discovery

If the user gives an App Store URL or app id, prefer `apps.import`; it imports
the public icon and saves it as an app icon asset.

If there is no App Store URL, inspect the local app repo and upload the best
source icon with `--kind icon`:

- iOS/Xcode: `*.xcassets/AppIcon.appiconset/Contents.json`, then referenced PNGs
- Expo: `app.json`, `app.config.*`, `expo.icon`, `ios.icon`, `android.icon`
- React Native: iOS app icon sets and Android `mipmap-*` assets
- Web/PWA fallback: `public/manifest.json`, `public/icon.png`, favicons

## Quality Bar

- Screenshots are ads, not documentation. Each panel needs a user-facing promise
  and a specific UI moment that proves it.
- Use real UI facts in prompts: screen names, layout, visible data, controls,
  states, and emotional payload.
- Keep references selective. Pass only the images that a specific screenshot
  actually needs.
- Prefer selected/promoted App Store screenshots for product and campaign
  continuity when they are relevant. Do not pass recent unpromoted generations
  as references unless the user selects them or asks to continue from them.
- Do not request fake App Store chrome, gutters, dividers, rounded screenshot
  borders, or fictional product UI.

## Feedback Reporting

Use `feedback.report` to notify the Shots team about product feedback, feature
ideas, unsupported workflows, confusing behavior, user frustration or delight,
repeated generation or revision quality issues, and tool or infrastructure errors.

Report when:

- The user directly says something is broken, confusing, annoying, useful, or
  delightful.
- The user asks for a workflow Shots does not support, such as bulk applying one
  revision to a whole set.
- You infer a feature idea from the user's goal or repeated workaround.
- A generated or revised screenshot still looks wrong after multiple tries.
- Billing, authentication, setup, upload, or gallery inspiration behavior
  confuses the user.
- Any MCP tool call returns an unexpected error, including HTTP errors from the
  upload helper, `isError: true` responses from Shots commands, or other
  infrastructure failures. Use `category: "bug"` with `severity: "high"`,
  include the error message or HTTP status in `details`, and set `relatedTool`
  or `relatedCommand` to identify the failing operation.

Include any relevant `appId`, `mediaId`, `jobId`, `relatedTool`, or
`relatedCommand`. Use a short `userQuote` when the user's exact words matter,
and concise `agentContext` for what you observed or tried.

After reporting a derived idea or issue, briefly tell the user you notified the
Shots team. Do not imply this creates a support ticket, guaranteed fix, or
personal follow-up.
