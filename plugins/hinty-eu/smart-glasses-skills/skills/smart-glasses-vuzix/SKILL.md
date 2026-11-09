---
name: smart-glasses-vuzix
description: Vuzix Z100 apps on Android and iOS with the Vuzix Ultralite SDK - bind through Vuzix Connect on Android or link the glasses inside your own app on iOS, request and release control of the display, draw text on the 640x480 monochrome green canvas, run live captions with LiveText, send notifications without control, and handle 1 to 3 taps on the frame. Covers JitPack, Swift Package Manager and CocoaPods setup, the SDK licence, background behaviour and the missing microphone and speaker. The Z100 is no longer sold, so this is for apps that serve existing owners. Use when the user mentions Vuzix, Z100, Ultralite, UltraliteSDK, Vuzix Connect or the Mentra Mach1 (same hardware), even for small tasks such as mapping taps to actions, because taps only arrive while the app holds control with a tap count set. Not for Vuzix Blade, Blade 2, M400 or M4000, which run Android on the glasses themselves, and not for writing MentraOS miniapps.
license: Apache-2.0
metadata:
  version: "1.0.1"
  last-updated: "2026-11-09"
---

# Vuzix Z100 with the Ultralite SDK

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). API names were checked against the public
[Android Javadoc](https://vuzix.github.io/ultralite-sdk-android/javadoc) and the
[iOS DocC](https://vuzix.github.io/UltraliteSDK-releases-iOS/documentation/ultralitesdk/). The snippets below were
written for this skill and not compiled here. Anything marked `unverified` must be checked on a real Z100.

## Decide first

**The Z100 is no longer sold** (as of 2026-11-09, details under "Licence and publishing"). The SDK, Vuzix Connect and
store distribution still work, so build for people who already own a pair, and do not make the Z100 the first or only
target of a new product.

The Z100 is a display only: 640x480, monochrome green, right eye, about 30 degrees field of view, Bluetooth LE.
It has **no microphone, no speaker and no camera**, and the SDK has no audio API. Your code runs on the phone; the
glasses render what the SDK sends.

| You want | Use | Needs control |
|---|---|---|
| Interactive screen, captions, a HUD that answers taps | `requestControl` + canvas, text layout or `LiveText` | yes |
| Passive alerts that coexist with other apps | `sendNotification` | no |
| Zero SDK work | Post a normal phone notification; Vuzix Connect mirrors it (ladder rung 4) | no |
| Audio in, audio out | Phone microphone, phone speaker or Bluetooth earbuds | n/a |
| One codebase for Z100 and other glasses | MentraOS miniapp (beta, no public distribution as of 2026-11-08) | n/a |

In the display-text ladder of the `smart-glasses` skill the Z100 supports rung 1 (**Vendor SDK**, this skill) and
rung 4 (**phone notification mirrored by the companion app**). Rung 5 (voice in the ear) only works through the
phone or earbuds, never through the glasses.

Current versions (as of 2026-11-08, both unchanged since March 2025):

- Android: `com.vuzix:ultralite-sdk-android:1.9` on JitPack ([repo](https://github.com/Vuzix/ultralite-sdk-android), tag `1.9`, 2025-03-14).
- iOS, watchOS, macOS: `UltraliteSDK` 1.9.0 via SPM, CocoaPods or XCFramework ([repo](https://github.com/Vuzix/UltraliteSDK-releases-iOS), release `v1.9.0`, 2025-03-17).

## How the two platforms differ

| | Android | iOS |
|---|---|---|
| Who owns Bluetooth | The **Vuzix Connect** app (`com.vuzix.connect`, required) | **Your app**, through CoreBluetooth inside the SDK |
| Pairing | The user pairs once in Vuzix Connect | Each app must link the glasses once ([Vuzix](https://support.vuzix.com/docs/display-process)) |
| Your permissions | None required by the SDK | Bluetooth usage string, `bluetooth-central` background mode |
| State API | `LiveData` (`getAvailable`, `getLinked`, `getConnected`, `getControlledByMe`) | `Bindable` (`isLinked`, `isConnected`) + `BondListener` |
| Control lost signal | `getControlledByMe()` emits `false` | none in the public API |
| Taps | `EventListener.onTap(tapCount)` | `Notification.Name.tap` with `userInfo["tap"]` |
| Minimum OS | Android 12 | iOS 14, watchOS 9, macOS 11 |

## The control model (both platforms)

1. The glasses show one app at a time. **Control goes to the last app that requests it**
   ([Display Process](https://support.vuzix.com/docs/display-process)). Another Z100 app can take it from you at
   any moment.
2. `requestControl` succeeds only when the SDK is available, glasses are linked and they are connected.
3. Layout, font, canvas texts, images and taps are configured **after** control is granted. Without control those
   calls do nothing, silently.
4. When control is lost, everything you configured is gone. Set it up again on the next grant.
5. Call `releaseControl()` as soon as the session ends. If you do not, the last frame can stay on the glasses.
   Releasing puts the glasses back into notification mode.
6. Request control only for a user-driven session. For passive information Vuzix recommends notifications instead.
   Never re-request in a loop: you would fight the other app for the display.

## Core flow on Android

Setup details (Gradle, manifest, lifecycle): [references/android.md](references/android.md).

```kotlin
import android.content.Context
import android.os.Handler
import android.os.Looper
import androidx.lifecycle.Observer
import com.vuzix.ultralite.Anchor
import com.vuzix.ultralite.EventListener
import com.vuzix.ultralite.Layout
import com.vuzix.ultralite.TextAlignment
import com.vuzix.ultralite.TextWrapMode
import com.vuzix.ultralite.UltraliteColor
import com.vuzix.ultralite.UltraliteSDK

/** One text block on the Z100. Call every method from the main thread (LiveData rule). */
class Z100Text(context: Context, private val onAction: (String) -> Unit) {
    private val sdk = UltraliteSDK.get(context.applicationContext)
    private val main = Handler(Looper.getMainLooper())
    private var wanted = false
    private var textId = -1
    private var pending: String? = null

    private val onConnected = Observer<Boolean> { connected ->
        // Fires right away with the current value, then on every change
        if (connected == true && wanted && !sdk.isControlledByMe()) sdk.requestControl()
    }
    private val onControl = Observer<Boolean> { mine ->
        if (mine == true) setUp() else textId = -1   // lost: layout and canvas are gone
    }
    private val events = object : EventListener {
        override fun onTap(tapCount: Int) {
            when (tapCount) { 1 -> onAction("repeat"); 2 -> onAction("skip") }
        }
    }

    fun start() {
        wanted = true
        sdk.addEventListener(events)
        sdk.getControlledByMe().observeForever(onControl)
        sdk.getConnected().observeForever(onConnected)
        // isAvailable() false = Vuzix Connect missing or not bound yet; isLinked() false = not paired in Connect
    }

    private fun setUp() {
        // timeout 30 s (0 = keep on), hide status bar, no tap animation, report single and double taps
        sdk.setLayout(Layout.CANVAS, 30, true, false, 2)
        val canvas = sdk.getCanvas()
        textId = canvas.createText(" ", TextAlignment.LEFT, UltraliteColor.WHITE, Anchor.TOP_LEFT,
            0, 0, UltraliteSDK.Canvas.WIDTH, UltraliteSDK.Canvas.HEIGHT, TextWrapMode.WRAP, true)
        canvas.commit()                                   // nothing shows until commit()
        pending?.let { show(it) }
    }

    fun show(text: String) {
        pending = text                                    // redrawn after the next grant
        if (textId < 0) return
        val canvas = sdk.getCanvas()
        canvas.updateText(textId, text)
        canvas.commit()
    }

    fun stop() {
        wanted = false
        sdk.removeEventListener(events)
        sdk.releaseControl()                              // back to notification mode
        // Remove observers a moment later so the final "control lost" still arrives
        main.postDelayed({
            sdk.getConnected().removeObserver(onConnected)
            sdk.getControlledByMe().removeObserver(onControl)
        }, 500)
        textId = -1
        pending = null
    }
}
```

## Core flow on iOS

Setup details (SPM or CocoaPods, Info.plist, linking, background): [references/ios.md](references/ios.md).

```swift
import UIKit
import UltraliteSDK

/// One text block on the Z100. Call everything on the main thread.
final class Z100Text {
    var onAction: ((String) -> Void)?
    private var connectedListener: BondListener<Bool>?   // keep a strong reference
    private var tapObserver: NSObjectProtocol?
    private var textId: Int?
    private var pending: String?

    /// First run: the user links the glasses inside your app (required once per app on iOS).
    @MainActor func linkIfNeeded(from presenter: UIViewController) {
        if UltraliteManager.shared.currentDevice != nil {
            start()
            return
        }
        // unverified: when exactly the callback fires (link done or picker dismissed) is not documented
        presenter.present(UltralitePickerController { [weak self] in self?.start() }, animated: true)
    }

    func start() {
        guard connectedListener == nil, let device = UltraliteManager.shared.currentDevice else { return }
        let listener = BondListener<Bool>(listener: { [weak self] connected in
            DispatchQueue.main.async {
                if connected { self?.takeControl() } else { self?.textId = nil }
            }
        })
        connectedListener = listener
        device.isConnected.bind(listener: listener, shouldFire: true)
        tapObserver = NotificationCenter.default.addObserver(forName: .tap, object: nil, queue: .main) { [weak self] note in
            switch Z100Text.tapCount(note) {
            case 1: self?.onAction?("repeat")
            case 2: self?.onAction?("skip")
            default: break
            }
        }
    }

    /// Call while the app is in the foreground (see references/ios.md, background).
    private func takeControl() {
        guard let device = UltraliteManager.shared.currentDevice else { return }
        let granted = device.requestControl(layout: .canvas, timeout: 30, hideStatusBar: true,
                                            showTapAnimation: false, maxNumTaps: 2,
                                            autoReleaseControlOnDisplayTimeout: false)
        guard granted else { return }
        device.canvas.clear(shouldClearBackground: true)   // old text ids are not valid after a new grant
        textId = device.canvas.createText(text: " ", textAlignment: .left, textColor: .white, anchor: .topLeft,
                                          xOffset: 0, yOffset: 0, isVisible: true,
                                          width: Ultralite.DISPLAY_WIDTH, height: Ultralite.DISPLAY_HEIGHT,
                                          wrapMode: .wrap)
        device.canvas.commit()
        if let text = pending { show(text) }
    }

    func show(_ text: String) {
        pending = text                                    // redrawn after the next grant
        guard let device = UltraliteManager.shared.currentDevice, let id = textId else { return }
        device.canvas.updateText(text: text, id: id)
        device.canvas.commit()
    }

    func stop() {
        UltraliteManager.shared.currentDevice?.releaseControl()
        if let l = connectedListener { UltraliteManager.shared.currentDevice?.isConnected.unbind(listener: l) }
        if let t = tapObserver { NotificationCenter.default.removeObserver(t) }
        connectedListener = nil; tapObserver = nil; textId = nil; pending = nil
    }

    /// The value type of userInfo["tap"] is not documented: accept the common numeric wrappers.
    static func tapCount(_ note: Notification) -> Int {
        switch note.userInfo?["tap"] {
        case let v as Int64: return Int(v)
        case let v as Int: return v
        case let v as NSNumber: return v.intValue
        default: return 0
        }
    }
}
```

## Taps

Any touch on the frame is a tap; left and right are not distinguished, and there are no swipes. Set `maxNumTaps`
(Android `setLayout`, iOS `requestControl`) to 1, 2 or 3; the default 0 reports **nothing**. Higher values add
delay before each tap is reported. Use 2 for "repeat / skip", add 3 only if you need "hide". Ignore taps while
nothing is on screen (adjusting the glasses triggers false taps). Details: [references/input.md](references/input.md).

## Text on the display

- Shortest path: `Layout.TEXT_BOTTOM_LEFT_ALIGN` (iOS `.textBottomLeftAlign`) + `sendText`. One font, one colour,
  the glasses place and wrap the text.
- Positioned text: `Layout.CANVAS`, up to **7 text blocks**, 3 small images, 1 animation and a 640x480 background.
  Four levels per pixel: `BLACK` (transparent, no light), `DIM`, `MID`, `WHITE`.
- **Live captions:** the `LiveText` helper (Android `com.vuzix.ultralite.utils.scroll.LiveText`, iOS
  `ScrollLayout.LiveText`) on the `SCROLL` layout appends words to the bottom line and scrolls finished lines up, like
  TV closed captions. It renders text on the phone into image slices, so any script the phone font supports works.
- Budget: about 42 characters of mixed Latin text per line in the text layout at the default size, up to 7 lines
  (MentraOS measurement, community, unverified by us). Keep captions to 2-3 lines.

Layouts, fonts, scripts, RTL, images and character budgets: [references/display.md](references/display.md).

## Notifications without control

Android `sendNotification(key, title, message, peekText, icon)` and `clearNotification(key)`, iOS
`sendNotification(title:message:) -> String`. They work while another app holds control, but then only a one-line
peek (Android `peekText` or the title) is shown. Prefer them for passive alerts; do not send the same text as a
notification and on your canvas at the same time.

## Licence and publishing (as of 2026-11-09)

- The SDK is proprietary, under the
  [Vuzix SDK License and Confidentiality Agreement](https://www.vuzix.com/pages/vuzix%C2%AE-software-development-kit-license-and-confidentiality-agreement)
  (dated 2023-07-24). You accept it by clicking or **by using the SDK** (§2.2). No signature, key, account or fee.
- Grant (§3.1): limited, worldwide, royalty-free, non-exclusive, solely for apps that run on or communicate with
  Vuzix hardware.
- Do not copy (except backup), modify, redistribute, decompile or reverse engineer the SDK (§3.3). Depend on JitPack
  or CocoaPods; do not commit the AAR or XCFramework to a public repo.
- Apps for military, defence, law enforcement or first-responder markets need Vuzix's prior written consent (§4.7).
- No right to Vuzix trademarks or logos (§3.7). Vuzix may collect usage statistics only after asking (§6.1).
- The official sample apps are separate repos under BSD-3-Clause.
- Publishing: a Z100 app is an ordinary phone app on Google Play or the App Store. Vuzix runs no store and no review
  for Z100 apps ([Extentos](https://extentos.com/docs/ecosystem/platforms/vuzix), community). Vuzix Connect is still
  listed on both stores (2026-11-09).
- Hardware: launched 2024-11-20 at USD 499 ([Vuzix](https://ir.vuzix.com/news-events/press-releases/detail/2104/vuzix-announces-general-availability-of-z100-smart-glasses)).
  **Vuzix no longer lists the Z100.** Its product page showed "Sold Out" on 2026-07-10 and redirects to the general
  smart-glasses page since 2026-09-06 (still on 2026-11-09); that page offers the LX1, M400 and the Ultralite OEM
  Platform, not the Z100 ([archived 2026-10-12](https://web.archive.org/web/20261012144148/https://www.vuzix.com/pages/smart-glasses)).
  Vuzix's Q2 2026 report blames part of the drop in product sales on discontinued products: "smart glasses that were
  discontinued at the end of 2025" (CFO on the 2026-08-13 call, [transcript](https://www.tradingkey.com/news/transcripts/262107145-tradingkey)),
  "products that were discontinued" ([10-Q](https://ir.vuzix.com/reports-filings/all-sec-filings/content/0001104659-26-095889/0001104659-26-095889.pdf)).
  Neither names the products; the Z100 leaving the catalogue fits that timing. Mentra's Mach1 is a white-label Z100
  ([Vuzix on X](https://x.com/Vuzix/status/1886838744050811080), 2025-02), formerly sold by Mentra and no longer
  listed on mentraglass.com (2026-11-09).
- **Build only for existing owners.** Nobody new can buy the glasses from Vuzix or Mentra, so a Z100 adapter makes
  sense as one rung behind a shared interface, not as the product's main target.

This is a reading of the licence for engineering decisions, not legal advice.

## Testing without hardware

Vuzix ships no glasses simulator. Put the SDK behind your own small interface (`connect`, `show`, `clear`,
`onAction`) and test your logic against a fake. On Android without Vuzix Connect, `isAvailable()` stays `false`, which
is a useful "not installed" test. The iOS XCFramework includes a Simulator slice, so the app builds and runs there,
but nothing connects. See [references/troubleshooting.md](references/troubleshooting.md) for a first-day hardware
checklist.

## Pitfalls

1. Forgetting `commit()` after canvas changes: nothing appears.
2. Calling `setLayout`, `setFont` or canvas methods before control is granted: silently ignored.
3. `maxNumTaps` left at 0: taps never arrive ([iOS #4](https://github.com/Vuzix/UltraliteSDK-releases-iOS/issues/4)).
4. Not releasing control: the old frame stays on the glasses.
5. iOS: no public "control lost" event. Re-request control when your app returns to the foreground during a session.
6. iOS: `isConnected` never turns true until your app has linked the glasses once.
7. Android: `isAvailable()` can be `false` right after start (the SDK "may not be available for immediate use");
   observe `getAvailable()` before telling the user Vuzix Connect is missing.
8. More than 7 canvas texts or images over 9900 bytes: older blocks are overwritten, big images are dropped.

## References

- [references/android.md](references/android.md) - JitPack dependency, manifest, Vuzix Connect, lifecycle, threading.
- [references/ios.md](references/ios.md) - SPM, CocoaPods, Info.plist, linking in your app, background behaviour.
- [references/display.md](references/display.md) - layouts, canvas limits, fonts, scripts and RTL, line budgets, LiveText.
- [references/input.md](references/input.md) - taps, power button, display events, mapping to app actions.
- [references/troubleshooting.md](references/troubleshooting.md) - known issues with links, support, hardware checklist.

For choosing between brands, the cross-brand ladder and other glasses, use the `smart-glasses` skill
(`references/brands/vuzix-z100.md`). For speech-to-text and caption timing, use `smart-glasses-live-captions`.
