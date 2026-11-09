# Non-Latin scripts, RTL and fonts

Last checked: 2026-11-08. Verification: Even G2 font coverage checked against Even's own font tables
(`@evenrealities/pretext` 0.1.4) and the Even Hub simulator; everything else `docs-only`. No script was tested on
glasses hardware.

## Per brand (as of 2026-11-08)

| Display | Font | Works | Missing or unknown | Source |
|---|---|---|---|---|
| Even Realities G2 | one LVGL font in firmware, fallback chain Latin, Cyrillic and Greek, CJK, a small emoji set | Latin incl. Central European letters, Cyrillic (Russian, Ukrainian), Greek, Chinese, Japanese, Korean; Even's language page lists those for text display | Arabic, Hebrew, Thai and Indic scripts are silently dropped (no placeholder); some symbols such as U+2713 check mark are missing; no RTL, no alignment | https://hub.evenrealities.com/docs/build/display, https://github.com/even-realities/everything-evenhub/issues/37, https://support.evenrealities.com/hc/en-us/articles/13755354799247-Language-Support |
| Meta Ray-Ban Display Web App | Noto Sans in Meta's UI toolkit; any web font you ship | what your font stack covers; the browser does bidi and shaping | Meta's localization notes say CJK, Arabic and Devanagari render "only if the system font stack covers them"; which fonts are on the device is not published | https://github.com/meta/meta-wearables-webapp/blob/main/plugins/meta-wearables-webapp-game/docs/localization.md |
| Meta DAT display | system text styles | unverified per script | unverified | https://wearables.developer.meta.com/docs/develop/dat/display-overview/ |
| Rokid Glasses (CXR-L) | the glasses' Android system fonts | Chinese (the platform's home market); Japanese reported working on the Global app (community) | Arabic RTL support is an open question with no answer (Rokid/community issue #20, opened 2026-09-13) | https://github.com/Rokid/community/issues/20 |
| Vuzix Z100 | the SDK generates glyphs on the phone for characters the glasses lack and uploads them; the iOS framework bundles Noto Sans, Noto Sans CJK and Noto Emoji | Latin, Cyrillic, CJK expected; iOS SDK 1.9.0: "Notifications now support any language glyphs"; `TextAlignment.AUTO` picks left or right by language | Arabic shown reversed was reported (ultralite-sdk-android issue #2); Vuzix said 1.9 fixes it and closed the issue after the 1.9 release (2025-03-20), not verified by us; first use of new characters may be slower (glyph upload) | https://github.com/Vuzix/ultralite-sdk-android/issues/2, https://github.com/Vuzix/UltraliteSDK-releases-iOS/releases/tag/v1.9.0 |
| USB-C display glasses | the phone's own text rendering | everything the phone renders | nothing extra | - |
| Phone notification on glasses | the companion app's font on the glasses | depends on the app | test each script on the device | - |
| Android XR display glasses | Google Sans Flex in the Glimmer guidance; Android text stack | Android's script support | unverified on the glasses | https://developer.android.com/design/ui/ai-glasses/guides/styles/type |

## Rules for any target

1. **Know what the target cannot draw, before showing it.** On Even G2, filter with the font tables and count what
   you removed:

   ```ts
   import { getAdvW } from '@evenrealities/pretext'
   function forG2(text: string): { text: string; dropped: number } {
     let out = '', dropped = 0
     for (const ch of text.normalize('NFC')) {
       if (ch === ' ' || getAdvW(ch.codePointAt(0)!) > 0) out += ch
       else if (!/[\u200B-\u200F\uFE0F\uFEFF]/.test(ch)) dropped++ // invisible characters do not count
     }
     return { text: out, dropped }
   }
   ```

   When `dropped` is more than a few characters, say so on the display ("some characters not shown") instead of
   showing a sentence with holes. The Even example plugin does this in its status line.
2. **Normalise text** to NFC, replace unusual spaces with plain spaces, and drop zero-width characters and emoji
   variation selectors before measuring.
3. **Pick the STT language from the conversation, not the display.** A translator can transcribe Arabic and show the
   English translation on a Latin-only display. That is often the best answer for Even G2 today.
4. **Never test only with English.** Keep a test line per script you support, for example `Zażółć gęślą jaźń`,
   `Съешь же ещё этих мягких булок`, `日本語の字幕テスト`, `مرحبا بالعالم`, `שלום עולם`, `สวัสดีครับ`, `नमस्ते दुनिया`.

## Right-to-left text

- **Wrap in logical order**, measure each line as a logical string, and let the renderer reorder it.
- **Web targets:** put each caption line in its own element with `dir="auto"` (the web example does this), so an
  Arabic line runs right to left and a mixed line keeps numbers and Latin words in the right order.
- **Android and iOS:** `StaticLayout` and Core Text handle bidi and Arabic shaping. Vuzix canvas text has
  `TextAlignment.AUTO`; check on the device that RTL text is not reversed.
- **Targets with a simple glyph renderer** (fixed firmware fonts) need two things you cannot fake by reversing the
  string: the bidi algorithm (Unicode UAX #9) and Arabic contextual shaping (each letter has up to four forms).
  Without both, render to an image.

## CJK and Thai

- No spaces between words: break between characters, or better at word boundaries from `Intl.Segmenter`
  (`granularity: 'word'`), which also handles Thai. The example `wrap()` does this.
- CJK characters are about twice as wide as Latin letters. With a character budget, count each as two.
- Line-start rules (do not start a line with `。`, `、`, `」` and similar) matter less for live captions than for
  books; a simple fix is to keep closing punctuation with the previous character.
- Hangul must be composed (NFC). A decomposed Korean string can show as separate jamo on some glasses (reported on
  MentraOS for Even G1, https://github.com/Mentra-Community/MentraOS/issues/3740).

## Render-to-image fallback

When the font lacks the script, draw the text on the phone and send a bitmap:

1. Render with the platform's text engine (Canvas 2D in a WebView, `StaticLayout` on Android, Core Text on iOS) at the
   glasses' pixel size, white or green on black.
2. Hand the bitmap over in the format the target takes.
   - **Even G2:** apps cannot ship or upload a font ([FAQ](https://hub.evenrealities.com/docs/reference/faq),
     2026-10-09), and no RTL or Arabic shaping is documented for text containers, so the image is the only way.
     Draw at exactly the image container's size (at most 288x144, four per page); the official UI skill describes
     `imageSizeInvalid` as "image dimensions do not match container". `updateImageRawData` accepts `number[]`, `Uint8Array`, `ArrayBuffer` or base64; pass the
     encoded PNG and let the SDK convert it to 4-bit greyscale itself (the official `image` template does this). Image
     containers cannot capture input: keep one full-screen text container with `content: ' '` and
     `isEventCapture: 1` behind them. Fill images only after the page exists, await each call and pace about 100 ms
     between image sends.
   - **Vuzix:** 2-bit `LVGLImage` or canvas background bitmaps up to 640x480.
3. Send finals only. Images are slow over BLE: on Even G2 a full screen takes about 800 ms (Even docs); Vuzix notes
   that "sending large bitmaps is often slower than sending text".
4. Keep a text path for scripts the font has, and switch per line, not per session.

Even G2 code for this path: `smart-glasses` skill, `references/brands/even-g2.md`, section "Arabic and other scripts
the font lacks", and the official `even-glasses-ui` skill. Vuzix: the `smart-glasses-vuzix` skill.

## Fonts on web targets

- Ship the fonts for your scripts from your own origin as subset WOFF2 files (Meta's performance guidance for Web
  Apps: drop third-party font CDNs, subset to the characters you render, `font-display: swap`).
- Re-measure after fonts load (`document.fonts.ready`), or the first lines are wrapped with fallback metrics.
- Check the first-load budget on Meta Ray-Ban Display (under 300 KB and under 15 requests, per Meta's guidance):
  a CJK font is several megabytes unsubset.
