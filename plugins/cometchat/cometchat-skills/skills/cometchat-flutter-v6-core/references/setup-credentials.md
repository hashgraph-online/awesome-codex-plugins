# setup-credentials — detect, reconcile, fetch, write, authorize

The full version of `SKILL.md` §"Setup & credentials". Load when doing first-time setup or debugging auth.

## 1. Detect the project (`npx @cometchat/skills detect --json`, topped up by reading the repo — `RULES.md`)
Parse, recording `null` rather than guessing when a signal is absent:

| Signal | Where |
|---|---|
| Flutter/Dart constraints | `pubspec.yaml` → `environment:` |
| Existing CometChat + **major** | `pubspec.yaml` deps + `pubspec.lock` (`cometchat_chat_uikit`) |
| State management | deps: `flutter_bloc` · `riverpod` · `provider` · `get` · `mobx` |
| Navigation | deps/source: `go_router` · `auto_route` · plain `Navigator` |
| Config strategy | `--dart-define` in run configs · `envied` · `flutter_dotenv` · a constants file |
| Existing credentials | `cometchat-settings.json` · `.cometchat/config.json` · `--dart-define` keys |
| App entry | `lib/main.dart` — where `runApp` is, and what wraps it |
| Platform floors | `android/app/build.gradle.kts` (`minSdk`) · `ios/Podfile` (`platform :ios`) |

## 2. version_conflict — STOP
A non-v6 `cometchat_chat_uikit` present on an **add** request is a STOP, not a warning: reconcile first,
never mix majors (`RULES.md`). v5 → v6 is `cometchat-flutter-v6-migration`. If v6 is already wired and
working, this is a **re-entry** — summarize what exists and ask what to ADD, don't re-run setup.

## 3. Credentials — fetch through the CometChat MCP (offer it first), or paste manually
> **Account actions go through the CometChat MCP server** — the `cometchat` server at `https://mcp.cometchat.com/mcp`. One endpoint: its docs tools need no sign-in; its `cometchat_*` tools manage the user's CometChat account and ask them to sign in on first use. There is no CLI to install. The MCP knows nothing about Flutter — detection and writing the config are this skill's job (§4: the settings asset).

> **OFFER the fetch; don't default to manual paste.** When credentials are missing, present BOTH paths and default to the fetch: *"I can fetch your App ID / Region / Auth Key from your CometChat account through the CometChat MCP, or you can paste them — which do you prefer?"* Never silently skip to "paste them yourself", and never end the build with an "add credentials manually" TODO.

**Fetch path (user opted in).**
1. **Check the connection:** call `cometchat_whoami`.
   - **No `cometchat_*` tools** → the `cometchat` server isn't added, or the host has only the docs tools. **Don't block: go straight to the manual path below** and offer once: *"Or connect your CometChat account and I'll fetch them: sign in to the `cometchat` MCP server (Claude Code: `/mcp` → Authenticate; Codex: `codex mcp login cometchat`; Cursor: Settings → MCP → Connect; ChatGPT: connect the CometChat app)."* Not added → add the `cometchat` server (per-agent commands: `references/docs-map.md`).
   - **Needs sign-in** (`unauthorized`, or the agent says `cometchat` needs a sign-in) → not signed in yet, or it expired; the docs tools still work. Same as above: manual path plus the sign-in offer. Use whichever the user does first.
   - **Connection or server error** (timeout, 404/5xx, "failed to connect"; not `unauthorized`) → the server is down. Retry at most once, don't ask for a sign-in, and switch to the manual path with a one-line note.
2. **Pick the app — REUSE first, ASK with CURATED options, never auto-create.** An existing `.cometchat/config.json` or an already-set `*_COMETCHAT_APP_ID` → reuse it and skip. Otherwise call `cometchat_list_apps`; **you curate the list — never dump it.** Offer at most 4 selectable options: the **top 3** most relevant apps (matching framework/product, then newest; name · region · App ID) + **"Show all N apps"**; the free-text answer = paste an App ID. No selectable prompts → a numbered list, then WAIT. **Never create an app unasked** — only on explicit request, with `cometchat_create_app` after confirming the name and region (it can't be changed later).
3. **Fetch the credentials:** `cometchat_get_app_credentials` with the chosen `app_id` → `app_id`, `region`, `auth_key`, plus ready-made `env` lines (`vite`, `nextjs`, `cra`). Write them yourself (§4: the settings asset). The Auth Key is a secret: write it, never echo it back to the user.

**Manual path** (user prefers, or the MCP isn't available): Dashboard → Your App → Credentials → App ID, Region (`us`/`eu`/`in`), Auth Key (**dev only**). If neither path yields them, ASK and WAIT — never proceed with placeholders.

**Dashboard-gated features** (reactions, polls, translation, moderation filters, AI smart replies, ...): `cometchat_list_features` shows the app's extensions and AI features with their state; `cometchat_set_feature` turns one on or off — check `confirmed` in the result (false = CometChat accepted it but the app doesn't show it yet; tell the user to check the dashboard's Extensions page). AI features need an OpenAI key: only with a key the user gives you, `cometchat_set_openai_key`. Either way YOU still wire the client side (`cometchat-flutter-v6-features`).

**Other account tasks the MCP handles** (ask before any change): test users (`cometchat_create_users`, `cometchat_create_auth_token`), groups, a server-side REST API key for a token endpoint or data import (`cometchat_create_api_key`, scope `fullAccess` — server env only, never client code), webhooks, push setup (`cometchat_get_push_setup`), moderation, roles, team and usage (`cometchat_get_usage`). Tools that change existing data return `confirmation_required` with a summary instead of acting: show it to the user, and call again with `confirm: true` only after they agree. Some changes (API keys, login tokens, the OpenAI key, webhooks, app settings, team invites, deletes) return `approval_required` with a link: give it to the user; they approve that exact change in the browser and give you a code; call again with the same arguments plus `approval_code`. Never open or approve the link yourself.

## 4. Write the settings asset
`cometchat-settings.json` at the **project root** (beside `pubspec.yaml`):
```json
{
  "appId": "APP_ID",
  "region": "REGION",
  "credentials": { "authKey": "AUTH_KEY" },
  "uiKit": { "subscribePresenceForAllUsers": true, "enableCalling": false },
  "chatSDK": { "autoEstablishSocketConnection": true }
}
```
Register it (exact indentation matters in YAML):
```yaml
flutter:
  uses-material-design: true
  assets:
    - cometchat-settings.json
```
Then: `flutter pub get`. **Do NOT gitignore a registered asset** — a fresh clone / CI `flutter build bundle`
fails with *"No file or variants found for asset: cometchat-settings.json"* if the file is missing. Instead
**commit a placeholder `cometchat-settings.json`** (same shape, placeholder/empty `authKey` — never a real
dev key) so the asset path always resolves, and have each dev and CI overwrite it with real credentials
locally / at build time. Guard against committing a real key with a pre-commit hook or CI check, not
`.gitignore`. Never echo the Auth Key back to the user or into logs.
> Optional keys: `chatSDK.adminHost` / `chatSDK.clientHost` (dedicated/on-prem clusters only).
> `uiKit.enableCalling` stays `false` until the user asks for calls (→ `cometchat-flutter-v6-calls`).

### If the team already uses `--dart-define` / envied
The settings **file** is what `initFromSettings` reads — it cannot read `--dart-define`. Two honest options,
state the trade-off and let the user choose:
- Keep `initFromSettings` and generate `cometchat-settings.json` at build time from your existing secret
  source (CI writes the file). Keeps telemetry attribution.
- Or use the classic `UIKitSettingsBuilder` + `CometChatUIKit.init(...)` with `--dart-define` values —
  works, but loses `integrationSource="ai-agent"`. Only if the user prefers it after hearing the trade-off.

## 5. Authorize — confirm it actually worked
`initFromSettings` reaches `onSuccess`, then `login` reaches `onSuccess` with a `User`. Failure modes:
- **Wrong Region** — the single most common cause of an immediate auth error. `us` / `eu` / `in`, matching
  the Dashboard exactly.
- **UID doesn't exist** — `login` needs an existing user (Dashboard → Users; fresh apps seed
  `cometchat-uid-1...`). Never invent one.
- **Asset not found** — see `troubleshooting.md`.

## 6. Production
Omit `credentials.authKey`, mint a per-user auth token server-side, and call
`CometChatUIKit.loginWithAuthToken(...)` (`lifecycle.md`). Tell the user plainly that the Auth Key path you
wired is dev-only — flag dev-only AS dev-only.
