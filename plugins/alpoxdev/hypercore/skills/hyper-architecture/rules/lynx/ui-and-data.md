# Lynx UI and Data

> Read when touching elements, styles, layout, events, lists, host-provided data, or routing in a Lynx app.

## Elements

Lynx elements are not DOM nodes. They map to iOS `UIView`, Android `ViewGroup`, HarmonyOS components, or web custom elements.

`view`, `text`, `image`, `scroll-view`, `list`/`list-item`, `page`, `frame`, `input`, `textarea`, `overlay`, `refresh`, `scroll-coordinator`, `svg`, `title-bar-view`, `viewpager`.

Three habits carried over from web React break here:

- Text must live inside `<text>`. Bare text in a `<view>` does not render.
- Inline layout is nested `<text>`, not `display: inline`.
- `<image>` is an empty tag with `src`; `auto-size` sizes it from the image instead of a declared width and height.
- `<svg>` differs from web: pass markup with `content` or a URL with `src`.

## CSS differences

Selectors, specificity, and inline `style` largely match web. The layout model does not.

| Web behavior | Lynx behavior |
|---|---|
| `display: inline`, `display: block` | Not supported as `display` values; every element is block-level by default |
| `box-sizing: content-box` | Always `border-box` |
| Margin collapsing | Does not occur |
| `overflow: scroll` | Unsupported; use `<scroll-view scroll-x>` or `scroll-y` |
| `position: fixed` relative to viewport | Fixed nodes are promoted under the root node |
| Regular properties inherit | Only CSS custom properties inherit by default |

`display` modes that do exist:

- `flex` — CSS Flexbox, but `min-content` is unsupported and the flex shrink lower bound is treated as `0px`.
- `linear` — vertical main axis with `linear-direction` and `linear-weight`.
- `grid` — no `grid-area` and no line names.
- `relative` — Android `RelativeLayout` mental model, mobile only.

`position` supports `relative`, `absolute`, and `fixed`.

Units: `rpx` is 1/750 of the configured logical width from host screen metrics. `vw` and `vh` exist; on the web target `transform-vw` and `transform-vh` can re-base them per container.

Inheritance is opt-in and its default is easy to misread. `pluginReactLynx({ enableCSSInheritance: true })` makes a fixed list inherit — `direction`, `color`, `font-*`, `letter-spacing`, `line-height`, `text-align`, `text-decoration`, `text-shadow` — and `customCSSInheritanceList` extends that list. `enableCSSInheritance` defaults to `false`, so a font set on a container does not reach a child unless you set it again or enable inheritance.

`-x-` prefixed properties expose mobile capabilities such as `-x-auto-font-size`.

Version-sensitive CSS, all requiring a matching `engineVersion`:

- `!important` requires `engineVersion` 3.9 or later.
- 3.9 changed the `flex` shorthand so an omitted `flex-basis` parses as `0%` instead of `0`.
- 3.9 added `grid-row`/`grid-column` shorthands, `position: sticky`, and the HarmonyOS motion path.

Each of those is a deployment decision, not a styling detail: raising `engineVersion` to use one raises the host floor.

## Events

The attribute name encodes both the phase and whether propagation is intercepted.

| Attribute | Behavior |
|---|---|
| `bindtap` | Bubble phase, handler runs on background |
| `catchtap` | Bubble phase, stops propagation |
| `capture-bindtap` | Capture phase |
| `capture-catchtap` | Capture phase, stops propagation |
| `global-bindtap` | Global listening, regardless of the target node |
| `main-thread:bindtap` and variants | Handler runs synchronously on the main thread |

A background handler receives plain JSON. Non-touch events fire only on the target node. `stopPropagation()` exists only inside a main-thread script; on the background thread the `catch`/`capture` naming is the mechanism.

Handler style, per the official best practices:

- Pass function references, not inline arrows. An inline arrow is re-created per render and loses the inference that makes background-only marking work.
- Read data from `dataset` rather than closing over values.
- Prefer `currentTarget` over `target` so the handler stays correct when the event originates in a child.

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

## Lists

`<list>` virtualizes and recycles. Only children in the visible area are rendered, and the width and height of `<list>` are its viewport, "so they need to be fixed values."

Required attributes: `scroll-orientation`, `list-type` (`single`, `flow`, `waterfall`), `span-count`. Every direct child is a `<list-item>` with `item-key`, which must match the `key` used to build the list.

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

Recycling controls:

- `reuse-identifier` groups structurally identical items so nodes are reused across groups. It is auto-generated per loop shape at compile time; set it explicitly when two loops should share nodes.
- `recyclable={false}` opts a node out of recycling.
- `experimental-recycle-sticky-item` is enabled by default from some `engineVersion` threshold.

The lifecycle caveat that causes real bugs: every child component's JS instance is created up front, but its real UI node is created or reused only when scrolled near. So `useEffect` and `ref` fire even when no UI node exists. Use `main-thread:ref` when the code must know whether a node is actually attached.

## Host data

The host injects `initData` and updates it:

| Platform | Initial | Update |
|---|---|---|
| iOS | `LynxView.loadTemplate(meta.initialData)` | `updateData` |
| Android | `setInitialData` on the `LynxLoadMeta.Builder` | `updateMetaData` |
| HarmonyOS | `MetaData(new TemplateData(...))` | `updateMetaData` |

Read it with `useInitData()`, which re-renders on update, or `useGlobalProps()` for `lynx.__globalProps`. `__globalProps` can be `null` or `{}` when the host does not provide it, so a consumer must handle absence.

Type the contract by augmenting the interfaces once:

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

`useInitDataChanged` and `useGlobalPropsChanged` exist for code that must react to an update rather than re-render with it.

Host data is untrusted input. Validate `initData` at the boundary like any network payload: it arrives as JSON from the host and can be absent, partial, or stale after an update.

## Routing

There is no History API and no `document`, so routing is memory-based by necessity.

- **React Router** — install v6, not v7. ReactLynx exposes the React v17 API surface, and the docs state this directly. Use `MemoryRouter`; `<Link>` and `<NavLink>` render anchors and do not apply. Navigate with `useNavigate`.
- **TanStack Router** — memory routing is required. File-based routing works through `@tanstack/router-plugin/rspack`. Alias `react$` to `@lynx-js/react/compat` so `React.startTransition` resolves, set `isServer: false` because `document` is undefined, and add `url-search-params-polyfill` in the entry.

Both are supported. Pick by the repository's existing dependency, not by preference.

A routing library inside a Lynx app is part of the Lynx target, not a second framework.

## What is not here

`document`, `window`, DOM APIs, `localStorage`, `History API`, `<Link>`. The replacements are `lynx.reload`, `lynx.createSelectorQuery`, `GlobalEventEmitter`, native modules, and custom elements. A library that depends on `window` or `document` at import time fails at load, not at call.

`TextEncoder`/`TextDecoder` are missing in PrimJS; use `TextCodecHelper` where text codec work is needed. `fetch` depends on a host-provided HTTP service, so it is not available in every embedding.

## Checklist

- [ ] All text is inside `<text>`; no bare text node exists in a `<view>`.
- [ ] No `display: inline` or `display: block` was introduced.
- [ ] No `overflow: scroll` was introduced; a `<scroll-view>` is used instead.
- [ ] A container-level font or color is not assumed to inherit unless `enableCSSInheritance` is on.
- [ ] Any `!important`, `flex` shorthand, or `position: sticky` use is matched by the `engineVersion` it requires.
- [ ] Event handlers are function references, read `dataset`, and prefer `currentTarget`.
- [ ] Every virtualized feed is a `<list>` with fixed viewport, `list-type`, `span-count`, `scroll-orientation`, and `item-key` equal to `key`.
- [ ] Code that must know whether a list row's node exists uses `main-thread:ref`.
- [ ] `initData` and `globalProps` are typed by one augmentation and validated at the boundary.
- [ ] Absent `globalProps` is handled rather than assumed.
- [ ] Routing uses memory history, and no `<Link>`, `NavLink`, or History API call remains.
- [ ] Uploads and text codec paths handle the missing `TextEncoder`/`TextDecoder` and host-dependent `fetch`.

## Sources

> Checked 2026-11-07. These statements restate the package's dated snapshot, `references/official/lynx/lynx-2026-11-07.md`, which cites the Lynx documentation read on 2026-11-07.

| Claim | Source |
|---|---|
| Element set and element-to-native mapping | https://lynxjs.org/guide/ui/elements-components.md, https://lynxjs.org/llms.txt |
| Text-in-`<text>`, `<image>` with `auto-size`, and `<svg>` `content`/`src` | https://lynxjs.org/llms.txt |
| `display` modes, `box-sizing`, no margin collapsing, `overflow`, `position`, units, and inheritance defaults | https://lynxjs.org/guide/ui/layout/index.md, https://lynxjs.org/guide/ui/styling.md, https://lynxjs.org/llms.txt |
| `!important`, the `flex` shorthand change, `grid-row`/`grid-column`, `position: sticky` in 3.9 | https://lynxjs.org/blog/lynx-3-9.md |
| Event attribute naming and phases | https://lynxjs.org/guide/interaction/event-handling.md |
| Function references, `dataset`, and `currentTarget` guidance | https://lynxjs.org/react/best-practices.md |
| `<list>` fixed viewport, attributes, `reuse-identifier`, and `recyclable` | https://lynxjs.org/api/elements/built-in/list.md |
| Child JS instances created up front and `main-thread:ref` accuracy | https://lynxjs.org/react/lifecycle.md |
| `initData` injection per platform and `useInitData`/`useGlobalProps` | https://lynxjs.org/guide/use-data-from-host-platform.md |
| TypeScript augmentation of `InitData`, `GlobalProps`, `NativeModules`, `IntrinsicElements` | https://lynxjs.org/rspeedy/typescript.md |
| React Router v6 with `MemoryRouter` and no `<Link>` | https://lynxjs.org/react/routing/react-router.md |
| TanStack Router memory routing, `react$` alias, `isServer: false`, and the search-params polyfill | https://lynxjs.org/react/routing/tanstack-router.md |
| No `document`/`window`, and `TextCodecHelper` for the missing text codecs | https://lynxjs.org/llms.txt |
