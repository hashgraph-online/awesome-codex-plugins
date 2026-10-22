# Data-only mode — move Stream history to CometChat without touching the app

Use this mode when the user asks to migrate ONLY their data: "migrate only my data from Stream", "import my Stream users, groups and messages into CometChat", "don't change my app code", or when the app ALREADY runs on CometChat (`existing_cometchat: true`, no Stream SDK left) and only the history is missing. The request is the approval: run it to the end in one turn, like the full migration.

## What changes
- **Only** `scripts/cometchat-migration/` (`package.json`, the data script, `id.mjs`, `README.md`, `.gitignore`) and the report `COMETCHAT_MIGRATION.md`. The script's own `npm install` and its `export/` files stay inside that folder and are git-ignored. Nothing else in the repo is edited, removed, renamed or uninstalled — no app code, dependencies, env files, docs or config.
- In a git repo, `git switch -c cometchat-migration` first (never commit), same as the full migration.

## Steps
1. **Detect** as in SKILL.md step 1. A data-only request NAMES the vendor, so STOP (1) ("no Stream usage found") does NOT apply, and neither does STOP (2): the script is Node, so the app's platform doesn't matter. Don't run or fix the app's build.
2. **Identity — the one decision that matters.** Imported UIDs/GUIDs must equal the IDs the app logs in with, or users land in empty inboxes.
   - The app already logs in to CometChat → find how it builds the UID (the `login`/`loginWithAuthToken` call, the server's auth-token/create-user code) and copy that exact transform into `id.mjs`. If it passes Stream user IDs and channel CIDs through unchanged, `id.mjs` must too — don't "improve" it.
   - The app doesn't log in to CometChat yet → write `toCometChatId()` exactly as `concept-map.md` §IDs defines it, and make action item #1: "use this same `toCometChatId()` wherever your app or server logs users in to CometChat".
   - Record which case applied, and why, in the report.
3. **Write the script** per `data-migration.md` (export from the Stream server-side API → transform → CometChat Data Import API), reading secrets from env only.
4. **Run it for the user** exactly as SKILL.md step 8: ask for the source keys (`STREAM_API_KEY`, `STREAM_API_SECRET`) and the CometChat App ID, Region and full-access REST API key; `--dry-run` first (show user / group / member / message counts), then the real import; report what landed and what failed. If they don't share keys, leave running it as an action item.
5. **Report.** Write `COMETCHAT_MIGRATION.md` from `report-template.md` with **Mode:** data-only. Fill Summary, the import results and action items; set **Migrated** and **Removed** to "None — data-only (app code unchanged)". Always include the 6-month retention and re-host-attachments action items from `data-migration.md`.

## Verify
- `git status` shows changes ONLY under `scripts/cometchat-migration/` plus `COMETCHAT_MIGRATION.md`, with no `node_modules/` or `export/` files listed.
- `node --check scripts/cometchat-migration/migrate.mjs` passes, and the dry run ran (or its command is in the action items).
- `id.mjs` matches the app's existing CometChat login transform (case 1) or `concept-map.md` §IDs (case 2), and the report says which.
