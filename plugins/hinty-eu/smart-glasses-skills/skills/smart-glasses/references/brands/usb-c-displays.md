# USB-C display glasses (XREAL, VITURE, RayNeo Air and similar)

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). The code below was written against the
public Android and UIKit APIs and has not been compiled in this repo.

## At a glance
- Display: the glasses are a plain external monitor over one USB-C cable with DisplayPort Alt Mode (XREAL One, One Pro,
  1S; VITURE Luma, Luma Pro, Luma Ultra, Beast; RayNeo Air series). Birdbath optics with a tinted front.
- How your app puts text on it: rung 3. Android `Presentation` on the external display, iOS external display scene.
  Zero-code fallback: plug the glasses into a laptop and drag a full-screen web page onto them.
- Input: none reaches your app; the glasses' buttons control brightness and modes (unverified per model).
- Microphone and speaker: use the phone's mic. Many models have speakers (and some mics) that appear as a USB audio
  device and can take over routing (varies by model, unverified).
- Phones: Android phones with DP Alt Mode video out (Pixel 8 and later, Samsung Galaxy S flagships; many mid-range
  phones have none). iPhone per Apple: iPhone 15, 16 (not 16e), 17 (not 17e), 18 Pro and iPhone Duo. iPhone Air is not
  on Apple's list and RayNeo excludes it.
- Publishing to everyone today: yes, through your normal app store listing. No vendor SDK, programme or approval is
  involved (as of 2026-11-08; inference from the vendors documenting plain DP Alt Mode).
- Test without hardware: Android emulator secondary display; iOS Simulator external display.
- Official agent skill: none.

## Getting text on the display
1. **Android `Presentation`** on a display from `DisplayManager.getDisplays(DISPLAY_CATEGORY_PRESENTATION)`. No
   permission, no manifest entry. On Android 12+ the Presentation creates its own window context, so you can build it
   from the application context and it keeps showing while your app is in the background, as long as the process
   lives (keep a foreground service during a session). Before Android 12 pass an Activity context (unverified).
2. **iOS external display scene** with role `windowExternalDisplayNonInteractive` (iOS 16+). From iOS 27 the system
   connects that scene only after a view controller registers a scene accessory. Content shows only while your app is
   in the foreground; after an app switch iOS mirrors again (community reports, unverified).
3. **Mirroring** (no code) shows the whole phone screen: fine for a demo, useless as a HUD. **Laptop as the host**:
   the glasses are a monitor, so a full-screen browser window with a black background works today.

Vendor SDKs (XREAL SDK 3.x and RayNeo Air SDK for Unity, VITURE Glasses SDK for tracking and camera) are only for
head-locked or world-locked AR, not for 2D text.

Android (Kotlin, minSdk 31, call from the main thread):

```kotlin
class ExternalTextDisplay(context: Context) {
    private val app = context.applicationContext
    private val dm = app.getSystemService(DisplayManager::class.java)
    private var presentation: TextPresentation? = null
    private var text = ""

    private val listener = object : DisplayManager.DisplayListener {
        override fun onDisplayAdded(displayId: Int) = attach()
        override fun onDisplayRemoved(displayId: Int) = attach() // the Presentation cancels itself
        override fun onDisplayChanged(displayId: Int) {}
    }

    fun start() { dm.registerDisplayListener(listener, Handler(Looper.getMainLooper())); attach() }
    fun stop() { dm.unregisterDisplayListener(listener); presentation?.dismiss(); presentation = null }
    fun show(t: String) { text = t; presentation?.update(t) }

    private fun pickDisplay(): Display? =
        dm.getDisplays(DisplayManager.DISPLAY_CATEGORY_PRESENTATION).firstOrNull { d ->
            d.displayId != Display.DEFAULT_DISPLAY &&
                (d.flags and Display.FLAG_PRIVATE) == 0 &&
                // Android 16+ may mark built-in screens (foldable cover display) as presentation displays
                d.deviceProductInfo?.connectionToSinkType != DeviceProductInfo.CONNECTION_TO_SINK_BUILT_IN
        }

    private fun attach() {
        val d = pickDisplay()
        val current = presentation
        if (current != null && current.isShowing && current.display.displayId == d?.displayId) return
        current?.dismiss(); presentation = null
        if (d == null) return
        val p = TextPresentation(app, d)
        try { p.show(); p.update(text); presentation = p }
        catch (e: WindowManager.InvalidDisplayException) { /* refused, e.g. your own task is on that display */ }
    }
}

private class TextPresentation(outer: Context, display: Display) : Presentation(outer, display) {
    private var label: TextView? = null
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setCancelable(false)
        // Never call window.setType(): on Android 12+ it breaks the presentation (InvalidDisplayException)
        window?.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON or WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE)
        val m = context.resources.displayMetrics // the glasses' metrics, not the phone's
        label = TextView(context).apply {
            setBackgroundColor(Color.BLACK) // black reads as see-through on these optics
            setTextColor(Color.WHITE)
            setTextSize(TypedValue.COMPLEX_UNIT_PX, m.heightPixels * 0.07f)
            gravity = Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL
            maxLines = 3
            setPadding((m.widthPixels * 0.12f).toInt(), 0, (m.widthPixels * 0.12f).toInt(), (m.heightPixels * 0.08f).toInt())
        }
        setContentView(label!!)
    }
    fun update(t: String) { label?.text = t }
}
```

iOS (Swift). The scene delegate serves both paths; register the accessory on iOS 27+, return the configuration from
the app delegate on iOS 16-26:

```swift
final class ExternalDisplaySceneDelegate: UIResponder, UIWindowSceneDelegate {
    @MainActor static var text = "" { didSet { label?.text = text } } // set from your app
    @MainActor private static weak var label: UILabel?
    var window: UIWindow?
    func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options: UIScene.ConnectionOptions) {
        guard let ws = scene as? UIWindowScene else { return }
        let vc = UIViewController()
        vc.view.backgroundColor = .black // black reads as see-through
        let label = UILabel(frame: vc.view.bounds.insetBy(dx: ws.screen.bounds.width * 0.12, dy: 40))
        label.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        label.textColor = .white; label.numberOfLines = 3; label.textAlignment = .center
        label.font = .boldSystemFont(ofSize: max(18, ws.screen.bounds.height * 0.07))
        vc.view.addSubview(label)
        label.text = Self.text; Self.label = label
        let w = UIWindow(windowScene: ws) // attaching a window turns mirroring off
        w.rootViewController = vc; w.isHidden = false
        window = w
    }
    func sceneDidDisconnect(_ scene: UIScene) { window = nil }
}

func externalDisplayConfiguration() -> UISceneConfiguration {
    let c = UISceneConfiguration(name: "External display", sessionRole: .windowExternalDisplayNonInteractive)
    c.delegateClass = ExternalDisplaySceneDelegate.self
    return c
}

// iOS 16-26: in application(_:configurationForConnecting:options:) return externalDisplayConfiguration()
// when connectingSceneSession.role == .windowExternalDisplayNonInteractive.

// iOS 27+: the scene connects only while this view controller is presented and the registration is enabled.
@available(iOS 27.0, *)
func registerGlassesScreen(on vc: UIViewController) -> UISceneAccessoryRegistration {
    // unverified: iOS 27 names taken from Apple's documentation, not compiled
    vc.registerSceneAccessory(.externalNonInteractive(sceneConfiguration: externalDisplayConfiguration()))
}
```

Apps without the scene life cycle can still set `window.screen` to an entry of `UIScreen.screens` (deprecated since
iOS 16), but TN3187 says apps built with the SDK after iOS 26 must adopt scenes or they will not launch.

Content rules: black background, white or light text, two or three lines in the lower part of the view, font around
7 % of the display height, no white panels. These glasses suit watching, video calls, lectures and speaker notes.
They are a poor fit for face-to-face conversations: the dark lenses hide your eyes and a cable runs to the phone.

## Input
Map actions to the phone screen, a Bluetooth headset's media buttons (`MediaSession`) or notification actions.

## Audio
When the glasses enumerate as a USB audio device, Android may route capture there. Pin the phone mic with
`AudioRecord.setPreferredDevice()` on a `TYPE_BUILTIN_MIC` device if your app records.

## Testing without hardware
- Android: emulator Extended controls > Displays (up to two), or Developer options > "Simulate secondary displays".
- Check: text appears, survives Home, another app and the screen timeout, disappears after a Recents swipe, comes
  back when the display is added again. iOS Simulator: add an external display from the I/O menu.

## Publishing and distribution
Nothing extra. No vendor approval, no store category, no permission declaration.

## Pitfalls
- `window.setType()` on a Presentation throws `InvalidDisplayException` on Android 12+. Do not set a window type.
- A presentation is disallowed on the display that shows your app's own top task (Android 16 QPR3 desktop mode on
  Pixel 8+ and recent Samsung phones can put it there). The system dismisses it; listen for dismissal and retry.
- Phone locked: SystemUI shows its own lock-screen presentation on external displays (AOSP `KeyguardDisplayManager`),
  so your text is replaced by a clock. `FLAG_KEEP_SCREEN_ON` on your window keeps the screen timeout from locking it
  (inference from AOSP, unverified on devices). The power button still locks.
- Samsung may start DeX when a display is connected. Mirroring mode is the known-good case (unverified under DeX).
- iPhone 16e, 17e and Air have USB 2 ports without video out. Lightning iPhones need Apple's Lightning Digital AV
  Adapter plus the glasses vendor's HDMI adapter (RayNeo, VITURE docs). The glasses also drain the phone's battery.

## Official resources
- Android: https://developer.android.com/reference/android/app/Presentation ,
  https://developer.android.com/develop/ui/compose/layouts/adaptive/support-connected-displays ,
  https://developer.android.com/studio/run/emulator-extended-controls
- Apple: https://developer.apple.com/documentation/uikit/presenting-content-on-a-connected-display ,
  https://developer.apple.com/documentation/technotes/tn3187-migrating-to-the-uikit-scene-based-life-cycle ,
  https://support.apple.com/en-us/105099 (iPhone models with USB-C video out)
- Vendors: https://tutorials.xreal.com/docs/glasses/one-series/first-use/connect-device ,
  https://www.rayneo.com/pages/product-compatibilities
