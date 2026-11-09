# Display: layouts, canvas, fonts, scripts and budgets

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). API facts from the
[Android Javadoc](https://vuzix.github.io/ultralite-sdk-android/javadoc) and the
[iOS DocC](https://vuzix.github.io/UltraliteSDK-releases-iOS/documentation/ultralitesdk/); limits also from
[Display Process](https://support.vuzix.com/docs/display-process).

## Hardware

- 640x480 (4:3), monochrome green microLED waveguide, **right eye only**, about 30 degrees field of view
  (Vuzix product page [archived 2026-07-10](https://web.archive.org/web/20260710075701/https://www.vuzix.com/products/z100-smart-glasses);
  the live URL redirects since 2026-09-06). The SDK constants
  agree: Android `UltraliteSDK.Canvas.WIDTH = 640`, `HEIGHT = 480`; iOS `Ultralite.DISPLAY_WIDTH` / `DISPLAY_HEIGHT`.
- The display adds light. Four levels per pixel (Android `UltraliteColor`, iOS `Canvas.Color`):
  `BLACK` / `.black` adds no light (fully see-through), `DIM`, `MID`, `WHITE` (brightest green). There is no colour.
- Brightness is a user setting. iOS exposes `Ultralite.Property.brightness` (range undocumented).

## Layouts

Choose the layout with Android `setLayout(...)` or iOS `requestControl(layout: ...)`, after control is granted.

| Android `Layout` | iOS `Ultralite.Layout` | What it is | How you send content |
|---|---|---|---|
| `DEFAULT` | `.default` | Notification-only mode | nothing; signals you are done |
| `TEXT_BOTTOM_LEFT_ALIGN` | `.textBottomLeftAlign` | Text at the bottom, left aligned | `sendText` |
| `TEXT_BOTTOM_CENTER_ALIGN` | `.textBottomCenterAlign` | Text at the bottom, centred | `sendText` |
| `NAVIGATION` | `.navigation` | Text with a turn icon | Android `sendText(text, Icon)`, iOS `sendTextAndImage(text:image:)` |
| `CANVAS` | `.canvas` | Free drawing | canvas text, images, animation, background |
| `SCROLL` (1.3+) | `.scroll` | Teleprompter of image slices | `ScrollingTextView` / `ScrollLayout`, `LiveText`, `AutoScroller` |

`sendText` does nothing on `DEFAULT` or `CANVAS`. `hideStatusBar: true` only applies to the canvas layout.
Android `Icon` values for navigation: `ARRIVE`, `CUSTOM`, `KEEP_LEFT`, `KEEP_RIGHT`, `LEFT`, `NONE`, `RIGHT`, `START`,
`STRAIGHT`, `UTURN`; send your own with `sendIcon(LVGLImage)` and use `Icon.CUSTOM`.

## Pick a text path

| Path | Best for | Scripts | Speed | Notes |
|---|---|---|---|---|
| Text layout + `sendText` | A plain text wall | Glasses font | Fast | No position or colour control, the glasses wrap |
| Canvas `createText` / `updateText` | HUDs, two-level text (question + answer) | Glasses font | Fast | Up to 7 blocks, one font for all |
| `LiveText` on `SCROLL` | **Live captions**, streaming AI answers | Anything the phone font renders | Medium | Rendered on the phone into image slices |
| Background bitmap | Static labels, rich layout, exact typography | Anything the phone renders | Slow | 640x480 max, 2-bit |
| `sendNotification` | Passive alerts, no control needed | Glasses font | Fast | Peeks only while another app holds control |

Vuzix's own advice: large bitmaps are slower than text; for responsive UIs keep changing text in foreground text
objects and put static labels in the background.

## Canvas limits and behaviour

- **7 text blocks, 3 images, 1 animation, 1 full-screen background.** Creating more texts or images overwrites the
  earlier ones. An animation uses the image slots (only its last 3 frames are used).
- Image data at most **9900 bytes** per image (bigger images are not created or updated). Vuzix suggests foreground
  images under 100x100 px.
- Background: at most 640x480, otherwise nothing is drawn. An `LVGLImage` background must be
  `LVGLImage.CF_INDEXED_2_BIT`. `LVGLImage.fromBitmap(bitmap, cf)` converts an Android `Bitmap`
  (`CF_INDEXED_1_BIT` or `CF_INDEXED_2_BIT`).
- `createText`: width or height `-1` means automatic. Returns an id, or `-1` (Android) / `nil` (iOS) on failure.
  Methods given an invalid id do nothing and return `false`.
- Wrap modes. Android `TextWrapMode`: `WRAP` (default), `TRUNCATE` (ends with dots), `SCROLL` (back and forth),
  `SCROLL_CIRCULAR`, `CLIP`. iOS `Canvas.TextWrapMode`: `.default`, `.wrap`, `.truncate`, `.scrollBackAndForth`,
  `.scrollCircular`, `.clip`.
- Anchors: `TOP_LEFT`, `TOP_CENTER`, `TOP_RIGHT`, `MIDDLE_LEFT`, `CENTER`, `MIDDLE_RIGHT`, `BOTTOM_LEFT`,
  `BOTTOM_CENTER`, `BOTTOM_RIGHT` (iOS uses `.midLeft` / `.midRight`). Alignment: `AUTO`, `LEFT`, `CENTER`, `RIGHT`.
- `moveText` / `moveImage` with `durationMs` (1.3+) animate a move; `0` is immediate.
- **Commit:** changes appear only after `commit()`, but "uncommitted changes may be shown early in some situations",
  so commit right after the last change of a frame. Android `clear()` removes background, images and texts; iOS
  `clear(shouldClearBackground:)` does the same and needs no commit.
- iOS-only drawing helpers: `drawStaticText(text:font:color:x:y:maxWidth:)` and the attributed-string variants render
  text with any `UIFont` into the background; also `drawRect`, `drawLine`, `drawBackgroundTiled`. Remove with
  `clearBackground()` or `clearBackgroundRect(x:y:width:height:)`.
- iOS splits large background images into several payloads; `drawBackground(..., shouldCommitImmediately: true)`
  draws them progressively.

## Fonts and size

- Android `setFont(fontFamily, style, textSize)`: a built-in system font family as understood by `Typeface.create`
  (`null` = default), a `Typeface` style, and the size in pixels. It applies to all text and lasts until control is
  released; `clearFont()` restores the default. Needs control.
- iOS: `setCustomFontForAllText(font: UIFont?)` exists but has no documentation, and `Ultralite.Property.fontSize`
  can be set with `setIntProperty`. Both unverified.
- One font for all text blocks: show emphasis with brightness (`MID` for context, `WHITE` for the key line).

## Line and character budgets

Measured by MentraOS for its Z100 driver (Apache-2.0, community, not verified by us): in the text layout the default
font behaves like Noto Sans Regular at 21 px, about **42 characters of mixed Latin text** fit in roughly 387 px before
the glasses wrap, and they plan for **7 lines**
([profile](https://github.com/Mentra-Community/MentraOS/blob/dev/mobile/modules/engine/src/utils/display/profiles/z100.ts)).

For the canvas you choose the font size and block width. A planning estimate (unverified on hardware) from the same
metrics: mixed Latin text averages about 0.44 x font size per character, Cyrillic about 0.67 x, CJK about 1.0 x.

| Font px | Latin chars per 600 px | Cyrillic chars per 600 px | CJK chars per 600 px | Lines in 480 px at 1.25 line height |
|---|---|---|---|---|
| 21 | ~64 | ~42 | ~28 | ~18 |
| 28 | ~48 | ~32 | ~21 | ~13 |
| 34 | ~40 | ~26 | ~17 | ~11 |
| 40 | ~34 | ~22 | ~15 | ~9 |

The display fits a lot, the eye does not: for glanceable text use 2-3 lines of 28-34 px and leave a margin. Fit lines
on the phone before sending so a wrap never pushes the newest words off screen:

```kotlin
/** Word-wraps by a character budget and keeps the newest lines (captions grow at the bottom). */
fun fitLines(text: String, maxChars: Int, maxLines: Int): String {
    val lines = mutableListOf<String>()
    var line = StringBuilder()
    for (word in text.trim().split(Regex("\\s+"))) {
        if (word.isEmpty()) continue
        val chunks = word.chunked(maxChars)             // hard-split words longer than a line
        for (chunk in chunks) {
            val needed = if (line.isEmpty()) chunk.length else line.length + 1 + chunk.length
            if (needed > maxChars && line.isNotEmpty()) { lines += line.toString(); line = StringBuilder() }
            if (line.isNotEmpty()) line.append(' ')
            line.append(chunk)
        }
    }
    if (line.isNotEmpty()) lines += line.toString()
    return lines.takeLast(maxLines).joinToString("\n")
}
```

## Live captions with LiveText

Both SDKs ship a closed-caption helper on the `SCROLL` layout: it appends new words to the bottom line, scrolls finished
lines up, and can edit earlier lines. It renders on the phone, so any script your phone font supports works.

- Android `com.vuzix.ultralite.utils.scroll.LiveText` (1.4+). Constructor (1.7+):
  `LiveText(sdk, lineHeight, lineWidth, startingLineIndex, numSlicesVisible, textPaint)`. Javadoc starting values:
  `lineHeight` 48 (range 30-120), `lineWidth` 640, `startingLineIndex` 0, `numSlicesVisible` 3. `sendText(full)` takes
  the whole string that should be visible now; it throws `IllegalStateException` without control or without the
  `SCROLL` layout. `clear()` empties the view.
- iOS `ScrollLayout.LiveText(xOffset:width:height:startingLineIndex:animationDuration:)` (all parameters have
  defaults). Set `font` and `text` or `attributedText`, call `start()` after `requestControl(layout: .scroll, ...)`,
  then keep updating `text`. `clear()` empties the view.

```kotlin
import android.graphics.Color
import android.text.TextPaint
import com.vuzix.ultralite.Layout
import com.vuzix.ultralite.UltraliteSDK
import com.vuzix.ultralite.utils.scroll.LiveText

/** Captions on the Z100. Call setUp() each time getControlledByMe() emits true. */
class Z100Captions(private val sdk: UltraliteSDK) {
    private var live: LiveText? = null
    private var committed = ""

    fun setUp() {
        sdk.setLayout(Layout.SCROLL, 0, false, false, 2)    // timeout 0: stay on while captions run
        val paint = TextPaint(TextPaint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE        // the slice is converted to 2-bit: dark text would be invisible
            textSize = 36f             // unverified: best size for lineHeight 48; tune on device
        }
        live = LiveText(sdk, 48, 640, 0, 3, paint)
    }

    /** Partial results replace the tail until final = true. */
    fun onCaption(text: String, final: Boolean) {
        val full = if (committed.isEmpty()) text else "$committed $text"
        if (final) committed = full.takeLast(400)          // keep the string bounded
        try { live?.sendText(full) } catch (e: IllegalStateException) { live = null }   // control lost
    }

    fun clear() { committed = ""; live?.clear() }
}
```

On iOS, whether `LiveText` needs a `scrollLayout?.config(...)` call before `start()` is not documented (unverified).
For known text (a teleprompter) use `AutoScroller` instead; for full control use `ScrollingTextView` (Android) or
`ScrollLayout` (iOS) with your own slices (slice height 30-120 px, 4-16 slices).

## Scripts, RTL and emoji

- Text rendered by the glasses (`sendText`, canvas text, notifications): the SDK compiles glyphs the glasses lack and
  sends them (the Javadoc mentions "non-standard characters for which a custom font needs to be compiled", and that
  the notification icon may be dropped when there are too many). Expect a delay the first time new characters
  appear, and test each script you ship (unverified per script).
- RTL: Arabic and Hebrew in notifications appeared reversed before 1.9. Vuzix said the fix would ship in 1.9 and
  closed the issue on 2025-03-20, after the 1.9 release, whose notes say only "1.9 upload"
  ([Android #2](https://github.com/Vuzix/ultralite-sdk-android/issues/2); not verified by us). RTL in canvas text is
  not documented.
- When shaping matters (Arabic, Hebrew, Indic scripts, Thai, complex CJK), render on the phone: `LiveText`, bitmaps,
  or iOS `drawStaticText`. The iOS DocC says `LiveText` "can support any language that the font supports".
- Emoji: not documented for glasses-rendered text; avoid them (the display is monochrome anyway).

## Screen power and timeouts

- `timeout` (seconds) in `setLayout` / `requestControl`: the display turns off after that much inactivity; `0` keeps
  it on. New content wakes it.
- `screenOff()` / `screenOn()`: explicit power. On Android both need control. iOS: after `screenOff()` "the next time
  a new message is sent to device it will power on the screen", and `screenOn()` is not needed before canvas or text
  drawing.
- Events: Android `onDisplayOn`, `onDisplayOff`, `onDisplayTimeout`; iOS `.display_state`, `.displayTimeout`.

## Notifications as a display path

- Android `sendNotification(key, title, message, peekText, icon)` (1.5+). The same `key` updates or clears it
  (`clearNotification(key)`, 1.2+). `peekText` is the single line shown when the notification only peeks. Icon:
  `LVGLImage`, recommended 40x40 (`NOTIFICATION_ICON_WIDTH_HEIGHT`), or `null` for the default.
- iOS `sendNotification(title:message:) -> String`; see [ios.md](ios.md) for ANCS and queueing.
- While any app holds a non-default layout, a notification only peeks (title or `peekText`)
  ([Android #1](https://github.com/Vuzix/ultralite-sdk-android/issues/1)).
- Without the SDK at all, a regular phone notification is mirrored by Vuzix Connect (ladder rung 4; the App Store
  listing says "Notifications from your mobile device will be displayed in your smart glasses"). The user can limit
  which notifications Connect forwards (per the Android sample's notes; unverified on iOS).
