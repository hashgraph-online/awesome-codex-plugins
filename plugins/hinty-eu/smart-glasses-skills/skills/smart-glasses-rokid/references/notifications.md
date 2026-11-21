# Notifications: the no-SDK fallback

Last checked: 2026-11-08. Verification: docs-only. Rokid documents no developer contract for notification mirroring;
everything here comes from reviews and community projects, as linked. Test on a real pair before you promise it.

## When to use it

Rung 4 of the display-text ladder: your app posts an ordinary phone notification and Hi Rokid shows it on the
glasses. It needs no SDK, no authorisation in Hi Rokid and no code on the glasses, and it works the same way for
an iPhone app. Use it for:

- short alerts and hints that can arrive a little late;
- iPhone apps that do not want the CXR-L iOS integration;
- a first version, before the CXR-L integration is done.

Do not use it for live captions or anything that changes several times per second. There is no layout control and no
known in-place update on the glasses.

## What is known (as of 2026-11-08)

- Hi Rokid mirrors phone notifications to the lenses as green text; reviewers enabled email, messengers and doorbell
  alerts ([WiFiHiFi review](https://wifihifi.com/rokid-smart-glasses-review-forget-meta-these-are-the-glasses-to-get/),
  [Engadget](https://www.engadget.com/wearables/rokids-smartglasses-are-surprisingly-capable-153027590.html)).
- Rokid's own FAQ, on chat apps: pop-up notifications for the app must be enabled **on the phone**, and the phone must
  stay connected to the glasses over Bluetooth ([Rokid FAQ](https://global.rokid.com/pages/faq)). So a notification
  your user has silenced or set to "no banner" on the phone should not be expected on the glasses either.
- The user chooses which notifications reach the glasses in Hi Rokid; a review notes the per-app selection takes
  effort ([WhistleOut](https://www.whistleout.com.au/MobilePhones/Reviews/rokid-glasses-review)). The exact menu path
  is not documented publicly; unverified.
- The wearer can move the notification position higher, lower or to the side (WiFiHiFi).
- **Backlog replay:** one reviewer saw the same set of notifications replay "in a long stream that could last upwards
  of a minute" each time the glasses went back on, and reported it as a bug (WiFiHiFi). Assume old notifications can
  reappear after the glasses come back on.
- Mirrored notifications are transient. A community glasses app exists just to keep a scrollable history of them
  ([ShaBP/rokid-notification-history](https://github.com/ShaBP/rokid-notification-history)).
- iPhone: the Hi Rokid iOS app (1.16.0, 2026-10-30, iOS 16+) is the companion there, and the Rokid FAQ covers iPhone
  setup (calls via Bluetooth "Share Contacts"). The FAQ's notification answer is not platform-specific; no review we
  could read today confirms iPhone notification mirroring explicitly. Treat it as likely but unverified.
- Delay: no measurement published. Reviews mention lag in navigation and translation, not for notifications.

## Make your notifications glasses-friendly

- **Title**: 2-4 words. **Text**: one sentence, under about 80 characters. The glasses show green text on a narrow
  area; long text gets cut or scrolls (behaviour unverified).
- One new notification per message, and cancel all but the last one or two. With the backlog replay above, anything
  you leave posted can come back after the glasses go back on. Do not update one notification in place: whether Hi
  Rokid forwards an update, replaces the old text or ignores it is undocumented, and Android sheds updates to an
  existing notification above 5 per second per app.
- A high-importance channel with sound and vibration off. Rokid's FAQ asks for pop-up notifications on the phone, and
  on Android a pop-up (heads-up) notification needs `IMPORTANCE_HIGH`. Not ongoing: mirroring apps commonly skip
  ongoing notifications; whether Hi Rokid does is unverified.
- At most one every 2-3 seconds; the glasses show one at a time.
- No emoji, no special symbols, plain sentences.
- Tell the user to enable your app in Hi Rokid's notification settings, and offer a "send test notification" button.

The same rules apply to every brand on this rung; the reasoning and sources are in the `smart-glasses` skill
(`references/brands/notification-glasses.md`).

### Android

```kotlin
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat

private const val CHANNEL = "glasses_hints"
private var nextId = 4200
private val posted = ArrayDeque<Int>()

fun createChannel(ctx: Context) {
    val ch = NotificationChannel(CHANNEL, "Hints on glasses", NotificationManager.IMPORTANCE_HIGH).apply {
        setSound(null, null)                                 // pops up, but silent on the phone
        enableVibration(false)
    }
    ctx.getSystemService(NotificationManager::class.java).createNotificationChannel(ch)
}

/** Needs POST_NOTIFICATIONS on Android 13+. Call from the main thread. */
fun postHint(ctx: Context, title: String, text: String) {
    val n = NotificationCompat.Builder(ctx, CHANNEL)
        .setSmallIcon(android.R.drawable.ic_dialog_info)   // use your own monochrome icon
        .setContentTitle(title.take(30))
        .setContentText(text.take(80))
        .setCategory(NotificationCompat.CATEGORY_MESSAGE)
        .setTimeoutAfter(30_000)                            // stale hints disappear from the phone
        .setAutoCancel(true)
        .build()
    val nm = NotificationManagerCompat.from(ctx)
    val id = nextId++                                       // a new post per hint, never an update
    nm.notify(id, n)
    posted.addLast(id)
    while (posted.size > 2) nm.cancel(posted.removeFirst()) // a replay cannot bring back old hints
}

fun clearHints(ctx: Context) {
    val nm = NotificationManagerCompat.from(ctx)
    posted.forEach { nm.cancel(it) }
    posted.clear()
}
```

### iOS

```swift
import UserNotifications

@MainActor private var hintIds: [String] = []

@MainActor func postHint(title: String, body: String) {
    let content = UNMutableNotificationContent()
    content.title = String(title.prefix(30))
    content.body = String(body.prefix(80))
    content.sound = nil
    let id = UUID().uuidString                              // a new request per hint, never a replaced one
    UNUserNotificationCenter.current().add(UNNotificationRequest(identifier: id, content: content, trigger: nil))
    hintIds.append(id)
    if hintIds.count > 2 {
        UNUserNotificationCenter.current().removeDeliveredNotifications(withIdentifiers: [hintIds.removeFirst()])
    }
}

@MainActor func clearHints() {
    UNUserNotificationCenter.current().removeDeliveredNotifications(withIdentifiers: hintIds)
    hintIds.removeAll()
}
```

Ask for authorisation with `requestAuthorization(options: [.alert])` first. On iOS a foreground app does not show its
own notifications unless your `UNUserNotificationCenterDelegate` returns `.banner` from `willPresent`; check whether
Hi Rokid mirrors notifications that iOS did not present as a banner (unverified).

## Combining with the SDK path

A good pattern for Android: use CXR-L `CUSTOM_VIEW` when the session is `Started`, and fall back to a notification
when the user has not authorised your app, Hi Rokid is too old, or the session is closed. Do not send both at once;
the wearer would see every hint twice.

## Other glasses

The same notification code serves several brands: Even Realities, Vuzix and others mirror phone notifications
through their companion apps too. See the `smart-glasses` skill for the cross-brand ladder.
