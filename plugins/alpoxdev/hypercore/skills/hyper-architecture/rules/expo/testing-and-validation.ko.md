# Testing과 Validation

완료를 주장하기 전에 읽습니다. 이 파일은 risk depth, check 순서, 필수 scenario, 완료 기록을 소유합니다.

## Risk depth

새 architecture/material refactor는 `standard`, native module, permission, auth/secret, offline data, EAS config, platform divergence 변경은 `thorough`를 사용합니다. Install, native generation, credential, publication gate에는 final-output check와 trajectory check를 함께 적용합니다.

## Check 순서

1. 실제 manifest의 repository-defined format/lint/typecheck/test를 실행합니다.
2. 변경 feature/boundary module의 focused unit/component test를 실행합니다.
3. 설치 SDK에 맞는 Expo diagnostic(일반적으로 `npx expo-doctor`)을 실행합니다. 이 도구가 dependency 호환성을 React Native Directory와 대조하며, New Architecture를 끌 수 없게 된 지금은 이 경로가 유일한 복구 수단입니다.
4. App-config/plugin 변경은 resolved config(`npx expo config`)와 승인된 경우 native output/diff를 검사합니다. `NODE_ENV`와 load되는 `.env` file이 실행 command를 따르므로 resolved output을 만든 command를 기록합니다.
5. `asyncRoutes`, Metro config, Babel config를 바꾼 뒤에는 결과를 판정하기 전에 `npx expo start --clear`나 `npx expo export --clear`로 cache를 비웁니다. 그렇지 않으면 stale cache가 code 실패처럼 보입니다.
6. Routing 변경은 initial route, guard redirect, dynamic/deep-link param, deep link에서의 back, not-found 동작을 실행합니다. Guard가 false로 바뀔 때 stale history entry가 남지 않는지 확인합니다.
7. Native/platform 변경은 project의 documented development-build/build path로 Android/iOS를 각각 검증합니다.

Command를 지어내지 않습니다. Host, credential, simulator/device, package install, authorization 부족으로 native check를 못 하면 정확한 gap과 가장 강한 non-equivalent static check를 기록하고 platform 성공을 주장하지 않습니다.

`npx @expo/agent-cli@latest`(`status`, `dev`, `smoke`)와 `npx expo command:ps`/`command:events`는 agent loop용 선택 diagnostic입니다. Expo CLI, EAS CLI, `expo-doctor`를 감싸는 도구이지 대체물이 아니며 실험 단계입니다. CI 성격의 실행에서는 `EXPO_NO_DEV_MENU=1`을 두어 launch URL이 dev menu를 띄우지 않게 합니다.

## Test 기준선

- 설치 version에 맞춘 `jest-expo`와 React Native Testing Library.
- Router 58의 `expo-router/testing-library`는 `@testing-library/react-native` 14 이상을 요구합니다.
- `renderRouter`는 promise를 반환하고 `testRouter`의 `navigate`, `push`, `replace`, `back`, `setParams`, `dismissAll`은 async입니다. `canGoBack()`만 동기입니다. Assert 전에 await합니다.
- Test file은 `app`/`src/app` 아래에 두지 않습니다. 그 아래 file은 모두 route나 layout입니다. `__tests__`나 별도 directory를 씁니다.
- Network를 mock할 때는 fetch 경계에서 mock하고, 대체 구현이 아니라 `AbortSignal.timeout` 같은 `expo/fetch` 동작을 기준으로 검증합니다.

## 필수 scenario

- 요청 platform의 happy path.
- Invalid/missing runtime data/config.
- 영향 범위의 API timeout/offline/auth expiration.
- 영향 범위의 permission granted/denied/blocked/fresh-install.
- Secure storage unavailable/corrupt/missing value와, 문제가 되는 경우 재설치 후 잔존 여부. iOS Keychain은 uninstall보다 오래 살 수 있습니다.
- 영향 범위의 deep-link/malformed route param과, `unstable_settings.anchor`가 있을 때와 없을 때의 anchor·back 동작.
- Guard 동작: 미인증 접근 redirect, active screen의 접근 상실, redirect loop 부재.
- 영향 범위의 server output 동작: `+api.ts` route가 해당 method에 응답하는지, 지원하지 않는 method가 405를 반환하는지, throw한 `StatusError`가 그 status를 만드는지.
- Platform-specific module 부재 또는 lifecycle 차이.
- 이동한 import, alias, route type, persisted schema regression.

## Architecture readback

Route thinness, feature ownership, dependency direction, cycle 부재, secret leak 부재, intentional state ownership, platform seam, orphan file 부재를 확인합니다. Generated/native diff는 authored source와 분리해 review합니다.

## Completion record

다음을 기록합니다.

```text
Claim -> Risk -> Evidence -> Verification -> Result -> Caveat
```

설치 version, 실제 실행 command, Android/iOS coverage, skipped check, `ship`/`iterate`/`caveated ship`/`block` 중 하나를 포함합니다. 관찰된 실패만 수정하고 2회 pass 후 멈추며 통과를 위해 check를 약화하지 않습니다.

## Sources

> 확인 2026-11-04. 이 서술은 이 패키지의 공식 snapshot `references/official/expo/expo-react-native-2026-11-04.md`를 재진술한 것이며, 그 파일이 다음 URL을 인용합니다: https://docs.expo.dev/router/reference/testing/, https://docs.expo.dev/router/migrate/sdk-57-to-58/, https://docs.expo.dev/develop/unit-testing/, https://docs.expo.dev/guides/new-architecture/, https://docs.expo.dev/guides/environment-variables/, https://expo.dev/changelog/sdk-58..
