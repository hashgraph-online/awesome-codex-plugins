---
name: cross-platform-design
description: Use when the user wants one codebase across web, iOS, Android, Windows, and Mac, asks for the same app on all platforms, or names Compose Multiplatform, Tauri 2, React Native, Flutter, .NET MAUI, Avalonia, or Uno Platform. Builds cross-platform UI by translating each surface into the host platform's native idiom rather than pixel-cloning. SKIP when only one platform is targeted.
---

# cross-platform-design — translate idiom, not pixels

Goal: ship one codebase that respects each platform's HIG/Material/Fluent — not a Flutter app that looks like Flutter on every OS.

## Step 0 — Preserve UX and UI decisions

If Stark produced a UX decision brief or UI decision brief, keep both as the source of truth. Translate them per platform instead of pixel-cloning.

Read:

- `../../references/ui-patterns/surface-taxonomy.md`
- `../../references/ui-patterns/ui-decision-brief.md`
- `../../references/ui-patterns/visual-hierarchy.md`
- `../../references/ui-patterns/motion-budget.md`

The shared product should preserve job, state coverage, action hierarchy, and visual hierarchy. Navigation, controls, typography, icons, and motion must become platform-specific.

## Step 1 — Pick the right framework for the design intent

| User priority | Recommended stack |
|---|---|
| Native feel + Kotlin codebase + iOS support | **Compose Multiplatform 1.8+** (iOS stable since May 2025) |
| Tiny binary, web team, desktop-first | **Tauri 2** (Rust + native webviews; ~3MB) |
| Native Android views + iOS, large ecosystem | **React Native** (New Arch + Fabric + Hermes) |
| Single Skia raster across platforms (custom design system) | **Flutter** — only if pixel control matters more than native feel |
| .NET shop, XAML cross-platform | **Uno Platform 5+** (reuses WinUI XAML) |
| .NET shop, mobile-first | **.NET MAUI** (warn: weaker desktop, weaker iOS feel) |
| Cross-platform desktop + custom theming | **Avalonia 11** with Fluent/Mac themes |

## Step 2 — Native-feel ranking by platform

When the user picks a stack, **state the fidelity tradeoff per platform** in one line each.

### Compose Multiplatform 1.8+
- Android: native (excellent)
- iOS: stable but Material widgets won't feel HIG — you must implement Cupertino-styled Compose components, or accept a Material aesthetic on iOS
- Desktop: good for Compose-driven design, not native Fluent
- Web (Wasm): experimental

### Tauri 2
- Windows: WebView2 chrome — Mica works via window-backdrop API but font rendering and focus rings will look subtly off vs WinUI 3
- macOS: WKWebView — looks like a web app, not an AppKit/SwiftUI app
- Linux: WebKitGTK
- Mobile (iOS/Android): preview, not production-ready

### React Native (New Architecture)
- iOS: real UIKit views, decent. Liquid Glass requires `expo-glass-effect` or native modules; partial adoption.
- Android: real Android views, M3 themable but won't get spring physics or shape morphing without manual work.
- Desktop: react-native-windows / react-native-macos exist, fidelity weaker

### Flutter
- All platforms: Skia custom-painted. Never feels native to anyone.
- Material 3 widgets exist but lag platform updates (no spring physics parity, no shape morphing primitives, no real dynamic color).
- **Avoid** for any project where "native feel" is a stated requirement.

### Uno Platform
- Windows: native WinUI (excellent)
- iOS / Android / Mac / Web: reuses XAML rendering — distinctive fidelity but not 1:1 with each platform's idiom
- Best XAML cross-platform path

### .NET MAUI
- Windows: weak WinUI integration
- macOS: Catalyst (deprecated direction)
- iOS: looks like Android in costume
- **Generally avoid for design-first work**

## Step 3 — Translation rules: same product, different idiom

**Settings screen example:**
- iOS → grouped `Form` with `Section { ... }` headers, Liquid Glass toolbar, switch toggles
- Android → `LargeTopAppBar` + `LazyColumn` with `ListItem` rows, switches with M3 thumbs
- Windows → `NavigationView` + scrollable `SettingsCard` stack with Mica backdrop
- Web → asymmetric grid with sidebar nav and editorial section headers

**Tab bar example:**
- iOS → bottom `TabView` (5 tabs max, Liquid Glass)
- Android → `NavigationBar` (3–5) or `NavigationRail` adaptive
- Windows → `NavigationView` Top or Left
- Web → top nav with motion-reveal

**List detail example:**
- iOS → `NavigationSplitView` on iPad/Mac, push-pop on iPhone
- Android → `ListDetailPaneScaffold` (adaptive)
- Windows → Master-detail with Mica
- Web → URL-driven two-pane with View Transitions

Never copy the iOS tab bar onto Windows. Never copy the Android FAB onto iOS. Idiom > pixel.

## Step 4 — When to route to a single-platform skill

If the user is shipping to one canonical platform first (almost always the case), route to that platform's skill (`apple-design`, `android-design`, `windows-design`, `web-design`) and translate later. Don't start in cross-platform mode unless they explicitly say "build cross-platform from day one."

## Step 5 — Anti-slop ban list (cross-platform-specific)

- Same UI pixel-for-pixel on every platform
- Defaulting to Flutter without warning about non-native feel
- Defaulting to Electron (use Tauri 2 if web stack is mandated)
- Material widgets unmodified on iOS — must Cupertino-skin or accept "Material on iOS" warning
- Cupertino widgets unmodified on Android — same in reverse
- Ignoring per-platform navigation idioms (always-bottom-tabs, always-hamburger)
- One typeface across all platforms — each OS has a system face
- One motion language across all platforms when native motion differs
- One density level across mobile, tablet, desktop, and web

## Step 6 — Reference cross-platform apps that translate well

- **Notion** — web-first but adapts respectably to each native platform
- **Telegram** — fully native on each platform; same product, different code per OS
- **Spotify** — same brand, idiomatic per platform
- **Linear** — desktop via Electron but obsessively polished; web is canonical

## Step 7 — Tokens & assets

When generating cross-platform output, ship tokens once and translate:
- Use the **DTCG W3C token format** as the source of truth
- See `../../scripts/token_export.py` to translate one token JSON into Tailwind theme + Compose Material3 ColorScheme + SwiftUI Color extension + Fluent ResourceDictionary
- See `../../assets/tokens/` for per-platform reference token bundles
