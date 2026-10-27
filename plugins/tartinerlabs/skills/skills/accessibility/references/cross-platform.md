# Cross-Platform Apps

One codebase reaches two screen readers — VoiceOver and TalkBack — that behave differently. Test on both; a label that reads well on one can be missing or doubled on the other.

## React Native and Expo

First-class path. Check the installed React Native version before relying on a prop.

### Names, Roles, and State

| Need | Props |
|---|---|
| Name | `accessibilityLabel="Delete project"` (or `aria-label`, RN 0.71+) |
| Hint (optional, brief) | `accessibilityHint="Removes it from all devices"` |
| Role | `accessibilityRole="button"`, `"header"`, `"link"`, `"switch"`, `"image"` — or `role` (RN 0.71+), whose values differ: `heading` not `header`, `img` not `image`, `slider` not `adjustable` |
| State | `accessibilityState={{ selected, checked, disabled, expanded, busy }}` (or `aria-checked`, `aria-expanded`, … RN 0.71+) |
| One element for a row | `accessible` on the container, with a combined `accessibilityLabel` |
| Hide decoration | `accessibilityElementsHidden` (iOS) and `importantForAccessibility="no-hide-descendants"` (Android) — or `aria-hidden` |
| Swipe or hidden actions | `accessibilityActions={[{ name: "archive", label: "Archive" }]}` with `onAccessibilityAction` |

Prefer `Pressable` with a role and label over `TouchableOpacity` wrappers without them; icon-only buttons always need a label.

### Announcements and Settings

- `AccessibilityInfo.announceForAccessibility("Saved")` for status changes (`announceForAccessibilityWithOptions` for queueing on iOS)
- `accessibilityLiveRegion="polite"` (Android only) on a view whose text changes
- `AccessibilityInfo.isReduceMotionEnabled()` and `isScreenReaderEnabled()` return promises — read them once and subscribe to `addEventListener("reduceMotionChanged", …)`; Reanimated users can use `useReducedMotion()`
- Keep `allowFontScaling` on; avoid fixed heights so text can grow
- Touch targets: `hitSlop` or padding to reach 44 pt (iOS) / 48 dp (Android)

### Navigation

- Native-backed stacks and tabs (Expo Router, React Navigation) announce screen changes and handle the back gesture and button
- Modals: set focus to the modal's heading on open (`AccessibilityInfo.sendAccessibilityEvent(ref, "focus")`) and mark it modal (`aria-modal` / `accessibilityViewIsModal` on iOS)

### Testing

- **React Native Testing Library** — query by role and label (`getByRole("button", { name: "Delete project" })`), which fails when names are missing
- **Native tools on the built app** — Xcode Accessibility Inspector and `performAccessibilityAudit()` for iOS; Accessibility Scanner for Android (`references/apple.md`, `references/android.md`)
- **Manually** — VoiceOver and TalkBack through every primary flow; largest text size on both
- **Expo web** output is a web app — test it with `references/web.md`

## Flutter

Material and Cupertino widgets carry semantics; for custom widgets use `Semantics(label:, button:, header:, …)`, `MergeSemantics` to combine a row, and `ExcludeSemantics` for decoration. Test with `flutter test` semantics matchers plus VoiceOver and TalkBack.

## Others

Kotlin Multiplatform with Compose Multiplatform follows `references/android.md` semantics; Capacitor and other web-view apps follow `references/web.md` inside the web view.
