# SeparateWeb Capture

Website screenshot, web page capture, and UI crop extraction for Codex.

SeparateWeb Capture is a Codex plugin that turns web pages into inspectable visual assets: full-page screenshots, grouped UI crops, and JSON manifests.

Use it when Codex needs real page evidence before implementing or reviewing UI.

## Install As A Codex Plugin

In Codex, open Plugins, choose Add marketplace, then use:

```text
Source:
https://github.com/AUN-PN/SeparateWeb.git

Git ref:
main

Sparse paths:
```

Leave `Sparse paths` empty.

The Codex marketplace metadata lives at:

```text
.agents/plugins/marketplace.json
plugins/separateweb-capture/.codex-plugin/plugin.json
plugins/separateweb-capture/skills/separateweb-capture/SKILL.md
```

After adding the marketplace, install or enable `SeparateWeb Capture` from the Codex Plugins list.

## Install As A Local Skill

Install the skill payload with `npx`:

```bash
npx separateweb-capture
npx separateweb-capture --target claude
npx separateweb-capture --target both
```

Default target is Codex. Use `--target claude` for Claude Code personal skills, or `--target both` for Codex and Claude.

## Use

Set a default destination for future captures:

```bash
npx separateweb-capture patch /absolute/output/path
```

Capture one page:

```bash
npx separateweb-capture capture https://example.com --single
```

Capture a root URL and crawl same-origin pages:

```bash
npx separateweb-capture capture https://example.com
```

Supported command options:

```text
--out <dir>
--width <px>
--height <px>
--max-pages <n>
--single
--all
--help
```

The package binaries are `separateweb` and `separateweb-capture`. Use `npx separateweb-capture` when the binary is not installed globally. Use `separateweb` after `npm link` or global install.

## Example Capture

This example was captured from a local game UI page:

```bash
node scripts/capture.mjs capture 'file:///path/to/design-game/index.html' --single
```

Output:

```text
Captured: captures/2026-05-18T21-39-53-265Z-index-html-4ed73889
Pages: 1
Succeeded: 1
Failed: 0
Blocks: 36
```

Detected item groups:

```json
{
  "card-large": 4,
  "button": 7,
  "price": 8,
  "badge": 3,
  "icon": 3,
  "media": 3,
  "navigation": 1,
  "card": 4,
  "panel": 1,
  "stat": 2
}
```

Full-page capture:

![Orbit Store full-page capture](docs/examples/orbit-store/full-page.png)

Capture output now separates visual assets into two folders:

```text
with-text/full-page.png
with-text/items/<kind>/*.png
without-text/full-page.png
without-text/items/<kind>/*.png
```

`manifest.json` keeps `items[].image.path` pointed at the current no-text crop, and adds `items[].textImage.path` for the matching with-text crop.

Extracted UI items:

| Kind | Example |
|---|---|
| `card-large` | ![Large card crop](docs/examples/orbit-store/card-large.png) |
| `badge` | ![Badge crop](docs/examples/orbit-store/badge-data-cores.png) |
| `media` | ![Transparent media crop](docs/examples/orbit-store/media-treasure.png) |

## What's Included

```text
.codex-plugin/plugin.json           Codex plugin manifest
skills/separateweb-capture/SKILL.md Codex skill trigger and workflow
scripts/capture.mjs                 Capture script
assets/icon.png                     Composer icon
assets/logo.png                     Plugin logo
LICENSE                             MIT license
```

The required Codex entrypoint is `.codex-plugin/plugin.json`. The skill in `skills/separateweb-capture/SKILL.md` defines when Codex should use this plugin.

## Use Cases

- Website screenshot tool for frontend teams
- Playwright screenshot capture for visual QA
- UI crop extraction from live web pages
- Web design asset capture for implementation references
- AI coding agent visual context from real URLs
- Codex plugin for webpage inspection

## Codex Usage

Ask Codex:

```text
separateweb capture https://example.com
separateweb capture https://example.com --single
separateweb capture https://example.com/docs
separateweb capture https://example.com/docs --all
separateweb patch /absolute/output/path
```

Codex should run the script from this plugin root:

```bash
node scripts/capture.mjs capture <url>
node scripts/capture.mjs patch <dir>
```

## Commands

```bash
separateweb capture <url> [--out <dir>] [--width <px>] [--height <px>] [--max-pages <n>] [--single|--all]
separateweb patch <dir>
separateweb patch --clear
separateweb select <manifest.json>
separateweb create <manifest.json> --items <indexes> --path <dir>
```

## Capture Rules

- `capture https://example.com` crawls same-origin paths.
- `capture https://example.com/` crawls same-origin paths.
- `capture https://example.com --single` captures only the root page.
- `capture https://example.com/docs` captures only `/docs`.
- `capture https://example.com/docs --all` crawls same-origin paths starting from `/docs`.
- `--max-pages` accepts `1` to `200`.

## Troubleshooting

- If capture fails, report the exact error from `scripts/capture.mjs`.
- If output is missing, check the printed `Manifest` path first.
- If selected items do not export, confirm the manifest path and `--items` indexes.

## License

MIT License.
