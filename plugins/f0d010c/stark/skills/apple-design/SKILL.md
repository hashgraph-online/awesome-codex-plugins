---
name: apple-design
description: Build apps for iOS 26 / iPadOS 26 / macOS 26 (Tahoe) / watchOS 26 / visionOS 26 across all common stacks — system-like SwiftUI, branded SwiftUI (HIG + custom identity), React Native, Flutter Cupertino, and Electron/Tauri 2 for macOS. Use when the user asks for SwiftUI, an iOS app, iPad app, Mac app, Apple Watch app, visionOS app, an App Store deliverable, or anything Apple-platform deliverable. ALWAYS ask the user which track first — do not default to SwiftUI. SKIP when the target is only Android, Windows, or web-in-browser.
---

# apple-design — pick the track first

Apple platforms have multiple stacks with different visual ceilings and cost. **Ask the user which one before any code.**

## Step 0 (MANDATORY) — Ask the user which track

> Which track for this app?
>
> **1. System-like native (SwiftUI strict + Liquid Glass + HIG)** — feels like Settings, Notes, Reminders, Mail. Best for: utilities, productivity. Visual ceiling: medium. Stays App Store-friendly. Examples: Things 3, NetNewsWire, Soulver.
>
> **2. Branded native (SwiftUI + HIG + custom identity)** — native chrome (Liquid Glass, SF Symbols, Dynamic Type) but bespoke content surface (custom typography, hero atmospheres, magazine layouts). Best for: consumer/media/creative apps that want fit-in *and* identity. Visual ceiling: high. Examples: Ivory, Reeder, Mela, Craft, CARROT Weather.
>
> **3. React Native (New Architecture + Fabric + Hermes)** — real UIKit views, decent native feel, JavaScript codebase, cross-platform with Android. Liquid Glass partial via `expo-glass-effect`. Best for: cross-platform apps with web-team velocity. Examples: Discord mobile, Coinbase, Microsoft Office mobile.
>
> **4. Flutter Cupertino** — Skia-painted UIKit-look. Always one OS behind, no Liquid Glass. Cross-platform. Best for: utility apps where pixel control beats native feel. Visual ceiling: high if you bring your own design language; low if you try to mimic iOS.
>
> **5. Electron / Tauri 2 (macOS only — no iOS)** — web stack desktop apps. Tauri 2 (~5MB, WKWebView) or Electron (~150MB, bundled Chromium). Same React/Tailwind/Motion code as web. Best for: cross-platform desktop with brand-first identity. Examples: Spotify, Discord, VSCode, Slack, Figma desktop, Linear.
>
> Which? Or describe priorities (App Store, brand vs HIG fit, cross-platform reach) and I'll pick.

If brief gives a strong signal (e.g. "iOS App Store launch" → 1 or 2; "cross-platform with our existing React team" → 3 or 5; "web team building desktop-only" → 5), state your pick + reasoning in one sentence. If ambiguous, ask.

## Step 0b — Once picked, route

| Track | Reference docs | Default stack |
|---|---|---|
| 1. System-like SwiftUI | `../../references/apple-hig.md` + `../../references/liquid-glass.md` | SwiftUI 7 + Xcode 26 + iOS 26 SDK strict |
| 2. Branded SwiftUI | Same as 1 | Same as 1 + custom display font + hero atmospheres + bespoke surfaces |
| 3. React Native | `../../references/web-fonts.md` + cross-platform docs | RN 0.78+ New Arch + Expo Router + react-native-screens |
| 4. Flutter Cupertino | None for native fidelity (will feel imported) | Flutter 3+ stable |
| 5. Tauri 2 / Electron (macOS) | `../../references/web-fonts.md` + `../../references/web-motion.md` + `../../references/web-bans.md` + `../../references/awwwards-ceiling.md` | React 19 + Tailwind v4 + Motion |

For tracks 3, 4, 5: web/cross-platform anti-slop rules apply. Read the web design references.

State the chosen aesthetic direction and track in one sentence at top of response, then proceed.

## Step 0c — UI decision brief

Before code, read:

- `../../references/ui-patterns/surface-taxonomy.md`
- `../../references/ui-patterns/ui-decision-brief.md`
- `../../references/ui-patterns/visual-hierarchy.md`
- `../../references/ui-patterns/motion-budget.md`

Write the UI decision brief and adapt it to the chosen Apple platform. iPhone task flows need thumb reach and progressive disclosure; iPad/Mac productivity surfaces need NavigationSplitView, inspector, keyboard flow, and stable density; media/consumer apps may use branded surfaces while preserving HIG controls, SF typography, SF Symbols, Dynamic Type, and safe areas.

## Step 1 — Liquid Glass first (only if track 1 or 2)

Apple's unified design language across iOS 26, iPadOS 26, macOS 26 Tahoe, watchOS 26, tvOS 26, visionOS 26. Treat as default.

Apply via:
- `.glassEffect()` modifier on surfaces that should refract underlying content
- `GlassEffectContainer { ... }` to coordinate multiple glass surfaces (avoids overlapping refraction artifacts)
- `.buttonStyle(.glass)` for buttons that should adopt Liquid Glass
- `.toolbar { ... }` automatically lifts to glass on iOS 26+
- `.scrollEdgeEffectStyle(.soft)` — replaces hard chrome edges with material lensing

Lineage to remember: Aqua → iOS 7 blur → Dynamic Island → visionOS → Liquid Glass. The aesthetic is "digital meta-material" — light bends through it.

Read `../../references/liquid-glass.md` for full Liquid Glass adoption checklist.

## Step 2 — SwiftUI 7 modern APIs (Swift 6.2 / Xcode 26)

Always prefer:
- `@Observable` macro on view models — never `ObservableObject` + `@Published`
- `@Entry` for one-line `EnvironmentValues` / `FocusedValues` / `Transaction` keys
- `Group(subviews:)` and `ForEach(subviewsOf:)` for custom containers
- `MeshGradient(width:height:points:colors:)` for distinctive backgrounds — replaces flat gradients
- `NavigationSplitView` with `.inspector { ... }` for iPad/Mac three-pane
- `TabView` with sidebar-adaptable `.role`
- `.searchable` (morphs into a glass pill on iOS 26)
- `.symbolEffect(.bounce)` / `.pulse` / `.variableColor` / `.replace.byLayer` on SF Symbols
- `MotionScheme` and spring physics — `.spring(response:dampingFraction:)`, never linear/easeIn/easeOut on UI motion

## Step 3 — HIG compliance

- **Layout grid**: 8pt base, 4pt half-step. Never 10/15/20. Use `.padding()` defaults — they encode the system's grid.
- **Safe areas**: every screen wraps in safe area handling. `.safeAreaInset(edge:)` for content bars.
- **Dynamic Type**: support xSmall → AX5. Use `Font.TextStyle` (`.largeTitle`, `.title`, `.headline`, `.body`, `.caption`). Never hard-coded points.
- **SF Symbols 7** is the only icon system. ~6,900 glyphs, 9 weights × 3 scales. Use `Image(systemName:)`.
- **Accessibility**: `.accessibilityLabel/Hint/Value`, `.accessibilityElement(children:.combine)`, traits like `.isButton`, `.isHeader`. Mandatory.

Read `../../references/apple-hig.md` for HIG section deep-dive.

## Step 4 — macOS specifics (macOS 26 Tahoe)

- SwiftUI is now first-class for new Mac apps. Drop into AppKit only for: complex `NSTextView` + custom rich text, Quick Look extensions, custom `NSToolbar` items, `NSOpenPanel` extensions.
- Catalyst is deprecated in spirit. Prefer SwiftUI multiplatform target.
- Patterns:
  - `NavigationSplitView { sidebar } content: { ... } detail: { ... }`
  - `.inspector { ... }` for trailing pane (Craft, Notes pattern)
  - `MenuBarExtra("Name", systemImage: ...) { ... }` for menu-bar apps
  - `Settings { TabView { ... } }` scene for prefs window
- Vibrancy materials: `.background(.regularMaterial)`, `.ultraThin/Thin/Regular/Thick/UltraThick`
- For sidebar background: `.background(NSVisualEffectView { $0.material = .sidebar })` via `NSViewRepresentable` if needed

## Step 5 — Cross-platform fidelity warnings

State the tradeoff if the user asks for non-Swift on Apple:

| Stack | Liquid Glass adoption | Verdict |
|---|---|---|
| SwiftUI / UIKit native | Full automatic | **Use this** |
| React Native (New Arch + Fabric + Hermes) | Partial via expo-glass-effect / native modules | Decent for utility apps, off in nav transitions/haptics |
| Flutter Cupertino | Pixel-recreates iOS but always one OS behind, no Liquid Glass | Will feel wrong on iOS 26+ |
| .NET MAUI | Looks like Android in costume | Never use on Apple |

If user insists on cross-platform, route to `cross-platform-design` and warn that any non-SwiftUI path will fail Liquid Glass adoption.

## Step 6 — Anti-slop ban list (Apple-specific)

- Inter / Roboto / SF Pro replaced by web fonts — only **SF Pro / SF Pro Rounded / SF Mono / New York**
- Material Design elevation shadows — use materials (`.regularMaterial`) and Liquid Glass instead
- Hamburger drawer navigation — use `TabView` (iOS), `NavigationSplitView` (iPad/Mac)
- FontAwesome / Material Symbols / Lucide icons — only SF Symbols 7
- Linear/easeIn/easeOut animation curves — only spring physics
- `.padding(20)` magic numbers — use system spacing or 8/16/24 grid
- Bottom sheets without `.presentationDetents([.medium, .large])`
- Custom switch / checkbox UI replacing `Toggle`
- Full-bleed content under nav without `.scrollEdgeEffectStyle(.soft)`
- Ignoring `.safeAreaInset` — content collides with home indicator
- Hard-coded points instead of `Font.TextStyle` (breaks Dynamic Type)
- Custom scroll indicators — use `ScrollIndicators(.hidden)` only when justified
- Web-style dashboards squeezed into iPhone screens
- Decorative cards where grouped Form, List, inspector, or split view is the platform idiom

## Step 7 — Reference apps that nail HIG

- **Things 3** — typographic restraint, magic-plus, perfect Dynamic Type
- **Reeder Classic** / **Reeder 5** — `NavigationSplitView` exemplar on iPad/Mac
- **Ivory (Tapbots)** — bespoke yet HIG-correct; haptic + `.symbolEffect` choreography
- **Mela** — text-first, native share sheets, no chrome
- **Craft** — multi-pane Mac, inspector pattern, vibrancy
- **NetNewsWire** — open-source HIG textbook
- **Soulver 3** — Mac-native typography + sidebar
- **CARROT Weather** — system materials + variable color symbols
- **Overcast** — type hierarchy, Dynamic Type, accessibility
- **Fantastical** — sidebar + inspector + menu-bar mode

## Step 8 — Tokens & assets

- Apple Design Resources Figma kits (iOS 26, macOS 26): https://developer.apple.com/design/resources
- SF Symbols 7 app: https://developer.apple.com/sf-symbols
- HIG: https://developer.apple.com/design/human-interface-guidelines
- Icon Composer (WWDC25 session 361) for Liquid Glass app icons
- System color spec: https://developer.apple.com/design/human-interface-guidelines/color (use `.primary`, `.secondary`, `.tint`, `Color(.systemBackground)` — never raw hex)

Token JSON: see `../../assets/tokens/apple-system.json`
