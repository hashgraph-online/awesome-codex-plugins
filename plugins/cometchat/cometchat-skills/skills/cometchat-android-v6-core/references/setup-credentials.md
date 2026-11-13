# setup-credentials — detect, credentials, authorize (Android v6)

> Ground truth: `ui-kit/android/getting-started-kotlin.md` + `getting-started-jetpack.md` + installed `chatuikit-core-android` 6.0.5 `CometChatUIKit.initFromSettings` + catalog `android-v6.json`, verified 2026-08-20; settings keys and error codes re-checked on 6.1.1 source 2026-10-15.

## 1. Detect project (gradle / cohort)
- Confirm it's an Android project: `settings.gradle` or `settings.gradle.kts` exists (plus an app module with `build.gradle(.kts)`).
- **Cohort** (decides which ONE kit artifact to install — never both):
  - **Compose** → the app module's `build.gradle(.kts)` mentions `androidx.compose` or `buildFeatures { compose = true }` (or the `kotlin.compose` plugin) → `com.cometchat:chatuikit-compose-android:6.1.1`
  - **Views** → otherwise (XML layouts / `viewBinding`) → `com.cometchat:chatuikit-kotlin-android:6.1.1`
- Get the cohort from `npx @cometchat/skills detect --json` (`android_variant`, per RULES.md) or by
  reading the gradle files yourself. Confirm against the gradle file if ambiguous (a hybrid app hosting Compose in Views counts as Compose only if chat screens will be composables; ASK if unclear).
- Kit prerequisites (both cohorts): API 28+ target samples; `jvmTarget "11"`; Views additionally `viewBinding = true`, Compose `compose = true`.

## 2. Config reuse — don't re-ask
A prior `.cometchat/config.json` (written by an earlier setup), an existing `app/src/main/assets/cometchat-settings.json`, or `COMETCHAT_*` entries in `local.properties` → reuse them, skip re-setup, don't re-provision or re-ask.

## 3. version_conflict — STOP gate
If ANY module declares a non-v6 CometChat UI Kit — `com.cometchat:chat-uikit-android` at 5.x/4.x (the old artifact name), or a mixed 5.x `chatuikit-*` — STOP. Surface it, reconcile (upgrade to v6 via `upgrading-from-v5`, or load matching-version skills), then continue. Never mix majors, and never install both `chatuikit-kotlin-android` and `chatuikit-compose-android` in one app (duplicate classes + doubled resources).

## 4. Env — the PRIMARY credential file is `assets/cometchat-settings.json` (read by `initFromSettings`)
The skill writes the app's credentials into a **gitignored** `app/src/main/assets/cometchat-settings.json` — the file `CometChatUIKit.initFromSettings(context, callback)` reads (it also persists `integrationSource="ai-agent"` for telemetry; `lifecycle.md`):
```json
{
  "appId": "your_app_id",
  "region": "us",
  "credentials": { "authKey": "your_auth_key" },
  "uiKit": { "subscribePresenceForAllUsers": true, "enableCalling": false }
}
```
- `appId` + `region` are REQUIRED (`ERR_SETTINGS_INVALID` otherwise); a missing file fails init with `ERR_SETTINGS_FILE_NOT_FOUND`.
- `credentials.authKey` is **dev only** — for prod builds OMIT it (login uses a server-minted auth token; `appId`/`region` are not secrets).
- `uiKit.enableCalling: true` auto-inits the Calls SDK (see `cometchat-android-v6-calls`); default false.
- **Gitignore it** — append `app/src/main/assets/cometchat-settings.json` to `.gitignore` (it carries the dev Auth Key) and never echo the key back to the user.

**Build-time extras only — `local.properties` → `BuildConfig`.** For non-credential values the app CODE reads at build time (e.g. a default demo UID), use the standard Android pattern (this is NOT the init credential path):
```properties
# local.properties (gitignored by Android Studio — verify)
COMETCHAT_DEMO_UID=cometchat-uid-1
```
```kotlin
// app module build.gradle.kts
import java.util.Properties
val localProps = Properties().apply {
    val f = rootProject.file("local.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}
android {
    buildFeatures { buildConfig = true }   // required for buildConfigField to emit
    defaultConfig {
        buildConfigField("String", "COMETCHAT_DEMO_UID",
            "\"${localProps.getProperty("COMETCHAT_DEMO_UID", "")}\"")
    }
}
```
Groovy variant, briefly: `def p = new Properties(); rootProject.file('local.properties').withInputStream { p.load(it) }` then `buildConfigField 'String', 'COMETCHAT_DEMO_UID', "\"${p.getProperty('COMETCHAT_DEMO_UID', '')}\""` inside `defaultConfig` (+ `buildFeatures { buildConfig true }`). Code reads `BuildConfig.COMETCHAT_DEMO_UID` — never a hardcoded literal.

## 5. Credentials — fetch through the CometChat MCP (offer it), or paste manually
> **Account actions go through the CometChat MCP server** — the `cometchat` server at `https://mcp.cometchat.com/mcp`. One endpoint: its docs tools need no sign-in; its `cometchat_*` tools manage the user's CometChat account and ask them to sign in on first use. There is no CLI to install. The MCP knows nothing about Gradle or Android — detection and writing the config are this skill's job (§4: `assets/cometchat-settings.json`, gitignored).

> **OFFER the fetch; don't default to manual paste.** When credentials are missing, present BOTH paths and default to the fetch: *"I can fetch your App ID / Region / Auth Key from your CometChat account through the CometChat MCP, or you can paste them — which do you prefer?"* Never silently skip to "paste them yourself", and never end the build with an "add credentials manually" TODO.

**Fetch path (user opted in).**
1. **Check the connection:** call `cometchat_whoami`.
   - **No `cometchat_*` tools** → the `cometchat` server isn't added, or the host has only the docs tools. **Don't block: go straight to the manual path below** and offer once: *"Or connect your CometChat account and I'll fetch them: sign in to the `cometchat` MCP server (Claude Code: `/mcp` → Authenticate; Codex: `codex mcp login cometchat`; Cursor: Settings → MCP → Connect; ChatGPT: connect the CometChat app)."* Not added → add the `cometchat` server (per-agent commands: `references/docs-map.md`).
   - **Needs sign-in** (`unauthorized`, or the agent says `cometchat` needs a sign-in) → not signed in yet, or it expired; the docs tools still work. Same as above: manual path plus the sign-in offer. Use whichever the user does first.
   - **Connection or server error** (timeout, 404/5xx, "failed to connect"; not `unauthorized`) → the server is down. Retry at most once, don't ask for a sign-in, and switch to the manual path with a one-line note.
2. **Pick the app — REUSE first, ASK with CURATED options, never auto-create.** An existing `.cometchat/config.json` or an already-set `*_COMETCHAT_APP_ID` → reuse it and skip. Otherwise call `cometchat_list_apps`; **you curate the list — never dump it.** Offer at most 4 selectable options: the **top 3** most relevant apps (matching framework/product, then newest; name · region · App ID) + **"Show all N apps"**; the free-text answer = paste an App ID. No selectable prompts → a numbered list, then WAIT. **Never create an app unasked** — only on explicit request, with `cometchat_create_app` after confirming the name and region (it can't be changed later).
3. **Fetch the credentials:** `cometchat_get_app_credentials` with the chosen `app_id` → `app_id`, `region`, `auth_key`, plus ready-made `env` lines (`vite`, `nextjs`, `cra`). Write them yourself (§4: `assets/cometchat-settings.json`, gitignored). The Auth Key is a secret: write it, never echo it back to the user.

**Manual path** (user prefers, or the MCP isn't available): Dashboard → Your App → Credentials → App ID, Region (`us`/`eu`/`in`), Auth Key (**dev only**). If neither path yields them, ASK and WAIT — never proceed with placeholders.

**Dashboard-gated features** (reactions, polls, translation, moderation filters, AI smart replies, ...): `cometchat_list_features` shows the app's extensions and AI features with their state; `cometchat_set_feature` turns one on or off — check `confirmed` in the result (false = CometChat accepted it but the app doesn't show it yet; tell the user to check the dashboard's Extensions page). AI features need an OpenAI key: only with a key the user gives you, `cometchat_set_openai_key`. Either way YOU still wire the client side (`cometchat-android-v6-features`).

**Other account tasks the MCP handles** (ask before any change): test users (`cometchat_create_users`, `cometchat_create_auth_token`), groups, a server-side REST API key for a token endpoint or data import (`cometchat_create_api_key`, scope `fullAccess` — server env only, never client code), webhooks, push setup (`cometchat_get_push_setup`), moderation, roles, team and usage (`cometchat_get_usage`). Tools that change existing data return `confirmation_required` with a summary instead of acting: show it to the user, and call again with `confirm: true` only after they agree. Some changes (API keys, login tokens, the OpenAI key, webhooks, app settings, team invites, deletes) return `approval_required` with a link: give it to the user; they approve that exact change in the browser and give you a code; call again with the same arguments plus `approval_code`. Never open or approve the link yourself.

## 6. Authorize / verify
Credentials are valid when `CometChatUIKit.initFromSettings(...)` hits `onSuccess` and `CometChatUIKit.login(uid, ...)` succeeds for a UID that exists (§7). `ERR_SETTINGS_FILE_NOT_FOUND` → the assets JSON is missing; `ERR_SETTINGS_INVALID` → `appId`/`region` missing in it; other auth errors → most commonly a **Region mismatch**. Do not render chat UI until login resolves (`lifecycle.md`).

## 7. Which user to log in as (the login UID) — do NOT invent one
`login(uid, callback)` authenticates a user that **must already exist** in your CometChat app; it does **not** create one. Logging in a missing UID fails (`ERR_UID_NOT_FOUND`) and the screen stays blank.
- **Never suggest a legacy/guessed sample UID** (`superhero1`, `cc-user-*`, etc. are NOT seeded in modern apps). The ONLY tentative suggestion is `cometchat-uid-1..5`, labelled *"if this is a freshly-created app"* — fresh apps are pre-seeded with `cometchat-uid-1`...`cometchat-uid-5` (the docs samples log in as `cometchat-uid-1`).
- **Use a real UID:** Dashboard → your app → **Users** tab lists every UID. ASK the user; prefer their answer over any suggestion.
- **Create one (dev):** Dashboard → Users → Add User, or `CometChatUIKit.createUser(user, callback)` (uses the init Auth Key; dev only) — fetch exact shapes from docs if you need programmatic creation.
- **Production:** never the Auth Key, never a hardcoded UID. Per real end-user, create a matching CometChat user server-side (REST API + API key), mint a per-user **auth token** from your backend, and log in with `CometChatUIKit.loginWithAuthToken(authToken, callback)` (`lifecycle.md`).

## §1a — Cohort selection (the first decision, and the least reversible)

Score STRUCTURAL signals, not a loose `/compose/` text match (it matches "composer", the kit's
own artifact name), and read BOTH
Groovy and Kotlin DSL (`build.gradle` **and** `build.gradle.kts` — an earlier version read only the
Groovy names and returned `framework: null` for every Kotlin-DSL project).

| `android_variant` | Signals that produced it | Action |
|---|---|---|
| `compose` | `buildFeatures { compose = true }`, `org.jetbrains.kotlin.plugin.compose`, `androidx.compose.*`, `compose-bom` — and no Views signal | Use **Compose** (`...-compose-*`). Do not ask; do not offer Views. Emitting XML into a Compose app is a defect. |
| `views` | `viewBinding`/`dataBinding` enabled, or `app/src/main/res/layout/` exists — and no Compose signal | Use **Views** (`...-kotlin-*`). |
| `mixed` | both sets present — typically an app mid-migration | **ASK and WAIT.** Say what you found: "your app has both Compose and XML screens — the chat screens can be either." Never pick silently. |
| `unknown` | neither (new/empty project) | **ASK and WAIT**, with a recommendation: Compose for greenfield, Views if the team's existing screens are XML. |

`android_cohort_signals: { composeHits, viewsHits }` is returned so you can SHOW the evidence
("I detected Compose: compose plugin + compose-bom, no XML layouts").

**Existing CometChat install.** When `existing_cometchat` is true, detect also returns
`installed_uikit`, `android_uikit_major` and `version_conflict`. A v4/v5 `chat-uikit-android` is a
**STOP**: adding v6 beside it produces duplicate-class build failures. Tell the user which version
they are on and offer the upgrade (`cometchat-android-v6-migration`) BEFORE any new feature work.
Only when the tree is clean (or already v6) do you proceed to credentials.
