---
name: separateweb-capture
description: Capture a URL into a full-page screenshot, cropped UI item PNGs, and a JSON manifest. Use when the user says `separateweb capture <url>`, asks to capture a website, or wants UI extraction assets without running the SeparateWeb web app.
---

# SeparateWeb Capture

Use this skill when the user asks:

```text
separateweb capture <url>
npx separateweb-capture capture <url>
separateweb patch <path>
```

Use `npx` when the package is not linked globally. This is the safest default for Claude Code personal skills:

```bash
npx separateweb-capture capture <url>
npx separateweb-capture patch <path>
```

Use `separateweb-capture` with no capture command only to install the local skill payload:

```bash
npx separateweb-capture
npx separateweb-capture --target claude
npx separateweb-capture --target both
```

If `separateweb` is installed or linked globally, this shorthand is also valid:

```bash
separateweb capture <url>
separateweb patch <path>
```

If running from the plugin root, the local script is also valid:

```bash
node scripts/capture.mjs capture <url>
node scripts/capture.mjs patch <path>
```

Optional flags:

```bash
--out <dir>
--path <dir>
--width <px>
--height <px>
--max-pages <n>
--single
--all
```

Capture behavior:

- `capture https://example.com` and `capture https://example.com/` crawl same-origin paths by default.
- `capture https://example.com --single` captures only the home page.
- `capture https://example.com/path` captures only that page by default.
- Use `--single` to force one page.
- Use `--all` to force same-origin crawl from any start URL.
- Captured items are grouped by type under `items/<kind>/`.

Examples:

```bash
npx separateweb-capture capture https://domain.com
npx separateweb-capture capture https://domain.com --single
npx separateweb-capture capture https://domain.com/about
npx separateweb-capture capture https://domain.com/about --all
```

Patch selection:

```bash
npx separateweb-capture patch /absolute/output/path
npx separateweb-capture select captures/<jobId>/manifest.json
npx separateweb-capture create captures/<jobId>/manifest.json --items 1,3,5 --path /absolute/output/path
```

Use `patch <path>` to set the default machine path where future `capture` outputs are written. Use `create` only when exporting selected items from an existing manifest.

Default output:

```text
captures/<jobId>/site-manifest.json
captures/<jobId>/page-001-<slug>/full-page.png
captures/<jobId>/page-001-<slug>/manifest.json
captures/<jobId>/page-001-<slug>/items/<kind>/*.png
```

Single-page capture writes `full-page.png`, `manifest.json`, and `items/<kind>/*.png` directly under `captures/<jobId>/`.

After running, report:

- `Captured`
- `Manifest`
- `Blocks`
- exact error if capture failed

Do not start a Nuxt dev server. This plugin is script-only.
