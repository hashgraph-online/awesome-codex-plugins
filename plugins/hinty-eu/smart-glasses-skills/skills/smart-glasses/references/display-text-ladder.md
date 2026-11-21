# The display-text ladder

Read this when your app must put text in front of the wearer (or into their ear) and should work on whatever
glasses they own, with one interface and an automatic fallback.

Last checked: 2026-11-08. Verification: docs-only for the brand facts. The interfaces below have the same shape as
the ones in [`examples/live-captions/`](../../../examples/live-captions/) (repository `hinty-eu/smart-glasses-skills`);
the Android and iOS targets compile in CI (iOS since 2026-11-09); neither has run on glasses. The selection code in this file is
written for it and has not been compiled.

## The five rungs

Try them top to bottom. Higher rungs give you layout and fast updates; lower rungs work on more glasses.

| Rung | Name | Works on (as of 2026-11-08) | You control | Updates | Public today |
|---|---|---|---|---|---|
| 1 | **Vendor SDK** | Even Hub ([even-g2](brands/even-g2.md)), Meta DAT ([meta-display](brands/meta-display.md)), Rokid CXR-L ([rokid](brands/rokid.md)), Vuzix Ultralite ([vuzix-z100](brands/vuzix-z100.md)), Android XR Glimmer ([android-xr](brands/android-xr.md)); also Brilliant Lua, MentraOS | Position, lines, brightness | A few per second over BLE | Even, Rokid, Vuzix yes; Meta, Android XR display, Mentra no |
| 2 | **Web app on the glasses** | Meta Ray-Ban Display Web Apps, INMO Air3 Chrome, RayNeo X3 Pro with a sideloaded browser ([standalone](brands/standalone-android-glasses.md)), any second screen | Full HTML and CSS | Frame rate, needs network on the glasses | INMO yes; Meta Developer Mode only |
| 3 | **USB-C display glasses as an external display** | XREAL, VITURE, RayNeo Air ([usb-c-displays](brands/usb-c-displays.md)) | A whole screen | Frame rate, cable | Yes |
| 4 | **Phone notification mirrored by the companion app** | Even, Rokid, Vuzix, RayNeo, INMO Go3, Halliday, MentraOS, Android XR ([notification-glasses](brands/notification-glasses.md)) | Title and one sentence | One every 2-3 s | Yes |
| 5 | **Voice in the ear** | Every pair with speakers: Ray-Ban Meta, Oakley Meta ([meta-audio-glasses](brands/meta-audio-glasses.md)), Rokid, Android XR, Halo; Even G2 and Vuzix only through the user's earbuds | Words, timing | One short utterance at a time | Yes |

When each rung applies:
- **Rung 1** whenever the brand's SDK can reach the user's pair and you can publish to them. It is the only rung with
  input from the glasses on most brands.
- **Rung 2** when code runs on the glasses (standalone Android, Meta Web Apps) or the "glasses" are a monitor. One
  page serves several brands. Needs a network path from the glasses to your server.
- **Rung 3** when the user plugs display glasses into the phone. No SDK, no store review, any script the phone renders.
- **Rung 4** for every pair that has no usable SDK for you: alerts, answers, one caption per few seconds. Never for
  continuous live captions.
- **Rung 5** for audio-only glasses, and as the last fallback everywhere. Short items, newest replaces older.

## The shared interface

Every rung implements one interface, so the caption or hint logic never knows which glasses it drives. The budget
is what the display can hold; `partials = false` marks rungs that should only get final text (rungs 4 and 5), and
`minIntervalMs` throttles BLE links.

```kotlin
data class LineBudget(val lines: Int, val cols: Int, val partials: Boolean = true, val minIntervalMs: Long = 0)

enum class InputAction(val wire: String) { REPEAT("repeat"), SKIP("skip"), HIDE("hide") }

interface GlassesDisplay {          // all calls on the main thread
    val id: String                  // sent in the hello message: "rokid", "vuzix", "external", "speech", ...
    val budget: LineBudget
    fun connect()                   // permissions, companion approval, display control; progress goes to the host
    fun show(lines: List<String>)   // replaces everything; lines already fit the budget
    fun onFinal(text: String) {}    // speaking rungs use this, drawing rungs ignore it
    fun clear()                     // blank, stay connected
    fun disconnect()                // give the display back, release everything
}
```

```swift
struct LineBudget: Equatable { var lines: Int; var cols: Int; var partials = true; var minInterval: TimeInterval = 0 }

@MainActor protocol GlassesDisplay: AnyObject {
  var id: String { get }
  var budget: LineBudget { get }
  func connect()
  func show(_ lines: [String])
  func onFinal(_ text: String)    // give it an empty default in an extension
  func clear()
  func disconnect()
}
```

```ts
export interface LineBudget { lines: number; cols: number; partials: boolean; minIntervalMs: number }
export type InputAction = 'repeat' | 'skip' | 'hide'

export interface GlassesDisplay {
  readonly id: string
  readonly budget: LineBudget
  connect(): Promise<void>
  show(lines: string[]): void       // keep one write in flight inside, newest text wins
  onFinal?(text: string): void
  clear(): void
  disconnect(): void
}
```

Each display reports gestures as `InputAction`s to its host ([input.md](input.md)). Line fitting (keep the last
lines for captions, the first lines for answers) lives in the `smart-glasses-live-captions` skill.

## Picking a rung at runtime

Rules:
1. List candidates in ladder order; within a rung, put the brand your users own most often first.
2. A probe must be cheap and silent: is the companion app installed, is a display attached, is Bluetooth audio
   connected. Probes cannot prove that the glasses are on the user's face; `connect()` is the real test.
3. When `connect()` or the session fails for good (permission denied, control refused, session closed), mark that
   candidate failed and take the next one. Tell the user which rung is active.
4. Clear the failed set on new hardware events (Bluetooth device connected, display added, app returns to the
   foreground) and try again from the top.
5. Remember the last rung that worked and let the user override it in settings.

```kotlin
class Candidate(val rung: Int, val id: String, val available: () -> Boolean, val create: () -> GlassesDisplay)

class Ladder(private val candidates: List<Candidate>, private val use: (GlassesDisplay?) -> Unit) {
    private val failed = mutableSetOf<String>()
    var currentId: String? = null
        private set

    fun select() {
        val next = candidates.firstOrNull { it.id !in failed && runCatching(it.available).getOrDefault(false) }
        if (next?.id == currentId) return
        currentId = next?.id
        use(next?.create())                     // null: nothing on the glasses, keep the phone UI
    }
    fun onFailed(id: String) { failed += id; if (id == currentId) select() }
    fun retryAll() { failed.clear(); select() }
}

fun hasExternalDisplay(ctx: Context) = ctx.getSystemService(DisplayManager::class.java)
    .getDisplays(DisplayManager.DISPLAY_CATEGORY_PRESENTATION)
    .any { it.displayId != Display.DEFAULT_DISPLAY && (it.flags and Display.FLAG_PRIVATE) == 0 }

fun bluetoothAudioOut(ctx: Context) = ctx.getSystemService(AudioManager::class.java)
    .getDevices(AudioManager.GET_DEVICES_OUTPUTS).any {
        it.type == AudioDeviceInfo.TYPE_BLUETOOTH_A2DP ||
            (Build.VERSION.SDK_INT >= 31 && it.type == AudioDeviceInfo.TYPE_BLE_HEADSET)
    }

// Android 11+: declare these packages in <queries>, or the check always fails
fun installed(ctx: Context, pkg: String) = runCatching { ctx.packageManager.getPackageInfo(pkg, 0) }.isSuccess

val ladder = Ladder(listOf(
    Candidate(1, "rokid", { CxrSessionManager.getInstance(ctx).checkRokidAppCompatibility(ctx) is RokidAppStatus.Compatible }) { RokidDisplay(host) },
    Candidate(1, "vuzix", { UltraliteSDK.get(ctx).run { isAvailable() && isLinked() } }) { VuzixDisplay(host) },
    // Meta DAT: registered and a display-capable device present (brands/meta-display.md); Beta testers only today
    Candidate(3, "external", { hasExternalDisplay(ctx) }) { PresentationDisplay(host) },
    Candidate(4, "notification", {
        NotificationManagerCompat.from(ctx).areNotificationsEnabled() &&
            listOf("com.rokid.sprite.global.aiapp", "com.vuzix.connect").any { installed(ctx, it) } // add yours
    }) { NotificationDisplay(host) },
    Candidate(5, "speech", { bluetoothAudioOut(ctx) }) { SpeechDisplay(host) },
)) { d -> if (d != null) controller.setDisplay(d) }
```

The Rokid check comes from the `smart-glasses-rokid` skill and the Vuzix calls from the Ultralite Javadoc
(`isAvailable()`, `isLinked()`). Register a `DisplayManager.DisplayListener` and a Bluetooth connection receiver and
call `retryAll()` from them.

```swift
struct Candidate {
  let rung: Int
  let id: String
  let available: @MainActor () async -> Bool
  let create: @MainActor () -> GlassesDisplay
}

@MainActor final class Ladder {
  private let candidates: [Candidate]          // in ladder order
  private let use: (GlassesDisplay?) -> Void
  private var failed: Set<String> = []
  private(set) var currentId: String?
  init(_ candidates: [Candidate], use: @escaping (GlassesDisplay?) -> Void) { self.candidates = candidates; self.use = use }

  func select() async {
    for c in candidates where !failed.contains(c.id) {
      guard await c.available() else { continue }
      if c.id != currentId { currentId = c.id; use(c.create()) }
      return
    }
    currentId = nil; use(nil)
  }
  func markFailed(_ id: String) async { failed.insert(id); if id == currentId { currentId = nil; await select() } }
  func retryAll() async { failed.removeAll(); await select() }
}

@MainActor func externalDisplayConnected() -> Bool {   // iOS 27+: only after you register the scene accessory
  UIApplication.shared.connectedScenes.contains { $0.session.role == .windowExternalDisplayNonInteractive }
}
func bluetoothAudioOut() -> Bool {
  AVAudioSession.sharedInstance().currentRoute.outputs.contains { [.bluetoothA2DP, .bluetoothLE, .bluetoothHFP].contains($0.portType) }
}
func canNotify() async -> Bool { await UNUserNotificationCenter.current().notificationSettings().authorizationStatus == .authorized }

// let ladder = Ladder([
//   Candidate(rung: 1, id: "vuzix", available: { UltraliteManager.shared.currentDevice != nil }, create: { VuzixDisplay(host: host) }),
//   Candidate(rung: 3, id: "external", available: { externalDisplayConnected() }, create: { ExternalDisplay(host: host) }),
//   Candidate(rung: 4, id: "notification", available: { await canNotify() }, create: { NotificationDisplay(host: host) }),
//   Candidate(rung: 5, id: "speech", available: { bluetoothAudioOut() }, create: { SpeechDisplay(host: host) }),
// ]) { if let d = $0 { controller.setDisplay(d) } }
```

TypeScript, for one web codebase that ships as an Even Hub plugin and as a page for glasses browsers:

```ts
import { waitForEvenAppBridge } from '@evenrealities/even_hub_sdk'   // import first: the SDK replaces timers

export interface Candidate { rung: 1 | 2 | 3 | 4 | 5; id: string; available(): Promise<boolean>; create(): GlassesDisplay }

export async function pickDisplay(candidates: Candidate[], failed: ReadonlySet<string> = new Set()) {
  for (const c of candidates) {                       // in ladder order
    if (failed.has(c.id)) continue
    try { if (await c.available()) return c } catch { /* a probe that throws means no */ }
  }
  return null
}

const within = <T>(p: Promise<T>, ms: number, fallback: T) =>
  Promise.race([p, new Promise<T>((r) => setTimeout(() => r(fallback), ms))])

export const probes = {
  // unverified: how waitForEvenAppBridge behaves outside the Even app; the timeout covers a promise that never settles
  evenHub: () => within(waitForEvenAppBridge().then(() => true, () => false), 1500, false),
  metaWebApp: async () => 'install' in navigator,     // present only in the glasses browser (brands/meta-display.md)
  page: async () => true,                             // rung 2: this page is already on some screen
  speech: async () => 'speechSynthesis' in globalThis,
}
```

## Pitfalls per rung

- **Rung 1.** Probes see the companion app, not the glasses: Rokid and Vuzix only fail at `connect()`. Vuzix control
  is last-requester-wins, so another app can take the display at any time; Meta DAT ends the Display session on Back
  and when the glasses microphone opens; an Even plugin can lose its WebView in the iOS background, and QR-sideloaded
  builds stop when the phone locks. Treat "session ended" as a normal event, not a crash, and offer "show on glasses
  again" on the phone.
- **Rung 2.** The glasses need a route to your server (Wi-Fi or a phone hotspot) and HTTPS for Meta Web Apps. A
  hidden page suspends timers and sockets: catch up with a plain HTTP request when it becomes visible.
- **Rung 3.** The phone lock screen replaces your content with a clock on the external display; Samsung may start
  DeX; on iOS the content shows only while your app is in the foreground (community reports). Black background only.
- **Rung 4.** You cannot detect whether the companion app forwards your notification or whether the wearer enabled
  your app there. Ask once during onboarding and show the steps. Post a new notification per message, at most one
  every 2-3 seconds: glasses show one at a time, Android sheds updates to an existing notification above 5 per second
  per package, and no brand documents how it forwards updates ([notification-glasses.md](brands/notification-glasses.md)).
- **Rung 5.** Open-ear speakers leak: people nearby hear it. Never speak partial results. Opening the glasses mic
  (HFP) drops output to mono voice quality; record from the phone mic unless you need the wearer's voice
  ([audio-routing.md](audio-routing.md)).
- **All rungs.** Never fall from a display rung to voice without telling the user. Keep the phone UI showing the same
  text, so a broken rung is visible at once.

## Implementations

[`examples/live-captions/`](../../../examples/live-captions/) implements these rungs against one caption server:
`android/` (Rokid, Vuzix, Meta DAT in the `meta` flavor, Presentation, notification, speech), `ios/` (Vuzix,
external display, notification, speech), `web-glasses/` (Meta Web Apps, glasses browsers, second screens) and
`even-hub/` (Even Hub plugin). The examples let the user pick the rung from a list; the `Ladder` above is the
automatic version of that list. Brand specifics stay in the brand files and in the `smart-glasses-rokid` and
`smart-glasses-vuzix` skills.
