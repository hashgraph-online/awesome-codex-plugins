---
name: android-design
description: Use when the user asks for an Android app, Compose UI, Material 3, Material You, Pixel-style app, foldable adaptive layout, React Native Android, Flutter Android, Compose Multiplatform, or any Android deliverable. Builds Android 16+ apps across system-like Compose, branded Compose, React Native, Flutter, and Compose Multiplatform. ALWAYS ask which track first. SKIP when the target is only iOS, Windows, or web-in-browser.
---

# android-design — pick the track first

Android has multiple stacks with different visual ceilings. **Ask the user which one before any code.**

## Step 0 (MANDATORY) — Ask the user which track

> Which track for this app?
>
> **1. System-like native (Jetpack Compose + Material 3 Expressive strict)** — feels like Pixel Launcher, Google Calendar, Settings. Best for: utilities, system tools, productivity. Spring physics, shape morphing, wavy progress, dynamic color (Material You). Examples: Read You, Androidify sample, Files by Google.
>
> **2. Branded native (Compose + custom Material theme)** — native chrome (M3E motion, predictive back, edge-to-edge) but bespoke content surface (custom typography, hero atmospheres, magazine layouts). Visual ceiling: high. Examples: Fitbit redesign, Google Calendar's editorial moments, Niantic apps.
>
> **3. React Native (New Architecture + Fabric + Hermes)** — real Android views, decent native feel, JavaScript codebase, cross-platform with iOS. Material themable but won't get spring physics or shape morphing without manual work. Examples: Discord mobile, Coinbase, Microsoft Office.
>
> **4. Flutter** — Skia-painted custom rendering. Cross-platform single codebase. Lags Material updates (no M3 Expressive parity, no real dynamic color). Visual ceiling: high if you ship your own design language; weak if mimicking Material. Examples: Google Pay, BMW My BMW, Toyota.
>
> **5. Compose Multiplatform (1.8+)** — same Compose code, runs Android + iOS + Desktop + Web (Wasm experimental). Native on Android, Material-look on iOS (you must Cupertino-skin or accept). Best for: Kotlin shop wanting cross-platform from one codebase.
>
> Which? Or describe priorities (Play Store launch, cross-platform reach, brand vs Material fit) and I'll pick.

If brief gives strong signal (e.g. "Pixel-style camera" → 1; "cross-platform with React team" → 3; "Kotlin shop, ship to all platforms" → 5), state your pick + reasoning in one sentence. If ambiguous, ask.

## Step 0b — Once picked, route

| Track | Reference docs | Default stack |
|---|---|---|
| 1. System-like Compose | `../../references/material3-expressive.md` | Compose BOM 2026.04 + Material3 1.4 + adaptive layouts strict |
| 2. Branded Compose | Same as 1 | Same as 1 + custom display font + hero atmospheres + bespoke surfaces |
| 3. React Native | `../../references/web-fonts.md` + cross-platform docs | RN 0.78+ New Arch + Expo Router |
| 4. Flutter | None for native fidelity | Flutter 3+ stable |
| 5. Compose Multiplatform | `../../references/material3-expressive.md` | CMP 1.8 stable + shared Compose |

For tracks 3 and 4: web/cross-platform anti-slop rules apply. Read web references.

State the chosen aesthetic direction and track in one sentence at top of response.

## Step 0c — UI decision brief

Before code, read:

- `../../references/ui-patterns/surface-taxonomy.md`
- `../../references/ui-patterns/ui-decision-brief.md`
- `../../references/ui-patterns/visual-hierarchy.md`
- `../../references/ui-patterns/motion-budget.md`

Write the UI decision brief and adapt it to the chosen Android track. Compact screens need thumb-reachable primary actions, sheets, edge-to-edge, and adaptive navigation; tablets/foldables need list-detail or supporting panes; operational tools should stay dense and scannable while preserving Material 3 Expressive motion, dynamic color, and predictive back.

## Step 1 — Material 3 Expressive default (only if track 1 or 2)

Launched at I/O 2025. Default for Pixel 10 / Android 16 QPR1. Generated UI must adopt:

- **Spring physics on every motion** — `MotionScheme.expressive()`. Never `FastOutSlowIn` on M3E surfaces.
- **Shape morphing** — 35 new shapes (squircle, pill, cookie, clover). Use `MaterialShapes.Cookie4Sided`, `Pill`, etc. Buttons/chips/loaders morph between states.
- **Emphasized typography** — bigger, heavier headlines. Use `MaterialTheme.typography.displayLarge` with intent.
- **New components**:
  - `FloatingToolbar` (pill-shaped, drifts with content)
  - `ButtonGroup` / `SplitButton`
  - `FloatingActionButtonMenu`
  - `ContainedLoadingIndicator` (cycles through M3E shapes)
  - **Wavy progress** — `LinearWavyProgressIndicator`, `CircularWavyProgressIndicator` with variable amplitude
  - Large/Small/XL button sizes
- **Tonal elevation** — surface tone shifts, never `Modifier.shadow()` for elevation
- **Dynamic color (Material You)** — `dynamicColorScheme()` from wallpaper on Android 12+

Read `../../references/material3-expressive.md` for the M3E adoption checklist.

## Step 2 — Compose currency (BOM 2026.04.01)

```kotlin
implementation(platform("androidx.compose:compose-bom:2026.04.01"))
implementation("androidx.compose.material3:material3:1.4.0")
// or for shape-morphing chips:
implementation("androidx.compose.material3:material3:1.5.0-alpha18")
```

Use:
- `currentWindowAdaptiveInfo()` + `NavigationSuiteScaffold` (auto-swaps Bar/Rail/Drawer by WindowSizeClass)
- `ListDetailPaneScaffold`, `SupportingPaneScaffold`, `NavigableListDetailPaneScaffold`
- `SharedTransitionLayout { ... }` for shared element transitions (stable)
- `PredictiveBackHandler` / `BackHandler` — **mandatory** on Android 16, default ON Android 15+
- `LookaheadAnimationVisualDebugging` for inspecting bounds during dev

## Step 3 — Edge-to-edge is mandatory

Android 16 (API 36) deprecated `windowOptOutEdgeToEdgeEnforcement`. Every screen:
- Wraps in `Scaffold` with content padding from insets
- Uses `WindowInsets.systemBars`, `.statusBars`, `.navigationBars`
- Predictive back must be wired
- Status bar color cannot be set opaque — banned on Android 16

## Step 4 — Adaptive layouts

- **Compact** (phone portrait) → `NavigationBar` (3–5 items)
- **Medium** (foldable inner / tablet portrait) → `NavigationRail`
- **Expanded** (tablet landscape / desktop) → `NavigationDrawer` (modal or permanent) + `ListDetailPaneScaffold`
- **Foldables**: handle tabletop / book postures via `WindowInfoTracker`

## Step 5 — Typography & icons

- **Default body**: Roboto Flex (variable). Headlines: per-app brand expression — but stay within M3E weight/size scale.
- **Material Symbols** (variable axes: weight, fill, grade, optical size) — never FontAwesome/Lucide.
- Get Material Symbols from https://fonts.google.com/icons

## Step 6 — Anti-slop ban list (Android-specific)

- iOS-style top nav bars / chevron-back headers
- Hamburger drawer when `NavigationBar` (3–5 items) or `NavigationRail` fits
- Hard `Modifier.shadow(elevation = 8.dp)` — use `tonalElevation` on `Surface` instead
- Custom back stacks ignoring system back / predictive animation
- Opaque colored status bars — banned on Android 16
- Bottom sheets without drag handle / non-draggable
- Static easing curves on M3E surfaces — `MotionScheme.expressive()` only
- SF Symbols / Material Symbols-Outlined-only (use variable axes)
- Inter / SF Pro on Android — Roboto Flex / Google Sans / Material default
- Centered FAB layouts where docked FAB pattern is canonical
- Standard Material 3 baseline 2023 — must be M3 Expressive
- Web-style desktop dashboards squeezed into mobile Compose
- Decorative motion that hides progress, state, or navigation changes

## Step 7 — Reference apps that nail M3 Expressive

- **Pixel Launcher / Android 16 System UI** — shape morph + springs
- **Google Calendar** — floating toolbar + tonal surfaces
- **Fitbit (2025 redesign)** — `ContainedLoadingIndicator` cycling shapes; floating toolbar
- **Pixel Camera 10.1** — wavy progress in capture
- **Google Docs/Sheets/Slides homepages** — M3E typography
- **Chrome (M3E redesign)** — adaptive nav
- **Read You** (community RSS, OSS) — canonical M3 + dynamic color
- **Androidify** sample app — official Compose M3E reference

## Step 8 — Architecture defaults

- **MVVM** with `ViewModel` + `StateFlow` + `collectAsStateWithLifecycle()`
- **Hilt** for DI
- **Navigation Compose 3** with type-safe routes
- **Coil 3** for image loading (replaces Glide for Compose-first apps)
- **Ktor** or **Retrofit + KotlinX Serialization** for networking
- **Room** for local persistence

## Step 9 — Tokens & assets

- M3 token spec: https://m3.material.io/foundations/design-tokens/how-to-use-tokens
- Theme Builder (web): https://m3.material.io/theme-builder
- Theme Builder Figma plugin: https://www.figma.com/community/plugin/1034969338659738588
- M3 Figma kit: https://www.figma.com/community/file/1035203688168086460
- Material Symbols: https://fonts.google.com/icons
- M3E component catalog: https://github.com/meticha/material-3-expressive-catalog

Token JSON: see `../../assets/tokens/material3-expressive.json`
