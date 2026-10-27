# Cross-Platform Apps

One codebase, two sets of user expectations. An iPhone user and an Android user bring different habits to the same screen (`rules/jakobs-law.md`), so the core decision is what follows each OS and what stays the same everywhere.

## Follow the OS vs Keep It Yours

| Follow each OS (users' muscle memory lives here) | Keep consistent across platforms (your product) |
|---|---|
| Back navigation — iOS edge swipe, Android system back | Brand, colour, typography, illustration |
| Navigation chrome — tab bar, top bar, sheets | Information architecture and screen order |
| Date/time pickers, action sheets, alerts | Content, copy, and terminology |
| Haptics and system feedback | Feature set and flows |
| Permission prompts and system dialogs | Layout of your own content |
| Share sheets, keyboards, autofill | Empty states, onboarding, error messages |

The common failure is shipping one platform's conventions to both — an iOS-style custom back chevron with no Android system-back handling, or iOS action sheets on Android. When in doubt, use the component that renders natively on each OS.

## React Native and Expo

First-class path. Check the installed versions before relying on an API.

### Navigation

- Use Expo Router's (or React Navigation's) native-backed **stack** — it gives the iOS edge swipe and Android predictive back without extra code
- Tabs: Expo Router's `NativeTabs` (`expo-router/native-tabs`) renders each OS's real tab bar — Liquid Glass on iOS 26+, Material on Android — instead of a JavaScript imitation of one
- Modals: `presentation: "modal"` or `"formSheet"` on a stack screen, which maps to native sheets on iOS
- Android back: handled by the native stack; for custom screens that must intercept it (unsaved draft), use `BackHandler` and let the user leave after one confirmation (`references/android.md`)

### Platform Differences in Code

- `Platform.select({ ios: …, android: … })` or `.ios.tsx` / `.android.tsx` files for the few components that truly differ — keep the logic shared
- Native date/time pickers (`@react-native-community/datetimepicker`) rather than one custom picker for both
- `Alert.alert` for system alerts; an action sheet on iOS and a bottom sheet or menu on Android for option lists
- `@expo/ui` renders real SwiftUI on iOS and Jetpack Compose on Android from React — its Universal components give each OS its native controls from one component tree, which is the "follow the OS" column above in one package
- `expo-glass-effect` (`GlassView`) only for custom floating controls that need glass; it falls back to a plain `View` below iOS 26 and on Android, so the design must work without it

### Layout

- `react-native-safe-area-context` (`useSafeAreaInsets`, `SafeAreaView`) for notches, home indicators, and Android edge-to-edge insets
- `KeyboardAvoidingView` (or the router/screen's keyboard handling) so the focused field and primary button stay visible
- Touch targets: `hitSlop` to reach 44 pt (iOS) / 48 dp (Android) on small icons (`rules/fitts-law.md`)

### Feedback

- `Pressable` with a visible pressed style on every touchable; `android_ripple` on Android
- `expo-haptics`: `selectionAsync()` for picker and toggle changes, `notificationAsync(NotificationFeedbackType.Success | Warning | Error)` for outcomes, `impactAsync()` for physical-feeling moments — sparingly
- Motion details (springs, gestures with Reanimated) belong to an animation skill when installed; this guide only decides that feedback is needed

### Text Input

- `keyboardType`, `autoComplete` (`"email"`, `"one-time-code"`, `"postal-code"`, …), and `textContentType` (iOS) so each OS autofills (`rules/defaults.md`)
- `returnKeyType="next"` and focus the next field on submit

### Expo Web

When the same code ships to the web, the web output is judged as a web app — load `references/web.md` for it: hover, keyboard, and focus states the native build never needed.

## Flutter and Others

Flutter, Kotlin Multiplatform, and Capacitor face the same split. The table at the top applies unchanged; Flutter's `Cupertino` widgets and adaptive constructors (`Switch.adaptive`, `showAdaptiveDialog`) are its tools for following each OS.
