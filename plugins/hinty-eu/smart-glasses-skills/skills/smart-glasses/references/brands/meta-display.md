# Meta Ray-Ban Display + Meta Neural Band (Device Access Toolkit Display, Web Apps)

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). Code was written against the public API
reference and has not been compiled or run on glasses.

## At a glance
- Display: 600x600, full colour, right eye only, about 20 degrees FOV, 30 Hz content, 30 to 5,000 nits adaptive
  (600x600: "The display resolution is 600x600" in
  [Meta's DAT display overview](https://wearables.developer.meta.com/docs/develop/dat/display-overview/), official; the
  rest from [Road to VR](https://roadtovr.com/meta-ray-ban-smart-glasses-display-price-release-date-specs/), press).
  Black is transparent.
- How your app puts text on it: rung 1 (DAT Display capability from your Android or iOS app) or rung 2 (a Web App:
  an HTTPS page in the glasses' browser). Rung 5 (TTS in the ear) as fallback. Rung 4 is not a path to plan on: at
  launch only built-in messaging showed; press reports a later all-or-nothing phone notification mirror
  ([UploadVR, 2026-09-27](https://www.uploadvr.com/meta-ray-ban-display-gets-new-features-online-ordering-international-launch/));
  Meta announced phone notifications with per-app control "coming soon" on 2026-09-23
  ([Meta](https://about.fb.com/news/2026/09/new-features-for-meta-ray-ban-display-navigation-hologram/)). Whether
  third-party notifications reach every wearer today is unverified (2026-11-08).
- Input: Neural Band (EMG wristband) and temple touchpad. DAT: button taps come back as callbacks. Web Apps: `keydown`
  `ArrowUp/Down/Left/Right` and `Enter` move focus and press buttons (spatial navigation); Back is `history.back()`.
- Microphone for your app: DAT only, over Bluetooth HFP, beamformed to the wearer, and opening it ends the Display
  session (as of 2026-11-08; Meta's fix for Display comes "at a later date"). Web Apps: no microphone, no camera. Capture audio on the phone.
- Speaker: open-ear. DAT has no audio API (use A2DP). Web Apps: `speechSynthesis` (one `en-US` voice) and Web Audio.
- Phones: DAT 1.0.1 needs Android 10+ (Kotlin 2.2+) or iOS 17.2+ (Xcode 26.4+), Meta AI app V292+, glasses V128+.
  Web Apps run on the glasses (glasses v125+, Meta AI app v272+).
- Publishing to everyone today: no, on either path (as of 2026-11-08, see Publishing). Sold and supported only in the
  US, CA, UK, FR, DE, IT ([Meta help center](https://www.meta.com/help/ai-glasses/4961066940605960/), 2026-11-08).
- Test without hardware: DAT MockDeviceKit display preview; Chrome extension "Meta Ray-Ban Display Simulator" (both).
- Official agent skill: `npx skills add meta/meta-wearables-dat-android` / `npx skills add meta/meta-wearables-dat-ios`
  (skills.sh); Meta's READMEs document `claude plugin marketplace add facebook/meta-wearables-dat-android` +
  `claude plugin install mwdat-android@mwdat-android-marketplace` (iOS: `-ios`, `mwdat-ios`; `facebook/` redirects to
  `meta/`). Web Apps (not on skills.sh):
  `/plugin marketplace add https://github.com/meta/meta-wearables-webapp` + `/plugin install meta-wearables-webapp@meta-wearables`.
  Docs MCP: `https://mcp.developer.meta.com/wearables` over HTTP, no auth. Meta's `dat-docs-mcp` skill says the
  `mwdat-android` / `mwdat-ios` plugin registers it in Claude Code with no separate setup
  ([skill](https://github.com/meta/meta-wearables-dat-android/tree/main/plugins/mwdat-android/skills/dat-docs-mcp),
  checked 2026-11-09). Without the plugin, our own command (not from Meta's docs):
  `claude mcp add --transport http wearables-dat https://mcp.developer.meta.com/wearables`.
  **For SDK details install the official skill**; this file covers cross-brand decisions.

## Getting text on the display

| | DAT Display (rung 1) | Web App (rung 2) |
|---|---|---|
| Code runs | In your phone app; the SDK sends layouts over Bluetooth | In Chromium on the glasses |
| Caption text from | Phone mic and your STT inside the app | Your server via `fetch` / WebSocket (glasses Wi-Fi or tether) |
| UI | FlexBox, Text, Button, Image, Icon, Video; each send replaces the screen | Any HTML/CSS, 600x600 at DPR 1, responsive |
| Who can use it today | Invited Beta testers or Developer Mode users | Developer Mode users who add your URL |
| Main risks | HFP and Back end the session, panel sleeps | Hidden page suspends timers, slow link, eligibility |

Pick DAT when your phone app already owns audio and STT. Pick a Web App for the fastest prototype or when one page
should also serve other web-capable glasses.

### DAT Display: flow and minimal Kotlin
1. Maven Central: `com.meta.wearable:mwdat-core:1.0.1`, `mwdat-display:1.0.1`, debug-only `mwdat-mockdevice:1.0.1`.
   No token since 2026-09-15; the GitHub Packages repo (it needed a GitHub token, versions before 0.7.0) is obsolete
   ([announcement](https://github.com/meta/meta-wearables-dat-android/discussions/180)).
2. Manifest meta-data `com.meta.wearable.mwdat.APPLICATION_ID` and `CLIENT_TOKEN`: `0` in Developer Mode, Developer
   Center values for Beta. iOS: `MWDAT` dict (`AppLinkURLScheme`, `MetaAppID`, `ClientToken`, `TeamID`), HTTPS
   Universal Link callback for Beta.
3. `BLUETOOTH_CONNECT` before `Wearables.initialize(context)` (once), `Wearables.startRegistration(activity)`, wait for
   `RegistrationState.REGISTERED`. Start the session from a user action, add Display after `STARTED`.

```kotlin
import com.meta.wearable.dat.core.Wearables
import com.meta.wearable.dat.core.selectors.AutoDeviceSelector
import com.meta.wearable.dat.core.session.DeviceSession
import com.meta.wearable.dat.core.session.DeviceSessionState
import com.meta.wearable.dat.display.Display
import com.meta.wearable.dat.display.addDisplay
import com.meta.wearable.dat.display.types.DisplayState
import com.meta.wearable.dat.display.views.* // ButtonStyle, FlexBoxBackground, TextColor, TextStyle
import kotlinx.coroutines.*

// Precondition: Wearables.initialize(...) succeeded and registrationState is REGISTERED.
class CaptionDisplay(private val scope: CoroutineScope, private val onError: (String) -> Unit) {
    private var session: DeviceSession? = null
    private var display: Display? = null
    fun start() { // call from a button: the wearer must start display sessions
        if (session != null) return
        Wearables.createSession(AutoDeviceSelector(filter = { it.isDisplayCapable() })).fold(
            onSuccess = { s ->
                session = s
                scope.launch { s.errors.collect { onError(it.description) } }
                scope.launch {
                    s.state.collect { st ->
                        if (st == DeviceSessionState.STARTED && display == null) {
                            s.addDisplay().fold(onSuccess = { display = it }, onFailure = { e, _ -> onError(e.description) })
                        }
                        if (st == DeviceSessionState.STOPPED) { display = null; session = null } // terminal
                    }
                }
                s.start() // subscribe first, then start
            },
            onFailure = { e, _ -> onError(e.description) }, // NO_ELIGIBLE_DEVICE, DAT_APP_ON_THE_GLASSES_UPDATE_REQUIRED
        )
    }

    // Sends the whole screen; previous content and its click handlers are replaced.
    suspend fun show(previous: String, current: String, onHide: () -> Unit) {
        val d = display?.takeIf { it.state.value == DisplayState.STARTED } ?: return
        d.sendContent {
            flexBox(gap = 8, padding = 24, background = FlexBoxBackground.CARD) {
                if (previous.isNotEmpty()) text(previous, style = TextStyle.BODY, color = TextColor.SECONDARY)
                text(current, style = TextStyle.BODY)
                button(label = "Hide", style = ButtonStyle.OUTLINE, onClick = onHide) // onHide: d.clearDisplay()
            }
        }.onFailure { e, _ -> onError(e.description) }
    }
}
```

Swift, same shape: `createSession(deviceSelector: AutoDeviceSelector(wearables:filter:))` with `$0.supportsDisplay()`,
`try session.start()`, wait for `.started` on `stateStream()`, `try session.addDisplay()`, `display.start()` (iOS only),
then `try await display.send(FlexBox(direction: .column, spacing: 8) { Text(line, style: .body) })`. No SwiftUI in that file.

Rules for live text ([display overview](https://wearables.developer.meta.com/docs/develop/dat/display-overview/)):
- One root `flexBox` per send, no partial updates, vertical scrolling only, no state kept on the glasses. Coalesce
  partial STT results; no rate limit is published, start at a few sends per second and measure (our advice).
- The panel dims after 20 s without input and sleeps at 25 s. The session survives, no API observes or controls sleep,
  and `sendContent` waking it is unconfirmed ([Meta staff, 2026-10-29](https://github.com/meta/meta-wearables-dat-android/discussions/152)):
  add an earcon or short TTS when the wearer must look.
- Glyph coverage is undocumented: for unverified scripts draw text into a bitmap and send `image(bitmap = ...)`.
  Trust the API reference over guides (guides show `paddingAll`, the parameter is `padding`).

### Web App: minimal page
HTTPS only. `navigator.install` exists only on the glasses (a runtime check). Budget: first load under 300 KB and 15
requests, 30 Hz panel, slow CPU. Meta's UI kit sets routine text at 28 px / 36 px, about 35-40 characters per line (our
estimate). The page speaks the `examples/live-captions` protocol from the server's own HTTPS origin (e.g. a TLS tunnel).
Input follows Meta's guidance: real `<button>`s, focus moved by the built-in spatial navigation, `click` handlers, no
arrow or Enter handling of our own.

```html
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Captions</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Live captions"><meta name="mrbd-web-app-capable" content="yes">
<style>
  html, body { margin: 0; height: 100%; background: #000; color: #fff; font: 28px/36px sans-serif; }
  main { box-sizing: border-box; height: 100%; padding: 24px; display: grid; grid-template-rows: minmax(0, 1fr) auto; gap: 16px; }
  #lines { overflow: hidden; display: flex; flex-direction: column; justify-content: flex-end; } #lines p { margin: 0; } .old { color: #cfd3d9; }
  button { font: inherit; color: #fff; background: #27282d; border: 0; border-radius: 16px; padding: 8px 20px; }
  button:focus-visible { outline: 3px solid currentColor; outline-offset: 4px; }
</style></head>
<body><main><div id="lines" aria-live="polite"></div>
  <div><button id="repeat">Repeat</button> <button id="skip">Skip</button> <button id="hide">Hide</button></div></main>
<script type="module">
  const room = encodeURIComponent(new URLSearchParams(location.search).get('room') ?? '');
  const box = document.getElementById('lines');
  const done = []; let partial = ''; let ws;
  function render(m) {
    if (m.type === 'clear') { done.length = 0; partial = ''; }
    else if (m.type === 'caption') {
      // repeat:true is the last final sent again ("show this again"): do not add it twice
      if (m.final) { if (!(m.repeat && done.at(-1) === m.text)) done.push(m.text); done.splice(0, done.length - 3); partial = ''; }
      else partial = m.text;
    }
    else return;
    const rows = [...done, partial].filter(Boolean);
    box.replaceChildren(...rows.map((t, i) => Object.assign(document.createElement('p'), { textContent: t, className: i < rows.length - 1 ? 'old' : '' })));
  }
  const send = (o) => ws?.readyState === WebSocket.OPEN && ws.send(JSON.stringify(o));
  function connect() {
    ws = new WebSocket('wss://' + location.host + '/ws?room=' + room);
    ws.onopen = () => send({ type: 'hello', target: 'meta-webapp', lines: 4, cols: 36 });
    ws.onmessage = (e) => render(JSON.parse(e.data));
    ws.onclose = () => { if (document.visibilityState === 'visible') setTimeout(connect, 2000); };
  }
  // A hidden page suspends timers: drop the socket, catch up from /latest when visible again.
  document.addEventListener('visibilitychange', async () => {
    if (document.visibilityState === 'hidden') { ws?.close(); return; }
    const r = await fetch('/latest?room=' + room); if (r.ok) render(await r.json());
    connect();
  });
  // Arrow keys move focus between the buttons on their own; Enter (pinch or touchpad tap) clicks the focused one.
  for (const id of ['repeat', 'skip', 'hide']) document.getElementById(id).addEventListener('click', () => send({ type: 'action', action: id }));
  document.getElementById('repeat').focus();
  connect();
</script></body></html>
```

Install: Developer Mode in Meta AI, then add the URL by hand or scan a QR of `fb-viewapp://web_app_deep_link?appName=<name>&appUrl=<https-url>`
with both values percent-encoded (an unencoded `?room=` is dropped). The add screen labels the app "unverified".

## Input
- DAT: the device owns focus. Band swipes move it between your buttons, a pinch fires `onClick`, `ActionRole.PRIMARY`
  gets first focus. Callbacks belong to the last screen sent.
- Back (two-finger temple tap or band gesture) ends the DAT session and real glasses do not deliver it in 1.0.x, even
  with `consumeBack = true` ([ios #349](https://github.com/meta/meta-wearables-dat-ios/issues/349), open). Put "Hide" on
  screen and offer "show on glasses again" on the phone.
- `Inputs` (raw Nav, Select, Drag, capture button) is beta, dev and Beta channels only, and Terms §2.8 keep it out of
  production. Without interactive content a single tap pauses the session and tap-and-hold stops it ([inputs](https://wearables.developer.meta.com/docs/develop/dat/inputs/)).
- Web Apps: native `<button>`s and built-in spatial navigation, no global focus index, no synthetic click on `Enter`.
  Meta: "let Chromium WebView or UI Toolkit own directional focus movement and activation", handle keys directly only
  for "a custom interaction that cannot be expressed with ordinary controls", and call `preventDefault()` only when you
  mean to replace the default; a listener that moves focus without it runs alongside the built-in traversal. Back is
  `popstate` (history capped at five entries), `Escape` is desktop-only, password fields do not open the composer
  ([input and navigation](https://wearables.developer.meta.com/docs/develop/webapps/build/input-and-navigation/), read
  2026-11-08).

## Audio
- A2DP (output) and HFP (glasses mic) are exclusive; HFP drops output to 16 or 8 kHz mono and beamforms to the wearer,
  so it is the wrong mic for captioning others ([microphones and speakers](https://wearables.developer.meta.com/docs/develop/dat/microphones-and-speakers/)).
- Opening HFP/SCO ends the Display session on current glasses software ([android #210](https://github.com/meta/meta-wearables-dat-android/issues/210),
  [ios #342](https://github.com/meta/meta-wearables-dat-ios/issues/342), open). Meta staff, 2026-11-04: glasses software
  192.1 "should cover most of the displayless cases", and "the display should be coming out at a later date". A
  developer kept the Display alive with `BluetoothHeadset.startVoiceRecognition()` (community, unverified). Phone
  calls end the session too.
- In-stream PCM needs a camera stream, is beta and keeps the capture LED on. On-glasses `Speech` is beta and "silently
  stops reporting text" after about a minute ([known issues](https://wearables.developer.meta.com/docs/develop/dat/knownissues/),
  which also list no HFP audio on iPhone 17 with iOS 26, fixed in iOS 27). Default for captions and assistants: phone
  mic, your STT, text to the Display, TTS over A2DP only on demand.

## Testing without hardware
- DAT: `MockDeviceKit` pairs `GlassesModel.META_RAYBAN_DISPLAY` / `.metaRayBanDisplay`; `createPreviewView` renders your
  content in the app; `startTestServer(9000)` + `adb forward tcp:9000 tcp:9000` shows it in Chrome with the simulator
  extension, whose d-pad and Select reach your handlers (iOS: only from the iOS Simulator) ([display simulation](https://wearables.developer.meta.com/docs/develop/dat/display-simulation/)).
  Keep mockdevice out of release builds. The FAQ line "Device Kit currently doesn't support display glasses" is stale.
- Web Apps: the same [extension](https://chromewebstore.google.com/detail/jpjlmmodokemlepklkdbimceggpbjcll) sends arrow
  and Enter events but does not move focus; launch Chrome with `--enable-spatial-navigation`. No console on the glasses.
  Only hardware shows real gestures and focus, sleep and wake, glyphs, Bluetooth latency and HFP behaviour.

## Publishing and distribution
- DAT: "Publishing DAT integrations to all users isn't open yet, and right now there's no public application or review
  process for early access" ([Meta staff, 2026-11-05](https://github.com/meta/meta-wearables-dat-android/discussions/229)).
  Android: the APK may be on Google Play, but only people invited to your one private Beta channel can register, others
  see "Error loading this integration". Tester limit: the channel's Users tab ([release channels](https://wearables.developer.meta.com/docs/develop/dat/set-up-release-channels/);
  the May 2026 [blog](https://developers.meta.com/blog/build-for-display-glasses/) said up to 100).
- iOS: no App Store. The SDK links `ExternalAccessory`, Apple wants an MFi PPID that Meta cannot issue
  ([ios discussion #313](https://github.com/meta/meta-wearables-dat-ios/discussions/313), 2026-09-28). Use TestFlight + Beta.
- Developer Mode lets any wearer register an unpublished app (one at a time), but Developer Terms §4.1 require
  Integration Review before general release. Do not plan a launch on it.
- Web Apps: developer preview; share the URL or QR with Developer Mode users. Meta curates the Explore app and "will
  share how to submit your experience soon" ([Explore](https://developers.meta.com/wearables/explore), no date). Country
  and account age checks can hide Web Apps, Developer Mode changes neither ([troubleshoot](https://wearables.developer.meta.com/docs/develop/webapps/troubleshoot/)).
- Policy ([Acceptable Use Policy](https://wearables.developer.meta.com/acceptable-use-policy), updated 2026-09-22, binds
  unpublished apps too): no covert collection of recognisable audio or video of anyone, no hiding the capture LED, no
  analysing people around the wearer, no identifying people by voice or face from device sensors without a Meta-approved
  exception (accessibility is named). Captioning is encouraged: "narrow purpose, short retention, obvious to bystanders".
  SDK analytics and crash reports are on by default; opt out with `ANALYTICS_OPT_OUT` / `CRASH_REPORTING_OPT_OUT`.

## Pitfalls
- `DAT_APP_ON_THE_GLASSES_UPDATE_REQUIRED` can also mean the glasses failed to start the DAT app. Check
  `Wearables.isDevMode` then: it resets if you call `startRegistration()` while registered or reinstall. Guard
  registration; recover with one `startUnregistration()` + one `startRegistration()`, then one `Wearables.reset()` +
  `initialize()` (never looped), then reboot the glasses ([android #192](https://github.com/meta/meta-wearables-dat-android/issues/192),
  [ios #180](https://github.com/meta/meta-wearables-dat-ios/issues/180)). The glasses-side install fails below 10% battery.
- Registration loops: on Android register from a `ComponentActivity` that stays open until Meta AI returns
  ([android #223](https://github.com/meta/meta-wearables-dat-android/issues/223)). Developer Mode is per device, may reset
  after updates, and a second dev app unregisters the first. The iOS Developer Mode tap may only say "Copied to
  clipboard" ([ios #325](https://github.com/meta/meta-wearables-dat-ios/issues/325), open). Beta registration with no
  callback is usually a version or ID mismatch in Developer Center ([ios #219](https://github.com/meta/meta-wearables-dat-ios/issues/219)).
- `NO_ELIGIBLE_DEVICE`, Android: grant `BLUETOOTH_SCAN` ("Nearby devices") too, detection fails silently without it
  ([Meta staff in android #144](https://github.com/meta/meta-wearables-dat-android/issues/144)). iOS: create the
  `AutoDeviceSelector` early or wait for an active device before `createSession`.
- `INSUFFICIENT_SDK_VERSION` is terminal (ship a new build), `DWA_OUT_OF_STU_RANGE` only warns, `CAPABILITY_DENIED` can be
  per-user server gating; keep them apart ([version dependencies](https://wearables.developer.meta.com/docs/develop/dat/version-dependencies/)).
- Sessions "ended by device" on some glasses releases ([android #227](https://github.com/meta/meta-wearables-dat-android/issues/227),
  [ios #332](https://github.com/meta/meta-wearables-dat-ios/issues/332)). Never combine photo capture with Display.
- iOS `Info.plist`: Meta's display skill keeps `external-accessory` + `com.meta.ar.wearable`, the DisplayAccess sample
  omits them, and that protocol triggers Apple's MFi review. Sources disagree; verify per build.
- DAT content is missing from the glasses' Display Recording ([ios #223](https://github.com/meta/meta-wearables-dat-ios/issues/223)).
- Web Apps: Developer Mode prompt missing on iOS ([#21](https://github.com/meta/meta-wearables-webapp/issues/21)), Web Apps
  menu missing on Android ([#26](https://github.com/meta/meta-wearables-webapp/issues/26)), deep-link install "Something
  went wrong" ([#29](https://github.com/meta/meta-wearables-webapp/issues/29)), simulator QA wants a fixed 600x600 viewport
  ([#28](https://github.com/meta/meta-wearables-webapp/issues/28)). SVG favicons fail. Stale build: Restart from the app menu.

## Official resources
- DAT: https://wearables.developer.meta.com/docs/develop/dat/display-overview/, https://github.com/meta/meta-wearables-dat-android, https://github.com/meta/meta-wearables-dat-ios
- Web Apps: https://wearables.developer.meta.com/docs/develop/webapps, https://github.com/meta/meta-wearables-webapp, https://github.com/meta/meta-ray-ban-display-ui-toolkit-web
- Markdown docs https://wearables.developer.meta.com/llms.txt, FAQ https://developers.meta.com/wearables/faq/, Terms https://wearables.developer.meta.com/terms
