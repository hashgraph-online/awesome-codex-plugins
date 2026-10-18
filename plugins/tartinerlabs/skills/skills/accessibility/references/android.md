# Android (Jetpack Compose)

Material 3 components are accessible by default — they expose roles and state to TalkBack and Switch Access and enforce 48 dp touch targets. Most work is describing images and custom components, merging related content, and testing.

## Semantics

| Need | API |
|---|---|
| Name for an icon or image | `Icon(…, contentDescription = "Delete project")` |
| Decorative image, or icon already described by text | `contentDescription = null` |
| Role for a custom clickable | `Modifier.clickable(role = Role.Button, onClickLabel = "Open project") { … }` or `Modifier.semantics { role = Role.Button }` |
| Heading | `Modifier.semantics { heading() }` |
| State in words | `Modifier.semantics { stateDescription = "Downloaded" }` |
| One element for a row | `Modifier.semantics(mergeDescendants = true) { }` |
| Replace children's semantics | `Modifier.clearAndSetSemantics { contentDescription = "…" }` |
| Swipe or hidden actions | `Modifier.semantics { customActions = listOf(CustomAccessibilityAction("Archive") { archive(); true }) }` |
| Announce changes | `Modifier.semantics { liveRegion = LiveRegionMode.Polite }` |

Toggleable rows: `Modifier.toggleable(value, role = Role.Switch, onValueChange = …)` on the whole row, so the label and switch are one target.

## Targets, Text, and Settings

- Minimum touch target 48 dp; Material components apply it, custom ones use `Modifier.minimumInteractiveComponentSize()`
- Text sizes in `sp`; layouts that grow with font scale rather than clip
- Respect the system animation setting (animator duration scale / "Remove animations") for custom animations

## Testing

1. **Compose UI tests** (Compose 1.8+, `androidx.compose.ui:ui-test-junit4-accessibility`): `composeTestRule.enableAccessibilityChecks()` runs the Accessibility Test Framework on interactions
2. **Espresso** (View-based screens): `AccessibilityChecks.enable()`
3. **Accessibility Scanner** app on a device for quick checks
4. **Manually** — TalkBack through every primary flow; Switch Access; largest font size and display size
