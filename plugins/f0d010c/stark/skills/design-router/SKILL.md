---
name: design-router
description: 'Use when the user asks to build, design, mock up, scaffold, audit, or improve any interface, flow, screen, page, component, app, UX, onboarding, checkout, dashboard workflow, or product flow and the target platform or flow is ambiguous. Routes to ux-design, web, Windows, Apple, Android, cross-platform, or design-token skills. SKIP when the request explicitly names one platform and no UX flow work is implied.'
---

# design-router — platform dispatch

This skill is the entry point when a UI/UX request is ambiguous. Goal: pick the right UX and platform skill, do not over-eagerly route to web.

## Step 0 - Decide whether UX comes first

Route to `ux-design` before platform visuals when the request includes:

- "UX", "user journey", "flow", "wireframe", "information architecture", "IA", "usability"
- onboarding, signup, checkout, paywall, forms, settings, permissions, dashboard workflow, admin workflow
- CRM, admin panel, internal tool, SaaS dashboard, marketplace, editor/canvas tool, setup wizard, command palette, data table
- empty/loading/error states, long-running task progress, retry/resume, bulk actions, saved filters, audit trails
- making an app easier to use, less confusing, better for daily use, or better for conversion/retention

If the request is both UX and platform-specific, read `ux-design` first, then the matching platform skill.

## Step 1 — Read the request for platform signals

Scan for explicit signals (in priority order):

| Signal in request | Route to |
|---|---|
| "onboarding", "checkout", "signup", "form flow", "empty state", "loading state", "error state", "admin workflow", "CRM", "internal tool", "SaaS dashboard", "user journey" | `ux-design` first, then platform skill |
| "translate this UI", "translate this screen", "translate this design", "port this UI", "convert this screen", "from iOS to Windows", "from Apple to Android" | `cross-platform-design` first, then the target platform skill |
| "design tokens", "export tokens", "DTCG", "token JSON", "ColorScheme", "Typography tokens", "Tailwind tokens", "SwiftUI tokens", "Compose tokens" | `design-tokens` |
| `.tsx` `.jsx` `.html` `.svelte` `.vue`, "Tailwind", "Next.js", "Astro", "shadcn", "landing page", "marketing site", "dashboard in React" | `web-design` |
| `.xaml` `.cs` (with `WinUI`/`UWP`/`WPF`), "Windows app", "Fluent", "Mica", "WinUI", "Win11", "Microsoft Store app", "PowerToys-style" | `windows-design` |
| `.swift` `.swiftui`, "SwiftUI", "iOS app", "iPadOS", "macOS", "Liquid Glass", "HIG", "SF Symbols", "App Store", "Tahoe" | `apple-design` |
| `.kt` `.kts`, "Compose", "Jetpack Compose", "Material 3", "Material You", "Pixel app", "Android app" | `android-design` |
| "Tauri", "Electron", "Flutter", "React Native", "Expo", "Compose Multiplatform", "CMP", "Uno Platform", "Avalonia", "MAUI" | `cross-platform-design` |

## Step 2 — When signals are absent

Ask one question, no more:

> "Which platform is this for? **(1) Web** - React/Tailwind/Astro **(2) Windows** - WinUI 3 / WPF **(3) iOS / macOS** - SwiftUI **(4) Android** - Jetpack Compose **(5) Cross-platform** - Tauri 2, Compose Multiplatform, React Native, Flutter. If this is mainly UX, describe the user flow and I'll start there."

Do not assume web. Web defaults are how the official `frontend-design` skill produces native-looking-wrong code.

## Step 3 — Multi-target requests

If the user wants the same product on multiple platforms (e.g. "iOS + Android + web"):
1. Ask which platform is **canonical** (where the design originates). Usually iOS or web.
2. Build the canonical version first.
3. Then translate per-platform via `cross-platform-design` or successive single-platform skills, **respecting each idiom**, not pixel-cloning.

Same product ≠ same UI. A Settings screen on iOS uses grouped Form, on Android uses LargeTopAppBar + LazyColumn, on Windows uses NavigationView + SettingsCard. Translate idiom, not pixels.

## Step 4 — Hand off

Once routed, the UX or platform SKILL.md takes over. State what you picked and why in one sentence, then proceed.

If UX ran first, carry its `UX decision brief` into the platform skill and preserve the job, state coverage, action hierarchy, and recovery path.

For any build/redesign request, also carry a `UI decision brief` from `../../references/ui-patterns/ui-decision-brief.md` into the platform skill. This keeps visual hierarchy, density, component grammar, and motion budget explicit.

## Anti-patterns this skill exists to prevent

- Generating React/Tailwind when user wants a Windows app
- Pasting Inter on iOS where SF Pro belongs
- Reaching for Tauri/Electron when the user said "Windows app" (those are web-in-window — use WinUI 3 unless web stack is mandated)
- Defaulting to Material Design on Apple platforms
- Making a beautiful screen while ignoring empty/error/loading states and repeated-use flow

When uncertain, ask. One clarifying question is cheaper than 800 lines of wrong-platform code.
