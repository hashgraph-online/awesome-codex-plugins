---
name: windows-design
description: Use when the user asks for a Windows app, Win11 UI, XAML, Fluent design, WinUI, WPF, PowerToys-style tool, Microsoft Store app, music/photo/creative app, Tauri desktop, Electron desktop, or any Windows desktop deliverable. Builds Windows 11/12 apps across system-like WinUI 3, branded WinUI 3, Tauri 2, and Electron. ALWAYS ask which track first. SKIP when the user explicitly wants only Apple, Android, or web-in-browser.
---

# windows-design — pick the track first

Windows desktop has four distinct tracks. Each has different visual ceilings, different cost. **Ask the user which one before any code.** Do not default.

## Step 1 (MANDATORY) — Ask the user which track

Present these four options verbatim. Do not pick for them.

> Which track do you want for this app?
>
> **1. System-like native (WinUI 3 strict)** — feels like Settings/Calculator/Notepad. Best for: productivity utilities, internal tools, system panels. Visual ceiling: medium. Binary ~30MB. Users who care: Windows power users, IT admins. Examples: PowerToys, Snipping Tool, Sound Recorder.
>
> **2. Branded native (WinUI 3 + branded Fluent)** — native chrome (Mica, Snap Layouts, ThemeResource auto dark/light/HC) but bespoke content surface (custom accent, custom display font, hero atmospheres, magazine layouts). Best for: consumer apps that want fit-in *and* identity. Visual ceiling: high but XAML-bound. Binary ~30MB. Examples: Apple Music for Windows, Files (community), Microsoft Photos rewrite, DevHome.
>
> **3. Tauri 2 + React/Tailwind/Motion** — same React code as Electron but uses Windows' built-in WebView2 instead of bundled Chromium. Full visual freedom (mesh gradients, custom motion, real imagery, anything CSS can do). Binary ~5–10MB. RAM ~30–80MB. Mica still available via Tauri API. Examples: Cap, Spacedrive, ClashVerge, Pot.
>
> **4. Electron + React/Tailwind/Motion** — bundles full Chromium. Same dev experience as Tauri but heavier. Binary ~150–250MB. RAM ~300–500MB. Largest ecosystem, every dev knows it. Examples: Spotify, Discord, VSCode, Slack, Notion, Figma desktop, Claude desktop, ChatGPT desktop.
>
> Which? Or describe priorities (binary size, visual ambition, brand vs fit-in) and I'll pick.

If the user has already given enough signal in the brief (e.g. "I want a system tray utility" → 1; "I want it to look like Awwwards site" → 3; "Spotify-style" → 3 or 4), state your pick + reasoning in one sentence and proceed. But if ambiguous, ask.

## Step 1b — Once picked, route

| Track | Reference docs | Default stack |
|---|---|---|
| 1. System-like WinUI 3 | `../../references/fluent-design.md` | WinUI 3 + WinAppSDK 1.8 + CommunityToolkit.Mvvm + SettingsControls |
| 2. Branded WinUI 3 | `../../references/fluent-design.md` + `../../references/branded-fluent.md` | Same as 1 + custom accent override + embedded display font + bespoke surfaces |
| 3. Tauri 2 + Web | `../../references/web-fonts.md` + `../../references/web-motion.md` + `../../references/web-bans.md` + `../../references/awwwards-ceiling.md` | React 19 + Tailwind v4 + Motion (motion.dev) + Tauri 2 shell |
| 4. Electron + Web | Same as 3 | React 19 + Tailwind v4 + Motion + Electron shell + electron-builder |

For tracks 3 and 4, the web design rules from `web-design` SKILL apply — same anti-slop ban list, same typography curation, same aesthetic direction discipline.

## Step 1c — UI decision brief

Before code, read:

- `../../references/ui-patterns/surface-taxonomy.md`
- `../../references/ui-patterns/ui-decision-brief.md`
- `../../references/ui-patterns/visual-hierarchy.md`
- `../../references/ui-patterns/motion-budget.md`

Write the UI decision brief and adapt it to the selected Windows track. Windows utilities and admin tools should favor operational density, stable navigation, SettingsCard/NavigationView idioms, and low motion. Branded consumer apps may use richer content surfaces, but native chrome, Mica/Acrylic rules, Segoe UI Variable, and Fluent icons still apply.

## Step 2a — Branded vs system-like (only if track 1 or 2 picked)

Track 1 = system-like. Track 2 = branded. The user already picked. Skip to step 2.

For reference: branded means native chrome + bespoke content surface. Read `../../references/branded-fluent.md`.

## Step 2 — WinUI 3 idioms

Every Win11 app must:
- Extend the title bar into the client area via `AppWindow.TitleBar` API (preserve Snap Layouts hover)
- Apply **Mica** as the top-level window backdrop (`SystemBackdrop="Mica"`) — opaque, desktop-tinted
- Apply **Acrylic** only to transient surfaces: flyouts, command bars, menus
- Use **Mica Alt** for tabbed apps (Terminal, Edge, Files)
- Use 8px corner radius on windows, 4px on controls, 0px in dense grids
- Use **tonal elevation** (background brush shifts) — never CSS-style drop shadows
- Wire light/dark via `ThemeResource` brushes, never hex literals

**Reveal effect** is deprecated in Win11 styling. Do not generate it.

## Step 3 — Typography & icons

- **Segoe UI Variable** is the only correct face. Wire variable axes (wght 100–700, optical size). Never Segoe UI plain.
- **Segoe Fluent Icons** font for iconography. 1 epx monoline. Sizes: 16/20/24/32/40/48/64.
- For body text in productivity: weight 400, size 14, line height 20. For headlines: optical size adjusts automatically — let it.

## Step 4 — Layout components (use these, not custom)

| Need | Use |
|---|---|
| Top-level navigation | `NavigationView` (Left, LeftCompact, Top modes) |
| Settings | `SettingsCard` (CommunityToolkit.WinUI.Controls.SettingsControls) |
| Inline alert | `InfoBar` (Severity: Informational/Success/Warning/Error) |
| Coachmark | `TeachingTip` |
| Disclosure | `Expander` |
| Path / breadcrumb | `BreadcrumbBar` |
| Tabbed segment toggle | `SelectorBar` |

Refer to **WinUI Gallery** (https://github.com/microsoft/WinUI-Gallery) for canonical control usage. When generating, mirror its patterns exactly.

## Step 5 — Architecture

- **CommunityToolkit.Mvvm** (`[ObservableProperty]`, `[RelayCommand]`) — never raw `INotifyPropertyChanged`
- DI via `Microsoft.Extensions.Hosting`
- Settings persistence via `Windows.Storage.ApplicationData.Current.LocalSettings` or `Microsoft.UI.Xaml.Settings`
- Localization via `.resw` resource files (not hardcoded strings)

## Step 6 — Anti-slop ban list (Windows-specific)

Reject all of these:

- Inter / Roboto / system-ui on native chrome — only Segoe UI Variable
- CSS-style `box-shadow` — use tonal elevation brushes (`LayerFillColorDefaultBrush` etc.)
- Custom hamburger menu where `NavigationView` belongs
- Acrylic on long-lived window backgrounds (use Mica)
- Mica on flyouts (use Acrylic)
- Hardcoded hex colors — breaks dark mode + high contrast. ThemeResource only.
- Hand-rolled title bar that breaks Snap Layouts hover
- Square 90° corners
- Material Design ripples
- iOS-style segmented controls with sliding pill (use SelectorBar instead)
- Bottom tab bars (Android idiom)
- Custom scrollbars that override `ScrollViewer` (breaks dynamic thinning)
- FontAwesome / Material Symbols icons (use Segoe Fluent Icons)
- Marketing-page spacing in productivity/admin tools
- Decorative cards replacing SettingsCard, table/list, or master-detail surfaces

## Step 7 — Reference apps to emulate

- **Files** (files.community) — Mica + tabs + dual-pane + command palette
- **PowerToys** (recently redesigned by Niels Laute) — canonical NavigationView + InfoBar settings shell
- **Windows Terminal** — title-bar tab integration, JSON theming
- **Microsoft Photos (2024 rewrite)** — WinUI 3 + AI surfaces
- **Snipping Tool / Clipchamp** — modern command bar + teaching tips
- **DevHome** — dashboard widget pattern
- **Notepad (rewrite)** — minimal Fluent restraint

## Step 8 — Tokens & assets

- Token JSON (DTCG): see `../../assets/tokens/fluent-2.json` shipped with this plugin
- Fluent 2: https://fluent2.microsoft.design
- Win design downloads (Figma + icons + Segoe): https://learn.microsoft.com/windows/apps/design/downloads
- WinUI source: https://github.com/microsoft/microsoft-ui-xaml

Read `../../references/fluent-design.md` for deep token + spacing reference.

## Step 9 — Fidelity tradeoffs to communicate

When the user picks a non-native stack, **state the loss explicitly** in one line:
- Tauri 2: "~3MB binary, but WebView2 chrome — Mica still works via window-backdrop API but font rendering and focus rings will look subtly off vs WinUI 3."
- Avalonia: "Cross-platform but Fluent theme is custom-drawn, not 1:1 with Win11."
- Electron: "Don't. Use Tauri 2 if web stack is mandated."
