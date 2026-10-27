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

## 3. Credentials — OFFER the fetch FIRST (never degrade to "paste it yourself")
**(a) Fetch from the dashboard — the default.** Load the CLI on demand:
```bash
npx @cometchat/skills-cli@3 auth login
npx @cometchat/skills-cli@3 provision list --json
npx @cometchat/skills-cli@3 provision use --app-id <id> --json
```
- **Never auto-create an app.** List, show the top few plus a "show all", and ASK which.
- `provision use` returns App ID / Region / Auth Key **and** writes a neutral `.cometchat/config.json`.
  It does **not** know Flutter — writing the settings asset is the skill's job.

**(b) Manual paste** — Dashboard → Your App → Credentials. Use only if the user declines (a) or the CLI
can't run. Ask and WAIT; never guess a value.

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
  `cometchat-uid-1…`). Never invent one.
- **Asset not found** — see `troubleshooting.md`.

## 6. Production
Omit `credentials.authKey`, mint a per-user auth token server-side, and call
`CometChatUIKit.loginWithAuthToken(...)` (`lifecycle.md`). Tell the user plainly that the Auth Key path you
wired is dev-only — flag dev-only AS dev-only.
