---
name: cometchat-migrate-from-twilio
description: "Migrate an app from Twilio Conversations (or the deprecated Programmable Chat) to CometChat in ONE prompt, on any platform in this pack. Twilio is headless (no UI Kit), so this is client/SDK-mode: keep the app's own UI, swap the data layer to the CometChat Chat SDK (or, for a fresh chat UI, the CometChat UI Kit), rewrite the token server, remove features CometChat lacks, write a data-migration script, uninstall Twilio, verify the build, and end with a report. Triggers: 'migrate from Twilio to CometChat', 'migrate my app to CometChat' (Twilio detected), 'replace Twilio Conversations with CometChat', 'move off Twilio chat', 'twilio-conversations to cometchat', 'twilio programmable chat migration'."
license: "MIT"
compatibility: "FROM Twilio Conversations (`@twilio/conversations`, `twilio-conversations` iOS/Android, `twilio_conversations` Flutter) or Programmable Chat (`twilio-chat`, deprecated) → the CometChat family this pack detects. Node >=18 for the data-migration script."
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat migration twilio conversations programmable-chat competitor switch sdk data-import"
---

> **Ground truth:** the TWILIO side (what to look for) is baked in `references/inventory.md` + `references/feature-map.md` — confirm each hit by reading the user's code and, where unsure, Twilio's current Conversations docs. The COMETCHAT side is never from memory: symbols from the target family's skills + catalog, feature existence from `features.json`, signatures via `cometchat-<family>-core/references/docs-map.md` (Docs MCP first — `RULES.md` → Fetch discipline). REST pages under `DOCS_BASE = https://www.cometchat.com/docs`.

## Companion skills (read first)
- `cometchat-<family>-core` — the init → login → render (or the Chat SDK init/login) the migrated app lands on; `<family>` resolved in step 1.
- `cometchat-security` — the server token endpoint that replaces Twilio access tokens.

## Use this skill when
"migrate my app from Twilio to CometChat", "replace Twilio Conversations", or "migrate my app to CometChat" when `npx @cometchat/skills detect --json` reports `migrate_from` vendor `twilio`. Sendbird/Stream apps → their own skills.

## The single-prompt contract (read before step 1)
The migration request IS the approval (`RULES.md` → Competitor migration). Run every step to the end in one turn: no plan/approve gate, no questions — take the documented default and record it under *Defaults taken*. Work on a `cometchat-migration` git branch; never commit/push. You DO run the data-import script — but only at the very end and only after the user hands you the credentials (step 8); that single credential prompt is the sole exception to "no questions". Removing Twilio is the requested outcome; non-Twilio code is only rewired. Only STOP if: no Twilio usage found (hand to `cometchat`), the platform has no family in this pack (deliver the inventory as the report), or the app didn't build before you started (record it, migrate anyway, label pre-existing).

## Twilio is headless — so this is client/SDK mode
Twilio Conversations ships **no UI Kit**; the app already has its **own chat UI** on the Twilio client. Default migration therefore **keeps that UI and swaps the data layer** to the CometChat **Chat SDK** (`cometchat-<family>-core` docs-map → SDK), mapping CometChat objects into the app's existing view models at the boundary. If the user instead wants CometChat's prebuilt UI, offer to replace their UI with the family UI Kit (a bigger change) — but the safe default is data-layer-only.

## Migration workflow (BAKED — do every step, in order)
Every step applies to every app: users and history exist even in a small app, so steps 4 (`toCometChatId`) and 8 (data script) are ALWAYS delivered; skip only a step whose subject truly doesn't exist (no server → step 7), listed as `skipped: <why>`.
1. **Detect.** `npx @cometchat/skills detect --json` → framework, `existing_cometchat`, `migrate_from`. Resolve `<family>` (`peers.yaml`; per-platform targets in `references/inventory.md`). Run the app's build once and record pass/fail.
2. **Inventory.** Grep per `references/inventory.md` (packages, `Client`/`Conversations.Client`, access-token fetch, `getConversationBySid`/`create`, `sendMessage`, `getMessages`, participants, `stateChanged`/message listeners, media, attributes, push, the token server). Record each hit `file:line → purpose`.
3. **Feature map.** For each Twilio feature, use `references/feature-map.md`, then check the CometChat id in the family's `features.json` AND the docs (UI Kit + SDK). Present → migrate. **An empty MCP search is INCONCLUSIVE, not "unsupported":** re-query with CometChat vocabulary (e.g. "media recorder"/"voice notes", not "voice message recorder"; drop version/platform over-qualifiers), then **LIVE-FETCH** the likely docs page (`fetch_cometchat_doc_page`, or a plain fetch of the docs URL + `.md`), then cross-check the family **CATALOG** (installed component/symbol list). Mark **UNSUPPORTED only** when the CATALOG lacks it AND the live doc fetch (not merely an empty MCP search) also finds nothing (then remove + list). Never call unsupported from memory or from an empty search; if it genuinely can't be verified, KEEP it + `needs-verification`.
4. **Install CometChat + wire init/login** per `cometchat-<family>-core`. **Identity:** the CometChat UID is the app's Twilio **identity** through one shared `toCometChatId()` (`references/concept-map.md` §IDs), used by client login, the token server, and the data script.
5. **Replace the data layer, file by file** (`references/concept-map.md`): Twilio `Client` init/token → CometChat init/login; `Conversation` → a user or group conversation; `Participant` → group member; `Message` send/get → CometChat send/messages request; `stateChanged`/`messageAdded` listeners → CometChat listeners (removed on unmount); media → attachments; `attributes` → metadata. Keep the app's UI; map at the boundary. Remove each Twilio import as its last use goes.
6. **Remove unsupported features FULLY** — code, UI entry points, state, deps, tests. Log each for the report.
7. **Server side.** Replace the Twilio **access-token** endpoint (API Key/Secret + Conversations Service SID → JWT) with a CometChat auth-token endpoint (`cometchat-security`; create user if missing → `POST /v3/users/{uid}/auth_tokens`). Map Twilio webhooks (`onMessageAdded`, etc.) to CometChat webhooks; drop/list any with no equivalent. Replace other Conversations REST calls with CometChat REST, or remove + list.
8. **Data-migration script — write it, then run the import for the user.** `scripts/cometchat-migration/` per `references/data-migration.md`: export users/conversations/participants/messages from the Twilio Conversations REST API → transform with the shared `toCometChatId()` → import via the CometChat Data Import API. When the code migration is done, tell the user the **data-import script is ready** and ask for the credentials it needs — the Twilio keys (`TWILIO_ACCOUNT_SID`, `TWILIO_API_KEY`, `TWILIO_API_SECRET`, `TWILIO_CONVERSATIONS_SERVICE_SID`) and the CometChat **App ID, Region and full-access REST API key**. (This one credential prompt is the sole exception to the no-questions contract.) The moment they provide them, **RUN the import yourself** from env vars — never write secrets into a repo file: a `--dry-run` first (show counts), then the real import, then report results. Only messages within CometChat's **6-month retention window** import — tell the user to **reach out to CometChat to import messages older than 6 months**. If they decline to share credentials, leave running it as an action item.
9. **Uninstall Twilio** — remove every Twilio dependency (`@twilio/conversations`, `twilio-conversations`, `twilio-chat`, the server `twilio` SDK) + lockfile, env vars, native config, CI secrets. Reinstall. Update the app's own docs (README/`.env.example`) and rename `twilio*` identifiers.
10. **Verify** (§Verify it works). Fix build errors you introduced. No live tests unless asked.
11. **Report.** Write `COMETCHAT_MIGRATION.md` from `references/report-template.md`; END the reply with its **Removed** + **Action items** lists.

## Common pitfalls
- **Identities that CometChat rejects.** Twilio `identity` strings can hold characters CometChat UIDs can't (alpha-dash, ≤100, lowercased). Sanitize with one shared function everywhere.
- **1:1 vs group.** A Twilio conversation with exactly two participants → a CometChat **user** conversation, not a two-person group.
- **Optimistic send / pagination / listeners** differ — see `references/concept-map.md` behavioral gotchas; keep the app's UX identical, only the data source changes.
- **Access token ≠ Auth Key.** Twilio's client token maps to a CometChat **auth token** (server-minted), not the Auth Key. Never ship the Auth Key.
- **Half-removed features / left-behind listeners** — remove entry points too; remove every listener on unmount.
- **Programmable Chat vs Conversations** — older apps use `twilio-chat` (Channel/Member/Message); the mapping is the same shape, note which the app uses.

## Verify it works
The app builds with the family's normal command · zero Twilio residue (`grep -rIiE 'twilio' .` finds only the report + data script) · every CometChat symbol exists in the catalog · every migrated feature is in `features.json`/docs; every UNSUPPORTED item is in the report with its files · client login, token server, and data script all use the same `toCometChatId()`.

**RUN it and read the logs — a compile is NOT a working app (do this; don't skip).** When you're done implementing, START the app and confirm it LOADS with the chat surface rendered and NO errors in the browser console / dev-server terminal (native: platform run + logs). Fix EVERY runtime error you introduced — a `Cannot read properties of undefined` from a half-migrated reference, or an SDK enum/class read at module-load before the SDK is ready, is a migration bug (see `cometchat-<family>-troubleshooting`). If it can't be started here, SAY SO and give the user the exact run command + what to watch for — never silently skip this.
