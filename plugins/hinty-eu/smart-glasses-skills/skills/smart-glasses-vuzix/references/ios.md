# iOS: UltraliteSDK setup, linking and background

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). Sources: the SDK
[README](https://github.com/Vuzix/UltraliteSDK-releases-iOS), the
[DocC reference](https://vuzix.github.io/UltraliteSDK-releases-iOS/documentation/ultralitesdk/), the
`Package.swift` and `UltraliteSDK.podspec` in that repository, and the BSD-3-Clause [sample apps](https://github.com/Vuzix/ultralite-sdk-ios-sample).

## Requirements

- iOS 14+, watchOS 9+ or macOS 11+, Swift 5.7+ (README; the podspec sets iOS 14.0 and watchOS 9.0).
- A Vuzix Z100 (no longer sold as of 2026-11-09; you need an existing pair). **Vuzix Connect is optional on iOS**: on iOS your app owns the Bluetooth connection
  ([Vuzix overview](https://support.vuzix.com/docs/overview-28)). Connect is still useful for firmware updates,
  settings and the notification path described below. The App Store listing
  ([Vuzix Connect](https://apps.apple.com/us/app/vuzix-connect/id6467056741)) shows version 1.10.1 from 2025-09-29,
  iOS 15.6+.
- Current SDK: **1.9.0** (release `v1.9.0`, 2025-03-17; CocoaPods trunk 1.9.0, 2025-03-18).

## Install

Pick one.

**Swift Package Manager.** In Xcode add `https://github.com/Vuzix/UltraliteSDK-releases-iOS`. The README tracks
`branch: "main"`; pin a version instead so builds are reproducible:

```swift
// Package.swift of your own package
dependencies: [
    // unverified: the tag is "v1.9.0"; SwiftPM normally accepts a leading "v" for version tags
    .package(url: "https://github.com/Vuzix/UltraliteSDK-releases-iOS", exact: "1.9.0"),
],
```

**CocoaPods** (also the path for React Native and Flutter, added for 1.9.0 after
[iOS #3](https://github.com/Vuzix/UltraliteSDK-releases-iOS/issues/3)):

```ruby
pod 'UltraliteSDK', '1.9.0'
```

The pod vendors a binary `UltraliteSDK.xcframework`. If your Podfile builds static libraries (no `use_frameworks!`),
check on the first CI build that the framework is embedded in the app (unverified).

**Embedded XCFramework.** Download `UltraliteSDK.zip` from the release, add the XCFramework to the target and embed
it. Do not commit it to a public repo: the licence forbids redistribution (§3.3).

## Info.plist

```xml
<key>NSBluetoothAlwaysUsageDescription</key>
<string>Bluetooth connects your Vuzix glasses to show text on them.</string>
<key>UIBackgroundModes</key>
<array>
    <string>bluetooth-central</string>
</array>
<key>LSApplicationQueriesSchemes</key>
<array>
    <string>vuzixconnect</string>
</array>
```

- `NSBluetoothAlwaysUsageDescription` is required by iOS for any CoreBluetooth use; both official samples set it.
- `bluetooth-central` is set by both official samples. It keeps Bluetooth events flowing while your app runs in the
  background; it does not keep a suspended app running.
- `vuzixconnect` is required by `isVuzixConnectInstalled()` (DocC).

## Link the glasses once, inside your app

Vuzix: "On iOS, each app must link to the glasses once, or the connected state will never become true"
([Display Process](https://support.vuzix.com/docs/display-process)). Two ways:

1. **`UltralitePickerController`**: an alert-style view controller that scans, lists nearby glasses and links the one
   the user taps. `init(_ callback: (() -> Void)?)`, `@MainActor`. Present it from any view controller.
2. **Your own UI** with `UltraliteManager`:

```swift
import CoreBluetooth
import UltraliteSDK

final class Z100Linker {
    private(set) var found: [CBPeripheral] = []

    /// Returns false when Bluetooth is off or permission is missing.
    func scan(onChange: @escaping ([CBPeripheral]) -> Void) -> Bool {
        let result = UltraliteManager.shared.startScan { [weak self] peripheral in
            DispatchQueue.main.async {
                guard let self else { return }
                self.found.append(peripheral)          // each device is reported once per scan
                onChange(self.found)
            }
        }
        return result == .SUCCESS                      // other cases: .DISABLED, .BLUETOOTH_PERMISSION_NEEDED
    }

    func link(_ peripheral: CBPeripheral, done: @escaping (Ultralite?) -> Void) {
        UltraliteManager.shared.stopScan()
        UltraliteManager.shared.link(device: peripheral) { device in
            DispatchQueue.main.async { done(device) }  // nil = link failed
        }
    }
}
```

Facts from DocC:

- `link(device:callback:)` may show iOS pairing prompts, so the result can take a while.
- Linking a new device unlinks the previous one. `UltraliteManager.shared.unlink()` removes the link.
- `UltraliteManager.shared.isLinked` is a `Bindable<Bool>`; `currentDevice` is the linked `Ultralite`.
- The `startScan` discussion names `BLUETOOTH_DISABLED`, but the enum case is `DISABLED`.
- The README pattern checks `currentDevice` at launch, which implies the link survives restarts (unverified).

If linking keeps failing after the glasses were used with another phone, have the user forget the glasses in iOS
Settings > Bluetooth and link again (unverified, general CoreBluetooth advice).

## Connection and control

- `currentDevice?.isConnected` is a `Bindable<Bool>`. `bind(listener:shouldFire:)` with `shouldFire: true` calls
  the listener immediately. Keep a strong reference to every `BondListener`; the samples store them as properties.
- `isPaired` means the device has exchanged messages with the SDK at some point, not only Bluetooth bonding.
- `requestControl(layout:timeout:hideStatusBar:showTapAnimation:maxNumTaps:autoReleaseControlOnDisplayTimeout:) -> Bool`.
  `timeout` in seconds, `0` keeps the display on. `autoReleaseControlOnDisplayTimeout: true` releases control when
  the display times out, which suits a glanceable "quick view".
- The old `setLayout(layout:timeout:hideStatusBar:)` is deprecated in favour of `requestControl`.
- `releaseControl()` when you are done.
- **No public "control lost" signal.** DocC lists no control property or notification on `Ultralite`. If another app
  takes the display, you will not hear about it. Re-request control on the next user action, or when your app
  becomes active again during a running session (never in a loop).
- Alternative: subclass `UltraliteBaseViewController`. Set `layout`, `displayTimeout`, `hideStatusBar`,
  `showTapAnimation` and `maximumNumTaps` before `startControl()`, call `stopControl()` when done, and override
  `onTapEvent(taps:)`, `onPowerButtonEvent(isOn:)`, `onDisplayStateEvent(isOn:)`, `onDisplayTimeoutEvent()`,
  `onDisconnected()` and `onAppLeave()`. `isActive` tells whether this controller holds control. `showPairingPicker()`
  presents the picker. The `onTap(notification:)` family is deprecated.

## Background and the locked phone

Not documented by Vuzix. What is known:

- `onAppLeave()` exists on the base view controller ("Called when application leaves the foreground") and the official
  sample stops control there. That is a sample choice, not a rule.
- `bluetooth-central` delivers Bluetooth events in the background, but iOS suspends your app unless it has its own
  reason to run, such as an active audio session for microphone capture.
- Request control while your app is in the foreground. Treat `requestControl` from the background as likely to fail
  (unverified).
- Whether control survives locking the phone is unknown (unverified). If a session must continue in the background,
  test it on hardware first, and plan a fallback to `sendNotification`.

```swift
import UIKit
import UltraliteSDK

/// Re-takes the display when the user comes back to the app during a session.
final class ForegroundControl {
    private var token: NSObjectProtocol?
    var sessionRunning = false

    init(takeControl: @escaping () -> Void) {
        token = NotificationCenter.default.addObserver(
            forName: UIApplication.didBecomeActiveNotification, object: nil, queue: .main
        ) { [weak self] _ in
            guard self?.sessionRunning == true,
                  UltraliteManager.shared.currentDevice?.isConnected.value == true else { return }
            takeControl()   // your requestControl + canvas setup; old text ids are invalid
        }
    }

    deinit { if let token { NotificationCenter.default.removeObserver(token) } }
}
```

## Notifications

`sendNotification(title:message:) -> String` needs no control. DocC: if Vuzix Connect is installed, your app has
notification permission and the phone supports ANCS, the notification goes through ANCS (queued). Otherwise it goes
straight to the glasses, with no queue: it replaces whatever notification is showing. Ask for permission with
`UNUserNotificationCenter.current().requestAuthorization(options: [.alert])`.

`Ultralite` conforms to `UNUserNotificationCenterDelegate` (DocC). If your app or a library already owns the
notification delegate, forwarding its callbacks to the device may be needed (unverified). DocC says the returned
string identifies the notification, but documents no clear method on iOS.

## Threading

Not documented. `UltralitePickerController` and `UltraliteBaseViewController` are `@MainActor`, and the samples hop to
`DispatchQueue.main` inside scan and link callbacks. Call the SDK from the main thread and dispatch to main inside
`BondListener` closures before touching your state.

## Other platforms and properties

- watchOS and macOS are supported by the same package. The sample repo has a SwiftUI app with a watchOS target
  ([iOS #2](https://github.com/Vuzix/UltraliteSDK-releases-iOS/issues/2)).
- `getIntProperty` / `setIntProperty` and the string variants take `Ultralite.Property` (`deviceName`, `brightness`,
  `version`, `fontSize`). Value ranges are not documented (unverified).
- `batteryLevel` (`Bindable<Int>`) and `batteryChargeStatus` (`Bindable<Bool>`). The DocC summary of `batteryLevel`
  is wrong (it says "mac address"); read it as a percentage and treat negative values as unknown (unverified).
