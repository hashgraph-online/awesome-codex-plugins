# Routing and Navigation

Read when changing the route tree, a layout, a route group, or a param. This file owns route thinness, the navigation contracts, access control, error/loading boundaries, and the URL compatibility rule. It describes Expo Router 58; a project on an older Router must be reviewed against that version's behavior.

## Official boundary

For Expo Router projects, route files live in `src/app` when that route root is used; a root `app` may exist in older or brownfield projects, and `src/app` outranks it when both exist. `_layout.tsx` defines layout/navigation relationships, `(group)` organizes without adding a URL segment, `[param]` represents a dynamic segment, and `+not-found.tsx` handles unmatched routes. `asyncRoutes` is stable and on by default on web in SDK 58, with synchronous production loading on native.

## Thin routes

A route may declare routing metadata, read and validate route/search params, choose layout/navigation options, and compose a feature screen. Move reusable UI, network calls, storage, state machines, and business rules/expo into the owning feature/shared layer.

```tsx
import { ProfileScreen } from '@/features/profile';

export default function ProfileRoute() {
  return <ProfileScreen />;
}
```

Validate deep-link and route params before they reach domain logic. A route may also own its `ErrorBoundary` export and a layout may own `SuspenseFallback`; neither belongs in a feature module that cannot see the route contract.

## Access control

Do not rely on hiding UI. Use the navigator's protected-screen API, which keeps guarded screens registered and renders a redirect when the guard is false:

```tsx
import { Stack } from 'expo-router';
import { useSessionReady } from '@/features/auth';

export default function RootLayout() {
  const isSignedIn = useSessionReady();

  return (
    <Stack>
      <Stack.Protected guard={isSignedIn} redirectTo="/sign-in">
        <Stack.Screen name="account" />
      </Stack.Protected>
      <Stack.Screen name="sign-in" />
    </Stack>
  );
}
```

- Declare each screen once. A screen can belong to only one active group at a time, so a conditional group replaces duplicating the same screen in two branches.
- Protected screens are evaluated on the client only. They produce no static HTML but remain requestable if a URL is known, so they are not a replacement for server-side authorization on any route that returns privileged data.
- `redirectTo` is available from SDK 58. Without it the navigator falls back to its anchor route and then its first accessible screen.
- Model session readiness explicitly so the first render is deterministic, and keep the guard free of redirect loops. A guard that flips from true to false also drops the screen's history entries.

## Navigation contracts

Enable typed routes only when the installed Expo Router supports them and generated types are integrated. Typed routes remain beta and opt-in through `experiments.typedRoutes`; generation writes a git-ignored `expo-env.d.ts`, the plugin option `partialRouteTypes` defaults to `true`, and CI can generate types with `npx expo customize tsconfig.json`. Prefer typed href objects for dynamic routes. Keep route names in routing code rather than scattering string constants through features.

Navigate with complete hrefs. In Router 58, `screen`, `params`, and `initial` are ordinary params rather than instructions for building nested state, and ancestor params are no longer copied into descendants:

```tsx
const router = useRouter();

router.push({ pathname: '/(tabs)/feed/[id]', params: { id: '42' } });
```

Passing `{ withAnchor: true }` is the explicit opt-in when the anchor route should be loaded beneath the destination. Prefer `useRouter()` over the module-level `router` inside components, and keep `useNavigation` for navigator-specific APIs such as events and options.

Declare every screen that should appear in a navigator. JavaScript tabs, top tabs, drawer, headless tabs, and native tabs show only declared screens, and `href: null` hides a tab and makes its route unreachable. The `initialRouteName` navigator prop is removed; export `unstable_settings.anchor` from that stack's layout instead. Do not use `anchor` to choose the launch screen, which the URL decides.

`unstable_settings` does not work with async routes during development, which is why it is still unstable. Verify deep-link back behavior after patching 58.0.x, where a layout without `unstable_settings.anchor` no longer uses the route named like its group as the anchor.

## Navigator entry points

| Navigator | SDK 58 import | Earlier |
|---|---|---|
| Native tabs | `expo-router/native-tabs` | `expo-router/unstable-native-tabs` on SDK 54 through 57 |
| JavaScript tabs | `expo-router/js-tabs` | `expo-router` tabs export before SDK 56 |
| JavaScript stack | `expo-router/js-stack` | `expo-router` stack export before SDK 56 |

`withLayoutContext` is deprecated in favor of `integrateWithRouter`, `createStackNavigator` was removed from `expo-router/js-stack`, and custom navigators built with `createStandardRouterNavigator` or `integrateWithRouter` expose a `.Protected` child. Importing from `@react-navigation/*` directly is unsupported since SDK 56; the codemod replaces most of those imports.

## Error and loading boundaries

Screen error boundaries keep navigator UI, such as headers and tab bars, mounted when a screen throws. Precedence is the route's own `ErrorBoundary` export, then a navigator `unstable_screenErrorBoundary` prop, then `unstable_settings.screenErrorBoundary` from the layout. Nested layouts inherit the layout setting unless they set their own or set it to `null`.

```tsx
export const unstable_settings = { screenErrorBoundary: ScreenErrorBoundary };
```

Layouts can export `SuspenseFallback` (SDK 56 and later) to customize loading UI for child routes, and it receives `route` and `params` props. Custom fallbacks do not apply while async routes are on, so a web app that relies on one must set `asyncRoutes: { web: false }`.

Use `activityEnabled` on a navigator or screen to hide inactive content while keeping its state, and `NavigationAwareActivity` to scope the same behavior to part of a screen. `freezeOnBlur` has no effect in SDK 58.

When a screen must block its own removal, `usePreventRemove` receives a callback whose `repeat` function continues the exact blocked action. Set the prevention condition to `false` before calling `repeat` or `disablePrevention`, and never dispatch from a raw `removePrevented` listener while prevention is active.

## Platform and web

Android back actions, iOS gestures, web URLs, modals, and tab lifecycles are not identical. Three SDK 58 deltas matter for architecture reviews:

- Expo Router no longer supplies `react-native-safe-area-context` insets on web. Use CSS `env(safe-area-inset-*)` for web spacing instead of `SafeAreaView` or `useSafeAreaInsets`.
- On iOS 26 and later, Stack headers are transparent with Liquid Glass and content goes under them. Use `contentInsetAdjustmentBehavior="automatic"` on the screen's scroll view, or set `headerTransparent: false`, rather than `SafeAreaView`.
- The experimental web modal implementation was removed. Render web modal overlays through a custom navigator instead of assuming the old behavior.

Test affected navigation behavior on each requested platform. Preserve URL/deep-link compatibility during route moves or explicitly define redirects/migration behavior.

## Sources

> Claims checked 2026-11-04. These statements restate the package's official snapshot, `references/official/expo/expo-react-native-2026-11-04.md`, which cites https://docs.expo.dev/router/migrate/sdk-57-to-58/, https://docs.expo.dev/router/advanced/protected/, https://docs.expo.dev/router/advanced/router-settings/, https://docs.expo.dev/router/advanced/native-tabs/, https://docs.expo.dev/router/reference/typed-routes/, https://docs.expo.dev/router/reference/src-directory/, https://docs.expo.dev/router/error-handling/, https://docs.expo.dev/router/reference/testing/, https://docs.expo.dev/versions/v58.0.0/sdk/router/, and https://expo.dev/changelog/sdk-58.
