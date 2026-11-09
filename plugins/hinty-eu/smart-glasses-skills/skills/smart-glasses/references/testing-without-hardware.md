# Testing glasses apps without the glasses

Read this when you need to run, test or put a glasses app in CI before (or instead of) having the hardware: what each
vendor's simulator really covers, a fake-glasses pattern for brands with no simulator, and what only a device shows.

Last checked: 2026-11-08. Verification: docs-only, except the Even simulator, which ran our sample plugin on
2026-11-08 (`simulator`). The code in this file was written for it and not compiled here.

## What each target offers

| Target | Tool | Covers | Does not cover | Automate with |
|---|---|---|---|---|
| Even Realities G2 | Official simulator (Windows, macOS, Linux) | Containers, input events, PC mic as `audioEvent`, screenshots, console | BLE timing, exact font and brightness, image size limits, LZ4 path, status events, permissions, background and lock, iOS WebView quirks | HTTP API on `--automation-port` |
| Meta DAT (Display and camera glasses) | MockDeviceKit (`mwdat-mockdevice`, debug builds only) | Mock pairing, power, fold, don and doff, touchpad tap and tap-and-hold, permission results, camera feed from a file or the phone camera, Display preview; Meta's skills add beta `Inputs` and `Speech` injection (not on the docs page) | HFP conflicts, Back, panel sleep, glyph coverage, Bluetooth latency, Meta's registration servers | Instrumented tests, XCTest |
| Meta Web Apps | Chrome extension "Meta Ray-Ban Display Simulator" | 600x600 layout, arrow and Enter events, environments, brightness, recording | Focus movement (start Chrome with `--enable-spatial-navigation`), real gestures, glasses CPU, country gating | A browser test at a fixed 600x600 viewport (our suggestion) |
| Android XR glasses | Glasses emulator in Android Studio Canary, paired with a phone AVD | Projected activity, touchpad, host mic, audio-only mode, bridged notifications, screenshots | Camera capture ("not available yet"), optics, battery, heat | `adb`, emulator controls |
| USB-C display glasses | Android emulator secondary display; iOS Simulator external display | `Presentation` and scene life cycle, layout at the external resolution | Optics and tint, USB audio routing, Samsung DeX, lock screen on a real phone | Instrumented tests |
| Phone notifications (rung 4) | Android XR emulator; `adb shell dumpsys notification`; `adb shell cmd notification post` | Channel importance, flags, posting rate, Android XR bridging rules | What Even, Rokid, Vuzix or RayNeo companion apps actually forward | `adb` |
| Rokid Glasses (CXR-L) | None | Nothing; native libraries are ARM only | Everything | A fake behind your interface |
| Vuzix Z100 | None | Android: `isAvailable()` stays `false` without Vuzix Connect; iOS: the XCFramework runs in the Simulator | Connection, control, taps | A fake behind your interface |
| Brilliant Labs Halo | `halo-emulator` 2.3.0 (PyPI, 2026-10-24, experimental) | Your Lua against a stubbed device API and a 256x256 framebuffer | The BLE link and its timing (inference) | Python tests |
| Snap Specs | Lens Studio Preview, Device Type Override = Spectacles | Additive display, left, right and centre views, interaction | "emulators don't reflect full performance or thermal behavior" (Snap) | Lens Studio |
| MentraOS | The miniapp runs without glasses; "the display just won't have anywhere to draw" | App logic | Display output, input | Not yet ([#4931](https://github.com/Mentra-Community/MentraOS/issues/4931): the Bluetooth SDK's `connectSimulated()` is internal and only logs calls) |
| Standalone Android (RayNeo X3 Pro, INMO Air3) | Emulator with a 640x480 hardware profile; `xg-glass-sdk run --sim` | Layout and font size | Optics, binocular layout, touchpad | `adb` |

Brand details: [even-g2.md](brands/even-g2.md#testing-without-hardware), [meta-display.md](brands/meta-display.md#testing-without-hardware),
[meta-audio-glasses.md](brands/meta-audio-glasses.md#testing-without-hardware), [android-xr.md](brands/android-xr.md),
[usb-c-displays.md](brands/usb-c-displays.md#testing-without-hardware), [notification-glasses.md](brands/notification-glasses.md#testing-without-hardware),
[brilliant-labs.md](brands/brilliant-labs.md), [snap-spectacles.md](brands/snap-spectacles.md), [mentra.md](brands/mentra.md),
[standalone-android-glasses.md](brands/standalone-android-glasses.md#testing-without-hardware).

## Even Hub simulator in a test

`npm i -g @evenrealities/evenhub-simulator`, then `evenhub-simulator http://localhost:5173 --automation-port 9898`.
Endpoints ([simulator docs](https://hub.evenrealities.com/docs/test/simulator)): `GET /api/ping`,
`GET /api/screenshot/glasses` (576x288 RGBA, lit pixels have alpha above 0), `GET /api/screenshot/webview`,
`GET /api/console` (`?since_id=N`), `POST /api/input` with `up`, `down`, `click`, `double_click`,
`long_press`, `long_press_release` or `context_menu`. The console endpoint also accepts the HTTP DELETE method,
which clears the buffer. `--aid <device>` / `--no-aid` choose the audio input.

```ts
// Node 20+. Have the plugin log one marker line per glasses write, e.g. console.log('[glasses] ' + text).
const SIM = 'http://127.0.0.1:9898'
export async function press(action: 'up' | 'down' | 'click' | 'double_click' | 'long_press'): Promise<void> {
  const r = await fetch(`${SIM}/api/input`, {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ action }),
  })
  if (!r.ok) throw new Error(`input ${action} -> ${r.status}`)
}
export async function waitForLog(marker: string, timeoutMs = 5000): Promise<void> {
  const end = Date.now() + timeoutMs
  while (Date.now() < end) {
    const text = await (await fetch(`${SIM}/api/console`)).text() // unverified: exact JSON shape, so match on text
    if (text.includes(marker)) return
    await new Promise(r => setTimeout(r, 200))
  }
  throw new Error(`no "${marker}" in simulator console`)
}
```

Gotchas: input is ignored until a capture container exists; restart the simulator after code edits, because hot
reload makes `createStartUpPageContainer` return 1 ([#32](https://github.com/even-realities/everything-evenhub/issues/32));
there is no shutdown endpoint, so kill the process. Running it on a headless Linux CI runner without a display server
is unverified. Even's official skill covers the simulator in depth: `npx skills add even-realities/everything-evenhub`.

## Meta: MockDeviceKit and the simulator extension

Add `com.meta.wearable:mwdat-mockdevice` to debug builds only. In a test: enable the kit (it fakes registration;
it can also start unregistered to test that flow), pair a mock model (`RAYBAN_META`, `META_RAYBAN_DISPLAY`), power it
on and don it, set permission results, and set a camera feed (an H.265 file or the phone camera, which then needs the
phone's own camera permission). For Display: put `createPreviewView()` in a square container, or call
`startTestServer(9000)`, `adb forward tcp:9000 tcp:9000` and open `http://127.0.0.1:9000/` in Chrome with the
extension; its d-pad and Select reach your handlers. On iOS the Chrome preview works only from the iOS Simulator
([display simulation](https://wearables.developer.meta.com/docs/develop/dat/display-simulation/)). Meta's official
skills include a MockDeviceKit testing skill: `npx skills add meta/meta-wearables-dat-android` (or `-ios`).

Web Apps: the same extension previews a page but does not move focus; use a 600x600 viewport and
`--enable-spatial-navigation`. There is no console on the glasses, so log to your server during tests.

## Android XR glasses emulator

Latest Android Studio Canary; start the phone AVD, then the glasses AVD, run the app on the phone AVD
([emulator](https://developer.android.com/develop/xr/jetpack-xr-sdk/run/emulator/glasses)). The touchpad is the area
below the display (right side = towards the lenses), with a Two Finger mode. Microphone uses the host mic. Test
audio glasses by switching on Audio-only mode in the Glasses app, then cold boot the phone AVD. The display snooze
timeout is off by default; turn it on with `adb shell dumpsys activity service com.google.android.glasses.core/com.google.android.projection.core.app.service.AndroidProjectionCoreService preferences_set pref_automatic_snooze_timeout true`.
For notifications enable your app in the Glasses app on the phone AVD. Official skills:
`npx skills add android/skills --skill display-glasses-with-jetpack-compose-glimmer` and `--skill projected-hardware`.

## Notifications without glasses (rung 4)

Check the phone side; the forwarding itself needs the real companion app and glasses.
- `adb shell dumpsys notification --noredact` shows channel importance, flags and posting history for your package.
- `adb shell cmd notification post -t "Title" mytag "Body"` posts a test notification from the shell (check
  `adb shell cmd notification help` on your Android version).
- A debug-only `NotificationListenerService` in a second app sees roughly what a companion app sees (title, text,
  ongoing flag, channel). Log those fields to compare with the rules in [notification-glasses.md](brands/notification-glasses.md).

## Rokid, Vuzix and every brand without a simulator: fake the glasses

Put each vendor SDK behind one small interface, test everything above it against a fake, and run the same contract
tests against the real adapter on a phone with glasses. The real adapter should also log exactly what it sends (Rokid
JSON, Vuzix text and ids), with `Log.i` on Rokid because its R8 rules strip `Log.d` from release builds.

```kotlin
// imports: kotlinx.coroutines.flow.*, kotlinx.coroutines.test.runTest, org.junit.Test, org.junit.Assert.assertTrue
interface Glasses {
    val limits: Limits
    val state: StateFlow<LinkState>
    val actions: Flow<Action>                       // taps, ring, buttons mapped to shared actions
    suspend fun connect(): Result<Unit>
    suspend fun show(lines: List<String>): Result<Unit>
}
data class Limits(val lines: Int, val cols: Int, val minIntervalMs: Long, val glyphOk: (Char) -> Boolean = { true })
enum class Action { REPEAT, SKIP, HIDE }
enum class LinkState { DISCONNECTED, READY, PAUSED, LOST }

/** Records what a real adapter would send and fails loudly where the hardware would fail quietly. */
class FakeGlasses(override val limits: Limits, private val now: () -> Long = System::currentTimeMillis) : Glasses {
    data class Frame(val atMs: Long, val lines: List<String>)
    val sent = mutableListOf<Frame>()
    private val _state = MutableStateFlow(LinkState.DISCONNECTED)
    override val state: StateFlow<LinkState> = _state
    private val _actions = MutableSharedFlow<Action>(extraBufferCapacity = 8)
    override val actions: Flow<Action> = _actions
    var failNext: Throwable? = null

    override suspend fun connect(): Result<Unit> { _state.value = LinkState.READY; return Result.success(Unit) }
    override suspend fun show(lines: List<String>): Result<Unit> {
        if (_state.value != LinkState.READY) return Result.failure(IllegalStateException("state ${_state.value}"))
        failNext?.let { failNext = null; return Result.failure(it) }
        check(lines.size <= limits.lines && lines.all { it.length <= limits.cols }) { "frame too big: $lines" }
        check(lines.all { line -> line.all(limits.glyphOk) }) { "glyph the glasses cannot draw: $lines" }
        sent.lastOrNull()?.let { check(now() - it.atMs >= limits.minIntervalMs) { "sent faster than the link allows" } }
        sent += Frame(now(), lines)
        return Result.success(Unit)
    }
    fun press(a: Action) = _actions.tryEmit(a)
    fun setState(s: LinkState) { _state.value = s }   // pause for the assistant, lose the link, come back
}

/** Run with FakeGlasses on the JVM, and with the real adapter in an instrumented test next to real glasses. */
abstract class GlassesContract {
    abstract fun create(): Glasses
    @Test fun refusesTextBeforeConnect() = runTest { assertTrue(create().show(listOf("hi")).isFailure) }
    @Test fun showsAfterConnect() = runTest { val g = create(); g.connect(); assertTrue(g.show(listOf("hi")).isSuccess) }
}
```

Use realistic limits per target (for example Even about 10 lines of about 60 Latin characters, Halo 32 ASCII
characters per line; see [display-text-ladder.md](display-text-ladder.md)). The same shape in TypeScript serves web and
Even targets:

```ts
export type Action = 'repeat' | 'skip' | 'hide'
export interface Glasses { connect(): Promise<void>; show(lines: string[]): Promise<void>; onAction(cb: (a: Action) => void): void }
export class FakeGlasses implements Glasses {
  sent: { at: number; lines: string[] }[] = []
  private cb: (a: Action) => void = () => {}
  constructor(private limits: { lines: number; cols: number; minIntervalMs: number }) {}
  async connect() {}
  async show(lines: string[]) {
    if (lines.length > this.limits.lines || lines.some(l => [...l].length > this.limits.cols)) throw new Error(`too big: ${lines}`)
    const last = this.sent.at(-1)
    if (last && Date.now() - last.at < this.limits.minIntervalMs) throw new Error('sent faster than the link allows')
    this.sent.push({ at: Date.now(), lines })
  }
  onAction(cb: (a: Action) => void) { this.cb = cb }
  press(a: Action) { this.cb(a) }
}
```

Brand notes: Rokid's native libraries are ARM only, so an x86 emulator throws `UnsatisfiedLinkError` when you create
a session; test the JSON builders and line fitting on the JVM ([Rokid skill](../../smart-glasses-rokid/SKILL.md#testing-without-hardware)).
Vuzix: on Android without Vuzix Connect `isAvailable()` stays `false`, a useful "not installed" test
([Vuzix skill](../../smart-glasses-vuzix/SKILL.md#testing-without-hardware)).

## What still needs a device

Plan a first hardware day with this list; no tool above reproduces it:
- Bluetooth latency and the real update rate the link sustains (Even, Rokid, Vuzix, Meta, Halo).
- Glyph coverage and readability outdoors: fonts, brightness levels, accents, CJK, RTL.
- Real gestures, false taps when the wearer adjusts the frame, gestures the system reserves (Back, menus).
- Background and lock: phone in a pocket for 10 minutes, battery managers killing the companion app, reconnect after
  walking out of range, panel sleep (Meta dims at 20 s), Android XR snooze.
- Audio routes: HFP switches, a phone call mid-session, the vendor assistant taking the mic.
- Registration, pairing and companion-app versions (Meta Developer Mode, Hi Rokid Global or China, Vuzix linking).
- Which notifications each companion app forwards, and how fast.
- Heat and battery over a one-hour session.

Record the results with firmware, companion-app and SDK versions; per-brand checklists are in the Rokid and Vuzix
troubleshooting files ([Rokid](../../smart-glasses-rokid/references/troubleshooting.md),
[Vuzix](../../smart-glasses-vuzix/references/troubleshooting.md#first-day-with-hardware)).
