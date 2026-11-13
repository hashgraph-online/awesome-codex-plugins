# Native Platforms

Use for iOS, Android, macOS and Windows interfaces built with the platform's own toolkit (SwiftUI, UIKit, Jetpack Compose, AppKit, WinUI) or a cross-platform one (React Native, Flutter). The other references are web-first: their principles (hierarchy, states, truthful content, contrast) carry over; their CSS does not.

The platform's guidelines outrank this file and every aesthetic profile: Apple's Human Interface Guidelines, Material Design for Android, Fluent for Windows. Read the current guideline for the component you are building; do not rely on remembered values.

## Start from the platform, not from a web layout

- **Use system components first.** Navigation stacks, tab bars, sheets, lists, menus, pickers, alerts and search fields come with correct behavior, accessibility and future OS updates built in. Restyle them through the supported APIs (tint, font, material); rebuild one only when the product has a requirement the system component cannot meet, and say which.
- **One platform is not the other.** Do not ship an iOS tab bar on Android or a Material floating action button on iOS. On a cross-platform toolkit, branch the navigation pattern, back behavior, pickers and system dialogs per platform even when the content is shared.
- **Navigation follows the platform.** iOS: tab bar for top-level areas, push for depth, sheets for self-contained tasks, edge-swipe back. Android: navigation bar or rail, top app bar, predictive system back that every screen must honor. Desktop: sidebar plus toolbar, menus and keyboard shortcuts for every command.
- **Respect the system's edges.** Lay out inside safe areas and window insets; let backgrounds extend under bars and the home indicator, never controls or text. Handle the keyboard, the Dynamic Island or camera cutout, and foldable or resizable windows.

## Type, size and color come from the system

- **Scale with the user's text size.** Use the semantic text styles (iOS Dynamic Type styles such as body and headline; Material type roles; `sp` units on Android) instead of fixed point sizes, and check the largest accessibility sizes: text must wrap or the layout must reflow, never truncate essential content.
- **Touch targets:** at least 44×44 pt on iOS and 48×48 dp on Android, whatever the visual size of the control. Pointer targets on desktop can be smaller, but keep them reachable by keyboard.
- **Use semantic colors.** System label, background, separator and tint colors adapt to light and dark appearance, increased contrast and elevated surfaces. Define brand colors as an asset or theme with a light and a dark value each; never hard-code one hex for both.
- **Contrast still applies.** Text needs 4.5:1 (3:1 for large text) in both appearances and with "Increase Contrast" on; measure the pairs with `check_contrast`.
- **System materials and effects** (blur, vibrancy, platform glass or tonal elevation) belong to the layers the platform gives them to: bars, sheets, sidebars. Do not imitate them with custom translucent panels behind body text.

## Behavior users expect

- **Motion:** use the system transitions and springs; keep gestures interruptible and reversible; honor Reduce Motion (cross-fade instead of slide or zoom).
- **Feedback:** haptics for confirmation, warning and selection changes, used sparingly and never as the only signal.
- **State:** loading, empty, error and offline states for every screen that fetches; restore scroll position and unsaved input after backgrounding or rotation.
- **Input:** correct keyboard type, content type and autofill hints for every field; return-key action that matches the task; hardware keyboard and pointer support on tablets and desktop.
- **Permissions:** ask at the moment the feature needs it, after explaining why in the product's own words, and keep the feature usable in a reduced form when the user declines.

## Accessibility is checked on a device

- Every control has an accessibility label, a role or trait, and a value where it has one; decorative images are hidden from assistive technology.
- Order and grouping make sense when read aloud: run VoiceOver (iOS, macOS) or TalkBack (Android) through the main flow.
- Everything works with the largest text size, Bold Text, Reduce Motion, Increase Contrast, Switch Control or Switch Access, and full keyboard navigation on desktop.
- Custom gestures have a visible, single-tap alternative.

## Verification

`detect_antipatterns`, `review_and_gate` and `verify_rendered` read web source and web pages only; they report nothing about a native build. Verify native work by building and running it: the Xcode or Android Studio previews and simulators for layout across sizes, appearances and text sizes, the platform accessibility inspector, and a real device for touch, haptics and performance. Report which of those you ran and which you did not; a build that compiles is not evidence that the interface works.
