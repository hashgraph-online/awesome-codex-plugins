# Apple Platforms (SwiftUI, UIKit, AppKit)

Apple's system colours, text styles, and materials already adapt to light and dark mode, accessibility settings, and new OS designs. Customise on top of them: put the direction in a few asset-catalog colours, a display treatment, and the content. Leave the system chrome alone.

## Colour

- **Colour sets in the asset catalog** with Any and Dark appearances (and High Contrast variants where needed). Xcode generates `Color.ink`, `Color.surface`, and so on from them.
- **`AccentColor`** in the asset catalog, or `.tint()` on the root view, sets the app-wide accent. System controls pick it up.
- **Neutrals**: a tinted canvas can replace `systemGroupedBackground`. Keep the system's dark-mode logic: elevation through lighter steps, as the system's base (`#000000`), secondary (`#1C1C1E`), and tertiary (`#2C2C2E`) grouped backgrounds do.
- **Semantic system colours** (`.primary`, `.secondary`, `Color(.label)`, `Color(.separator)`) for text and dividers, unless the direction needs a tinted ink
- **Category colours** belong on content (list row icons, chips, card faces), never on navigation bars or tab bars

## Type

- **Text styles** (`.largeTitle`, `.title`, `.headline`, `.body`, `.caption`) so Dynamic Type works. Change the weight or design, not the size: `.font(.largeTitle.bold())` and `.font(.system(.largeTitle, weight: .heavy))`.
- **Screen titles**: the navigation bar's large title, or `.largeTitle.bold()` for a custom header. `.headline` is a 17pt label style, not a title.
- **SF Pro as the display face.** Use Heavy or Black weights, `.fontWidth(.expanded)` or `.condensed` for a distinct headline (iOS 16+), and `.fontDesign(.rounded)` or `.serif` for Character-led or Editorial directions.
- **Leave tracking alone.** SF Pro applies size-specific tracking automatically. Manual `.tracking()` is for all-caps labels only.
- `.monospacedDigit()` for counters, prices, and timers. Use `.contentTransition(.numericText())` when they change.
- **Custom fonts** scale with `.custom("Name", size: 17, relativeTo: .body)` (SwiftUI) or `UIFontMetrics` (UIKit)

## Surfaces

- **System containers first**: `List` with `.insetGrouped`, `Form`, `GroupBox`. They are the platform's card system.
- **Materials** (`.regularMaterial`, `.thinMaterial`) for custom floating elements over scrolling content
- **Liquid Glass** (OS 26) belongs on the navigation layer: system bars, tab bars, toolbars, and sheets get it automatically. For custom floating controls use `.glassEffect()`. Never put glass on scrolling content or on cards in a list.
- **`TabView` as Apple ships it.** Keep the default tab bar: no custom background, selection colour, icon sizing, or hand-drawn replacement. The selected tab already takes the app's `AccentColor`, and SF Symbols switch to their filled variant on their own. The ink-for-selection advice in `rules/actions.md` is for the app's own controls, not the system tab bar.
- **Corner radii**: `.clipShape(.rect(cornerRadius: 20, style: .continuous))` for Apple's continuous corners. For nested corners, use `ConcentricRectangle` or `ContainerRelativeShape` inside a container that sets `.containerShape(_:)`, so inner corners follow the container's radius.
- **Shadows**: one soft `.shadow(color: .black.opacity(0.08), radius: 16, y: 8)` style at most. Use none in dark mode.

## Actions

- `.buttonStyle(.borderedProminent)` with `.tint()` and `.buttonBorderShape(.capsule)` gives a branded primary that keeps system pressed, disabled, and accessibility behaviour
- `.controlSize(.large)` for bottom-pinned primaries on phones
- Alerts, confirmation dialogs, and menus keep system styling

## Icons and Imagery

- **SF Symbols** in one rendering mode per context (`.monochrome`, `.hierarchical`, `.palette`). Symbols match the weight of adjacent text automatically.
- **Symbol effects** (`.symbolEffect`) for small state changes, sparingly
- **Widgets, Live Activities, and App Store screenshots** are showcase surfaces: use the signature visual and the direction at full volume

## Platform Notes

- **iPad and Mac**: the same tokens with more whitespace. Use sidebars (`NavigationSplitView`), not a stretched phone layout.
- **watchOS**: black background, the accent on one element, large numerals
- **visionOS**: glass windows are the surface. Content colour, not window colour, carries the direction.
- **tvOS**: focus effects are the selection state, so let the system draw them
