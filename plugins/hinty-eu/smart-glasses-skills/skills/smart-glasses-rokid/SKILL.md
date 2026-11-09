---
name: smart-glasses-rokid
description: Rokid Glasses apps driven from an Android phone with Rokid's public CXR-L SDK - authorise once in the Hi Rokid companion app (Global or China build), open a custom view on the green display and update its text, stream the glasses microphone as 16 kHz PCM, survive pauses for the Rokid assistant, and fall back to phone notifications mirrored by Hi Rokid (also on iPhone) when the SDK path is not an option. Covers Maven setup, CXR-L versus CXR-M and CXR-S, R8 rules, iOS notes, input limits and real community issues. Use when the user mentions Rokid, Rokid Glasses, RV101, CXR, CXR-L, CXR-M, CXR-S, Hi Rokid, Rokid AI App or YodaOS-Sprite and wants a phone app to put text on the glasses or read their microphone. Not for apps that run on the glasses themselves (see RealComputer/GlassKit or Rokid's bare-metal docs), not for AIUI agents (use the yodaos-project/aiui skill), and not for Rokid Max or other USB-C display glasses (use the smart-glasses skill).
license: Apache-2.0
metadata:
  version: "1.0.1"
  last-updated: "2026-11-09"
---

# Rokid Glasses from a phone (CXR-L)

Last checked: 2026-11-09. Verification: docs-only (no hardware test yet). SDK names, roles and versions were read
from Rokid's SDK overview ([developerdoc.rokid.com/sdk](https://developerdoc.rokid.com/sdk?lang=en); the English and
Chinese pages both show CXR-L 1.1.2 dated 2026-09-08), the Rokid Maven metadata, CocoaPods trunk, and the public
signatures of the published `client-l` 1.1.2 artifact. The snippets were written for this skill and not compiled here.
Rokid publishes no licence for CXR-L, so this skill only describes the API in its own words and links to Rokid.

## Decide first

Rokid Glasses (retail model RV101) are display glasses: monochrome green micro-LED waveguides for both eyes,
black is transparent. They also have a camera, four microphones, speakers and a temple touchpad, and run
YodaOS-Sprite, an Android-based OS (Android 12 by community measurement). The phone app **Hi Rokid** owns the
Bluetooth link. Your phone app never talks to the glasses directly with CXR-L: every call goes through Hi Rokid.

Rokid's SDKs (as of 2026-11-08, SDK overview page):

| SDK | Runs on | Needs Hi Rokid | Access | Latest |
|---|---|---|---|---|
| **CXR-L** (`com.rokid.cxr:client-l`) | phone, Android + iOS | yes, it is the proxy | public | 1.1.2 (2026-09-08); iOS `RGCxrClient` 1.1.1 on CocoaPods trunk (1.1.1.1 in Rokid's sample project) |
| CXR-M (`com.rokid.cxr:client-m`) | phone, Android | no, direct link | business only (`Glasses.BD@rokid.com`) | 1.1.0 on the portal, 1.2.2 on Maven |
| CXR-S (`com.rokid.cxr:cxr-service-bridge`) | glasses, inside your glasses APK | used with CXR-L `CUSTOM_APP` | public, documented inside the CXR-L docs | 1.8 on Maven (2026-10-30) |
| Bare-metal development | glasses (AOSP) | no | public | 1.0.0 (2026-06-05) |

CXR-S has no entry of its own on the overview: it is mentioned only inside the CXR-M entry ("can be used with the
on-device CXR-S SDK") and in a CXR-L changelog line (1.0.3: glasses-side CXR-S integration merged into the CXR-L docs).

The overview says CXR-M "cannot run alongside" the Rokid AI App on the same phone, and it needs business onboarding.
For an app that ordinary owners install next to Hi Rokid, **CXR-L is the only option**.

| You want | Use |
|---|---|
| Text on the glasses from your Android app, no glasses code | CXR-L `CUSTOM_VIEW` (this skill) |
| Touchpad gestures, your own UI or anything beyond a text layout | CXR-L `CUSTOM_APP` plus your APK on the glasses (CXR-S), see [input.md](references/input.md) |
| An app that lives on the glasses | Not this skill: [RealComputer/GlassKit](https://github.com/RealComputer/GlassKit) (`npx skills add RealComputer/GlassKit`) or Rokid's bare-metal docs |
| An agent inside Hi Rokid's Agent Store | Not this skill: Rokid AIUI, `npx skills add yodaos-project/aiui` |
| iPhone | CXR-L iOS (`RGCxrClient`, see [setup.md](references/setup.md#ios)) or notifications |
| Zero SDK work, Android or iPhone | A normal phone notification mirrored by Hi Rokid, [notifications.md](references/notifications.md) |
| Spoken output | Text-to-speech on the phone; the glasses play phone audio over Bluetooth |
| Teleprompter, translation or AI scenes built by Rokid | CXR-M only (business contract); not reachable from CXR-L |

In the display-text ladder of the `smart-glasses` skill, Rokid Glasses support rung 1 (**Vendor SDK**, CXR-L),
rung 4 (**phone notification mirrored by the companion app**) and rung 5 (**voice in the ear**).

A newer model, Rokid Glasses 2 (480x380, 25 degree field of view), was announced in China on 2026-10-27 and goes on
sale there on 2026-11-11, with no sale date outside China
([Notebookcheck, 2026-10-28](https://www.notebookcheck.net/Rokid-Glasses-2-launch-with-upgraded-design-bigger-battery-and-Dolby-Audio-support.1435436.0.html),
press). Whether CXR-L 1.1.2 drives it is unverified.

## Setup in brief

Details, versions and the R8 rules: [references/setup.md](references/setup.md).

```kotlin
// settings.gradle.kts: only the com.rokid.cxr group comes from Rokid's repository
dependencyResolutionManagement {
    repositories {
        google()
        mavenCentral()
        exclusiveContent {
            forRepository { maven { url = uri("https://maven.rokid.com/repository/maven-public/") } }
            filter { includeGroup("com.rokid.cxr") }
        }
    }
}
// app/build.gradle.kts
dependencies { implementation("com.rokid.cxr:client-l:1.1.2") } // pin it, never a -SNAPSHOT
```

- `minSdk` 28. Native libraries ship for `arm64-v8a` and `armeabi-v7a` only, so creating a session on an x86
  emulator throws `UnsatisfiedLinkError`. Catch `Throwable` around `create()`.
- The library merges `<queries>` for both Hi Rokid packages into your manifest.
- The library's consumer R8 rules remove **your** `Log.d` and `Log.v` calls in release builds. Log glasses state with `Log.i`.
- The user needs Hi Rokid installed, signed in, and the glasses connected **inside Hi Rokid** (pairing in Android
  Bluetooth settings is not enough). client-l 1.1.2 checks for Hi Rokid versionCode 10110000 (1.11.0) or newer.
- No app key, client secret or Rokid registration is documented for Android (as of 2026-11-08).
- Rokid publishes no licence for the SDK: none in the docs, none in the client-l 1.1.2 POM (checked 2026-11-09).
  Depend on the Maven artifact and do not copy SDK files,
  `.aar` contents or Rokid's sample code into your repository; write your own calls against the documented API.

## The core flow

1. Check that Hi Rokid is installed and new enough.
2. Ask Hi Rokid for permission (`requestAuthorization`). The first time Hi Rokid shows a consent screen; later calls
   return silently. Call it again after every process start: it also decides whether the Global or the China
   build of Hi Rokid serves the session.
3. Create a `CUSTOM_VIEW` session with your initial view JSON, add callbacks **before** `connect(token)`.
4. Wait for `onSessionStarted`. `connect()` returning does not mean the view is up.
5. Replace text with `customViewUpdate`. Keep the latest text and re-send it on start and resume.
6. Optional: `startAudioStream()` for the glasses microphone ([audio.md](references/audio.md)).
7. `close()` the session when done. A closed session cannot reconnect; create a new one.

```kotlin
import android.app.Activity
import android.content.Context
import android.content.Intent
import android.os.Handler
import android.os.Looper
import android.util.Log
import com.rokid.cxr.session.*

class RokidText(private val app: Context, private val onState: (String) -> Unit) {
    private val manager = CxrSessionManager.getInstance(app.applicationContext)
    private val main = Handler(Looper.getMainLooper())
    private var token: String? = null          // memory only, re-authorise after a process restart
    private var session: CxrSession? = null
    private var title = ""
    private var body = ""

    fun companionOk(): Boolean = manager.checkRokidAppCompatibility(app) is RokidAppStatus.Compatible

    fun authorize(activity: Activity) {
        // MEDIA for the view; add GlassPermission.MICROPHONE if you stream audio.
        // unverified: which scope the custom view strictly needs; the docs list CAMERA, MICROPHONE, MEDIA, DEVICE_MANAGE
        manager.requestAuthorization(activity, listOf(GlassPermission.MEDIA)) { r ->
            main.post {
                token = r.token?.takeIf { r.isSuccess && it.isNotEmpty() }
                onState(if (token != null) "authorized" else "auth_failed:${r.errorCode}")
            }
        }
        // If neither Hi Rokid build passes the version check the callback may never come: time out yourself.
    }

    /** Call from your Activity's onActivityResult for every request code while authorising. */
    fun onActivityResult(resultCode: Int, data: Intent?) {
        manager.parseAuthorizationResult(resultCode, data ?: Intent())
    }

    fun start() {
        val t = token ?: return onState("not_authorized")
        if (session != null) return
        val s = try {
            manager.create(SessionConfig(
                sessionType = SessionType.CUSTOM_VIEW,
                aiInterceptMode = AiInterceptMode.ALLOW_WITH_PAUSE,
                timeouts = SessionTimeouts(),
                viewData = TextCard.view(title, body),   // compact JSON, see display.md
            ))
        } catch (e: Throwable) {                         // a session is still open, or no ARM native libs
            Log.i("RokidText", "create failed: $e"); onState("create_failed"); return
        }
        session = s
        s.addLifecycleCallback(lifecycle)                // before connect
        s.connect(t)
        onState("connecting")
    }

    fun show(newTitle: String, newBody: String) {
        title = newTitle; body = newBody
        val s = session ?: return
        if (s.state != SessionState.Started) return      // sent again in onSessionStarted / onSessionResumed
        val r = s.customViewUpdate(TextCard.update(title, body))
        if (!r.isSuccess) Log.i("RokidText", "update ${r.code} ${r.message}")
    }

    fun stop() {
        session?.let { it.removeLifecycleCallback(lifecycle); it.close() }
        session = null
        onState("idle")
    }

    private val lifecycle = object : ISessionLifecycleCbk {
        override fun onConnectResult(success: Boolean, errorCode: SessionErrorCode?) {
            if (success) return
            if (errorCode == SessionErrorCode.NOT_AUTHENTICATED || errorCode == SessionErrorCode.TOKEN_EXPIRED) token = null
            session = null
            onState("connect_failed:$errorCode")
        }
        override fun onSessionStarted() { onState("started"); show(title, body) }
        override fun onSessionPaused(reason: PausedReason) = onState("paused:$reason")   // AI_ASSIST, BT_DISCONNECTED
        override fun onSessionResumed() { onState("started"); show(title, body) }
        override fun onSessionTerminating(reason: TerminatingReason, gracePeriodMs: Long) = onState("terminating:$reason")
        override fun onSessionClosed(reason: CloseReason) {
            session = null
            if (reason == CloseReason.LINK_LOST || reason == CloseReason.CHAIN_TORN) token = null
            onState("closed:$reason")                    // GLASSES_EXIT = the wearer left your view
        }
    }
}
```

`TextCard` builds the view JSON with `org.json`; it is in [display.md](references/display.md). Lifecycle callbacks
arrive on the main thread; audio may not.

What each state means for your app:

| Event | Meaning | Do |
|---|---|---|
| `onConnectResult(false, NOT_AUTHENTICATED / TOKEN_EXPIRED)` | token rejected | drop the token, `requestAuthorization` again |
| `onConnectResult(false, BT_NOT_CONNECTED / LINK_NOT_READY)` | glasses not connected in Hi Rokid | ask the user to open Hi Rokid |
| `onSessionPaused(AI_ASSIST)` | the wearer started the Rokid assistant, your view is hidden | keep state, wait |
| `onSessionResumed()` | view is back | re-send the latest text |
| `onSessionClosed(GLASSES_EXIT)` | the wearer closed your view on the glasses | respect it; reopen only on a new user action or new content |
| `onSessionClosed(LINK_LOST / CHAIN_TORN)` | link broken, token void | re-authorise, then a new session |

Capability calls before `Started` fail with `SESSION_NOT_STARTED`, during `Paused` with `SESSION_PAUSED`. Only one
session can be active per manager; `create()` throws while the old one is alive.

## Showing text well

Summary of [display.md](references/display.md):

- The view is a JSON tree of `LinearLayout`, `RelativeLayout`, `TextView` and `ImageView`; `id` goes inside `props`.
  Send it as **compact single-line JSON**: indented JSON fails silently (a comment in Rokid's sample).
- Updates are an array of `{"action":"update","id":...,"props":{...}}` with only the changed keys.
- Plan for a 480 px wide portrait area. Use black backgrounds and bright green text, `textSize` 16sp or more.
- Coalesce updates (a few per second). Community reports on some Global Hi Rokid builds say `customViewUpdate`
  returns success without redrawing; keep a "recreate the session" fallback behind a switch.

## Input, microphone, iPhone

- **Taps on a custom view do not reach the phone.** You do get pause, resume, close, wearing and screen events.
  Full touchpad events need your own APK on the glasses. See [input.md](references/input.md).
- **Glasses microphone:** `startAudioStream()` delivers PCM 16 kHz, mono, 16-bit, once the session is `Started` and
  `GlassPermission.MICROPHONE` was granted. See [audio.md](references/audio.md).
- **iPhone:** CXR-L iOS exists (`RGCxrClient` 1.1.1 on CocoaPods trunk; Rokid's sample project pins 1.1.1.1 from
  Rokid's private specs source, or uses the source modules bundled in the sample), with the same JSON and state
  model and an auth round trip through Hi Rokid by URL scheme. Notifications are the low-effort path. See
  [setup.md](references/setup.md#ios) and [notifications.md](references/notifications.md).

## Live captions

With the shared caption server of the `smart-glasses-live-captions` skill, the Rokid client:

- sends `{"type":"hello","target":"rokid","lines":3,"cols":22}` (3 lines of 24sp text, about 22 Latin characters
  each: an estimate, unverified on hardware; `examples/live-captions` uses the same numbers);
- on each `caption` message replaces the body text, keeps only the last lines that fit, and sends at most one
  `customViewUpdate` every 250 ms (also an estimate; the newest partial result wins); a caption marked
  `"repeat":true` is shown again, not appended a second time;
- on `clear` sends empty strings;
- maps shared actions (`repeat`, `skip`, `hide`) to buttons in the phone app, because glasses taps do not arrive.

## Testing without hardware

There is no CXR-L simulator (none found in the docs as of 2026-11-08). Put the class above behind your own interface,
unit-test the JSON builders and the line fitting, and drive the rest of the app from a fake. The ARM-only native
libraries mean the real path cannot run on an x86 emulator. AIUI Studio's web simulator is for AIUI agents only.

## Publishing

- Android: ship through Google Play or any store like a normal app. The CXR-L docs describe no Rokid review and no
  app key; the user grants access inside Hi Rokid. Community projects report a one-time "unverified app"
  confirmation in Hi Rokid.
- iOS: the CXR-L docs ask for a registered Rokid developer account and a bundle ID plus URL scheme; one community
  iOS project reports that auth worked without registration. Unverified either way.
- AIUI agents go through review in the Hi Rokid Agent Store; that is a different product path.

## Pitfalls (most common first)

1. Only `Log.i` survives release builds next to this SDK (consumer R8 rules).
2. Re-authorise after each process start, even with a stored token, before `connect`.
3. If both Hi Rokid builds are installed and the China build is new enough, the SDK picks the China build.
4. Hi Rokid must keep running. Aggressive battery managers on some phones kill it and the link drops.
5. `customViewUpdate` success does not prove a redraw on every Global build.
6. The Maven `1.2.X-SNAPSHOT` (updated 2026-11-05) is a moving target; stay on 1.1.2.

More, with links: [references/troubleshooting.md](references/troubleshooting.md).

## References

- [setup.md](references/setup.md) - Maven, artifacts, manifest, R8, Hi Rokid Global vs China, iOS, credentials.
- [display.md](references/display.md) - view JSON, text layout limits, update pacing, teleprompter-like flows.
- [audio.md](references/audio.md) - glasses microphone stream, format, routing, speakers.
- [input.md](references/input.md) - which events reach a phone app and how to get real touchpad events.
- [notifications.md](references/notifications.md) - the no-SDK fallback on Android and iPhone, timing quirks.
- [troubleshooting.md](references/troubleshooting.md) - real issues and fixes.

## Official resources

- SDK overview: https://developerdoc.rokid.com/sdk?lang=zh
- CXR-L documentation (Chinese): https://custom.rokid.com/prod/rokid_web/84feb39f8ef141b0ad0326f902ab881f/pc/cn/fa92e9303bc848e6b4a20c062f2c792b.html
- Maven repository: https://maven.rokid.com/repository/maven-public/
- Community issue tracker: https://github.com/rokid/community/issues
- AIUI (agents on the glasses): https://github.com/yodaos-project/AIUI
- Hi Rokid: [Google Play](https://play.google.com/store/apps/details?id=com.rokid.sprite.global.aiapp), [App Store](https://apps.apple.com/us/app/id6749669942)
