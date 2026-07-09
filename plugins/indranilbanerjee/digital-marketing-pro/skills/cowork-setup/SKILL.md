---
name: cowork-setup
description: "One-shot setup that wires Digital Marketing Pro for team usage in Anthropic Cowork. Verifies the Cowork sandbox, checks for a Google Drive integration, creates the canonical Drive folder layout, and confirms team-ready brand-state routing. Use this the first time a Cowork user installs DMP OR when brand profiles aren't persisting across sessions."
argument-hint: "[--brand <name>] [--drive-root <folder-name>]"
effort: low
---

# /digital-marketing-pro:cowork-setup

The one-time setup that makes Digital Marketing Pro persistent in Cowork by a team. Wires up the Cowork → Drive routing so brand profiles, campaign plans, audit reports, and run records survive past the end of the current Cowork session.

## Why this skill exists

Cowork is the friendliest Anthropic surface for marketers — agency teams, in-house marketers, growth ops — who don't live in a terminal. The natural team workflow is "everyone uses Cowork; brand state and outputs live in our shared Drive". But DMP's filesystem layer was designed for local Claude Code (writes to `~/.claude-marketing/` on the host machine). In Cowork that path is the per-session Linux sandbox — vanishes at session end, invisible to the team.

**`${CLAUDE_PLUGIN_DATA}` does not help here either.** Anthropic's plugin docs describe it as the persistent per-plugin storage path. In Cowork it resolves to a session-scoped VM mount that disappears the same way (open: [claude-code#51398](https://github.com/anthropics/claude-code/issues/51398)). Every OAuth-backed MCP plugin hits the same wall.

v3.12.0 fixed this with environment-aware routing: when Cowork is detected AND a Drive MCP is configured, brand profiles and reports round-trip through Drive instead of the ephemeral sandbox. This skill is the one-shot setup that ensures both conditions are true before you start producing real work.

## Behavior

### Step 1 — Verify Cowork environment

```bash
python scripts/plugin-metadata.py --section environment
```

Parse the JSON. Three branches:

**`environment == "cowork-sandbox"`** — Proceed to Step 2.

**`environment == "claude-code-windows"` / `"-mac"` / `"-linux"`** — Tell the user:

> "You're running in local Claude Code, not Cowork. The Cowork-specific Drive routing isn't needed here — brand state at `~/.claude-marketing/` persists on your host as designed. If you ALSO want Drive backups for team sharing, you can run this skill anyway and it'll mirror state to Drive as a backup. Want to proceed?"

Only proceed if the user confirms.

**`environment == "unknown"`** — Show the indicators from the JSON and ask the user where they're running, then proceed assuming Cowork (since unknown-from-Cowork is the most likely case).

### Step 2 — Verify a Drive MCP is connected

Scan your available tools for any Google Drive MCP. Common signatures:

- `mcp__<id>__create_file`, `mcp__<id>__read_file_content`, `mcp__<id>__search_files`, `mcp__<id>__list_folder_items` — Anthropic-platform Drive integration (Settings → Integrations → Google Drive in Cowork)
- `mcp__pipedream-google-drive__*` — Pipedream aggregator
- `mcp__composio-google-drive__*` — Composio
- `mcp__zapier-google-drive__*` — Zapier
- Any tool whose name combines "drive" with "create" / "upload" / "search"

**If a Drive MCP is found:** confirm to the user which one ("Found: Anthropic platform Google Drive integration. I'll use this.") and proceed to Step 3.

**If NO Drive MCP is found:** stop the wizard with a clear message:

> "Cowork-mode DMP needs a Google Drive integration before it can persist brand state for your team. Easiest setup (60 seconds):
>
> 1. In Cowork, click your profile menu → **Settings** → **Integrations**
> 2. Find **Google Drive** in the list → click **Connect**
> 3. Sign in with the Google account that owns your team's shared Drive
> 4. Come back here and re-run `/digital-marketing-pro:cowork-setup`
>
> Alternative: a Notion MCP also works as a persistence target — DMP will treat each brand as a Notion page. If you'd prefer that route, add Notion to your Cowork Integrations panel and re-run this skill."

### Step 3 — Verify or create the canonical Drive folder

Default folder name: `DigitalMarketingPro` (under "My Drive" or wherever the user prefers). If `--drive-root <name>` was passed, use that instead.

Use the Drive MCP to:

1. Search for a top-level folder named `DigitalMarketingPro` (or the user's `--drive-root`)
2. If it exists, confirm the user wants to use it. Show its URL.
3. If it doesn't exist, create it. Show the URL of the new folder.

Then create the subfolder skeleton:

```
DigitalMarketingPro/
├── _brands/                  <- brand profile JSONs persist here per brand
├── _runs/                    <- per-run checkpoints (resume across sessions)
├── _plans/                   <- yearly + quarterly + campaign plans
└── (brand folders created on first content/audit/campaign run)
    └── <brand name>/
        ├── strategy/
        ├── seo/
        ├── campaigns/
        ├── audits/
        └── reports/
```

Don't create empty brand subfolders yet — those auto-create during the first run for that brand. Just `_brands/`, `_runs/`, and `_plans/` need to exist.

### Step 4 — Store the Drive root reference + team namespace

**Multi-team isolation**: ask the user "what's your team's Drive root folder name?" (default: `DigitalMarketingPro`). Different teams use different folder names → automatic namespace isolation. Examples:
- Solo / small team: `DigitalMarketingPro` (default)
- Agency named "ACME": `ACME DigitalMarketingPro`
- Two distinct teams sharing one Drive: each picks their own name

Then write the config via the canonical script (NOT a hand-written JSON file — use the script so the format stays in sync with the rest of the toolchain):

```bash
python scripts/drive-sync-state.py --action write-config --data '{
  "environment": "cowork-sandbox",
  "drive_root_folder_name": "<team folder name chosen>",
  "drive_root_folder_id": "<id from Step 3>",
  "drive_root_folder_url": "<webViewLink from Step 3>",
  "drive_mcp_tool_prefix": "<prefix detected in Step 2, e.g. mcp__abc123__>"
}'
```

The script writes to `~/.claude-marketing/_cowork-config.json` and adds a `configured_at` timestamp automatically.

Future Cowork sessions: every DMP operation (`brand-setup`, `status`, `seo-audit`, `campaign-plan`, etc.) reads this config first. If it exists AND the Drive folder still exists, all I/O routes to that root. If a different team picked a different folder name, their config lives at the same path but points elsewhere — no collision.

To verify it was written correctly:

```bash
python scripts/drive-sync-state.py --action read-config
```

### Step 5 — Set the user's expectations

Show a clean summary:

```
Digital Marketing Pro is now wired for Cowork team usage:

Environment:           Cowork sandbox (Linux)
Drive integration:     <name>
Output root in Drive:  My Drive/<folder name> (link)
Config saved at:       ~/.claude-marketing/_cowork-config.json

What this means in practice:

- /digital-marketing-pro:brand-setup -> profile lands in
  Drive/<folder>/_brands/<brand-slug>/profile.json (persists across sessions)
- /digital-marketing-pro:campaign-plan -> plan lands in
  Drive/<folder>/<brand>/campaigns/<YYYY-MM>/<slug>/PLAN.md
- /digital-marketing-pro:seo-audit -> audit + intermediates land in
  Drive/<folder>/<brand>/audits/<date>/
- /digital-marketing-pro:status -> reads brand state from Drive first,
  falls back to local sandbox if Drive call fails
- /digital-marketing-pro:resume -> picks up an interrupted run by
  pulling its checkpoint files from Drive/<folder>/_runs/

Your team accesses everything via Google Drive directly. No
Cowork-specific paths to remember.

Next step:
  /digital-marketing-pro:brand-setup "Your Brand Name"
```

### Step 6 — Optional: kick off a brand setup

If `--brand <name>` was passed, automatically launch `/digital-marketing-pro:brand-setup "<name>"` after the summary. This makes the very first run "one command, fully set up."

## How the Cowork-aware skills use this config

When the routing is configured, brand-setup writes locally to `~/.claude-marketing/{brand}/profile.json` AND records a pending Drive upload via `drive-sync-state.py --action add-pending-upload`. The agent then reads the pending list and uses its Drive MCP to push the file to `<root>/_brands/{brand}/profile.json`. On a future Cowork session, the agent reverses this: it reads `_cowork-config.json`, sees the team's Drive root, downloads `<root>/_brands/{brand}/profile.json` to the local sandbox, and marks it `profile-mark-downloaded` so the local hash matches the Drive copy.

Concretely: after every state-mutating DMP operation, the agent runs:

```bash
python scripts/drive-sync-state.py --action profile-needs-upload --brand <brand>
```

If `needs_upload: true`, the agent uses its Drive MCP to upload the file and then runs `--action profile-mark-uploaded` with the Drive file ID returned by the MCP.

## What this skill does NOT do

- It does not change DMP's behavior in local Claude Code (where host filesystem is fine).
- It does not migrate existing local-mode brands to Drive. To do that after the fact: re-run `/digital-marketing-pro:brand-setup "<brand>"` in Cowork after this skill finishes — the brand-setup skill will upload the local profile to Drive.
- It does not create a service-account JSON. Cowork-mode uses the MCP path exclusively (no Google Cloud setup needed).
- It does not check whether your Drive has enough space. Brand profiles + plans are tiny (<100KB typical), so this is rarely a concern, but flag it if you hit a quota error during a real run.
- It does not replace the local fallback — if a Drive call fails for any reason, DMP still writes locally and re-queues the upload.

## See also

- `/digital-marketing-pro:status` — confirm Cowork+Drive is detected after setup
- `/digital-marketing-pro:brand-setup` — actual brand setup (now Drive-default in Cowork)
- `/digital-marketing-pro:doctor` — per-action readiness check (now reports Cowork+Drive routing too)
- `scripts/plugin-metadata.py --section environment` — the underlying probe
- README "Cowork team usage" section — canonical doc for which surface to use
