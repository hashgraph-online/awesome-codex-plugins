# Even Realities G2 (Even Hub)

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet); our sample plugin passed the official simulator.

This file is the cross-brand summary. For SDK details install the official skill: `npx skills add even-realities/everything-evenhub`
(Claude Code plugin: `/plugin marketplace add even-realities/everything-evenhub`, then `/plugin install everything-evenhub@everything-evenhub`).
The older Even G1 is covered at the end.

## At a glance
- Display: two monochrome green micro-LED displays, one per eye. Apps draw on a 576x288 canvas per eye, black = off. The display is 4-bit greyscale (16 levels of green), but text has only five brightness levels (`textColor` 0-4); images and borders use the 16 levels ([display docs](https://hub.evenrealities.com/docs/build/display)). Consumer spec pages and press quote 640x350 for the panel; build for the 576x288 canvas the SDK exposes.
- How your app puts text on it: rung 1, an Even Hub plugin (your web app inside the Even phone app). Rung 4 also works: the Even app forwards phone notifications. Rung 5 needs the user's own earbuds, the glasses have no speaker.
- Input: touchpads on both temples, optional Even R1 ring with the same gestures, a system contextual menu with up to 10 of your items, IMU.
- Microphone for your app: yes, glasses (4-mic array, one processed mono stream) or phone mic, PCM 16 kHz, 16-bit LE, mono. No speech-to-text in the SDK.
- Speaker: none, and no audio output API.
- Phones / where your code runs: iOS (WKWebView) and Android (Chromium WebView) inside the Even Realities app. No app code runs on the glasses.
- Publishing to everyone today: yes, Even Hub store with manual review; free apps only ("no paid distribution yet"), published worldwide, no region targeting (as of 2026-11-08, [FAQ](https://hub.evenrealities.com/docs/reference/faq) updated 2026-10-09).
- Test without hardware: official simulator for Windows, macOS and Linux with an HTTP automation API. It is "not a hardware emulator".
- Official agent skill: `npx skills add even-realities/everything-evenhub` (14 skills on skills.sh including `harness`, MIT; checked 2026-11-09).

Versions on npm as of 2026-11-08: SDK `@evenrealities/even_hub_sdk` 0.0.16 (2026-09-24, needs Even app 2.2.10+, MIT),
CLI `@evenrealities/evenhub-cli` 0.2.0 (binary `evenhub`), simulator `@evenrealities/evenhub-simulator` 0.9.5 (2026-09-01; the [simulator page](https://hub.evenrealities.com/docs/test/simulator) still names v0.9.3), font metrics
`@evenrealities/pretext` 0.1.4. Starters: `npx degit even-realities/evenhub-templates/<minimal|text-heavy|asr|image> my-app`.
Use SDK 0.0.16: its changelog fixes repeated `setTimeout`/`setInterval` callbacks present in 0.0.14 and 0.0.15.

## Getting text on the display

Ranked options:
1. **Plugin text containers (rung 1).** The only way to place your own text where and when you want. Covered below.
2. **Phone notification (rung 4).** Your phone app posts a notification; the user turns your app on in the Even app under Settings > Notifications. With Auto Display on (the default) it pops up on the glasses; the glasses keep the 10 most recent ([support](https://support.evenrealities.com/hc/en-us/articles/14274501482639-Notifications), docs-only). No layout, no in-place updates. Fine for alerts, wrong for live captions.
3. **Image containers.** Only for what text cannot do (unsupported scripts, larger type). Max 4 per page, each up to 288x144, 4-bit. The SDK paces image sends at 100 ms; a full-screen refresh takes about 800 ms and draws in quarters ([display docs](https://hub.evenrealities.com/docs/build/display), [#48](https://github.com/even-realities/everything-evenhub/issues/48)).
4. **Off the official path.** MentraOS drives the G2 from its own phone app with a 576x288 canvas ([Mentra display docs](https://docs.mentraglass.com/app-devs/core-concepts/display/layouts.md)); community BLE reverse engineering exists ([i-soxi/even-g2-protocol](https://github.com/i-soxi/even-g2-protocol), no licence). Both put another host in place of the Even app; unverified for shipping products.

Display model ([display docs](https://hub.evenrealities.com/docs/build/display), updated 2026-10-09; names checked in SDK 0.0.16 typings):
- Containers at absolute pixel positions: up to 8 text or list containers plus up to 4 image containers per page (`containerTotalNum` 1-12). Exactly one container has `isEventCapture: 1`. `containerName` is max 16 characters and unique per page.
- No background fill, font choice, font size, bold or alignment. Text is left and top aligned; `\n` breaks lines. Decoration is border (`borderWidth` 0-5, `borderRadius` 0-10) and `paddingLength` 0-32. `textColor` 0-4 is brightness (default 4; 0 can be nearly invisible).
- Text length: 1000 characters on create or rebuild, 2000 on `textContainerUpgrade`. A full-screen container shows about 400-500 characters. Simulator 0.9.5 counts bytes: in our run on 2026-11-09 a rebuild and an upgrade with 963 UTF-8 bytes worked, while 1023 bytes (513 characters) and 1404 bytes returned `false` and left the old text. Hardware byte limits are not documented, so keep each container under 999 UTF-8 bytes (Polish and Cyrillic letters take 2 bytes, CJK 3).
- `textContainerUpgrade` replaces the whole text when you send only `containerID`, `containerName` and `content`, as the official templates do; the official `even-glasses-ui` skill passes `contentOffset: 0, contentLength: 0` for the same full replacement. The docs say only that the two fields "are for partial-string updates" and give no unit. Simulator 0.9.5 ignores both: on 2026-11-09 every upgrade we sent (offsets 0-6, lengths 0-12, Latin, Polish and Japanese text) replaced the whole text. Partial updates are unverified on hardware; do not rely on them.
- Lists: up to 20 items of 64 characters, no per-item styling, no in-place update (rebuild the page).
- One proportional LVGL font in firmware, 27 px line height: 10 lines on 288 px and about 60 Latin characters per full-width line (measured with `@evenrealities/pretext`).
- Scripts, checked in the official `@evenrealities/pretext` 0.1.4 font tables on 2026-11-08: Latin with Latin Extended-A (Polish, Czech, German, French, Nordic, Turkish), Cyrillic (Russian, Ukrainian), Greek, Chinese, Japanese kana and Korean Hangul render. Arabic, Hebrew, Thai and Devanagari have no glyphs and are dropped silently, no placeholder ([#37](https://github.com/even-realities/everything-evenhub/issues/37)). The FAQ says no emoji; U+2713 (check mark) is missing, while ▶ ● ■ ★ and box drawing exist. Filter text to glyphs you have verified.
- Page lifecycle ([page lifecycle](https://hub.evenrealities.com/docs/build/page-lifecycle)): `createStartUpPageContainer` once per launch (0 success, 1 invalid, 2 oversize, 3 out of memory); `textContainerUpgrade` changes one container's text without flicker; `rebuildPageContainer` swaps the whole layout (brief flicker, clears the custom menu unless you pass `menuObject` again); `updateImageRawData` fills an image container (never during create, one send at a time); `shutDownPageContainer(1)` exits through the system dialog.

What BLE costs mean for live text. Every SDK call goes phone -> Bluetooth -> glasses. Community timings (firmware 2.2.7.14, SDK 0.0.13,
[even-g2-notes performance](https://github.com/nickustinov/even-g2-notes/blob/main/docs/performance.md)): about 83 ms per
`textContainerUpgrade`, 165 ms per rebuild, 104 ms fixed per image call plus about 3.9 ms per KB. So for captions:
- update one text container; never render captions as images;
- keep one call in flight and let the newest partial result replace anything queued (a few updates per second at most; the official `asr` template debounces glasses writes to 120 ms and keeps the last 240 characters);
- cut the text yourself to the last lines that fit (there is no native auto-follow, [#45](https://github.com/even-realities/everything-evenhub/issues/45)), using `measureTextWrap` from `@evenrealities/pretext` (its `pxTruncate` keeps the start of a line, useful for titles);
- when three or more containers change at once, one rebuild is cheaper than several upgrades.

Minimal plugin, our own code (names checked against the SDK 0.0.16 typings; compiles with TypeScript 5.8, 5.9 and 7.0; run in
simulator 0.9.5 on 2026-11-08: the text shows, a tap updates it, a double tap closes the page):

```ts
import {
  waitForEvenAppBridge, CreateStartUpPageContainer, TextContainerProperty,
  TextContainerUpgrade, OsEventTypeList, StartUpPageCreateResult,
} from '@evenrealities/even_hub_sdk'

const bridge = await waitForEvenAppBridge() // SDK calls before this are lost

const ID = 1
const NAME = 'captions' // max 16 chars; every update repeats ID and name
const created = await bridge.createStartUpPageContainer(
  new CreateStartUpPageContainer({
    containerTotalNum: 1,
    textObject: [
      new TextContainerProperty({
        containerID: ID, containerName: NAME,
        xPosition: 0, yPosition: 0, width: 576, height: 288,
        paddingLength: 8, isEventCapture: 1, // exactly one container per page captures input
        content: 'Waiting for speech...',
      }),
    ],
  }),
) // once per launch; later layout changes use rebuildPageContainer
if (created !== StartUpPageCreateResult.success) console.warn('startup page failed', created)

// Live text: one write in flight, the newest text wins, stale partials are dropped.
let next: string | null = null
let writing = false
export async function showCaption(text: string): Promise<void> {
  next = text
  if (writing) return
  writing = true
  try {
    while (next !== null) {
      const content = next.slice(-400) // about one screen; fit exactly with @evenrealities/pretext
      next = null
      await bridge.textContainerUpgrade(new TextContainerUpgrade({ containerID: ID, containerName: NAME, content }))
    }
  } finally {
    writing = false
  }
}

// A single tap has no eventType (CLICK_EVENT is 0 and is dropped on the wire) and arrives in sysEvent.
const typeOf = (e?: { eventType?: OsEventTypeList }) => (e ? (e.eventType ?? OsEventTypeList.CLICK_EVENT) : null)
bridge.onEvenHubEvent(event => {
  const types = [typeOf(event.sysEvent), typeOf(event.textEvent), typeOf(event.listEvent)]
  if (types.includes(OsEventTypeList.DOUBLE_CLICK_EVENT)) {
    void bridge.shutDownPageContainer(1) // root page: system exit dialog, required by store review
  } else if (types.includes(OsEventTypeList.CLICK_EVENT)) {
    void showCaption('Tap received at ' + new Date().toLocaleTimeString())
  }
})
```

Build with Vite (`build.target` `esnext` for top-level await) and pack the `dist` folder with `app.json` (see Publishing).

### Arabic and other scripts the font lacks

Checked 2026-11-09 against the docs, the SDK 0.0.16 typings, the official `even-glasses-ui` skill and the official
`image` template ([evenhub-templates](https://github.com/even-realities/evenhub-templates)). Verification: `docs-only`.

- **Empty display with Arabic is expected.** The firmware font has no Arabic glyphs and "Characters outside the font
  set are silently dropped" ([display docs](https://hub.evenrealities.com/docs/build/display), updated 2026-10-09).
- **You cannot ship or upload a font.** FAQ: "Can I use my own font? No. The glasses render with a fixed system
  font." ([FAQ](https://hub.evenrealities.com/docs/reference/faq), updated 2026-10-09). No encoding, language or
  direction setting on a container changes this.
- **No RTL or shaping for text containers.** The docs describe left and top aligned plain text and document no
  direction option or Arabic shaping. Even with glyphs, Arabic would need bidi reordering and contextual letter forms.
- **Fallback: draw the text in the WebView and send it as an image.** Canvas 2D in the plugin's WebView applies the
  phone's shaping and right-to-left order. Keep the text path for supported scripts and switch per message (filter
  with `getAdvW` from `@evenrealities/pretext`). Rules for the image path:
  - Image containers cannot capture input (`ImageContainerProperty` has no `isEventCapture`), so keep one full-screen
    text container with `content: ' '` and `isEventCapture: 1` behind them.
  - Up to 4 image containers per page, each at most 288x144, 4-bit greyscale. They start empty and cannot be filled
    during `createStartUpPageContainer`: create, then call `updateImageRawData`.
  - `updateImageRawData` accepts `number[]`, `Uint8Array`, `ArrayBuffer` or base64. The official `image` template
    passes encoded PNG bytes and the SDK converts them to 4-bit greyscale itself (`imageToGray4Failed` if it cannot).
  - Draw at exactly the container's width and height. The official template says the SDK resizes, but the official
    UI skill describes `imageSizeInvalid` as "image dimensions do not match container"; matching sizes avoids both
    the error and resampling blur.
  - Await each call, one image in flight, and pace about 100 ms between image sends (SDK 0.0.14+ holds the image
    path for 100 ms, "Treat 100ms as a floor"). A full-screen refresh takes about 800 ms, so images suit short
    messages, not live captions.
  - After `shutDownPageContainer(1)` image sends fail until relaunch ([#18](https://github.com/even-realities/everything-evenhub/issues/18)).
  - Check on glasses: the simulator "is not a hardware emulator" and does not match font or greyscale rendering.

Our own sketch (`compiles`: names checked in the SDK 0.0.16 typings, type-checked with TypeScript 7.0, not run):

```ts
import { CreateStartUpPageContainer, ImageContainerProperty, ImageRawDataUpdate, ImageRawDataUpdateResult,
  TextContainerProperty, type EvenAppBridge } from '@evenrealities/even_hub_sdk'
const W = 288, H = 144 // one image container at its maximum size

export function createPage(bridge: EvenAppBridge) {
  return bridge.createStartUpPageContainer(new CreateStartUpPageContainer({
    containerTotalNum: 2,
    textObject: [new TextContainerProperty({ // input layer behind the image
      containerID: 1, containerName: 'input', xPosition: 0, yPosition: 0, width: 576, height: 288,
      content: ' ', isEventCapture: 1,
    })],
    imageObject: [new ImageContainerProperty({ // empty until the first updateImageRawData
      containerID: 2, containerName: 'line', xPosition: 144, yPosition: 72, width: W, height: H,
    })],
  }))
}

async function renderRtl(text: string): Promise<Uint8Array> {
  const c = document.createElement('canvas')
  c.width = W; c.height = H // exactly the container size
  const g = c.getContext('2d')!
  g.fillStyle = '#000'; g.fillRect(0, 0, W, H) // black = off
  g.fillStyle = '#fff'; g.font = '26px sans-serif'; g.direction = 'rtl'; g.textAlign = 'right'; g.textBaseline = 'middle'
  g.fillText(text, W - 8, H / 2) // one short line; wrap longer text with measureText first
  const png = await new Promise<Blob>((ok, no) => c.toBlob(b => (b ? ok(b) : no(new Error('toBlob'))), 'image/png'))
  return new Uint8Array(await png.arrayBuffer()) // encoded PNG; the SDK converts it to 4-bit greyscale
}

let queue: Promise<unknown> = Promise.resolve() // one image in flight, 100 ms apart
export const showRtl = (bridge: EvenAppBridge, text: string) => (queue = queue.then(async () => {
  const imageData = await renderRtl(text)
  const r = await bridge.updateImageRawData(new ImageRawDataUpdate({ containerID: 2, containerName: 'line', imageData }))
  if (r !== ImageRawDataUpdateResult.success) console.warn('image send', r) // imageSizeInvalid: wrong width or height
  await new Promise(done => setTimeout(done, 100))
}))
```

## Input
- Gestures: tap, double tap, swipe up, swipe down, long press and release, on the left temple, the right temple or the R1 ring (same gestures, [glossary](https://hub.evenrealities.com/docs/reference/glossary)). No haptics. The R1 is not yet compatible with G1.
- One callback, `bridge.onEvenHubEvent`. Envelopes: `sysEvent` (taps, double taps, long press, lifecycle, IMU; `eventSource` 1 = right temple, 2 = ring, 3 = left temple), `textEvent` or `listEvent` (scroll events from the capture container, no source), `audioEvent`, `menuItemClickEvent`.
- `OsEventTypeList` (SDK 0.0.16): CLICK 0, SCROLL_TOP 1, SCROLL_BOTTOM 2, DOUBLE_CLICK 3, FOREGROUND_ENTER 4, FOREGROUND_EXIT 5, ABNORMAL_EXIT 6, SYSTEM_EXIT 7, IMU_DATA_REPORT 8, LONG_PRESS 9, LONG_PRESS_RELEASE 10 (long press needs SDK 0.0.14+ and Even app 2.2.9+).
- Swipes: when the capture container overflows, the firmware scrolls it and you only get SCROLL_TOP or SCROLL_BOTTOM at the boundary (community, [input notes](https://github.com/nickustinov/even-g2-notes/blob/main/docs/input-events.md)). If swipes are commands, keep the capture container from overflowing. Throttle repeats (about 300 ms).
- Reserved by the system: tap then long press opens the system menu (Display off, Brightness, Close app) plus your `menuObject` items (max 10, labels max 32 UTF-8 bytes, fire-and-forget). Opening that menu sends FOREGROUND_ENTER (4) and closing it sends FOREGROUND_EXIT (5) ([contextual menu](https://hub.evenrealities.com/docs/build/contextual-menu)). On the root page a double tap must call `shutDownPageContainer(1)`; mode 0 or a custom exit screen there is rejected in review.
- Also: `onLaunchSource` (`'appMenu'` or `'glassesMenu'`), `onDeviceStatusChanged` (connection, wearing, battery, charging, in case), `imuControl` for head motion.
- Shared caption actions: tap = repeat, swipe down = skip, long press = hide, double tap = exit on the root page.

## Audio
- `bridge.audioControl(true, AudioInputSource.Glasses)` (wearer's voice) or `AudioInputSource.Phone` (the phone's microphone, better for the person opposite); `audioControl(false)` stops. The glasses source needs the startup page to exist first, the phone source does not. Declare `g2-microphone` or `phone-microphone` in `app.json` ([device APIs](https://hub.evenrealities.com/docs/build/device-apis), 2026-08-29). The plugin captures both itself: no second phone app is needed.
- Frames arrive as `event.audioEvent.audioPcm` (`Uint8Array`), PCM 16 kHz, signed 16-bit little-endian, mono, about 32 KB/s. The simulator sends 100 ms (3200 bytes) per event; the hardware chunk size is not documented.
- SDK 0.0.14+ adds `direction` and `speakerRole` (`self`, `other`, `unknown`) on glasses frames. It is the Even app's guess, "not a firmware identity assertion": use it as a hint only.
- No speech-to-text for plugins ([#9](https://github.com/even-realities/everything-evenhub/issues/9), open). Stream PCM to your own server or STT provider. Keep provider keys on a server: anyone can unpack an `.ehpk`. The official `asr` template leaves the provider as a stub and reads a key from `VITE_STT_API_KEY`, which Vite inlines into the bundle: replace that with your relay before you submit ("Never bundle secrets or API keys into the `.ehpk`", [app submission](https://hub.evenrealities.com/docs/ship/app-submission)).
- `getUserMedia` inside the plugin WebView fails with `NotAllowedError` on iOS ([#11](https://github.com/even-realities/everything-evenhub/issues/11)); use `audioControl` with the phone source.
- No speaker and no audio output API ([#26](https://github.com/even-realities/everything-evenhub/issues/26), open). Web Audio in the WebView needs a gesture on the phone screen and stops on lock.

## Testing without hardware
- Install and run: `npm i -g @evenrealities/evenhub-simulator`, then `evenhub-simulator http://localhost:5173 --automation-port 9898`. Binaries for Windows, macOS and Linux (x64 and arm64; Linux and Windows arm64 are experimental since 0.9.4). The PC microphone feeds `audioEvent`; simulator 0.9.5 refuses `AudioInputSource.Phone` until the startup page exists and tags those frames `glasses` either way (our run, 2026-11-09).
- Automation API ([simulator docs](https://hub.evenrealities.com/docs/test/simulator)): `GET /api/ping`, `GET /api/screenshot/glasses` (576x288 RGBA, lit pixels have alpha > 0), `GET /api/screenshot/webview`, `GET /api/console` (`?since_id=N`), `POST /api/input` with `{"action":"up|down|click|double_click|long_press|long_press_release|context_menu"}`. The console endpoint also accepts the HTTP DELETE method, which clears the buffer. Input is ignored until a capture container exists. There is no shutdown endpoint; kill the process.
- Not emulated: BLE timing, exact font rendering and brightness, list focus position, image size limits and the LZ4 path, status events (fixed device profile, `eventSource` always 1), permissions, background and lock, iOS WKWebView quirks. The network whitelist is not enforced (community). In our run on 2026-11-08 a double tap closed the page at once, with no exit dialog.
- Restart the simulator after code edits: on hot reload `createStartUpPageContainer` returns 1 and the display goes dead ([#32](https://github.com/even-realities/everything-evenhub/issues/32)).
- On hardware: QR sideload (`evenhub qr --url http://<LAN-IP>:5173`) stops when the phone locks; a private build survives briefly; a beta build survives lock and shows in the glasses menu ([beta testing](https://hub.evenrealities.com/docs/test/beta-testing)). Device logs are in the Even app's dev console in Developer Mode.

## Publishing and distribution
- Account: sign in at `hub.evenrealities.com/login` with your Even app account, then force-quit and reopen the Even app to get the developer section. There is no toggle and the docs mention no fee.
- `app.json` ([packaging](https://hub.evenrealities.com/docs/ship/packaging)): `package_id` reverse-DNS, lowercase letters and digits, no hyphens, permanent; `edition` `"202601"`; `name` max 20 characters and must not contain "Even", case-insensitive (auto-rejected as impersonation, [app submission](https://hub.evenrealities.com/docs/ship/app-submission)); `version` `x.y.z`, immutable once published; `permissions` is an array of `{name, desc}`; `network` whitelist entries are full origins (no wildcards, no bare hosts) and CORS still applies; `supported_languages` only `en de fr es it zh ja ko`.
- CLI flow: `evenhub login`, `evenhub pack app.json dist -o app.ehpk --sdk-ver 0.0.16` (without `--sdk-ver` the CLI stamps the floor of the latest SDK), `evenhub create app.ehpk` for the first build and `evenhub upload` after, `evenhub promote <version> --to beta`, `evenhub testers`. Public release is submitted in the portal.
- Beta: one slot per app and one flat tester list; testers accept an email invite and must show `Active`; CSV import up to 500 addresses per file.
- Review ([app submission](https://hub.evenrealities.com/docs/ship/app-submission), updated 2026-10-09): a reviewer installs the build as a beta tester and tests it with the phone locked and the Even app backgrounded, with glasses and ring input only, after 2 minutes idle. Also checked: an on-glasses message when setup is missing (never a black screen), setup remembered, root double tap exit, a privacy policy covering every permission, documented backend domains, no secrets, a greyscale icon, a non-empty changelog, no medical or financial advice. Review time is not published. Hotfixes are reviewed too. No rollback, fix forward only.
- Paid apps: "TBD. There is no paid distribution yet." Published versions are visible worldwide. Practical `.ehpk` limit about 10 MB (as of 2026-11-08, FAQ).
- The store opened in early April 2026 ([9to5Google, 2026-03-26](https://9to5google.com/2026/03/26/even-realities-even-hub-apps-and-better-conversate-mode/), press).

## Built-in features you compete with
Conversate, built into the Even app: Live Transcript (real-time captions), Prep Notes (documents loaded before a meeting), AI Cues
(Suggestions, Answers, Concepts, Bios) and AI Summary; it needs internet through the phone
([Conversate page](https://www.evenrealities.com/en-DE/conversate), checked 2026-11-08). Plugins are foreground-only, so a captions or
coaching plugin must beat Conversate on something concrete: a language it handles worse, your own documents or backend, or a domain.

## Pitfalls
- **Taps never reach a `textEvent` handler.** Taps arrive as `sysEvent` and a single tap has no `eventType` at all ([#30](https://github.com/even-realities/everything-evenhub/issues/30), [#31](https://github.com/even-realities/everything-evenhub/issues/31)). Read all envelopes, map a missing type to CLICK inside a present envelope, check DOUBLE before CLICK.
- **The exit dialog breaks images.** After `shutDownPageContainer(1)` every `updateImageRawData` returns `sendFailed` until relaunch, even when the user cancels ([#18](https://github.com/even-realities/everything-evenhub/issues/18), open). Review still requires mode 1 on the root page, so prefer text-only root pages.
- **Plugin turns white in the background on iOS.** iOS can kill the WebView content process and the host does not reload it ([#16](https://github.com/even-realities/everything-evenhub/issues/16)). The docs disagree (iOS "keeps running" vs FAQ "WebView is suspended"). Persist state eagerly and repaint on FOREGROUND_ENTER.
- **Official `background-state` skill uses APIs that do not exist.** `setBackgroundState` and `onBackgroundRestore` are not in SDK 0.0.16 (checked 2026-11-08). Use `bridge.setLocalStorage` or `localStorage` instead.
- **Microphone silently stops.** `audioControl` can return `false` until the plugin is reopened ([#35](https://github.com/even-realities/everything-evenhub/issues/35)). Watch for "no frames for a few seconds" and show it on the glasses.
- **SDK timers clash with native timer ids.** SDK 0.0.16 replaces `setTimeout` and `setInterval`, so `clearTimeout` with a native id can cancel an unrelated plugin timer ([#47](https://github.com/even-realities/everything-evenhub/issues/47)). Import the SDK first; do not mix timers captured before it loaded.
- **Text vanishes in some languages.** See the script list above ([#37](https://github.com/even-realities/everything-evenhub/issues/37)); there is one font size ([#48](https://github.com/even-realities/everything-evenhub/issues/48)).
- **Requests blocked.** Whitelist the exact origin, including `wss://` for WebSockets (the official `asr` template README shows both), and send CORS headers; wildcard behaviour is undocumented ([templates #1](https://github.com/even-realities/evenhub-templates/issues/1)). Expect sockets to drop when the WebView backgrounds.
- **Stale manifest from `evenhub init`.** It writes old `min_sdk_version` and `min_app_version` ([#29](https://github.com/even-realities/everything-evenhub/issues/29), [#33](https://github.com/even-realities/everything-evenhub/issues/33)); set `min_sdk_version` to your SDK and pass `--sdk-ver` to `pack`.
- **Developer section missing in the phone app.** Force-quit alone may not be enough and the entry point moved ([#34](https://github.com/even-realities/everything-evenhub/issues/34)).

## Even G1 (older model)
- No longer sold: "Even G1 is no longer available for purchase"; existing units keep warranty, support and security updates ([G1 page](https://www.evenrealities.com/en-CZ/products/g1-a), checked 2026-11-08). Even R1 is not yet compatible with G1.
- Even Hub docs describe only G2. The SDK's `DeviceModel` enum lists `g1`, but no G1 plugin support is documented (unverified).
- Open BLE protocol in [even-realities/EvenDemoApp](https://github.com/even-realities/EvenDemoApp) (BSD-2-Clause, Flutter demo): each arm is its own BLE link (send to the left arm, wait for its ack, then the right), text sent screen by screen, 1-bit 576x136 BMP images in 194-byte packets with a CRC check, microphone as LC3 audio, TouchBar tap events. Bitmaps take seconds ([#36](https://github.com/even-realities/EvenDemoApp/issues/36)), so send text.
- Community: [emingenc/even_glasses](https://github.com/emingenc/even_glasses) (Python, GPL-3.0, last push 2024-11). MentraOS supports G1 as text only: 640x200 panel, no positioned elements, no bitmaps ([Mentra display docs](https://docs.mentraglass.com/app-devs/core-concepts/display/layouts.md)).

## Official resources
- Docs: https://hub.evenrealities.com/docs/get-started/overview
- FAQ: https://hub.evenrealities.com/docs/reference/faq
- Changelog: https://hub.evenrealities.com/docs/reference/changelog
- SDK: https://www.npmjs.com/package/@evenrealities/even_hub_sdk
- CLI: https://www.npmjs.com/package/@evenrealities/evenhub-cli
- Simulator: https://www.npmjs.com/package/@evenrealities/evenhub-simulator
- Font metrics: https://www.npmjs.com/package/@evenrealities/pretext
- Templates: https://github.com/even-realities/evenhub-templates
- Official agent skills and issue tracker: https://github.com/even-realities/everything-evenhub
- G1 protocol demo: https://github.com/even-realities/EvenDemoApp
- Community notes (unofficial, measured on hardware): https://github.com/nickustinov/even-g2-notes , https://github.com/pangoleen/awesome-even-realities-g2
