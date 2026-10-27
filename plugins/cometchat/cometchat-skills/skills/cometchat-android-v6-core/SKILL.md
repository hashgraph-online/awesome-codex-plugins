---
name: cometchat-android-v6-core
description: "Foundational rules for the CometChat Android UI Kit v6 — the two UI cohorts and their artifacts, credentials via the gitignored assets settings file, initFromSettings → login → render ordering, the component map, and the production-ready core chat surface. Read this first for any Android CometChat task. Triggers: CometChat Android setup, Kotlin chat UI kit, Jetpack Compose chat."
license: "MIT"
compatibility: "Android minSdk >=28; compileSdk >=36; Kotlin >=2.1; AGP >=8.9.1; JVM target 11; com.cometchat:chatuikit-kotlin-android ^6 (XML Views) OR com.cometchat:chatuikit-compose-android ^6 (Jetpack Compose) — 6.0.x, verified 6.0.5; com.cometchat:chat-sdk-android ^5 (5.0.x); optional com.cometchat:calls-sdk-android ^5"
metadata:
  author: "CometChat"
  version: "1.1.0"
  tags: "chat cometchat android kotlin compose views core rules initialization native"
---

> **Ground truth:** `com.cometchat:chatuikit-{kotlin,compose}-android@6` + catalog `android-v6.json`
> (287 public symbols, generated from the INSTALLED 6.0.5 source) + `features.android-v6.json`.
> Official docs: <https://www.cometchat.com/docs/ui-kit/android/overview> · scoped index
> `…/ui-kit/android/llms-android-v6.md`. Verify every symbol against the catalog; fetch signatures
> from docs (`references/docs-map.md`); never trust memory.
>
> ⚠️ **ONE kit, TWO cohorts.** `chatuikit-kotlin-android` (XML Views) and `chatuikit-compose-android`
> (Jetpack Compose) are different artifacts with different namespaces. Component NAMES are shared, the
> wiring is not — Views uses `setOnX(...)` setters, Compose uses `onX =` params. **Never install both.**
> **v5 Java snippets do not compile against v6** (`com.cometchat.chatuikit.*` → `com.cometchat.uikit.*`);
> that migration is `cometchat-android-v6-migration`.
>
> ⚠️ **Some docs snippets are ahead of / behind the shipped kit.** Where a baked signature here differs
> from a docs page, the baked one was verified against the installed 6.0.5 source (gap logged
> internally). Compile before you trust a docs fence.

<!-- core is the companion the other android v6 skills read; it has no Companion block of its own. -->

## Use this skill when
"add chat to my Android app", "set up CometChat credentials", "integrate CometChat in Kotlin/Compose", "show a conversations + messages screen", "build a chat app". An unscoped "add chat" means the **production-ready core chat surface** below — not a bare list, and not the whole tab-based app (that grows via `cometchat-android-v6-{kotlin,compose}-placement`).

## Prerequisites & install
**Pick ONE cohort** — the app's existing UI stack decides:

```kotlin
// settings.gradle.kts → dependencyResolutionManagement.repositories
maven("https://dl.cloudsmith.io/public/cometchat/cometchat/maven/")

// app/build.gradle.kts — repo/exclude/compileOptions are COHORT-NEUTRAL (the duplicate-class
// collision comes via chatuikit-core-android, which BOTH cohorts pull); only the artifact differs
configurations.all {
    // REQUIRED — without it the first build fails at dexing with ~40
    // "Duplicate class org.jetbrains.annotations.*" errors (docs getting-started-{kotlin,jetpack}).
    exclude(group = "org.jetbrains", module = "annotations-java5")
}

// gradle.properties — REQUIRED, both lines (why: dexing dup-class; references/troubleshooting.md):
//   android.useAndroidX=true   android.enableJetifier=true

dependencies {
    implementation("com.cometchat:chatuikit-kotlin-android:6.0.5")
    // implementation("com.cometchat:calls-sdk-android:5.0.4")   // only for voice/video
}
android {
    buildFeatures { viewBinding = true }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_11; targetCompatibility = JavaVersion.VERSION_11 }
}
// JVM 11 (Kotlin 2.2+ rejects kotlinOptions{}). Fully-qualified: a mid-file .kts import won't compile.
kotlin { compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_11) } }
```
**Theme kit views under a `CometChatTheme.DayNight`-derived theme — REQUIRED (Views), not cosmetic.**
Kit views resolve `?attr/cometchat*` at inflate time; outside such a theme the FIRST kit view crashes
(`IllegalArgumentException`/`InflateException` on `?attr/cometchatPrimaryColor` — verified on device).
**Greenfield** → re-parent app-wide: `<style name="AppTheme" parent="CometChatTheme.DayNight" />` +
`<application android:theme="@style/AppTheme">`. **Brownfield** (app HAS its own theme) → do NOT
re-parent (`CometChatTheme.DayNight` parents MaterialComponents, so Material3-only host attrs stop
resolving — you'd break their screens); scope a derived style to the chat Activities (manifest
`android:theme`) + `ContextThemeWrapper` for fragment/tab-embedded views — recipe: `kotlin-placement` Placement 2.

Compose cohort: swap the artifact for `com.cometchat:chatuikit-compose-android:6.0.5` and use `buildFeatures { compose = true }` + the Kotlin Compose plugin. **Build floors — all forced by the transitive `androidx.core:core:1.18.0` and all failing with the SAME opaque `checkDebugAarMetadata` error, so bump them together:** **minSdk 28 · compileSdk 36 · AGP ≥ 8.9.1 · Gradle ≥ 8.11 · Kotlin ≥ 2.1** (exact error strings + fixes in `-troubleshooting`; verified on device). `chatuikit-core-android` and `chat-sdk-android` arrive transitively — never add the UI Kit twice, and never mix a v5 `chat-uikit-android` into the tree (**version_conflict — STOP**).

## Setup & credentials (essentials — full detail: `references/setup-credentials.md`)
1. **Detect the project AND pick the cohort — never guess.** `npx @cometchat/skills detect --json`
   (or READ the gradle files). The signals are
   `android_variant` ∈ **`compose` · `views` · `mixed` · `unknown`** (both Groovy and Kotlin DSL):
   **`compose`** → use Compose, don't offer Views · **`views`** → use Views · **`mixed`/`unknown`**
   → **ASK and WAIT** (recommend Compose for greenfield). **Announce the cohort and why before
   writing code** — the cohorts are different artifacts that must not coexist, so it is the one
   choice the user cannot cheaply undo. If `existing_cometchat` is true, resolve `version_conflict`
   FIRST (v4/v5 kit present ⇒ STOP + offer `cometchat-android-v6-migration`). Decision table +
   signals: `references/setup-credentials.md` §1.
2. **Credentials — OFFER to fetch from the dashboard FIRST**, never default to "paste it yourself": (a) load the CometChat CLI on demand (`npx @cometchat/skills-cli@3 auth login`, `provision list --json` → ask which app, `provision use --app-id <id> --json`); or (b) manual paste from Dashboard → Your App → Credentials. Ask & wait — never guess.
3. **Write `app/src/main/assets/cometchat-settings.json`** (the file `initFromSettings` reads) and **gitignore it**:
```json
{ "appId": "APP_ID", "region": "REGION", "credentials": { "authKey": "AUTH_KEY" },
  "uiKit": { "subscribePresenceForAllUsers": true, "enableCalling": false } }
```

> ⚠️ **`enableCalling: true` and the calls artifact go together or not at all** — the flag without
> `com.cometchat:calls-sdk-android` crashes the app at launch. Why and symptoms: docs
> getting-started-{kotlin,jetpack} + calling-integration. Leave the flag `false` in an app without calling.

   `appId` + `region` required (else `ERR_SETTINGS_INVALID`); missing file → `ERR_SETTINGS_FILE_NOT_FOUND`. **Auth Key is dev-only** — omit it in release builds and log in with a server-minted token (`cometchat-android-v6-production`).

## Integration ordering (BAKED — invariant)
Docs warning, verbatim: *"`init()` must resolve before you call `login()`. Calling `login()` before init completes will fail silently."*

```kotlin
import com.cometchat.chat.core.CometChat
import com.cometchat.chat.exceptions.CometChatException
import com.cometchat.chat.models.User
import com.cometchat.uikit.core.CometChatUIKit

// initFromSettings reads assets/cometchat-settings.json, persists integrationSource="ai-agent"
// for telemetry attribution, and auto-inits the Calls SDK when uiKit.enableCalling is true.
// Do NOT default to the classic UIKitSettingsBuilder + init() — it loses attribution.
CometChatUIKit.initFromSettings(this, object : CometChat.CallbackListener<String>() {
    override fun onSuccess(result: String) {                     // init resolved — only now login
        if (CometChatUIKit.getLoggedInUser() == null) {
            CometChatUIKit.login(uid, object : CometChat.CallbackListener<User>() {
                // ⚠️ inside this object, `this` is the LISTENER, not the Activity — navigating
                // with `Intent(this, …)` does not compile. Qualify it: `this@YourActivity`.
                override fun onSuccess(user: User) {
                    startActivity(Intent(this@MainActivity, ConversationActivity::class.java)); finish()
                }
                override fun onError(e: CometChatException) { /* render an error state */ }
            })
        } else { /* session already live — unlock */ }
    }
    override fun onError(e: CometChatException?) { /* render an error state; do NOT open chat */ }
})
```
Init once (Application or a splash gate), never per Activity. **Which UID?** `login()` needs a user that ALREADY exists — never invent one; take it from Dashboard → Users (fresh apps seed `cometchat-uid-1…`). Prod → `loginWithAuthToken`. Detail: `references/lifecycle.md`.

## Sizing — fill the parent, handle insets and the keyboard
The kit fills the box you give it — a collapsed surface is a HOST sizing defect, never a kit bug. Four invariants (full recipe: `references/layout.md`):
- **Fill**: `match_parent` / `0dp`+`layout_weight` (Views) — never `wrap_content` for a list or the chat surface.
- **Insets**: `enableEdgeToEdge()` **plus** consuming the insets. `enableEdgeToEdge()` ALONE draws
  the kit under the status bar — the toolbar title then collides with the clock (verified on device).
  Give the layout root an id and pad it:
  ```kotlin
  ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.root)) { v, insets ->
      val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
      val ime  = insets.getInsets(WindowInsetsCompat.Type.ime())      // message screen only
      v.setPadding(bars.left, bars.top, bars.right, maxOf(bars.bottom, ime.bottom))
      insets
  }
  ```
- **Keyboard**: `windowSoftInputMode="adjustResize"` (Views) so the composer stays visible while typing.
- **Embedded in a host you do NOT own** (a tab, a fragment, someone else's container): set the
  listener on YOUR subtree root, not the Activity root, and skip `enableEdgeToEdge()` — the host
  owns the window. Still consume insets: skipping them because "the host owns it" puts the toolbar
  back under the clock.
- **No load-transition reflow**: the surface is full-size from frame 1; the kit renders its own loading/empty state inside it.

## Component / API map (BAKED closed list — from `catalogs/android-v6.json`)
The closed list of shipped components lives in `references/component-props.md`
(and `catalogs/android-v6.json` is the oracle). Emit ONLY symbols that appear there.

## Import paths
`…kotlin.presentation.<area>.ui.<Component>` — **except the 3 calling components (no `.ui`)** and
formatters (`…kotlin.shared.formatters.*`). Full table: `references/component-props.md`.

## Callback names — Views uses `setOnX(...)`, Compose uses `onX =`
Same component, same intent, different wiring. Full signature table (verified vs 6.0.5):
`references/component-props.md` § Callback shapes.

> ⚠️ **Docs drift — trust `references/component-props.md`, not the docs pages** for callback
> shapes (the 3-arg thread callback and `setParentMessage` on the list are both wrong upstream).

## Golden path — the production-ready core surface (Kotlin XML Views)
The default for an unscoped "add chat". **One screen per Activity with a real back stack** — never a web-style two-pane split. Host Activities must be lifecycle-aware (`AppCompatActivity`/`ComponentActivity`/`FragmentActivity`) and manifest-registered.

```kotlin
// ConversationActivity.kt — the list, wired to open the message screen
class ConversationActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_conversation)          // hosts CometChatConversations at match_parent

        val conversations = findViewById<CometChatConversations>(R.id.conversations)
        conversations.setTitle("Chats")
        conversations.setOnItemClick { conversation ->
            val intent = Intent(this, MessageActivity::class.java)
            when (val entity = conversation.conversationWith) {
                is User -> intent.putExtra("user", entity)
                is Group -> intent.putExtra("group", entity)
            }
            startActivity(intent)
        }
        conversations.setOnSearchClick { startActivity(Intent(this, SearchActivity::class.java)) }
    }
}
```
```kotlin
// MessageActivity.kt — header + list + composer, all bound to the SAME target
class MessageActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_message)               // vertical LinearLayout, list = 0dp + weight 1

        val header = findViewById<CometChatMessageHeader>(R.id.message_header)
        val list = findViewById<CometChatMessageList>(R.id.message_list)
        val composer = findViewById<CometChatMessageComposer>(R.id.message_composer)

        val user = intent.getParcelableExtra<User>("user")
        val group = intent.getParcelableExtra<Group>("group")
        user?.let { header.setUser(it); list.setUser(it); composer.setUser(it) }
        group?.let { header.setGroup(it); list.setGroup(it); composer.setGroup(it) }

        header.setBackButtonVisibility(View.VISIBLE)   // the callback is inert without this
        header.setOnBackPress { finish() }
        list.setOnThreadRepliesClick { parent ->                 // ONE arg (verified vs 6.0.5)
            startActivity(Intent(this, ThreadActivity::class.java).apply {
                putExtra("raw_json", parent.rawMessage.toString())
                user?.let { putExtra("user", it) }; group?.let { putExtra("group", it) }
            })
        }
    }
}
```

### The core surface is FOUR things, not two
`contracts.android-v6.json` → `core-chat-surface` mandates all four by default; a list ↔ message screen is **half the surface**:

| Capability | Component | Wire |
|---|---|---|
| conversations | `CometChatConversations` | `setOnItemClick` |
| messages | `CometChatMessageHeader` + `List` + `Composer` | `setUser`/`setGroup` + `setOnBackPress` |
| **threaded replies** | `CometChatThreadHeader` | `setOnThreadRepliesClick` → push a thread Activity |
| **search** | `CometChatSearch` | `setOnSearchClick` → push a search Activity (global), and the in-chat case scoped with `setUid`/`setGuid` |

On Android both are **pushed screens**, not side panels. The callbacks above are only *entry points* — the pushed screens are where the mandated components render. Emit both, or the surface has tap targets that lead nowhere:

```kotlin
// ThreadActivity.kt — what setOnThreadRepliesClick pushes to.
// header takes the parent MESSAGE; list + composer take the parent message ID (Long).
val parent = BaseMessage.processMessage(JSONObject(intent.getStringExtra("raw_json")!!))
threadHeader.setParentMessage(parent)
threadList.setParentMessageId(parent.id)
threadComposer.setParentMessageId(parent.id)
// the thread list/composer ALSO need the conversation target, or replies silently never send:
user?.let { threadList.setUser(it); threadComposer.setUser(it) }
group?.let { threadList.setGroup(it); threadComposer.setGroup(it) }
// CometChatThreadHeader is DISPLAY-ONLY (no callbacks) → renders no back control; the HOST owns it
// here. Give the screen a toolbar back action (or say plainly it relies on system back) — a thread
// with no way out is a dead end.
```
`SearchScope` is REQUIRED for `setSearchIn` and lives in **`com.cometchat.uikit.core.constants`** —
import it explicitly; it is not re-exported from the component's package.
```kotlin
// SearchActivity.kt — global search; for IN-CHAT search scope it to the open conversation.
val search = findViewById<CometChatSearch>(R.id.search)
search.setSearchIn(listOf(SearchScope.CONVERSATIONS, SearchScope.MESSAGES))
user?.let { search.setUid(it.uid) }                    // in-chat scoping (omit for global)
group?.let { search.setGuid(it.guid) }
// CometChatSearch renders its OWN back arrow — without this it is inert (wire-or-hide).
search.setOnBackPressListener { finish() }
// Results must GO somewhere, carrying the SAME "user"/"group" extras the message screen reads.
// Passing the Conversation/BaseMessage itself navigates but never calls setUser/setGroup, so the
// screen loads forever ("no User/Group was set" — references/troubleshooting.md).
search.setOnConversationClick { openChat(it.conversationWith) }   // already the OTHER party
search.setOnMessageClick { m ->
    // group → the group; 1:1 → whoever is NOT me
    openChat(if (m.receiverType == CometChatConstants.RECEIVER_TYPE_GROUP) m.receiver
             else if (m.sender.uid == CometChatUIKit.getLoggedInUser()?.uid) m.receiver else m.sender)
}
// same when(entity) the conversations tap uses above — never push a screen with no target
private fun openChat(e: AppEntity?) = when (e) {
    is User -> startActivity(Intent(this, MessageActivity::class.java).putExtra("user", e))
    is Group -> startActivity(Intent(this, MessageActivity::class.java).putExtra("group", e))
    else -> Unit
}
```
Reuse existing navigation/theme/auth; add files + wiring only. Leave header call buttons and composer attach/emoji/voice as built-in defaults. Do NOT add tabs / detail screens / call logs / incoming call (`placement` growths) or gated extensions/AI unless asked — **the thread and search screens ARE the default.**

> **Jetpack Compose cohort:** the same four capabilities as composable params (`onItemClick =`, `onBackPress =`, `onThreadRepliesClick =`) inside a `NavHost` + `Scaffold` + `imePadding()`. Compose recipes SHIP — use `cometchat-android-v6-compose-{components,placement,customization}`; fall back to `references/docs-map.md` for long-tail params.
>
> ⚠️ **Compose "Auto — follow OS" (the default theming) is a CORE obligation, NOT automatic.** Unlike
> Views (`CometChatTheme.DayNight`) and iOS, the Compose kit ignores the device dark setting unless you
> wrap the gate + NavHost + every kit screen in `CometChatTheme(colorScheme = if (isSystemInDarkTheme())
> darkColorScheme() else lightColorScheme()){ … }` (from `com.cometchat.uikit.compose.theme.*`) — no
> wrapper ⇒ light defaults (verified; RULES.md §Ordering-invariants). This bare follow-OS wrapper is
> core; brand tokens are `cometchat-android-v6-compose-customization` §Theming.

## Deep references (load only when the task needs them)
- `references/setup-credentials.md` — detect, cohort, version_conflict, the CLI credential fetch, the settings file, UID rules.
- `references/lifecycle.md` — where to init, the login guard, auth-token prod path, logout, config changes.
- `references/layout.md` — the ONE mobile sizing standard (fill · insets · IME · no reflow · scroll containment).
- `references/component-props.md` — baked per-cohort signatures for the four drop-ins + the request-builder hooks.
- `references/docs-map.md` — intent → the exact docs `.md` twin (component table + SDK section + task guides).
- `references/anti-patterns.md` — the real-bug list (hardcoded creds, login-before-init, leaked listeners, wrap_content collapse, dead affordances, mixed cohorts).
- `references/troubleshooting.md` — symptom → cause → fix, the first stop when an integration renders wrong.

## Common pitfalls
version_conflict (a v5 `chat-uikit-android` in the tree) · both cohorts installed · minSdk below 28 · credentials hardcoded instead of the gitignored settings file · classic `init()` instead of `initFromSettings` · login (or UI) before init's `onSuccess` · `wrap_content` on the chat surface · composer hidden by the IME · thread screen missing the `user`/`group` target (replies never send) · trusting the 3-arg thread callback from the docs.

## Verify it works
Build + run → logcat shows init `onSuccess` then login `onSuccess` → conversations renders full-size; tap a conversation → the message screen loads for that user/group and messages send/receive; **"reply in thread" opens the thread screen and back returns**; the search entry point opens a real search screen and returns; the composer stays visible with the keyboard open; system bars don't overlap header/composer. Blank/stuck ⇒ something rendered before init resolved, wrong Region, or the Cloudsmith repo is missing. Compile gate: `./gradlew :app:assembleDebug   # in YOUR app`.

## Explain what you built (REQUIRED close)
Tell the user briefly: **(1) what I wired** (3–5 bullets, NAME the files); **(2) decisions & why**, flagging dev-only AS dev-only (Auth Key → server token for prod; the `<uid>`; the cohort); **(3) what I did NOT touch** (additive — navigation/auth/styles intact). Then **offer these THREE options and WAIT — do NOT auto-continue:**
- **① Add another feature** → check what's already wired, ASK which Dashboard extensions are enabled, suggest 3–4 gaps (calls · push · AI · notification feed · polls/stickers/translation). **Never suggest reactions or mentions — ON by default in v6.** → `cometchat-android-v6-features` / `-calls` / `-push`.
- **② Customize theming** → ask for brand color / light-dark / Material3 design system → `cometchat-android-v6-{kotlin,compose}-customization`.
- **③ Test it manually** → hand it back so they run it on a device.
