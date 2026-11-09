# Line fitting: partial results, wrapping, budgets, update rates

Last checked: 2026-11-08. Verification: the wrapping and state code below ran in `examples/live-captions`
(`web-glasses/fit.test.mjs`, headless Chromium at 600x600, Even Hub simulator 0.9.5 from npm; Even's simulator page
still names v0.9.3). Display budgets are
`docs-only` unless marked; character counts marked "estimate" are ours.

## Partial and final results

Streaming STT sends the current sentence again and again while it grows and changes, then marks it final:

```
partial  "we can meet"
partial  "we can meet at for"          <- a guess
partial  "we can meet at four tomorrow" <- revised, not appended
final    "We can meet at four tomorrow."
partial  "Does"                         <- next sentence, new line
```

Replace-last-line strategy:

1. Keep committed sentences (`finals`) and the current `partial` separately.
2. Wrap each final once, when it arrives, and cache its lines. Committed lines never move or re-wrap.
3. Wrap the partial on every update. It always starts on a fresh line, so replacing it cannot shift older text.
4. Show the newest N lines, newest at the bottom. When a partial is longer than the screen, show its tail.
5. On final, the partial's lines become committed lines (re-wrap once, the final text may differ slightly).
6. On `clear`, empty both.

Styling: draw the partial a step dimmer than committed text (web: a lighter grey; Even G2: a container with lower
`textColor`), so the wearer can tell which words may still change. A subtitle-style alternative for one-container
displays: keep the newest final bright in the live area until the next sentence starts, then move it up.

## Wrapping with real metrics

Character counts are a last resort. Measure with the target's own font when you can:

| Target | Measure with |
|---|---|
| Web page on glasses, second screen | `CanvasRenderingContext2D.measureText` with the computed font of the caption element |
| Even G2 plugin | `@evenrealities/pretext` (MIT): `getTextWidth(text)` for a line, `measureTextWrap(text, width)` to check the firmware wrap; official skill `even-font-measurement` |
| Android (Vuzix canvas, Presentation, your own bitmaps) | `Paint.measureText` or `StaticLayout` with the same typeface and size |
| iOS | `NSAttributedString.boundingRect(with:options:context:)` or `size(withAttributes:)` |
| Rokid custom view, notifications, Meta DAT presets | no metrics exposed: a character budget with 15 percent slack, CJK characters counted as two |

A greedy word wrap that also handles scripts without spaces (from `examples/live-captions/web-glasses/fit.js`):

```ts
const seg = new Intl.Segmenter(undefined, { granularity: 'word' }) // finds breaks in Chinese, Japanese, Thai

function wrap(text: string, maxWidth: number, measure: (s: string) => number): string[] {
  const out: string[] = []
  let line = ''
  const push = () => { if (line.trim()) out.push(line.trim()); line = '' }
  for (const { segment: p } of seg.segment(text.replace(/\s+/g, ' ').trim())) {
    if (!line && !p.trim()) continue                       // no leading spaces
    if (measure((line + p).trimEnd()) <= maxWidth) { line += p; continue }
    if (!p.trim()) { push(); continue }                    // break at the space
    push()
    if (measure(p) <= maxWidth) { line = p; continue }
    for (const ch of p) { if (line && measure(line + ch) > maxWidth) push(); line += ch } // hard break
  }
  push()
  return out
}
```

Leave a few pixels of slack (the example uses 4 px on the web and 6 px on Even G2) for rounding differences between
your measurement and the renderer, and set the renderer to never wrap on its own (CSS `white-space: nowrap`, or one
`\n`-separated string per container), so a rounding error clips a pixel instead of adding a line.

## Display budgets for captions

| Display | Canvas and font | Caption budget | Source |
|---|---|---|---|
| Even Realities G2 | 576x288 per eye, green; text has 5 brightness levels (`textColor` 0-4), images and borders 16; one firmware font, no size control, proportional, 27 px line height (10 lines) | 3 to 8 lines of about 55 to 60 Latin characters (estimate from the font tables: average advance about 9.5 px in English, 11 px in Russian); a full-screen container holds "roughly 400 to 500 characters" | https://hub.evenrealities.com/docs/build/display |
| Meta Ray-Ban Display Web App | 600x600 viewport, DPR 1, additive (black is transparent); Noto Sans; routine text 28/36 px in Meta's UI toolkit; standard inset 24 px | 3 to 4 lines at 32 to 40 px, about 26 to 32 characters per line (estimate) | https://wearables.developer.meta.com/docs/develop/webapps/build/display-and-layout/ |
| Meta DAT display | preset heading, body and meta text styles | 3 to 4 lines; each send replaces the whole screen, no partial updates | https://wearables.developer.meta.com/docs/develop/dat/display-overview/ |
| Rokid Glasses (CXR-L custom view) | monochrome green, 480 px (320 dp) wide; 480x398 per eye (Rokid blog, press), Android on the glasses reports 480x640 portrait at 240 dpi (community); text size in sp | 3 lines at 24 sp, about 22 Latin characters per line (estimate, unverified; the `smart-glasses-rokid` skill and `examples/live-captions` use the same) | https://global.rokid.com/blogs/news/rokid-glasses-are-lightweight-ar-smart-glasses-with-micro-led-displays-and-a-499-price-tag |
| Vuzix Z100 | 640x480 monochrome green, right eye; `TEXT_BOTTOM_LEFT_ALIGN` / `TEXT_BOTTOM_CENTER_ALIGN` for `sendText`, or `CANVAS` with up to 7 text blocks; `setFont(family, style, sizePx)` | 3 lines; the text layout wraps near 42 Latin characters (MentraOS measurement, community), so budget about 36; on the canvas about 40 per 600 px at 34 px (estimate) | https://vuzix.github.io/ultralite-sdk-android/javadoc/com/vuzix/ultralite/UltraliteSDK.Canvas.html |
| USB-C display glasses (XREAL One: 1920x1080; VITURE Luma Pro: 1920x1200 per eye) | a normal Android or iOS display; edges of the image are less sharp | 2 to 4 lines of large text in the central area, white or green on black | https://developer.android.com/reference/android/app/Presentation |
| Android XR display glasses (Compose Glimmer) | text sized in degrees: minimum 0.6, most text 0.7 to 0.9 degrees; `bodyLarge` 30 sp | not documented; plan 2 to 3 lines | https://developer.android.com/design/ui/ai-glasses/guides/styles/type |
| Phone notification mirrored to glasses | the companion app's own layout; Vuzix `peekText` is a single line | 1 to 2 lines of 30 to 40 characters (estimate); counts for Even, Rokid and Meta are not published | https://support.evenrealities.com/hc/en-us/articles/14274501482639-Notifications |

On iOS, an app gets a scene for an external display through the `windowExternalDisplayNonInteractive` role; Apple
documents that from iOS 27 the app must also register a scene accessory first
(https://developer.apple.com/documentation/uikit/presenting-content-on-a-connected-display).

Fewer lines are easier to read in front of one eye. Default to 3 or 4 lines and let the wearer raise it.

## Even G2 specifics

- Text lives in containers at fixed pixel positions: up to 8 text or list containers and 4 image containers per page.
  No alignment, no font size, no RTL: centre or bottom-align by padding with spaces and `\n`.
- `content` up to 1000 characters on create and rebuild, 2000 on `textContainerUpgrade`.
- `createStartUpPageContainer` once; then `textContainerUpgrade` per changed container (no flicker). Pass the same
  `containerID` and `containerName` as on create, or the call does nothing.
- To replace a container's text, send only `containerID`, `containerName` and `content`, as the official templates
  and the example do; the official `even-glasses-ui` skill passes `contentOffset: 0, contentLength: 0` for the same
  full replacement. The docs say only that the two fields "are for partial-string updates", with no unit (characters
  or bytes). Simulator 0.9.5 ignores both: on 2026-11-09 every upgrade we sent (offsets 0 to 6, lengths 0 to 12,
  Latin, Polish and Japanese text) replaced the whole text. Partial updates are unverified on hardware.
- Keep each container under 999 UTF-8 bytes, not just under the character limits: simulator 0.9.5 returned `false`
  for a rebuild and an upgrade over about 1000 bytes (513 Polish letters) and kept the old text (our run,
  2026-11-09). The example caps every container at 999 bytes.
- `n` line breaks make `n + 1` lines: padding an empty container with `\n` overflows it and shows a scrollbar (we hit
  this in the simulator).
- Exactly one container is the event-capture container. If its text overflows, the firmware scrolls it and only
  reports swipes at the ends. Make it a one-line status bar.
- Brightness per container (`textColor` 0 to 4) is the only emphasis: older lines at 2, the live sentence at 4. The
  simulator does not show greyscale levels the way the hardware does.

## Update rates

| Path | What limits it | Practice |
|---|---|---|
| Even G2 text | BLE; community measurement on firmware 2.2.7: about 83 ms per `textContainerUpgrade`, about 165 ms per rebuild; the official `asr` template debounces writes to 120 ms because "the BLE queue can't keep up with per-token writes" | one queue, 120 ms debounce, send only changed containers, newest frame wins |
| Even G2 images | about 100 ms fixed per image write, full screen about 800 ms; never send images in parallel | not for partial results |
| Meta Web App | 30 Hz panel; link about 500 kbps and 150 ms round trip (Meta's performance guidance) | DOM updates per message are fine; keep messages small |
| Meta DAT display | each send replaces the screen | coalesce to a few per second |
| Rokid CXR-L | not documented; community reports of `customViewUpdate` returning success without redrawing on some app versions (unverified) | at most one update every 250 ms (estimate); if the view freezes, close and reopen it |
| Vuzix Ultralite | not documented; `commit(callback)` reports when the glasses received the canvas | send the next frame after the callback |
| Android notifications | `NotificationManagerService` drops updates to an existing notification beyond 5 per second per app (`DEFAULT_MAX_NOTIFICATION_ENQUEUE_RATE`); glasses show one notification at a time | finals only, a new notification each, at most one every 2-3 s |
| Text-to-speech | the wearer's attention | finals or hints only |

Sources: https://github.com/even-realities/evenhub-templates/tree/main/asr,
https://raw.githubusercontent.com/nickustinov/even-g2-notes/main/docs/performance.md (community),
https://github.com/meta/meta-wearables-webapp,
https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/services/core/java/com/android/server/notification/NotificationManagerService.java

A latest-only queue works for every slow display:

```ts
function latestOnly<T>(write: (frame: T) => Promise<unknown>, debounceMs = 120) {
  let want: T | null = null, busy = false, timer: ReturnType<typeof setTimeout> | undefined
  const run = async () => {
    if (busy) return
    busy = true
    while (want !== null) { const f = want; want = null; try { await write(f) } catch { /* retry on the next frame */ } }
    busy = false
  }
  return (frame: T) => { want = frame; clearTimeout(timer); timer = setTimeout(run, debounceMs) }
}
```

## Scrolling and paging

- During live captions there is no free scrolling: the newest text is always in view.
- Map a "repeat" gesture to showing the last final again (and speaking it on audio targets), and "hide" to clearing
  the screen until the next sentence. A "skip" gesture commits the visible part and drops the rest of the sentence.
- For reading a long answer (assistant mode), switch to pages: freeze the stream, show page 1 of the text, page with
  swipes, return to live on a timeout or a tap.
- Teleprompter: pages advanced by the wearer (or by matching recognised words to the script, which developers report
  as fragile; a clicker is the dependable fallback).

## Testing without hardware

- Unit-test wrapping with a monospace `measure` (`s => [...s].length`) and a budget in characters.
- Web targets: a desktop browser at the device viewport (600x600 for Meta), checking that no line element is wider
  than its box and that the box does not overflow (`examples/live-captions` does this with Playwright).
- Even G2: the official simulator's automation API (`/api/screenshot/glasses`, `/api/console`, `/api/input`); log one
  line per frame in the simulator build and assert on it. Official skill: `even-test-with-simulator`.
