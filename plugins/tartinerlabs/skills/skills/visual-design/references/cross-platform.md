# Cross-Platform Apps (React Native, Expo, Flutter)

A cross-platform app's look is one design, defined once and shared by both platforms. Brand colour, type, imagery, and content stay the same everywhere. System chrome (tab bars, sheets, alerts, pickers) follows each OS. The tokens live in code, so define them once and import them everywhere.

## Tokens in React Native and Expo

- **One theme module** exporting colour, type, spacing, radius, and shadow tokens named by role. Components never use raw hex values or numbers.
- **Light and dark** as two objects of the same shape, chosen with `useColorScheme()`. Use the theme provider when a library supplies one (React Navigation's `ThemeProvider`, Tamagui, NativeWind's dark variants, Unistyles).
- **NativeWind / Tailwind**: put the tokens in the Tailwind theme and use CSS variables for light and dark, as on the web
- **Navigation chrome**: pass the tokens to React Navigation's theme or Expo Router's native tabs so headers and tab bars match, while keeping native components

## Fonts

Apple's system fonts (SF Pro, SF Mono, New York) are licensed for Apple platforms only. They cannot be bundled into an Android build, and Android's default (Roboto) looks different. For one consistent look, bundle an open-licence font on both platforms instead of relying on the system font.

| Apple system face | Open-licence replacements | Notes |
|---|---|---|
| SF Pro (text and display) | Inter, Geist | Inter is the closest match. Geist has more character and pairs with Geist Mono. |
| SF Pro Heavy/Black | Inter Display, Inter Tight, Geist at 800–900 | Heavy display weights for headlines and hero numbers |
| SF Pro Expanded | Archivo (width axis), Unbounded | Wide display headlines |
| SF Pro Rounded | Nunito, Manrope | Character-led directions |
| SF Mono | Geist Mono, JetBrains Mono | Timecodes, codes, tabular data |
| New York | Newsreader, Source Serif 4 | Editorial directions |

- Ship the font's licence file (usually SIL OFL 1.1) next to the font files
- **Expo**: embed fonts at build time with the `expo-font` config plugin in `app.json`, or load at runtime with `useFonts`, keeping the splash screen up until they load
- **Android weights**: refer to each weight by its own family name (for example `Geist-Bold`) unless your font setup maps `fontWeight` to files. Android does not reliably pick a weight from one custom family.
- **Tabular numbers**: `fontVariant: ['tabular-nums']`
- **Scaling**: keep `allowFontScaling` on. Cap extreme sizes with `maxFontSizeMultiplier` on dense layouts only.
- **Native-feeling exception**: an app that wants each platform's own look can use the system font (`System` on iOS, Roboto on Android) and accept that the platforms differ

## Surfaces and Depth

- **Shadows differ per OS**: iOS uses `shadowColor`, `shadowOpacity`, and `shadowRadius`, and Android uses `elevation`. Newer React Native versions support `boxShadow` on both. Keep one shadow token and map it per platform.
- **Blur**: `expo-blur` (`BlurView`) for floating bars over scrolling content. `expo-glass-effect` (`GlassView`) gives Liquid Glass on iOS 26+ and falls back to a plain view elsewhere, so the design must work without it.
- **Corner radius**: the same radius scale on both platforms. Set `borderCurve: 'continuous'` on iOS for Apple-style corners.

## Actions and Icons

- Build one `Button` component that implements the button system (`rules/actions.md`), with `Pressable` pressed states and `android_ripple`
- One icon library on both platforms (Lucide, Phosphor, or `@expo/vector-icons` with a single set), or SF Symbols on iOS via `expo-symbols` paired with Material Symbols on Android when the app follows each OS

## Flutter

- `ThemeData` with `ColorScheme` (seeded with `ColorScheme.fromSeed`, or set role by role), `TextTheme`, and component themes (`FilledButtonThemeData`, `CardThemeData`) carry the tokens
- Custom fonts in `pubspec.yaml`, with one family and weight entries. `FontFeature.tabularFigures()` for numbers.
- `ThemeExtension` for tokens Material has no role for (category colours, ink)
- Cupertino widgets or adaptive constructors where each OS's chrome should look native
