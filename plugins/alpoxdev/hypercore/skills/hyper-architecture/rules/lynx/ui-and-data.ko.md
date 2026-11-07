# Lynx UI와 Data

> Lynx app의 element, style, layout, event, list, host 제공 data, routing을 다룰 때 읽습니다.

## Element

Lynx element는 DOM node가 아닙니다. iOS `UIView`, Android `ViewGroup`, HarmonyOS component, web custom element로 대응됩니다.

`view`, `text`, `image`, `scroll-view`, `list`/`list-item`, `page`, `frame`, `input`, `textarea`, `overlay`, `refresh`, `scroll-coordinator`, `svg`, `title-bar-view`, `viewpager`.

Web React에서 가져온 습관 중 여기서 깨지는 것들입니다.

- Text는 `<text>` 안에 있어야 합니다. `<view>`의 bare text는 render되지 않습니다.
- Inline layout은 `display: inline`이 아니라 중첩 `<text>`입니다.
- `<image>`는 `src`를 가진 빈 tag입니다. `auto-size`는 선언한 width/height 대신 image에서 크기를 정합니다.
- `<svg>`는 web과 다릅니다. `content`로 markup을, `src`로 URL을 넘깁니다.

## CSS 차이

Selector, specificity, inline `style`은 대체로 web과 같습니다. Layout model이 다릅니다.

| Web 동작 | Lynx 동작 |
|---|---|
| `display: inline`, `display: block` | `display` 값으로 지원하지 않음. 모든 element가 기본 block-level |
| `box-sizing: content-box` | 항상 `border-box` |
| Margin collapsing | 일어나지 않음 |
| `overflow: scroll` | 미지원. `<scroll-view scroll-x>` 또는 `scroll-y` 사용 |
| `position: fixed`가 viewport 기준 | Fixed node는 root node 아래로 승격됨 |
| 일반 property가 상속됨 | 기본적으로 CSS custom property만 상속됨 |

실제로 존재하는 `display` mode입니다.

- `flex` — CSS Flexbox이지만 `min-content`가 미지원이고 flex shrink 하한이 `0px`로 처리됩니다.
- `linear` — `linear-direction`과 `linear-weight`를 쓰는 세로 main axis.
- `grid` — `grid-area`와 line name이 없습니다.
- `relative` — Android `RelativeLayout` 사고방식, mobile 전용.

`position`은 `relative`, `absolute`, `fixed`를 지원합니다.

단위: `rpx`는 host 화면 metric에서 정한 논리 width의 1/750입니다. `vw`와 `vh`가 있고, web target에서는 `transform-vw`와 `transform-vh`로 container마다 기준을 바꿀 수 있습니다.

상속은 opt-in이고 default를 잘못 읽기 쉽습니다. `pluginReactLynx({ enableCSSInheritance: true })`는 고정된 목록을 상속시킵니다. `direction`, `color`, `font-*`, `letter-spacing`, `line-height`, `text-align`, `text-decoration`, `text-shadow`이고 `customCSSInheritanceList`가 그 목록을 확장합니다. `enableCSSInheritance`의 default는 `false`이므로 container에 지정한 font는 상속을 켜거나 자식에 다시 지정하지 않으면 자식에 닿지 않습니다.

`-x-` 접두 property는 `-x-auto-font-size` 같은 mobile 기능을 노출합니다.

Version에 민감한 CSS이며 모두 맞는 `engineVersion`이 필요합니다.

- `!important`는 `engineVersion` 3.9 이상이 필요합니다.
- 3.9는 `flex` shorthand를 바꿔 `flex-basis`를 생략하면 `0`이 아니라 `0%`로 parse합니다.
- 3.9는 `grid-row`/`grid-column` shorthand, `position: sticky`, HarmonyOS motion path를 추가했습니다.

각각은 styling 세부가 아니라 배포 결정입니다. 하나를 쓰려고 `engineVersion`을 올리면 host 하한을 올리는 것입니다.

## Event

Attribute 이름이 phase와 전파 차단 여부를 함께 표현합니다.

| Attribute | 동작 |
|---|---|
| `bindtap` | Bubble phase, handler는 background에서 실행 |
| `catchtap` | Bubble phase, 전파 중단 |
| `capture-bindtap` | Capture phase |
| `capture-catchtap` | Capture phase, 전파 중단 |
| `global-bindtap` | 대상 node와 무관한 global listening |
| `main-thread:bindtap` 및 변형 | Handler가 main thread에서 동기 실행 |

Background handler는 plain JSON을 받습니다. Non-touch event는 target node에서만 발생합니다. `stopPropagation()`은 main-thread script 안에만 존재하고, background thread에서는 `catch`/`capture` 이름이 그 수단입니다.

공식 best practice에 따른 handler 작성 방식입니다.

- Inline arrow가 아니라 function reference를 넘깁니다. Inline arrow는 render마다 새로 만들어지고 background-only 추론을 깨뜨립니다.
- 값을 closure로 잡지 말고 `dataset`에서 읽습니다.
- Event가 자식에서 발생해도 handler가 맞게 동작하도록 `target`보다 `currentTarget`을 선호합니다.

```tsx
<view
  data-id={item.id}
  bindtap={onRowTap}
/>

function onRowTap(e) {
  'background only';
  openDetail(e.currentTarget.dataset.id);
}
```

## List

`<list>`는 virtualize하고 recycle합니다. 보이는 영역의 자식만 render되며, `<list>`의 width와 height는 viewport이므로 "고정 값이어야 합니다".

필수 attribute는 `scroll-orientation`, `list-type`(`single`, `flow`, `waterfall`), `span-count`입니다. 직접 자식은 모두 `<list-item>`이고 `item-key`를 가지며 이 값은 목록을 만들 때 쓴 `key`와 일치해야 합니다.

```tsx
<list
  scroll-orientation="vertical"
  list-type="single"
  span-count={1}
  style={{ height: '100vh' }}
>
  {rows.map((row) => (
    <list-item key={row.id} item-key={row.id}>
      <Row row={row} />
    </list-item>
  ))}
</list>
```

Recycling 제어입니다.

- `reuse-identifier`는 구조가 같은 item을 묶어 group 사이에서 node를 재사용합니다. Compile 시점에 loop 형태별로 자동 생성되며, 두 loop가 node를 공유해야 하면 직접 지정합니다.
- `recyclable={false}`는 node를 recycling에서 제외합니다.
- `experimental-recycle-sticky-item`은 특정 `engineVersion` 하한부터 기본 활성화됩니다.

실제 bug를 만드는 lifecycle 주의점입니다. 모든 자식 component의 JS instance는 미리 생성되지만 실제 UI node는 가까이 scroll될 때 만들거나 재사용합니다. 그래서 UI node가 없어도 `useEffect`와 `ref`가 실행됩니다. Node가 실제로 attach됐는지 알아야 하는 code는 `main-thread:ref`를 씁니다.

## Host data

Host가 `initData`를 주입하고 갱신합니다.

| Platform | 초기 | 갱신 |
|---|---|---|
| iOS | `LynxView.loadTemplate(meta.initialData)` | `updateData` |
| Android | `LynxLoadMeta.Builder`의 `setInitialData` | `updateMetaData` |
| HarmonyOS | `MetaData(new TemplateData(...))` | `updateMetaData` |

`useInitData()`로 읽고, 이 hook은 갱신 시 다시 render합니다. `lynx.__globalProps`에는 `useGlobalProps()`를 씁니다. Host가 제공하지 않으면 `__globalProps`가 `null` 또는 `{}`일 수 있으므로 소비자는 부재를 처리해야 합니다.

Interface를 한 번만 augment해 계약을 typing합니다.

```ts
// src/types/lynx.d.ts
declare module '@lynx-js/react' {
  interface InitData {
    userId: string;
    entryPoint: 'feed' | 'detail';
  }
}

declare module '@lynx-js/types' {
  interface GlobalProps {
    locale: string;
  }
}
```

갱신에 다시 render하는 대신 반응해야 하는 code에는 `useInitDataChanged`와 `useGlobalPropsChanged`가 있습니다.

Host data는 신뢰할 수 없는 입력입니다. 다른 network payload처럼 경계에서 `initData`를 검증합니다. JSON으로 host에서 오며, 없거나 일부만 오거나 갱신 후 오래된 값일 수 있습니다.

## Routing

History API도 `document`도 없으므로 routing은 필연적으로 memory 기반입니다.

- **React Router** — v7이 아니라 v6을 설치합니다. ReactLynx는 React v17 API surface를 노출하며 문서가 이를 직접 밝힙니다. `MemoryRouter`를 쓰고 `<Link>`와 `<NavLink>`는 anchor를 render하므로 해당하지 않습니다. 이동은 `useNavigate`로 합니다.
- **TanStack Router** — memory routing이 필수입니다. File 기반 routing은 `@tanstack/router-plugin/rspack`으로 동작합니다. `React.startTransition`이 resolve되도록 `react$`를 `@lynx-js/react/compat`로 alias하고, `document`가 undefined이므로 `isServer: false`를 두고, entry에 `url-search-params-polyfill`을 추가합니다.

둘 다 지원됩니다. 취향이 아니라 repository의 기존 dependency로 고릅니다.

Lynx app 안의 routing library는 Lynx target의 일부이며 두 번째 framework가 아닙니다.

## 여기 없는 것

`document`, `window`, DOM API, `localStorage`, History API, `<Link>`입니다. 대체물은 `lynx.reload`, `lynx.createSelectorQuery`, `GlobalEventEmitter`, native module, custom element입니다. Import 시점에 `window`나 `document`에 의존하는 library는 호출 시점이 아니라 load 시점에 실패합니다.

PrimJS에는 `TextEncoder`/`TextDecoder`가 없습니다. Text codec 작업이 필요하면 `TextCodecHelper`를 씁니다. `fetch`는 host가 제공하는 HTTP service에 의존하므로 모든 embedding에서 사용할 수 있는 것은 아닙니다.

## Checklist

- [ ] 모든 text가 `<text>` 안에 있고 `<view>`에 bare text node가 없습니다.
- [ ] `display: inline`이나 `display: block`을 도입하지 않았습니다.
- [ ] `overflow: scroll`을 도입하지 않고 `<scroll-view>`를 썼습니다.
- [ ] `enableCSSInheritance`가 꺼져 있으면 container의 font나 color 상속을 가정하지 않습니다.
- [ ] `!important`, `flex` shorthand, `position: sticky` 사용이 요구하는 `engineVersion`과 일치합니다.
- [ ] Event handler가 function reference이고 `dataset`을 읽으며 `currentTarget`을 선호합니다.
- [ ] 모든 virtualized feed가 고정 viewport, `list-type`, `span-count`, `scroll-orientation`, `key`와 같은 `item-key`를 갖춘 `<list>`입니다.
- [ ] List row node 존재 여부를 알아야 하는 code가 `main-thread:ref`를 씁니다.
- [ ] `initData`와 `globalProps`가 하나의 augmentation으로 typing됐고 경계에서 검증됩니다.
- [ ] 없는 `globalProps`를 처리하며 존재를 가정하지 않습니다.
- [ ] Routing이 memory history를 쓰고 `<Link>`, `NavLink`, History API 호출이 남아 있지 않습니다.
- [ ] Upload와 text codec 경로가 없는 `TextEncoder`/`TextDecoder`와 host 의존 `fetch`를 처리합니다.

## Sources

> 확인 2026-11-07. 이 서술은 이 패키지의 날짜가 있는 snapshot `references/official/lynx/lynx-2026-11-07.md`를 재진술한 것이며, 그 파일이 2026-11-07에 읽은 Lynx 문서를 인용합니다.

| Claim | Source |
|---|---|
| Element 집합과 element-to-native 대응 | https://lynxjs.org/guide/ui/elements-components.md, https://lynxjs.org/llms.txt |
| `<text>` 안의 text, `auto-size`를 쓰는 `<image>`, `<svg>`의 `content`/`src` | https://lynxjs.org/llms.txt |
| `display` mode, `box-sizing`, margin collapsing 부재, `overflow`, `position`, 단위, 상속 default | https://lynxjs.org/guide/ui/layout/index.md, https://lynxjs.org/guide/ui/styling.md, https://lynxjs.org/llms.txt |
| 3.9의 `!important`, `flex` shorthand 변경, `grid-row`/`grid-column`, `position: sticky` | https://lynxjs.org/blog/lynx-3-9.md |
| Event attribute 이름과 phase | https://lynxjs.org/guide/interaction/event-handling.md |
| Function reference, `dataset`, `currentTarget` 지침 | https://lynxjs.org/react/best-practices.md |
| `<list>` 고정 viewport, attribute, `reuse-identifier`, `recyclable` | https://lynxjs.org/api/elements/built-in/list.md |
| 자식 JS instance가 미리 생성되고 `main-thread:ref`가 정확한 점 | https://lynxjs.org/react/lifecycle.md |
| Platform별 `initData` 주입과 `useInitData`/`useGlobalProps` | https://lynxjs.org/guide/use-data-from-host-platform.md |
| `InitData`, `GlobalProps`, `NativeModules`, `IntrinsicElements`의 TypeScript augmentation | https://lynxjs.org/rspeedy/typescript.md |
| `MemoryRouter`를 쓰는 React Router v6, `<Link>` 부재 | https://lynxjs.org/react/routing/react-router.md |
| TanStack Router memory routing, `react$` alias, `isServer: false`, search-params polyfill | https://lynxjs.org/react/routing/tanstack-router.md |
| `document`/`window` 부재와 없는 text codec용 `TextCodecHelper` | https://lynxjs.org/llms.txt |
