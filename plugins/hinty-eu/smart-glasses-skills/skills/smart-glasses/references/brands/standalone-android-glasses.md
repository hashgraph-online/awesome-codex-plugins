# Standalone Android glasses (RayNeo X3 Pro, INMO Air3)

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet).

These glasses are an Android device themselves. Your code runs on the glasses, not on the phone, so you either open
a web page in a browser on the glasses or install an ordinary Android app.

## At a glance
- Display: RayNeo X3 Pro: binocular colour waveguide, 640x480 canvas, 30 degree FOV
  ([design spec](https://rayneo.gitbook.io/rayneo-devdoc/x-xi-lie/she-ji-gui-fan.md)). INMO Air3: 1080p colour
  (press).
- How your app puts text on it: rung 2 (web page in a browser on the glasses) or a native Android app on the glasses.
- Input: RayNeo: right temple touchpad sends one-dimensional `MotionEvent`s; the vendor SDK turns them into gestures.
  INMO Air3: temple tap and slide plus a ring; no official key mapping published.
- Microphone for your app: on the glasses through normal Android audio APIs (unverified on both devices).
- Speaker: yes on both (press).
- Where your code runs: on the glasses. X3 Pro runs Android 12 (API 31) with RayNeo AI OS 2.0. Air3 runs Android 14.
- Publishing to everyone today (as of 2026-11-08): RayNeo has no public store, users sideload over ADB. INMO Air3
  global version has Google Play, so a normal Play listing can reach it.
- Test without hardware: an Android emulator with a 640x480 hardware profile approximates the layout (our suggestion,
  not a vendor tool). `hkust-spark/xg-glass-sdk` has a simulator mode.
- Official agent skill: none.

## Getting text on the display

1. **Web page in a browser on the glasses** (lowest effort). INMO Air3 runs Chrome. RayNeo X3 Pro has no confirmed
   built-in browser; the community browser TapLink X3 (`informalTechCode/TAPLINKX3`, Apache-2.0) is sideloaded and
   maps tap to click, double tap to Back (so Back leaves your page; do not trap it). The text source is a server the glasses reach over Wi-Fi or the phone's
   hotspot.
2. **Native Android app on the glasses.** A normal Activity with a black background. Set `minSdk` to 31 or lower for
   the X3 Pro. RayNeo's ARDK for Android (v0.2.6, 2026-04-21, distributed as a download from the docs, no licence
   published) adds `BaseMirrorActivity` to lay out the same UI for both eyes and a `TempleAction` gesture flow. Read
   its docs and link to it; do not redistribute it.
3. **Phone notifications** (rung 4) also reach RayNeo glasses through the RayNeo AI app.

Design rules from RayNeo's spec, valid for any of these displays: pure black background (black is transparent),
font 16 px minimum, safe margins 30 px left and right and 20 px top and bottom, no large white or saturated areas,
red only for warnings, average pixel brightness under 13 % for content that stays on screen (25 % for short
content).

Web page (TypeScript, uses the shared live-captions protocol of this repo's example server):

```ts
const el = document.getElementById('caption')!;
const room = new URLSearchParams(location.search).get('room') ?? '';
const ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws?room=${room}`);
ws.onopen = () => ws.send(JSON.stringify({ type: 'hello', target: 'android-glasses-browser', lines: 3, cols: 32 }));
ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.type === 'caption') el.textContent = m.text;
  else if (m.type === 'clear') el.textContent = '';
};
const act = (action: 'repeat' | 'skip' | 'hide') => ws.send(JSON.stringify({ type: 'action', action }));

// This page has nothing focusable, so keys can map directly; with real buttons, let the browser move focus instead
addEventListener('keydown', (e) => {
  if (e.key === 'Enter') act('repeat');
  else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') act('skip');
});
addEventListener('click', () => act('repeat'));
// Double tap is Back on these browsers. Back means leave: do not push history entries to trap it (input.md).
addEventListener('pagehide', () => ws.close());
// Screen Wake Lock needs a secure context (https or localhost)
navigator.wakeLock?.request('screen').catch(() => {});
```

Native Activity (Kotlin). Log what the touchpad sends before you map it; the event path differs per device:

```kotlin
class GlassesTextActivity : ComponentActivity() {
    private lateinit var label: TextView
    private var downX = 0f
    private var downAt = 0L

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        label = TextView(this).apply {
            setBackgroundColor(Color.BLACK)
            setTextColor(Color.WHITE)
            setTextSize(TypedValue.COMPLEX_UNIT_PX, 28f) // RayNeo minimum is 16 px
            gravity = Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL
            setPadding(30, 20, 30, 20) // RayNeo safe margins at 640x480
        }
        setContentView(label)
    }

    fun show(text: String) = runOnUiThread { label.text = text }

    // Key-style touchpads and the emulator
    override fun onKeyDown(keyCode: Int, event: KeyEvent): Boolean = when (keyCode) {
        KeyEvent.KEYCODE_ENTER, KeyEvent.KEYCODE_DPAD_CENTER -> { onAction("repeat"); true }
        KeyEvent.KEYCODE_DPAD_RIGHT, KeyEvent.KEYCODE_DPAD_DOWN -> { onAction("skip"); true }
        else -> super.onKeyDown(keyCode, event)
    }

    // unverified: whether the RayNeo temple arrives as touch or generic motion; handle both
    override fun dispatchTouchEvent(ev: MotionEvent): Boolean { temple(ev); return super.dispatchTouchEvent(ev) }
    override fun dispatchGenericMotionEvent(ev: MotionEvent): Boolean { temple(ev); return super.dispatchGenericMotionEvent(ev) }

    private fun temple(ev: MotionEvent) {
        when (ev.actionMasked) {
            MotionEvent.ACTION_DOWN -> { downX = ev.x; downAt = ev.eventTime }
            MotionEvent.ACTION_UP -> {
                val dx = ev.x - downX
                if (abs(dx) < 20 && ev.eventTime - downAt < 300) onAction("repeat") else if (dx > 0) onAction("skip")
            }
        }
    }

    private fun onAction(action: String) { /* send to your server */ }
}
```

## Input
- RayNeo X3 Pro: touchpad events are `MotionEvent`s on the X axis only. The ARDK's `TouchDispatcher` and
  `BaseTouchActivity` / `BaseEventActivity` produce `TempleAction` values (`Click`, `DoubleClick`, `TripleClick`,
  `LongClick`, `SlideForward`, `SlideBackward`, X3 also `SlideUpwards`, `SlideDownwards`). A paired ring sends the same
  events. Keep double tap free for Back.
- INMO Air3: no official input documentation; community material for the Air2 maps tap to Enter, double tap to Back
  and slides to D-pad keys. Handle both key and motion events and test.

## Audio
Use `AudioRecord` and `TextToSpeech` on the glasses as on any Android device. The batteries are small (press reviews
report one to a few hours), so stream audio to a server only while the user is in a session.

## Testing without hardware
- Create an emulator hardware profile at 640x480 to check layout and font sizes. It does not simulate the optics,
  the binocular layout or the touchpad.
- `hkust-spark/xg-glass-sdk` (Apache-2.0) has adapters for RayNeo X2 (validated), X3 Pro (untested) and INMO Air3
  (validation pending), plus `xg-glass run --sim` with the laptop camera.

## Publishing and distribution
- RayNeo X3 Pro: enable ADB on the glasses (OS 25.8.13 or later: Settings > General, scroll to the far left and hit the
  edge 10 times), then `adb install your.apk`. On Windows 11 the ADB driver may need replacing with Zadig. We found no
  public app store for third-party glasses apps.
- INMO Air3: Google Play on the global version; sideloading is not documented officially.

## Pitfalls
- A plain Activity on the X3 Pro may not render correctly for both eyes; the ARDK mirror base class exists for that
  (unverified without it). Test a web page or a one-screen app first.
- Android 12 on the X3 Pro: libraries with `minSdk` 33 or newer will not install.
- INMO Air3 had a US/Canada recall (CPSC 26-797, 2026-09-24): the left temple can overheat, fixed by firmware V3.16.
  About 1,760 units were sold in the US and Canada, so the user base is small.
- RayNeo's site rate-limits automated fetches; read the GitBook docs instead.
- Enterprise Android glasses (Vuzix M400 and RealWear Navigator, both Android 13) work the same way but are out of
  scope here.

## Official resources
- https://rayneo.gitbook.io/rayneo-devdoc (RayNeo developer docs, Chinese)
- https://rayneo.gitbook.io/rayneo-devdoc/x-xi-lie/android-kai-fa/neng-li-jie-shao/chu-kong-ban-guan-li.md (touchpad)
- https://rayneo.gitbook.io/rayneo-devdoc/chang-jian-wen-ti/adb-tiao-shi/adb-zhi-ling.md (ADB)
- https://www.inmo.com/blogs/news/whats-difference-between-inmo-air3-and-meta-ray-ban-display-glasses
- https://cpsc.gov/Recalls/2026/INMO-International-Technology-Limited-Recalls-INMO-Air3-Smart-Glasses-Due-to-Risk-of-Serious-Injury-or-Death-from-Burn-Hazard
- https://github.com/informalTechCode/TAPLINKX3 (community)
- https://github.com/hkust-spark/xg-glass-sdk (community, cross-brand)
- https://github.com/extentos/smart-glasses-ecosystem (community capability map, CC BY 4.0)
