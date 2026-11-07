# Routing과 Navigation

route tree, layout, route group, param을 바꿀 때 읽습니다. 이 파일은 route thinness, navigation 계약, 접근 제어, error/loading 경계, URL 호환 규칙을 소유합니다. Expo Router 58을 설명하므로 더 오래된 Router를 쓰는 프로젝트는 그 version의 동작으로 다시 확인해야 합니다.

## Official boundary

Expo Router 프로젝트에서 해당 route root를 쓰면 route file은 `src/app`에 있습니다. 기존 프로젝트나 brownfield는 root `app`을 쓸 수 있고, 둘 다 있으면 `src/app`이 우선합니다. `_layout.tsx`는 layout/navigation 관계를 정의하고 `(group)`은 URL segment 없이 조직하며 `[param]`은 dynamic segment, `+not-found.tsx`는 unmatched route를 처리합니다. `asyncRoutes`는 stable이고 SDK 58에서 web 기본 활성이며 native production은 동기 loading을 유지합니다.

## Thin route

Route는 routing metadata 선언, route/search param 읽기와 검증, layout/navigation option 선택, feature screen composition을 담당할 수 있습니다. Reusable UI, network call, storage, state machine, business rule은 owning feature/shared layer로 옮깁니다.

```tsx
import { ProfileScreen } from '@/features/profile';

export default function ProfileRoute() {
  return <ProfileScreen />;
}
```

Deep-link/route param은 domain logic에 도달하기 전에 검증합니다. Route는 자체 `ErrorBoundary` export를, layout은 `SuspenseFallback`을 소유할 수 있으며, 둘 다 route 계약을 볼 수 없는 feature module에 두지 않습니다.

## 접근 제어

UI 숨김에 의존하지 않습니다. Guard가 false일 때 redirect를 render하면서 guarded screen을 등록 상태로 유지하는 navigator의 protected-screen API를 씁니다.

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

- Screen은 한 번만 선언합니다. 한 screen은 한 번에 하나의 active group에만 속할 수 있으므로 같은 screen을 두 branch에 복제하지 말고 조건 group으로 감쌉니다.
- Protected screen은 client에서만 평가합니다. Static HTML을 만들지 않지만 URL을 아는 사용자가 요청할 수 있으므로 privileged data를 반환하는 route의 server-side authorization을 대신하지 못합니다.
- `redirectTo`는 SDK 58부터 있습니다. 없으면 navigator의 anchor route와 그다음 접근 가능한 screen으로 돌아갑니다.
- 첫 render가 deterministic하도록 session readiness를 명시적으로 모델링하고 guard에 redirect loop를 만들지 않습니다. Guard가 true에서 false로 바뀌면 그 screen의 history entry도 제거됩니다.

## Navigation 계약

설치 Expo Router가 지원하고 generated type이 project에 통합될 때만 typed routes를 켭니다. Typed routes는 여전히 beta이고 `experiments.typedRoutes`로 켜는 opt-in이며, 생성 시 git에서 무시되는 `expo-env.d.ts`를 쓰고, plugin option `partialRouteTypes`의 기본값은 `true`이고, CI에서는 `npx expo customize tsconfig.json`으로 type을 만듭니다. Dynamic route는 typed href object를 선호합니다. Route name은 feature 전반에 string constant로 흩뿌리지 말고 routing code에 둡니다.

Navigation은 완전한 href로 합니다. Router 58에서 `screen`, `params`, `initial`은 nested state를 만드는 지시가 아니라 일반 param이고 ancestor param은 descendant로 복사되지 않습니다.

```tsx
const router = useRouter();

router.push({ pathname: '/(tabs)/feed/[id]', params: { id: '42' } });
```

Anchor route를 대상 아래에 적재해야 할 때는 `{ withAnchor: true }`를 명시적으로 넘깁니다. Component 안에서는 module-level `router`보다 `useRouter()`를 선호하고, event·option 같은 navigator 전용 API에는 `useNavigation`을 씁니다.

Navigator에 보여야 하는 screen은 모두 선언합니다. JavaScript tabs, top tabs, drawer, headless tabs, native tabs는 선언한 screen만 보여주며 `href: null`은 tab을 숨기는 동시에 그 route를 도달 불가로 만듭니다. `initialRouteName` navigator prop은 제거되었으므로 그 stack의 layout에서 `unstable_settings.anchor`를 export합니다. 시작 화면은 URL이 정하므로 `anchor`로 시작 화면을 고르지 않습니다.

`unstable_settings`는 개발 중 async route와 함께 동작하지 않으며 그래서 unstable입니다. 58.0.x patch에서는 `unstable_settings.anchor`가 없는 layout이 group 이름과 같은 route를 anchor로 쓰지 않으므로 patch 후 deep-link back 동작을 확인합니다.

## Navigator entry point

| Navigator | SDK 58 import | 이전 |
|---|---|---|
| Native tabs | `expo-router/native-tabs` | SDK 54부터 57까지 `expo-router/unstable-native-tabs` |
| JavaScript tabs | `expo-router/js-tabs` | SDK 56 이전의 `expo-router` tabs export |
| JavaScript stack | `expo-router/js-stack` | SDK 56 이전의 `expo-router` stack export |

`withLayoutContext`는 `integrateWithRouter`로 deprecated이고 `expo-router/js-stack`에서 `createStackNavigator`가 제거되었으며, `createStandardRouterNavigator`나 `integrateWithRouter`로 만든 custom navigator는 `.Protected` child를 제공합니다. SDK 56부터 `@react-navigation/*`를 직접 import하는 것은 지원되지 않으며 codemod가 그 import 대부분을 바꿔 줍니다.

## Error와 loading 경계

Screen error boundary는 screen이 throw해도 header와 tab bar 같은 navigator UI를 유지합니다. 우선순위는 route의 `ErrorBoundary` export, navigator의 `unstable_screenErrorBoundary` prop, layout의 `unstable_settings.screenErrorBoundary` 순입니다. Nested layout은 자체 값을 두거나 `null`로 끊지 않으면 layout setting을 상속합니다.

```tsx
export const unstable_settings = { screenErrorBoundary: ScreenErrorBoundary };
```

Layout은 `SuspenseFallback`(SDK 56 이후)을 export해 child route의 loading UI를 바꿀 수 있고, 이 component는 `route`와 `params` prop을 받습니다. Async route가 켜져 있는 동안에는 custom fallback이 적용되지 않으므로 그것에 의존하는 web 앱은 `asyncRoutes: { web: false }`를 설정합니다.

`activityEnabled`를 navigator나 screen에 주면 state를 유지하면서 비활성 content를 숨기고, `NavigationAwareActivity`는 같은 동작을 screen 일부에 적용합니다. `freezeOnBlur`는 SDK 58에서 아무 효과가 없습니다.

Screen이 자신의 제거를 막아야 할 때 `usePreventRemove`의 callback이 받는 `repeat` 함수가 차단된 동작을 그대로 이어서 수행합니다. `repeat`나 `disablePrevention`을 호출하기 전에 방지 조건을 `false`로 바꾸고, 방지가 활성인 동안 raw `removePrevented` listener에서 dispatch하지 않습니다.

## Platform과 web

Android back action, iOS gesture, web URL, modal, tab lifecycle은 동일하지 않습니다. Architecture review에서 중요한 SDK 58 차이는 세 가지입니다.

- Expo Router는 web에서 `react-native-safe-area-context` inset을 더 이상 제공하지 않습니다. Web 여백은 `SafeAreaView`나 `useSafeAreaInsets` 대신 CSS `env(safe-area-inset-*)`로 줍니다.
- iOS 26 이상에서 Stack header는 Liquid Glass와 함께 투명하고 content가 그 아래로 들어갑니다. `SafeAreaView` 대신 screen의 scroll view에 `contentInsetAdjustmentBehavior="automatic"`을 주거나 `headerTransparent: false`를 설정합니다.
- 실험적 web modal 구현이 제거되었습니다. 예전 동작을 전제하지 말고 custom navigator로 web modal overlay를 render합니다.

영향 navigation을 요청된 각 platform에서 시험합니다. Route 이동 시 URL/deep-link compatibility를 보존하거나 redirect/migration 동작을 명시합니다.

## Sources

> 확인 2026-11-04. 이 서술은 이 패키지의 공식 snapshot `references/official/expo/expo-react-native-2026-11-04.md`를 재진술한 것이며, 그 파일이 다음 URL을 인용합니다: https://docs.expo.dev/router/migrate/sdk-57-to-58/, https://docs.expo.dev/router/advanced/protected/, https://docs.expo.dev/router/advanced/router-settings/, https://docs.expo.dev/router/advanced/native-tabs/, https://docs.expo.dev/router/reference/typed-routes/, https://docs.expo.dev/router/reference/src-directory/, https://docs.expo.dev/router/error-handling/, https://docs.expo.dev/router/reference/testing/, https://docs.expo.dev/versions/v58.0.0/sdk/router/, https://expo.dev/changelog/sdk-58..
