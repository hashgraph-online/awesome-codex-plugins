# UI for small glasses displays

Read this before you lay out text, pick font sizes or colours, or decide how often and how long text appears on any
display glasses.

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). Numbers come from the brand files and the
sources linked there; anything marked "estimate" is our arithmetic, not a measurement on glasses.

## Additive optics: black is transparent

Waveguide and micro-LED displays (Even G2, Rokid, Vuzix Z100, Meta Ray-Ban Display, RayNeo X3 Pro, Halo, Android XR)
add light to the world. They cannot draw black or darken anything.

- **Background: pure black (`#000000`).** Black pixels are off and read as see-through. USB-C birdbath glasses behave
  the same way behind their tinted front.
- **Never use white or light backgrounds, cards or panels.** They hide the world, cause glare and halation (bright
  areas bleed into the text next to them) and drain the battery
  ([Google, Designing for transparent screens](https://design.google/library/transparent-screens)). Use thin borders
  or brightness instead of filled boxes.
- **Never use black or very dark text and icons.** They are invisible. Dark colours add little light and fade.
- **Weight:** medium or bold, never thin or hairline: thin strokes shimmer and become unreadable outdoors (Google, same
  page, and the official Glimmer skill).
- **Size by visual angle, not pixels.** Google sets the floor at about 0.6 degrees, roughly 18sp at the 1 m focal
  distance of Android XR glasses ([Android XR design](https://developer.android.com/design/ui/ai-glasses/guides/foundations/design-principles)).

## Monochrome green vs colour

- **Green only:** Even G2 (text has 5 brightness levels, `textColor` 0-4; images and borders 16 levels), Rokid
  Glasses (a green-only panel: send bright and dim green, `textColor` as `#AARRGGBB`), Vuzix Z100 (4 levels:
  `BLACK` = off, `DIM`, `MID`, `WHITE`). Design with brightness, not hue: the current line at full brightness, context
  one or two steps dimmer.
- **Colour:** Meta Ray-Ban Display, RayNeo X3 Pro, INMO Air3, Halo, USB-C glasses. Prefer near-white or desaturated
  text on black; saturated colours lose contrast against the world. Use red only for warnings (RayNeo design spec).
- Do not encode meaning in colour alone. The same app often runs on a green-only pair.

## Budgets per device

Plan for the practical column. "Fits" is what the canvas holds; "practical" is what stays readable at a glance.

| Device | Canvas and eyes | Fits | Practical for captions or hints | Source |
|---|---|---|---|---|
| [Even G2](brands/even-g2.md) | 576x288, both eyes, green | One font, 27 px lines: 10 lines, about 60 Latin chars per full-width line; 400-500 chars per full screen | 3-4 lines of the newest text (estimate) | Even docs, `@evenrealities/pretext` |
| [Meta Ray-Ban Display](brands/meta-display.md) | 600x600, right eye, colour, about 20 degrees | Web Apps: Meta's UI kit uses 28 px text on 36 px lines | About 35-40 chars per line, 3-4 lines plus buttons (estimate); DAT text sizes undocumented | Meta UI kit, our estimate |
| [Rokid Glasses](brands/rokid.md) | About 480 px wide (Android reports 480x640 portrait, press says 480x398 visible), both eyes, green | `textSize` 16sp or more per the docs; 24sp gives about 22-24 Latin chars | 3 lines of 24sp, about 22 Latin chars each, plus an optional title (estimate; same in the Rokid skill and the example) | Rokid docs, community |
| [Vuzix Z100](brands/vuzix-z100.md) | 640x480, right eye, 4 levels | Text layout: about 42 Latin chars and 7 lines | 3 lines; about 36 chars in the text layout, or 28-34 px on the canvas at about 40-48 chars per 600 px (estimate) | MentraOS measurement (community) |
| [USB-C display glasses](brands/usb-c-displays.md) | A full external monitor, both eyes | Anything | 2-3 lines in the lower part, font about 7% of display height | Our layout rule |
| [RayNeo X3 Pro](brands/standalone-android-glasses.md) | 640x480, both eyes, colour | Font 16 px minimum | Safe margins 30 px left and right, 20 px top and bottom | RayNeo design spec |
| [Brilliant Labs Halo](brands/brilliant-labs.md) | Round 256x256 drawable area, colour | 32 chars per line with the 8 px font; ASCII only; no wrap | 2-3 short lines in the centre (estimate) | Brilliant docs |
| [MentraOS](brands/mentra.md) | Per glasses | Design for 500x220 | Same as the underlying glasses | Mentra docs |
| [Android XR display](brands/android-xr.md) | Not on sale yet | Glimmer body text 20-30sp, captions 18sp | Follow the official Glimmer skill | Google |

Per-script character budgets differ: Cyrillic takes about 1.5x the width of Latin text and CJK about 2.3x at the same
size (Vuzix display notes, estimate). Measure with the platform's own text measurement where it exists
(`@evenrealities/pretext` on Even, `Paint.measureText` on Android, `NSString.size(withAttributes:)` on iOS).

## Safe areas and layout

- **Even G2:** the SDK canvas is the visible area. There is no alignment, so pad with `paddingLength` (4-8 px keeps
  text off the edge) and pad lines with spaces to centre them.
- **Rokid:** keep content centred vertically; the top and bottom of the 640 px height may be outside the visible
  398 rows.
- **RayNeo X3 Pro:** 30 px left and right, 20 px top and bottom at 640x480 (official). Use this as the default margin
  for any 640x480 panel without its own spec.
- **Meta Ray-Ban Display, Vuzix Z100:** no safe area published; our samples use 24 px padding on Meta. Both are
  right-eye only.
- **Captions:** newest line at a fixed position (bottom), older lines above and dimmer. Never let a wrap push the
  newest words off screen: cut to the last lines that fit before you send.
- One idea per screen. No headers, logos or status rows unless the wearer needs them right now.

## Brightness and lit pixels (APL)

- Keep the average picture level low. RayNeo's spec: average pixel brightness under 13% for content that stays on
  screen, under 25% for short content ([design spec](https://rayneo.gitbook.io/rayneo-devdoc/x-xi-lie/she-ji-gui-fan.md)).
  Use it as the rule of thumb on every brand: text and thin outlines only, no filled areas.
- Lit pixels cost battery and heat on the glasses and glare for the wearer. Large images are slow over BLE as well.
- Leave panel brightness to the wearer. Rokid's `setGlassBrightness` and the Vuzix brightness property exist, but the
  wearer adjusts for the light around them; Meta adapts automatically (30 to 5,000 nits, press).

## How long text may stay

- **Panels sleep.** Meta Ray-Ban Display dims after 20 s without input and sleeps at 25 s, with no API to observe or
  wake it (Meta docs). Rokid turns the screen off after about 20 s by default (community). Vuzix uses your
  `timeout` in seconds (`0` keeps it on; new content wakes it). Plan an earcon or a short spoken cue when the wearer
  must look after a quiet period.
- **Notifications** (rung 4) stay a few seconds; the companion app decides.
- **Content:** show it when needed and let it recede when the task is done
  ([Android XR design principles](https://developer.android.com/design/ui/ai-glasses/guides/foundations/design-principles)).
  Our defaults (not measured): a caption stays until it is replaced and clears 4-6 s after the last final result;
  an answer or hint stays 8-15 s or until the wearer dismisses it; never leave stale text on screen after a session.

## Update rates over BLE

| Path | Cost per update | Advice |
|---|---|---|
| Even Hub `textContainerUpgrade` | About 83 ms; a rebuild about 165 ms (community, firmware 2.2.7) | One call in flight, newest text wins; the official `asr` template debounces at 120 ms |
| Rokid `customViewUpdate` | Not published | 250 ms timer; an iOS community test stayed smooth at about 8 per second |
| Vuzix canvas or `LiveText` | Not published; `LiveText` sends image slices | 300 ms in our example |
| Meta DAT `sendContent` | Whole screen per send, no limit published | Start at 2 per second (500 ms) and measure |
| Notifications | Android sheds updates to an existing notification above 5 per second per package | A new notification per message, at most one every 2-3 s |
| Web app, USB-C display | Frame rate, no BLE | Replace text in place; no animation needed |

Partial speech results change several times a second. Coalesce them: keep one pending string, drop older ones, never
queue updates behind a slow link.

## Motion and walking

- Text on glasses is head-locked: it moves with the head. Do not make the wearer chase moving text. Avoid marquee and
  auto-scroll modes (Vuzix `TextWrapMode.SCROLL`) for live text; replace lines in place.
- Google: "Avoid UI and motion that could induce motion sickness, such as expecting users to read large amounts of
  text while walking", and avoid "sudden, distracting visual notifications" (design principles page above).
- Transitions should be slow or absent. Google found a 500 ms fade too fast to notice and uses almost two seconds for
  notification transitions; focus and input feedback must stay instant (transparent screens article).
- When you know the wearer is moving (head motion from Even's IMU, Android activity recognition, speed from GPS),
  show fewer lines and shift detail to voice (our advice).

## Scripts and right-to-left text

| Path | Renders | Watch out |
|---|---|---|
| Even Hub text containers | Latin with Extended-A, Cyrillic, Greek, Chinese, Japanese kana, Korean | Arabic, Hebrew, Thai, Devanagari dropped silently; no emoji |
| Halo (and Frame) | ASCII only (Frame adds Latin-1) | Rasterise other scripts on the host |
| Vuzix glasses-rendered text | Glyphs compiled per script by the SDK (unverified per script) | RTL notifications: Vuzix said 1.9 fixes them (unverified); `LiveText` renders on the phone, any script |
| Rokid custom view | Android system fonts on the glasses; CJK shown by community | RTL is an open question; no emoji |
| Meta DAT | Undocumented | Draw unverified scripts into a bitmap |
| Web apps, USB-C displays | Browser or phone fonts, full shaping | Check fonts on the glasses' browser |

Details, fallbacks and a per-language table: the `smart-glasses-live-captions` skill,
[references/scripts-and-fonts.md](../../smart-glasses-live-captions/references/scripts-and-fonts.md).

## Related
- [display-text-ladder.md](display-text-ladder.md), [input.md](input.md), [choose-target.md](choose-target.md).
- Official design guidance: Even Hub (`npx skills add even-realities/everything-evenhub`, skill
  `even-design-guidelines`), Android XR Glimmer (`display-glasses-with-jetpack-compose-glimmer`), Meta's
  [UI toolkit for Web Apps](https://github.com/meta/meta-ray-ban-display-ui-toolkit-web).
