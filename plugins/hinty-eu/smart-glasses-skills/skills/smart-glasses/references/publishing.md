# Publishing glasses apps: what can ship today

Read this before you promise users a release date: which glasses platforms let you ship to everyone as of 2026-11-08,
through which channel and review, and the store-compliance checklist for the phone app that carries the glasses code.

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet, nothing published by us). Every row links to
the source it rests on; re-check the source before you plan a launch.

> **Known to be changing (as of 2026-11-08)**
> - Meta DAT: "Publishing DAT integrations to all users isn't open yet" ([Meta staff, 2026-11-05](https://github.com/meta/meta-wearables-dat-android/discussions/229)); no date.
> - Meta DAT on iOS: Meta "isn't able to add third-party apps to its MFi Product Plan or issue PPIDs at this time" ([ios #313](https://github.com/meta/meta-wearables-dat-ios/discussions/313), 2026-09-28).
> - Meta Web Apps: Meta "will share how to submit your experience soon" ([Explore](https://developers.meta.com/wearables/explore)).
> - Android XR display glasses: "stay tuned for more updates on distribution" ([package and distribute](https://developer.android.com/develop/xr/package-and-distribute)); no display glasses on sale.
> - MentraOS: "There is currently no way to distribute a miniapp" ([distribution](https://docs.mentraglass.com/app-devs/getting-started/distribution.md)).
> - Even Hub paid apps: "TBD. There is no paid distribution yet" ([FAQ](https://hub.evenrealities.com/docs/reference/faq)).
> - Snap Specs: pre-order, "Expected to ship starting Fall 2026" ([specs.com](https://www.specs.com/smart-glasses/specs-27)).
> - Google Play: 16 KB page support blocks app updates from 2027-02-01 ([page sizes](https://developer.android.com/guide/practices/page-sizes)); targetSdk 36 required since 2026-08-31 ([target SDK](https://developer.android.com/google/play/requirements/target-sdk)).
> - Vuzix Z100: no longer sold. Vuzix no longer lists it (product page redirects since 2026-09-06, still on 2026-11-09) and its Q2 2026 report cites smart glasses discontinued at the end of 2025 ([vuzix-z100.md](brands/vuzix-z100.md#publishing-and-distribution)). Apps still publish, for existing owners only.
> - Rokid Glasses 2 support in CXR-L is unverified.

## Can everyone install it today?

| Target | Everyone today? | Channel | Vendor review | Before release | Source |
|---|---|---|---|---|---|
| Even Realities G2 plugin | **Yes**, free apps only | Even Hub store, worldwide, no region targeting | Manual review | QR sideload, private build, beta channel with invited testers | [FAQ](https://hub.evenrealities.com/docs/reference/faq), [submission](https://hub.evenrealities.com/docs/ship/app-submission) |
| Meta DAT, Android | **No** | APK may be on Google Play, but only users in your invite-only Beta channel can register; others see "Error loading this integration" | No public application or review process yet | Developer Mode, one Beta release channel | [discussion #229](https://github.com/meta/meta-wearables-dat-android/discussions/229) |
| Meta DAT, iOS | **No** | No App Store: the SDK's MFi accessory needs a PPID Meta cannot issue | n/a | TestFlight plus a Beta channel ("No PPID is needed for that") | [ios #313](https://github.com/meta/meta-wearables-dat-ios/discussions/313) |
| Meta Ray-Ban Display Web Apps | **No** | URL or QR for wearers in Developer Mode; the add screen says "unverified" | Explore is curated; submission "soon" | Developer Mode | [meta-display.md](brands/meta-display.md#publishing-and-distribution) |
| Ray-Ban Meta, Oakley Meta as a Bluetooth headset (TTS, HFP) | **Yes** | Your normal store listing | None, no Meta component (our reading) | n/a | [meta-audio-glasses.md](brands/meta-audio-glasses.md#publishing-and-distribution) |
| Rokid Glasses (CXR-L) | **Yes** | Your own Google Play or App Store listing; the user authorises your app in Hi Rokid | None documented for Android; iOS: the CXR-L docs (v1.2, 2026-09-08) require a registered Rokid developer account with your bundle ID | n/a | [SDK overview](https://developerdoc.rokid.com/sdk?lang=zh), [Rokid skill](../../smart-glasses-rokid/SKILL.md#publishing) |
| Vuzix Z100 | **Yes**, but the hardware is discontinued (existing owners only) | Your own store listing | None; SDK licence accepted by use | n/a | [vuzix-z100.md](brands/vuzix-z100.md#publishing-and-distribution) |
| Android XR audio glasses | **Yes** | Google Play mobile track, same APK | Play policies plus the glasses policies | Emulator | [package and distribute](https://developer.android.com/develop/xr/package-and-distribute) |
| Android XR display glasses | **Not yet** | "stay tuned" | n/a | Emulator only | same |
| MentraOS miniapp | **No** | None; the packaged ZIP is for a future store | n/a | QR on the local network | [mentra.md](brands/mentra.md) |
| Brilliant Labs Halo, Frame | **Yes** | Your own host app through any channel; "Halo doesn't have its own app launcher" | None | n/a | [brilliant-labs.md](brands/brilliant-labs.md) |
| Snap Specs Lens | **When Specs ship** | Publish from Lens Studio; Lens Explorer is reviewed separately | Moderation in 2-3 business days, 25 MB, no Experimental APIs | Lens Studio Preview | [publishing](https://developers.snap.com/spectacles/get-started/start-building/publishing-lens) |
| USB-C display glasses | **Yes** | Your normal store listing | None | n/a | [usb-c-displays.md](brands/usb-c-displays.md#publishing-and-distribution) |
| RayNeo X3 Pro (standalone) | **Sideload only** | `adb install` after enabling ADB; no public third-party store found | n/a | ADB | [standalone-android-glasses.md](brands/standalone-android-glasses.md#publishing-and-distribution) |
| INMO Air3 (standalone) | **Yes**, global version | Google Play on the glasses | Play | n/a | same |
| Phone notifications (rung 4) | **Yes** | Your normal app; the user enables it in the companion app | None | n/a | [notification-glasses.md](brands/notification-glasses.md#publishing-and-distribution) |

Practical rule: keep a brand-independent core and one adapter per brand, ship the adapters that can ship today (Even,
Rokid, Vuzix for existing owners, USB-C, notifications, voice), and keep Meta DAT behind a tester flag until publishing opens. For where
each rung fits, see [display-text-ladder.md](display-text-ladder.md) and [choose-target.md](choose-target.md).

## Brand notes that decide a launch

- **Even Hub.** `app.json`: permanent `package_id`, a `name` without "Even" (auto-rejected), immutable versions, exact
  network origins (`wss://` too). Reviewers test with the phone locked and the Even app backgrounded, glasses and ring
  input only, after 2 minutes idle; they expect a message on the glasses when setup is missing, a root double-tap exit
  through `shutDownPageContainer(1)`, a privacy policy covering every permission, a greyscale icon and no secrets in
  the bundle. No rollback. Details in [even-g2.md](brands/even-g2.md#publishing-and-distribution) and Even's skill
  `even-build-and-deploy` (`npx skills add even-realities/everything-evenhub`).
- **Meta.** Developer Mode is per device and allows one unpublished app at a time; Developer Terms §4.1 require
  Integration Review before general release. The [Acceptable Use Policy](https://wearables.developer.meta.com/acceptable-use-policy)
  binds unpublished apps too. Meta Ray-Ban Display is sold only in the US, CA, UK, FR, DE and IT; the full toolkit is
  limited to supported countries ([meta-display.md](brands/meta-display.md#publishing-and-distribution)).
- **Rokid.** No licence is published for CXR-L: depend on Rokid's Maven, never bundle the SDK files. Explain the
  one-time "unverified app" confirmation in Hi Rokid during onboarding (community report).
- **Vuzix.** The licence requires written consent for military, defence, law enforcement and first-responder apps,
  and forbids redistributing or reverse engineering the SDK.
- **Snap.** The developer policy says "Functionality should not be locked behind a purchase or paywall"
  ([policy](https://developers.specs.com/developer-policy)); pin the Lens Studio version per device generation.
- **Trademarks.** Describe compatibility in plain words ("works with Vuzix Z100"); no vendor logos, no implied
  endorsement. Meta's and Vuzix's terms grant no rights to their marks.

## Store-compliance checklist: iOS

- [ ] Built with Xcode 26 and the iOS 26 SDK, required for App Store Connect uploads since April 2026
      ([upcoming requirements](https://developer.apple.com/news/upcoming-requirements/)).
- [ ] `PrivacyInfo.xcprivacy` declares approved reasons for every required-reason API; since 2024-05-01 uploads without
      them are refused, and listed third-party SDKs need their own manifest and, as binaries, a signature
      ([Apple, 2024-02-29](https://developer.apple.com/news/?id=3d8a9yyh)). Check each glasses SDK you add.
- [ ] Purpose strings for what you use: `NSMicrophoneUsageDescription`, `NSBluetoothAlwaysUsageDescription`,
      `NSSpeechRecognitionUsageDescription` (Apple speech recognition), `NSLocalNetworkUsageDescription` (LAN devices
      or a dev server). Say what you do with the audio.
- [ ] `UIBackgroundModes` only for what you really do: `audio` for live capture, `bluetooth-central` for BLE glasses
      (Vuzix, Halo). Guideline 2.5.4 limits background modes to their intended purposes.
- [ ] External Accessory: `UISupportedExternalAccessoryProtocols` or the `external-accessory` background mode means App
      Review wants the accessory maker's MFi PPID in the review notes. Without one, remove them. Meta DAT is blocked here
      today, and whether its `Info.plist` entries are needed is disputed ([meta-display.md](brands/meta-display.md#pitfalls)).
- [ ] Export compliance: set `ITSAppUsesNonExemptEncryption` to `NO` only if you use exempt encryption such as HTTPS
      through the OS; otherwise answer the questions in App Store Connect
      ([Apple](https://developer.apple.com/documentation/security/complying-with-encryption-export-regulations);
      Meta testers asked the same in [ios #361](https://github.com/meta/meta-wearables-dat-ios/discussions/361)).
- [ ] Guideline 2.5.14: explicit consent and a visible or audible indication while recording; App Privacy answers
      cover audio data, transcripts and any third-party speech-to-text.
- [ ] External display apps adopt the scene life cycle (TN3187) or will not launch when built with newer SDKs
      ([usb-c-displays.md](brands/usb-c-displays.md)).
- [ ] TestFlight external testers go through Beta App Review; internal testers do not.
- [ ] Mention the required companion app and glasses in the description and review notes, and give reviewers a demo
      mode that works without the glasses (for example the phone screen or notification path).

## Store-compliance checklist: Android and Google Play

- [ ] `targetSdk` 36 for new apps and updates since 2026-08-31 (extension to 2026-11-01 on request). Play lists a lower
      API 34 floor for Android XR apps; projected glasses code ships inside your phone app, so plan for the phone rule
      (our reading).
- [ ] 16 KB page sizes if any native code is in the APK, including vendor AARs (Rokid CXR-L ships native libraries;
      a Mentra SDK starter kit had unaligned libraries, [#38](https://github.com/Mentra-Community/Mentra-Bluetooth-SDK-Starter-Kit/issues/38)).
      Check with APK Analyzer or `zipalign -c -P 16 -v 4 app.apk`; AGP 8.5.1+ and NDK r28+ align by default.
- [ ] Bluetooth: request `BLUETOOTH_CONNECT` (and `BLUETOOTH_SCAN`, with `android:usesPermissionFlags="neverForLocation"`
      if you never derive location) at runtime; a manifest entry alone does nothing. Do not mark
      `android.hardware.bluetooth` as required unless the app is useless without it.
- [ ] Foreground services typed and declared: `microphone` (`FOREGROUND_SERVICE_MICROPHONE`, started while visible),
      `connectedDevice` (`FOREGROUND_SERVICE_CONNECTED_DEVICE`, needs e.g. `BLUETOOTH_CONNECT` granted),
      `mediaPlayback` for long TTS; declare each type in Play Console under App content
      ([service types](https://developer.android.com/develop/background-work/services/fgs/service-types)).
- [ ] `POST_NOTIFICATIONS` runtime permission on Android 13+ if you use the notification rung.
- [ ] `<queries>` for every companion package you look up (`com.vuzix.connect`, Meta AI); the Rokid AAR merges its own.
- [ ] Data safety form: audio recordings, transcripts, whether a speech-to-text provider receives them, encryption in
      transit, deletion. Prominent in-app disclosure before collecting audio
      ([User Data policy](https://support.google.com/googleplay/android-developer/answer/10144311)).
- [ ] Android XR glasses policies if you target them: no persistent background recording, no bystander voice or face
      identification, camera double press only for the camera, Back always exits
      ([quality guidelines](https://developer.android.com/docs/quality-guidelines/android-xr/augmented)).
- [ ] New personal developer accounts (created after 2023-11-13) need a closed test with at least 12 testers opted in
      for 14 days before production ([Play help](https://support.google.com/googleplay/android-developer/answer/14151465)).
- [ ] Release builds tested with R8 on: Rokid's consumer rules strip `Log.d` app-wide, and vendor SDKs may need keep
      rules ([Rokid setup](../../smart-glasses-rokid/references/setup.md#r8-and-logging),
      [Vuzix Android](../../smart-glasses-vuzix/references/android.md#release-builds)).

Privacy and recording rules in more depth: [audio-routing.md](audio-routing.md#privacy-rules).
