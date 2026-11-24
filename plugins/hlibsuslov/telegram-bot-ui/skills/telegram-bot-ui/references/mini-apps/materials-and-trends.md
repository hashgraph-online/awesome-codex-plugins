# Materials, trends and platform change

How to keep a Mini App current when Apple, Google and Telegram redesign their interfaces without chasing every
fashion. It covers:
- glass and other materials as a token system that a redesign updates in one place;
- a radar of current interface trends, each with a decision for Mini Apps;
- the web platform features worth using inside Telegram's WebViews, with fallbacks;
- the procedure to follow when a platform ships something new.

Read it when someone asks for "glassmorphism", "the new iOS look", "modern", "trendy" or "2026 design", and
before adopting any CSS feature newer than the kit uses.

Labels:
- **[Official]** Telegram or the platform vendor;
- **[Heuristic]** this skill's rule;
- **[Check]** a version or a behaviour to confirm before relying on it, because it changes with every
  release (§5);
- **[Device]** confirm it on a real client.

Kit: the `--tma-glass-*` tokens, `.tma-glass`, `.is-thin`, `.is-thick`, `.tma-scroll-edge`, `data-tma-glass`.
Values with their sources: `data/mini-apps/design-sources.json` → `web_materials`. Gallery: the tab bar.

## 0. Taste over trend

A trend is adopted only when it passes all four tests **[Heuristic]**:

1. **It serves the task.** It makes something clearer, faster or more certain for the person using the app.
   "It looks modern" does not count.
2. **It matches Telegram's chrome today.** The app sits between Telegram's header and bottom buttons. A
   trend that makes it look foreign to that chrome is out, however fashionable.
3. **It degrades.** Old WebViews, low-end Android, reduced motion, reduced transparency and increased
   contrast all get a calm, complete version.
4. **It lives in tokens or one class.** If adopting it means touching every component, it will be wrong by
   the next platform release. Put it behind a token (§2) or a single kit class.

Trends that fail are written down as "avoid" in §3 with the reason, so the next agent does not reopen them.

## 1. Three layers, three update speeds

| Layer | Who draws it | Changes when | What the app does |
|---|---|---|---|
| Telegram's chrome: header, Close / Back, menu, MainButton, popups, invoice sheet | Telegram, natively | Telegram updates its app (on iOS, Liquid Glass since the iOS 26 era) **[Official]** | nothing; colour it (`setHeaderColor`, `setBottomBarColor`), never imitate it |
| The WebView engine | the OS or Telegram's desktop app | iOS: WKWebView, the Safari engine of the installed iOS. Android: Android System WebView (Chromium), updated through the store and sometimes months behind. Telegram Desktop: the platform's web view (WebView2 on Windows, WKWebView on macOS, WebKitGTK on Linux). Web clients: the user's browser **[Check]** | decides which CSS works: progressive enhancement (§4) |
| The app: everything between the chrome | you | when you ship | tokens, kit classes, one moment per screen |

The app's job is to stay a quiet neighbour of whatever the chrome looks like this year. Neighbour means the
same radii family, the same weight of materials and the same colours from `themeParams`. It never means a copy
of Telegram's controls.

## 2. Glass as a material system

### 2.1 What glass is for

Glass separates a **floating control** from **content scrolling underneath it**. It answers "this stays, that
moves". Apple's Liquid Glass and Telegram's iOS chrome use it for controls and navigation, not for content
**[Official, Apple HIG Materials]**. In a Mini App that means:

| Allowed (level) | Never |
|---|---|
| The floating tab bar, the floating circle next to it, bottom capsules (`regular`) | cells, rows and cards |
| Icon buttons and chips over photos and video (`.is-thin`) | the content of a sheet, text blocks |
| A sticky segmented control or search field over scrolling text (`.is-thick` + `.tma-scroll-edge`) | buttons inside content, the page background |
| — | glass on glass; glass as "premium" decoration (anti-slop §3) |

### 2.2 How the kit builds it

One class reads six tokens. The levels change only the tokens:

```css
:root {
  --tma-glass-tint: 62%;  --tma-glass-blur: 16px;  --tma-glass-saturate: 1.8;
  --tma-glass-rim: rgb(255 255 255 / .35);  --tma-glass-rim-low: rgb(0 0 0 / .08);
  --tma-glass-lift: 0 8px 24px rgb(0 0 0 / .14);
}
.tma-glass { background: color-mix(in srgb, var(--tma-surface) var(--tma-glass-tint), transparent);
             backdrop-filter: blur(var(--tma-glass-blur)) saturate(var(--tma-glass-saturate)); … }
.tma-glass.is-thin  { --tma-glass-tint: 45%; --tma-glass-blur: 6px;  … }
.tma-glass.is-thick { --tma-glass-tint: 80%; --tma-glass-blur: 24px; }
```

- **The tint comes from the theme surface** (`--tma-surface`, from `section_bg_color`), so glass follows the
  user's Telegram theme, light, dark or custom. It never uses a white or black of its own.
- **Solid when it must be.** The kit switches to the solid surface in each of these cases:
  - reduced transparency;
  - increased contrast;
  - no `backdrop-filter` support;
  - Android performance class `LOW`;
  - `data-tma-glass="off"`;
  - the `dense` style.

  An app never removes these fallbacks.
- **Text on glass** must pass contrast against the worst content that can scroll under it: a white photo
  in light mode, a black one in dark mode. Use `.is-thick` under text labels, semibold labels, and the
  `.tma-scroll-edge` fade under a sticky top control **[Heuristic]**.
- **No fake refraction.** Liquid Glass bends and splits light with a native shader. Approximating it with SVG
  displacement maps in `backdrop-filter: url(#…)` works only in Chromium. It costs frames on phones and looks
  different on every client. Frost, rim light and lift are what CSS does reliably **[Heuristic, Check]**.
- **Android.** Telegram's Android client does not draw iOS glass **[Device]**. The kit keeps glass on
  floating controls there, because it reads as a Material "floating surface". It goes solid on `LOW` and in
  the `dense` style. Never add glass on Android that iOS does not have.

### 2.3 When the platform redesigns

The kit's glass values come from the iOS 27 kit (frost "regular" 6, "medium-large" 16) translated to CSS, plus
this skill's approximation of tint, rim and lift. When Apple or Telegram change the material:

1. Read the new kit page through the Figma MCP ([figma-workflow.md](figma-workflow.md)): the material's
   frost, tint, highlight, shadow and where it is used.
2. Record the values in `design-sources.json` → `web_materials`, with the date and the source.
3. Change the `--tma-glass-*` tokens and the level overrides in `tma.css`. Change no component.
   `tests/test_mini_apps_materials.py` fails until the CSS and the data agree.
4. Look at the gallery in the stand in this matrix: light, dark, custom theme, reduced transparency,
   increased contrast, Android `LOW`. Text must pass contrast on the busiest photo.
5. Write the change in `CHANGELOG.md` and the date in [design-sources.md](design-sources.md).

The same procedure covers any new material: a new shadow model, a new corner style, a new elevation scale.
Each is a token family with data, a test and a matrix check.

## 3. Trend radar

The decision for each trend, for Mini Apps inside Telegram **[Heuristic]**. Status:
- **adopt** means use it now;
- **adapt** means take the idea in the Telegram-native form described;
- **avoid** means do not use it, for the reason given.

| Trend | Decision | For Mini Apps |
|---|---|---|
| Liquid Glass and translucent chrome (Apple, 2025 onwards) | adapt | on floating controls only, as a token material (§2); Telegram draws the rest |
| Material 3 Expressive: springier motion, bolder shape contrast, emphasized type (Google, 2025) | adapt | on Android, at most one emphasized moment per screen (a success, a hero figure). Controls keep the kit's shapes, because Telegram's Android chrome is not stock Material. Reduced motion turns it off |
| Bento grids of equal tiles as a page | avoid | a page of tiles hides the task. Quick actions (2-4 equal tiles, [components.md](components.md)) and product tiles are the grids that stay |
| Huge display type, editorial layouts | avoid in task screens | one figure per screen in the type scale; editorial only inside the one moment (a promo, an article) |
| Mesh and aurora gradients, glowing blobs, 3D orbs | avoid | anti-slop §2-4: a tonal gradient of one hue on one moment at most |
| Neumorphism, claymorphism | avoid | low contrast, no theme roles, fights Telegram's flat chrome |
| Dark mode first | adopt through the theme | the user's Telegram scheme decides. Never force dark, never ship only one |
| Dynamic colour (Material You, wallpaper tints) | adopt through the theme | `themeParams` is the user's personal palette already. Brand on one moment only |
| Micro-interactions and haptics | adopt with rules | one per moment, after the visible change ([haptics-and-device.md](haptics-and-device.md)) |
| Skeletons, optimistic UI | adopt with rules | skeletons for first loads, optimistic only for reversible actions ([forms-and-data.md](forms-and-data.md) §5) |
| AI surfaces: chat, streaming answers, generated UI | adapt | stream text with a visible stop and retry, say what the model did, no sparkles or "magic" ([../dynamic-feedback-and-streaming.md](../dynamic-feedback-and-streaming.md) for the bot side) |
| Animated stickers and custom emoji as illustration | adapt | Telegram-native and loved, but one per screen as the moment; never as icons (anti-slop §3, MA13) |
| Foldables and large phones | adopt | widths 320 to 669 (iPhone Duo inner, native-anatomy §1), container queries for components (§4) |
| Super-app patterns: mini-programs inside mini-programs, mega home screens | avoid | one bot, one job; deep links (`startapp`) between apps instead of nesting |
| Variable and custom fonts | avoid in UI | the system font loads instantly and matches Telegram (MA16). A brand face only inside the one moment |
| Spatial, 3D and parallax depth | avoid | motion sickness, battery. Depth from the material (§2), and the tilt card only as an opt-in moment with reduced motion (haptics-and-device §2) |

New trends get a row when someone asks for them. Decide with §0, write the reason, and add a lint rule if
the "avoid" is detectable in code.

## 4. Web platform features inside Telegram's WebViews

Use new CSS and DOM features as **progressive enhancement**: the app is complete without them, and
`@supports` or feature detection turns them on. "First version" below is a guide for planning. Confirm it
on MDN's compatibility data or caniuse before relying on it **[Check]**, and check the oldest iOS and Android
WebView your users have. Log `navigator.userAgent` on the server to know them.

| Feature | Use in a Mini App | First versions (Safari / Chromium) | Without it |
|---|---|---|---|
| `color-mix()`, `light-dark()` | adopt: the kit derives every tint from theme roles | 16.2 / 111; 17.5 / 123 | the kit's fallback colours |
| `:has()` | adopt sparingly (the kit uses it for tab-bar spacing) | 15.4 / 105 | a class set from JS |
| Container queries | adopt: components that sit at 320 to 669 px | 16 / 105 | the narrow layout |
| `<dialog>`, Popover API | adopt for sheets and menus: top layer, focus, Escape | 15.4; 17 / 114 | the kit's sheet with `inert` |
| `@starting-style`, `transition-behavior: allow-discrete` | adapt: sheet and toast entrances without JS | 17.5 / 117 | they appear without animation |
| View Transitions (same document) | adapt: push and pop between screens, a shared image from list to detail | 18 / 111 | the kit's CSS push animation |
| Scroll-driven animations (`animation-timeline: scroll()`) | adapt for one moment: a large title that collapses, the scroll edge | 26 / 115 **[Check]** | static |
| Anchor positioning | avoid until your oldest clients have it | 26 / 125 **[Check]** | the kit's menus |
| `text-wrap: balance` / `pretty` | adopt on titles and short paragraphs | 17.5 / 114; 26 / 117 **[Check]** | normal wrapping |
| `content-visibility: auto` | adopt on long lists and feeds | 18 / 85 | normal rendering |
| `field-sizing: content`, `interpolate-size` | adapt: growing text areas, animating to `auto` | Chromium first **[Check]** | fixed rows, no animation |
| Wide gamut colours (`display-p3`) | avoid outside the one moment | 10 / 111 | `themeParams` are sRGB hex anyway |

Rules **[Heuristic]**:

- **Respect user settings first.** Reduced motion turns off view transitions and scroll-driven effects.
  Reduced transparency turns off glass.
- **One new feature per moment.** A screen that combines view transitions, scroll-driven titles and
  starting-style toasts is a demo, not an app.
- **The kit adopts a feature once, behind a class or token, with a test.** Apps use the kit class instead of
  writing the feature again.

## 5. When a platform ships something new

A procedure for the next WWDC (June), Google I/O (May), Telegram release or Bot API update:

1. **Read the primary source:**
   - Apple: the HIG "What's new" and "Materials" pages and the new iOS kit in Figma;
   - Google: Material Design's release notes;
   - Telegram: the Bot API changelog and the Mini Apps page (`py -3 scripts/webapp_lookup.py` after the
     catalog refresh), and Telegram's blog for client redesigns.
2. **Classify each change** by the layer it touches (§1):
   - Telegram's chrome: nothing to build; check the app still looks like a neighbour;
   - the WebView engine: new features for §4;
   - design language: materials, shapes, motion, which belong in tokens (§2.3).
3. **Decide with §0** and write the row in §3 or §4, with the date and the reason.
4. **Change tokens and data first, components last.** Update `design-sources.json` with the date, the tokens
   in `tma.css`, and the tests that pin them.
5. **Check the matrix** in the stand: platforms, themes, widths and the accessibility settings. Report what
   was not checked on a device.
6. **Do not pre-empt.** Betas change before release. Keep beta findings in notes, and ship tokens after the
   release version is out.

## 6. Digging deeper

- **Apple:**
  - HIG Materials, Color, and "Adopting Liquid Glass";
  - the iOS kit in Figma ([figma-workflow.md](figma-workflow.md));
  - WebKit's blog: each Safari release lists new CSS features, and the Safari version is the iOS
    WKWebView's.
- **Google:**
  - Material Design 3, including "Expressive", for motion and shape tokens;
  - Chrome Platform Status and Chrome release notes for the Android System WebView.
- **Web:**
  - web.dev "Baseline" (a feature is safe when it is in all major engines);
  - MDN browser compatibility data;
  - caniuse.
- **Telegram:**
  - the Mini Apps page;
  - the Bot API changes page;
  - Telegram's blog for client redesigns;
  - the Telegram Mini Apps UI Kit in Figma.
- **Clean-interface practice:** the unslop catalogue (Damir Sokolovsky, CC BY 4.0) and impeccable's craft floor
  and polish pass (Apache 2.0), already adapted in [anti-slop.md](anti-slop.md). Read the originals when a
  tell is missing there, then add it there with the Telegram-specific decision.

## 7. Checklist

- [ ] Every "modern" request checked against §0; the decision written in §3 or §4.
- [ ] Glass only on floating controls, at the right level; text on it passes contrast on the busiest content.
- [ ] Glass values changed only through the `--tma-glass-*` tokens and `web_materials`, with the test green.
- [ ] Reduced transparency, increased contrast, Android `LOW`, no `backdrop-filter`: solid surfaces.
- [ ] New CSS features behind `@supports` or feature detection, the app complete without them, versions confirmed.
- [ ] Reduced motion turns off view transitions, scroll-driven effects and expressive motion.
- [ ] One new effect per moment; nothing that makes the app look foreign to Telegram's chrome.
