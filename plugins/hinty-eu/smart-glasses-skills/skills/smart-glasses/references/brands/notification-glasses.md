# Phone notifications mirrored by the glasses (the no-SDK rung)

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). Brand behaviour comes from vendor support
pages and app store listings; nobody documents exactly which third-party notifications are forwarded.

## At a glance
- Display: whatever the glasses show for a notification, usually an app name or title plus one to three lines for a
  few seconds.
- How your app puts text on it: rung 4. Post a normal phone notification; the glasses' companion app (or the OS on
  Android XR) forwards it. No SDK, no vendor account.
- Input: usually dismiss only. Android XR display glasses show the system clear action, plus direct reply for
  `MessagingStyle`; your own action buttons stay on the phone.
- Microphone for your app: not part of this path. Record on the phone.
- Speaker: Android XR audio glasses read bridged notifications aloud; some companion apps can too (Rokid, INMO Go3).
  Elsewhere use rung 5 (your own TTS).
- Phones: Android (companion apps use a notification listener) and iOS (glasses read Apple Notification Center Service,
  ANCS, over Bluetooth).
- Publishing to everyone today: yes, no store review. The user must enable your app in the companion app on most brands.
- Test without hardware: Android XR glasses emulator shows bridged notifications. For other brands you need the glasses.
- Official agent skill: none for this rung.

## Which glasses mirror notifications (as of 2026-11-08)

| Glasses | Third-party apps | Per-app control | Read aloud | Source and confidence |
|---|---|---|---|---|
| Even Realities G2 / G1 | Yes, any app that has posted once | Yes, toggle per app; G1 has less common apps off by default | No speaker | [support](https://support.evenrealities.com/hc/en-us/articles/14274501482639-Notifications) official |
| Rokid Glasses (Hi Rokid) | Yes (FAQ talks about WhatsApp pop-ups) | Unverified | Optional "Voice broadcast" | [FAQ](https://global.rokid.com/pages/faq), [app](https://apps.apple.com/us/app/hi-rokid-rokid-glasses/id6749669942) official |
| Vuzix Z100 (Vuzix Connect) | Yes, full-screen pop-ups when no SDK app owns the display | Unverified | No | [store](https://apps.apple.com/us/app/vuzix-connect/id6467056741), [docs](https://support.vuzix.com/docs/display-process.md) official |
| Meta Ray-Ban Display | Built-in messaging (texts, WhatsApp, Messenger) at launch; press reports a later all-or-nothing phone notification mirror; Meta announced phone notifications with per-app control "coming soon" on 2026-09-23 | Announced, not confirmed shipped | No | [Meta, 2026-09-23](https://about.fb.com/news/2026/09/new-features-for-meta-ray-ban-display-navigation-hologram/) official, [UploadVR, 2026-09-27](https://www.uploadvr.com/meta-ray-ban-display-gets-new-features-online-ordering-international-launch/) press; current state unverified |
| Ray-Ban Meta, Oakley Meta (no display) | Reads Messenger, WhatsApp, Instagram and phone messages only | Toggles | Yes | [Meta help](https://www.meta.com/en-gb/help/ai-glasses/493802475697609/) official |
| Android XR audio and display glasses | Yes, rules below | Yes, off by default unless "Suggested" | Yes on audio glasses | [behaviour](https://developer.android.com/develop/xr/jetpack-xr-sdk/glasses/notifications/behavior), [quality](https://developer.android.com/docs/quality-guidelines/android-xr/augmented) official |
| RayNeo X3 Pro, RayNeo iO | Yes (examples: WhatsApp, Slack, email) | Unverified | iO has no speaker | [RayNeo](https://www.rayneo.com/en-ca/blogs/news/smart-glasses-bluetooth-connectivity-guide-2026) official; iPhone unreliable per [review](https://gizmodo.com/rayneo-x3-pro-review-these-ar-glasses-may-haunt-my-dreams-2000699219) |
| INMO Go3 | Yes, "app alerts" | Yes per product page (unverified) | Yes, configurable | [app](https://apps.apple.com/us/app/inmo-global/id6758009618) official |
| Halliday | Yes, notification feature in the app | Unverified | Unverified | [app](https://apps.apple.com/us/app/halliday-dwg/id6744673885) official |
| MentraOS (G1, G2, Z100 when paired to the Mentra app) | Yes, MentraOS owns notification logic | Yes, per-app preferences | Unverified | [Mentra](https://docs.mentraglass.com/glasses-oems/firmware-spec.md) official |

Halliday and INMO Go have no public SDK as far as we could find (INMO gives its SDK to partners only, per
[press](https://www.smartwatchlife.jp/75167/)), so this rung is the only way to reach them. Brilliant Labs Halo is
different: it has an ANCS client in Lua, but your own Lua code has to draw it (see `brilliant-labs.md`).

Android XR is the only platform that documents its rules. A notification is bridged when the user enabled your app in
the Glasses app, the phone app and channel are enabled, Do Not Disturb is off, the channel is `IMPORTANCE_HIGH` or
`IMPORTANCE_MAX`, the title is not empty, it is not `FLAG_LOCAL_ONLY`, it is not ongoing (unless it qualifies as a
Live Update) and it does not use `RemoteViews`. Standard, `MessagingStyle`, `BigPictureStyle`, `ProgressStyle`,
`MediaStyle` and `CallStyle` render fully; other styles fall back to the title and text. Treat these rules as the
safe baseline for every brand.

## Getting text on the display

Rules that work across brands (engineering advice, unverified per device):
- One message = one new notification (a new id on Android, a new identifier on iOS). Title of a few words, text of one
  sentence (about 120 characters). Do not use one notification that you update in place: no brand documents how it
  treats an update (forwarded again, ignored, or shown as new), Android sheds updates to an existing notification
  above 5 per second per app (new posts are not rate-limited that way), and Android XR's bridging page describes
  incoming notifications, not updates. A new post is the one event every forwarder handles.
- Cancel all but the last two or three, so the shade stays short and a companion app that replays its backlog (Rokid,
  see Pitfalls) cannot bring stale text back.
- A separate non-ongoing channel at high importance. Android XR skips ongoing notifications by rule and other
  forwarders may too. Keep your foreground-service notification on its own low channel.
- Silence the channel on the phone (no sound, no vibration); the importance stays high.
- Post at most one notification every 2-3 seconds, newest text wins. Glasses show one at a time for a few seconds, so
  faster posting means the wearer misses lines. `examples/live-captions` (`NotificationDisplay.kt`,
  `NotificationDisplay.swift`) implements these rules.

Android (Kotlin):

```kotlin
object GlassesNotifier {
    private const val CHANNEL_ID = "glasses_text"
    private var lastPostMs = 0L
    private var nextId = 1000

    fun createChannel(ctx: Context) {
        val ch = NotificationChannel(CHANNEL_ID, "Text for glasses", NotificationManager.IMPORTANCE_HIGH).apply {
            setSound(null, null) // quiet on the phone
            enableVibration(false)
        }
        ctx.getSystemService(NotificationManager::class.java).createNotificationChannel(ch)
    }

    fun post(ctx: Context, title: String, text: String, minGapMs: Long = 2500): Boolean {
        if (Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(ctx, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) return false
        val now = SystemClock.elapsedRealtime()
        if (now - lastPostMs < minGapMs) return false
        lastPostMs = now
        val n = NotificationCompat.Builder(ctx, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title.take(40)) // never empty
            .setContentText(text.take(120))
            .setCategory(NotificationCompat.CATEGORY_MESSAGE)
            .setPriority(NotificationCompat.PRIORITY_HIGH) // Android 7.1 and older
            .setAutoCancel(true)
            .setTimeoutAfter(60_000)
            .build()
        val nm = NotificationManagerCompat.from(ctx)
        val id = nextId++
        nm.notify(id, n)
        nm.cancel(id - 3) // keep the last three
        return true
    }
}
```

Ask for `POST_NOTIFICATIONS` at runtime on Android 13+ (`ActivityResultContracts.RequestPermission()`), and tell the
user to enable your app in the glasses' companion app.

iOS (Swift):

```swift
import UserNotifications

@MainActor final class GlassesNotifier: NSObject, UNUserNotificationCenterDelegate {
    static let shared = GlassesNotifier()
    private var lastPost = Date.distantPast
    private var recent: [String] = []

    func setUp() async -> Bool {
        let center = UNUserNotificationCenter.current()
        center.delegate = self
        return (try? await center.requestAuthorization(options: [.alert])) ?? false
    }

    func post(title: String, body: String, minGap: TimeInterval = 2.5) {
        guard Date().timeIntervalSince(lastPost) >= minGap else { return }
        lastPost = Date()
        let content = UNMutableNotificationContent()
        content.title = String(title.prefix(40))
        content.body = String(body.prefix(120))
        let id = UUID().uuidString // a new request per message, never a replaced one
        UNUserNotificationCenter.current().add(UNNotificationRequest(identifier: id, content: content, trigger: nil))
        recent.append(id)
        if recent.count > 3 { // keep the last three
            UNUserNotificationCenter.current().removeDeliveredNotifications(withIdentifiers: [recent.removeFirst()])
        }
    }

    // Shows notifications posted while your app is in the foreground. unverified: that ANCS then forwards them
    nonisolated func userNotificationCenter(_ center: UNUserNotificationCenter,
                                willPresent notification: UNNotification) async -> UNNotificationPresentationOptions {
        [.banner, .list]
    }
}
```

iOS limits: your app can post only while it runs, so a live text app needs a background mode it really uses (audio
recording, Bluetooth). Focus modes and Scheduled Summary can hold notifications back; `interruptionLevel =
.timeSensitive` breaks through only with the Time Sensitive Notifications capability and the user's consent. Even
Realities requires "Show Previews: Always" for content to reach the glasses.

## Input
Expect dismiss only. Android XR display glasses show bridged notifications as heads-up notifications with the
system-provided clear action; `MessagingStyle` adds direct reply (voice or smart replies)
([behaviour](https://developer.android.com/develop/xr/jetpack-xr-sdk/glasses/notifications/behavior)). Your own
notification action buttons work on the phone and lock screen; whether other brands mirror them is unverified.

## Audio
Not part of this rung, except that Android XR audio glasses turn bridged notifications into audio read-outs. For other
audio-only glasses speak the text yourself (rung 5), and do not do both on Android XR or the user hears it twice.

## Testing without hardware
- Android XR: pair the Display Glasses or Audio Glasses emulator (Android Studio Canary), enable your app in the
  Glasses app on the host phone emulator.
- Other brands: no simulator. Check the phone side with `adb shell dumpsys notification` (importance, flags, rate).

## Publishing and distribution
Nothing extra. The user allows your notifications on the phone and enables your app in the companion app; explain why
during onboarding.

## Pitfalls
- Android rate limit: `NotificationManagerService` sheds updates above 5 per second per package
  (`DEFAULT_MAX_NOTIFICATION_ENQUEUE_RATE = 5f`, log line "Package enqueue rate is ... Shedding") and caps a package at
  50 active notifications ([AOSP](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/services/core/java/com/android/server/notification/NotificationManagerService.java),
  [docs](https://developer.android.com/develop/ui/views/notifications/build-notification)).
- Ongoing notifications are not bridged to Android XR glasses unless they qualify as Live Updates. Live Updates
  (`setRequestPromotedOngoing(true)`, `POST_PROMOTED_NOTIFICATIONS`) are meant for user-started activities such as
  navigation or calls; Google lists chat messages and alerts as inappropriate uses.
- Even G2 lists only apps that have already posted a notification, so post one during onboarding before asking the
  user to enable it. Even G1 had fixed bugs with duplicates and already-read notifications still showing
  ([support](https://support.evenrealities.com/hc/en-us/articles/14309475255183)).
- Rokid replayed a batch of old notifications for over a minute after the glasses were put back on
  ([review](https://wifihifi.com/rokid-smart-glasses-review-forget-meta-these-are-the-glasses-to-get/), press).
- RayNeo on iOS: the companion app may need to stay in the background; a reviewer got none from an iPhone 17.
- Vuzix Connect pauses notifications "for security" in some situations (release note 1.5.0) and does not show them
  while an SDK app owns the display.
- Meta's web apps for Ray-Ban Display cannot post notifications yet
  ([docs](https://wearables.developer.meta.com/docs/develop/webapps/build/)).

## Official resources
- Android: https://developer.android.com/develop/ui/views/notifications/build-notification ,
  https://developer.android.com/develop/ui/views/notifications/notification-permission
- Apple: https://developer.apple.com/documentation/usernotifications , ANCS specification:
  https://developer.apple.com/library/archive/documentation/CoreBluetooth/Reference/AppleNotificationCenterServiceSpecification/Introduction/Introduction.html
- Brands: the links in the table above, plus https://docs.mentraglass.com/app-devs/core-concepts/phone.md
