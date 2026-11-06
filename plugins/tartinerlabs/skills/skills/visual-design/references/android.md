# Android (Jetpack Compose)

Material 3 is a token system: colour roles, a type scale, and a shape scale passed to `MaterialTheme`. Express the direction by setting those tokens, not by styling components one at a time.

## Colour

- **`ColorScheme` roles**: `primary`/`onPrimary` for the main action, `primaryContainer` for tinted emphasis, `surface` and the `surfaceContainerLowest…Highest` steps for neutrals and elevation, `outline`/`outlineVariant` for dividers, and `error` for status
- **Tinted neutrals**: Material's `surface` roles are already tinted from the seed colour. A custom scheme sets them deliberately.
- **Ink primary**: a near-black `primary` with `onPrimary` off-white suits Product showcase directions. Keep a separate token for the accent.
- **Dynamic colour** (`dynamicLightColorScheme(context)` on Android 12+) replaces the palette with one derived from the user's wallpaper. It suits utility apps that want to feel native. Skip it when the brand colour is the identity, and keep the static scheme as the fallback either way.
- **Dark scheme as its own `darkColorScheme`.** Elevation comes from the surface container steps, not shadows.
- **Category colours** live in the app's own `CompositionLocal` or object, not in `ColorScheme` roles meant for chrome

## Type

- **`Typography`** roles: `display`, `headline`, `title`, `body`, and `label`, each Large, Medium, and Small. Map the direction's display face to `display*` and `headline*`, and the text face to the rest.
- **Units**: `sp` for all text so font scaling works
- **Tabular numbers**: `TextStyle(fontFeatureSettings = "tnum")` on numeric styles
- **Custom fonts** from `res/font` or downloadable Google Fonts (`GoogleFont.Provider`), declared as a `FontFamily` with each weight
- Roboto is the system default. A heavier weight or Roboto Flex's width axis gives it character without a custom face.

## Shape

- **`Shapes`** scale: `extraSmall`, `small`, `medium`, `large`, and `extraLarge`, with defaults from `ShapeDefaults` (newer Material 3 versions add `largeIncreased`, `extraLargeIncreased`, and `extraExtraLarge`). Set it once to the direction's radius scale, and components follow.
- Use pill buttons through `CircleShape` or `RoundedCornerShape(50)`, consistently

## Surfaces

- **Cards** (`Card`, `ElevatedCard`, `OutlinedCard`): pick one variant for the app
- **Elevation** through tonal surface colour rather than shadow, as Material 3 does by default
- **Edge-to-edge** (`enableEdgeToEdge()`; enforced when targeting Android 15+): the canvas colour runs behind the system bars, and insets come from `WindowInsets`
- **Blur** (`Modifier.blur`) works on Android 12+ only, so design a translucent-colour fallback

## Actions

- `Button` (filled) for the primary, `FilledTonalButton` or `OutlinedButton` for secondary, and `TextButton` for tertiary
- `ExtendedFloatingActionButton` only when the screen's primary action is creation, as Material intends
- Selection in `FilterChip`, `SegmentedButton`, and `NavigationBar` takes its colour from the theme. When that collides with a category colour, set it to ink or the accent through the component's colours (for example `FilterChipDefaults.filterChipColors(selectedContainerColor = …)`).

## Icons and Imagery

- **Material Symbols** (Outlined, Rounded, or Sharp) as one style, with filled for the active state
- **Adaptive and themed launcher icons** (monochrome layer) so the icon follows the user's theme
- **Play Store screenshots and feature graphics** are showcase surfaces
