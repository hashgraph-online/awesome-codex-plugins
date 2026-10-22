# Apple Platforms (SwiftUI, UIKit, AppKit)

Apple's Human Interface Guidelines (HIG) are what Apple users have learned — Jakob's law means departing from them costs learning time. Prefer system components: they bring the expected behaviour, Dynamic Type, accessibility, and future OS design changes for free, on every Apple platform.

Read **Shared** below, then only the sections for the platforms the change targets — from the Xcode target's supported destinations, `platforms:` in `Package.swift`, or `#if os(...)` branches. A multiplatform SwiftUI app reads each section its change affects.

## Shared

- **System components first** — `NavigationStack`/`NavigationSplitView`, `TabView`, toolbars, sheets, menus, `.confirmationDialog`, `.alert`. Each adapts to the platform it runs on; custom replacements must be rebuilt per platform and drift from the OS
- **Liquid Glass** (the OS 26 design across Apple platforms) — system bars, toolbars, tab bars, and sheets adopt it when built with the current SDK; custom-drawn chrome does not, and looks foreign (`rules/jakobs-law.md`). Glass belongs to the navigation layer floating above content, not the scrolling content itself — Apple's WWDC25 design guidance warns glass on the content layer collides with the navigation layer. Check legibility over changing backgrounds and with Reduce Transparency and Increase Contrast on. How glass looks (tint, shape, layering) is visual styling — out of scope here
- **SF Symbols** for icons — users recognise their meaning; pair unfamiliar ones with a label
- **Dynamic Type** — text styles (`.font(.body)`, `.font(.headline)`), not fixed sizes; check the largest accessibility sizes
- **Destructive confirmations** — `.confirmationDialog` with the destructive option in the `.destructive` role, separated from Cancel; `.alert` only for brief, blocking decisions
- **Empty states** — `ContentUnavailableView` with a title, short explanation, and the action that fills the screen
- **Progress** — `ProgressView`: indeterminate under a few seconds, determinate beyond (`rules/system-status.md`)
- **AutoFill** — `.textContentType(.emailAddress)`, `.oneTimeCode`, `.password`, `.newPassword`, `.postalCode` (`rules/defaults.md`)
- **Permissions** — each prompt shows once, with the purpose string (`NS…UsageDescription`) inside the system dialog. Write it as the user's benefit, and prime in your own UI first (`rules/reciprocity.md`)
- **System settings** (notifications, permissions) link to the app's page in Settings rather than being re-implemented

## iPhone

Load `references/mobile.md` alongside this section.

| Need | System pattern |
|---|---|
| Top-level sections (2–5) | `TabView` with a bottom tab bar — more than five overflow into "More", so pick the five that matter |
| Drill-down hierarchy | `NavigationStack` — swipe-from-left-edge back comes free; never disable it |
| Focused sub-task | `.sheet` with `.presentationDetents([.medium, .large])` when the user should keep context underneath |
| Full-screen task with its own flow | `.fullScreenCover`, with an explicit close button |

- Minimum hit target **44×44 pt**; keep small icons' hit area large with `.contentShape(Rectangle())` and padding
- Safe areas — controls clear of the Dynamic Island and home indicator
- Short titles, so the back button (which shows the previous title) stays meaningful; large title on root screens, inline deeper in
- Row actions: `.swipeActions` plus a visible alternative such as `.contextMenu` or an edit mode (`rules/signifiers.md`)
- Haptics: `.sensoryFeedback(.selection | .success | .error, trigger:)` for picker changes and outcomes — not for every tap
- `.keyboardType` and `.submitLabel(.next)` with `@FocusState` to move through forms

## iPad

Load `references/mobile.md` alongside this section. An iPad app is not a stretched iPhone app.

- Top-level navigation: a sidebar with `NavigationSplitView`, or a tab bar that adapts to a sidebar (`.tabViewStyle(.sidebarAdaptable)`)
- Windows can be resized to almost any width — layouts must adapt (compact width falls back to the iPhone layout), never assume full screen
- Pointer and keyboard are common: hover effects on custom controls (`.hoverEffect()`), `.keyboardShortcut` for frequent actions — users discover them by holding ⌘
- Popovers and context menus for secondary actions where an iPhone would use a sheet

## Mac

A desktop app with pointer and keyboard. Do not port iPhone patterns (bottom tab bars, full-screen sheets, swipe-only actions).

- **The menu bar holds every command** (`.commands`), with standard shortcuts — ⌘Z undo, ⌘W close, ⌘, for Settings (`Settings` scene). The menu bar sits at the screen edge, which makes it a near-infinite Fitts target (`rules/fitts-law.md`)
- Sidebar (`NavigationSplitView`) and toolbar for navigation and frequent actions; multiple windows are normal
- Right-click context menus everywhere a user might expect one; hover states on interactive elements
- Pointer precision allows denser layouts and smaller controls than touch, but keep standard control sizes
- Undo for destructive actions is the Mac norm — users expect ⌘Z to work (`rules/error-prevention.md`)

## Apple Vision Pro

People look at a control and pinch to select it — the eyes are the pointer.

- Minimum target **60×60 pt** (HIG) — eye targeting is less precise than touch
- The system highlights what the user is looking at; give custom controls `.hoverEffect()` so they light up too — that highlight is the signifier (`rules/signifiers.md`)
- Keep content within a comfortable field of view; don't make people turn their head for routine actions
- Toolbars and controls in ornaments attached to the window, not floating free
- Respect comfort: no forced motion, sudden immersion, or content that moves with the head

## Apple Watch

Interactions last seconds. One glance, one primary action.

- Show the one thing the user raised their wrist for; everything else a scroll away
- Digital Crown for scrolling and adjusting values; large, full-width buttons
- Glanceable information belongs in widgets and complications, not behind app launches
- Haptics are a primary feedback channel here — use them for outcomes and alerts, sparingly

## Apple TV

Navigation is by focus, with a remote, from across the room.

- Every interactive element must be reachable by focus, and the focused element unmistakable — system components handle both
- Large text and targets for reading at a distance; minimal text entry (offer sign-in from a phone instead)
- Back (the Menu/back button) must always work and never trap the user (`rules/error-prevention.md`)
