# Apple Platforms (SwiftUI, UIKit)

System controls are accessible by default — `Button`, `Toggle`, `Picker`, `Slider`, `NavigationLink`, `List` expose names, roles, and state to VoiceOver, Voice Control, Switch Control, and Full Keyboard Access. Most work is labelling custom views and images, grouping, and honouring user settings.

## Names, Roles, and Grouping (SwiftUI)

| Need | API |
|---|---|
| Name for a control or image | `.accessibilityLabel("Delete project")` |
| Extra usage hint (optional, brief) | `.accessibilityHint("Removes it from all devices")` |
| Current value | `.accessibilityValue("3 of 10")` |
| Role | `.accessibilityAddTraits(.isButton)`, `.isHeader`, `.isSelected` — or `.accessibilityHeading(.h1)` |
| Decorative image | `Image(decorative: "pattern")` or `.accessibilityHidden(true)` |
| One element for a row | `.accessibilityElement(children: .combine)` (or `.ignore` plus your own label) |
| Custom view acting like a control | `.accessibilityRepresentation { Toggle(…) }` |
| Swipe or hidden actions | `.accessibilityAction(named: "Archive") { … }` |
| Reading order | `.accessibilitySortPriority(_:)` |
| Quick navigation in long content | `.accessibilityRotor(_:entries:)` |
| Voice Control names | `.accessibilityInputLabels(["Delete", "Remove"])` |

Icon-only buttons: `Button { … } label: { Label("Delete project", systemImage: "trash") }` with `.labelStyle(.iconOnly)` keeps the name.

## User Settings (environment values)

- `@Environment(\.accessibilityReduceMotion)` — swap large motion for fades
- `@Environment(\.accessibilityReduceTransparency)` — solid backgrounds instead of translucent materials
- `@Environment(\.accessibilityDifferentiateWithoutColor)` — add shapes or icons to colour-coded states
- `@Environment(\.colorSchemeContrast)` — `.increased` when Increase Contrast is on
- `@Environment(\.dynamicTypeSize)` with `.isAccessibilitySize` — switch to stacked layouts at the largest sizes
- `@ScaledMetric var iconSize = 24.0` — scale non-text sizes with Dynamic Type

## Text and Layout

- Text styles (`.font(.body)`), never fixed `.system(size:)` for body text
- `ViewThatFits` or a size-class / `dynamicTypeSize` switch from `HStack` to `VStack`
- Minimum hit target 44×44 pt (`.contentShape(Rectangle())` and padding)

## Announcements

- iOS 17+: `AccessibilityNotification.Announcement("Saved").post()`
- UIKit / earlier: `UIAccessibility.post(notification: .announcement, argument: "Saved")`
- Screen changes: `UIAccessibility.post(notification: .screenChanged, argument: focusTarget)`

## UIKit Equivalents

`isAccessibilityElement`, `accessibilityLabel`, `accessibilityHint`, `accessibilityValue`, `accessibilityTraits`, `accessibilityCustomActions`, `adjustsFontForContentSizeCategory = true` with `UIFont.preferredFont(forTextStyle:)`, and `UIAccessibility.isReduceMotionEnabled`.

## Testing

1. **Accessibility Inspector** (Xcode → Open Developer Tool) — inspect elements and run its audit on a running app
2. **Automated audit in UI tests** (iOS 17+, XCUIAutomation): `try app.performAccessibilityAudit()` — fails on missing labels, small targets, contrast, clipped Dynamic Type, and more
3. **Manually** — VoiceOver through every primary flow; the largest accessibility text size; Reduce Motion, Increase Contrast, and Reduce Transparency on; Voice Control; Full Keyboard Access on iPad and Mac

## Accessibility Nutrition Labels

App Store product pages show which accessibility features an app supports, declared per device in App Store Connect under App Accessibility: VoiceOver, Voice Control, Larger Text, Dark Interface, Differentiate Without Color Alone, Sufficient Contrast, Reduced Motion, Captions, and Audio Descriptions. A feature counts only if users can complete all common tasks with it. Voluntary at first; Apple has said it will become required. Declare only what passes the manual checks above.
