---
name: cometchat-react-v7-placement
description: "Where CometChat chat goes in a React app shell and how to wire each layout — full-screen, sidebar/split, popup/widget, or embedded in an existing page. Triggers: 'add chat as a sidebar', 'full screen chat page', 'chat popup widget', 'embed chat in my dashboard'."
license: "MIT"
compatibility: "React >=18; @cometchat/chat-uikit-react ^7 (7.1.x, verified 7.1.0)"
metadata:
  author: "CometChat"
  version: "1.1.0"
  tags: "cometchat react placement layout uikit v7"
---

> **Ground truth:** `@cometchat/chat-uikit-react@7`. Uses only components defined in `cometchat-react-v7-core`/`-components` (from live v7 docs). Status: **catalog-verified vs installed 7.1.0 (exports-only web-v7.json).** Fetch layout-specific props from the component's **`.md` twin** (`../cometchat-react-v7-core/references/docs-map.md`).

## Companion skills (read first)
- `cometchat-react-v7-core` — install, `init→login→render`, provider. This skill ASSUMES it.
- `cometchat-react-v7-components` — the component catalog this composes.

## Use this skill when
Deciding/​wiring WHERE chat lives — and either (a) **growing the core surface into the whole combined chat app** (selector tabs ↔ messages ↔ details/thread/search side panel + incoming call) when the user asks for the full app, or (b) a scoped-down sidebar/split, popup/floating widget, or embedded panel. Triggers: "build a full chat app", "add users/groups/calls tabs and a side panel", "add chat as a sidebar", "full screen chat page", "chat popup widget", "embed chat in my dashboard". Note: a plain unscoped "add chat" defaults to the production-ready CORE surface (list ↔ message pane) in `cometchat-react-v7-core` — grow to the combined app below only on request.

## Prerequisites & install
Covered by core. No new package.

## Placement patterns (BAKED) — each composes core components
- **Core surface (THE DEFAULT for an unscoped "add chat") — production-ready, but lean.** Inside `CometChatErrorBoundary` → ONE `CometChatProvider`, a **two-column** layout: a `CometChatConversations` LIST ↔ a MESSAGE pane (`CometChatMessageHeader` + `CometChatMessageList` + `CometChatMessageComposer`), sized per `../cometchat-react-v7-core/references/layout.md`, with the **thread-replies panel** and the **in-chat scoped message search** wired by DEFAULT (opt-out only) and the global conversation search bar wired-or-hidden, collapsing to one pane on mobile. One small host state object coordinates {selected conversation, which side view (thread | in-chat-search | none)}. Complete and wired — NOT a bare demo — but NOT the whole app. See the "Core-surface recipe" below.
- **Grow to the full combined app (on request) — the whole app the official sample ships.** When the user asks for the full app, grow the core surface into a **three-column** layout, all under `CometChatErrorBoundary` → ONE `CometChatProvider`: a SELECTOR column (the list for the active tab — `CometChatConversations` / `CometChatUsers` / `CometChatGroups` / `CometChatCallLogs` — + a tab bar), a MESSAGE pane, and a mutually-exclusive SIDE panel (user/group details, a thread `CometChatThreadHeader` + list/composer, or a scoped `CometChatSearch`), plus `CometChatIncomingCall` mounted at root. One host state object coordinates {active tab, selected user/group, thread parent, which side panel}. It is the UNION of the core surface + these growths — see the "Combined-app recipe (grow target)" below. Least-code = reach for these drop-ins (HOW).
- **Sidebar / split:** conversations list in a fixed side panel; the message pane fills the rest. Selection state links list → message pane. (Scoped-down variant.)
- **Popup / floating widget:** a toggle button mounts the chat panel in an overlay; keep `CometChatProvider` mounted at app root so init/login persist across open/close. (Scoped-down variant.)
- **Embedded panel:** drop the message components into an existing page region; reuse the host layout/containers. (Scoped-down variant.)

> Default to the CORE surface for a plain "add chat"; grow to the full combined app when the user asks for the whole app; honor an explicit smaller scope (the narrower three).


## Recipes (FETCH — `references/recipes.md`)
The two production recipes — full TSX + the 3-column CSS — live in `references/recipes.md` (progressive disclosure; load it when you build):
- **Core-surface recipe** — THE DEFAULT for a plain "add chat": `CometChatErrorBoundary` → one `CometChatProvider` → two-column list ↔ message pane, thread panel + in-chat scoped search wired by default, mobile one-pane collapse.
- **Combined-app recipe** — the GROW target (whole app, on request): three columns (selector tabs ↔ message pane ↔ mutually-exclusive details/thread/search side panel) + `CometChatIncomingCall`.

Both encode the same invariants — **keep them when you emit the code**:
> **Selection has THREE obligations (AUDIT-079)** — a selection that only opens a pane is a dead-end: (1) render the pane; (2) REFLECT it in the list (pass `activeConversation`/`activeUser`/`activeGroup` so the row highlights); (3) every opened side panel is CLOSEABLE (wire `onBack`/`onClose`).
> **A list-header action ("New chat"/"Create group") goes in the list's `headerView`** — which REPLACES the default header, so render the title AND the button together inside it — NOT a sibling above the list (AUDIT-083; pattern in `../cometchat-react-v7-core/references/component-props.md`).

Both satisfy the reflow-free-surface standard (`../cometchat-react-v7-core/references/layout.md`) and collapse to one pane on mobile (below). The recipes use the `useIsMobile` hook defined in the **Responsive / mobile** section below.

## Responsive / mobile — one screen at a time (MANDATORY for any multi-pane layout)
Every pattern above that shows more than one pane (full-screen two-pane, sidebar/split, list+thread/detail) MUST collapse to a SINGLE screen at a time on small viewports — a fixed side-by-side layout that squashes on a phone is a defect (`RULES.md` §14), not a style choice. The kit has **no responsive shell** (no `WithMessages`/`CometChatUI`); you compose it from the same selection state, gated by a breakpoint.
- **Mobile = a navigation stack:** conversations list → tap a conversation → the message pane REPLACES the list full-screen → tap the header → the profile/thread panel REPLACES the message pane. Wide viewport → the SAME state renders side-by-side.
- **Reuse the built-in back button (don't hand-roll one):** `CometChatMessageHeader` ships `hideBackButton` (default `false`) + `onBack()`. On mobile wire `onBack` to clear the selection (pop to the list) and keep the button visible; on wide set `hideBackButton` (the list is always there).

```tsx
// SSR-guarded breakpoint hook
function useIsMobile(query = "(max-width: 768px)") {
  const read = () => typeof window !== "undefined" && window.matchMedia(query).matches;
  const [m, setM] = useState(read);
  useEffect(() => {
    const mq = window.matchMedia(query);
    const on = () => setM(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, [query]);
  return m;
}

// Mobile: render exactly ONE pane based on state; wide: render them side-by-side.
const isMobile = useIsMobile();
if (isMobile) {
  if (detail && selected) return <DetailOrThread onClose={() => setDetail(null)} />;
  if (selected) return (
    <MessagePane>
      <CometChatMessageHeader {...target} hideBackButton={false} onBack={() => setSelected(null)} />
      {/* list + composer */}
    </MessagePane>
  );
  return <CometChatConversations onItemClick={pick} />;   // list only
}
// wide → the two/three-pane layout, header with hideBackButton
```
Native (RN/Flutter): use the platform navigator (stack navigation) — one screen per route — not a web split view.

## Layout wiring per placement
- **Every placement satisfies the reflow-free-surface standard (`../cometchat-react-v7-core/references/layout.md`)** — pin a content-INDEPENDENT height (full-screen → `100dvh`; sidebar/split → the panes take a viewport or flex/grid-supplied height; popup/embedded → a fixed height e.g. `600px` or a sized grid/flex cell — **never `min-height`/`auto`**), prepare the ancestor chain, and size the columns with `min-height:0`/`overflow:hidden`. The kit fills its parent, so a content-driven container both collapses the chat to ~0px AND grows-into-place as content loads (the two named failure modes).
- Keep `CometChatProvider` at a stable ancestor (not remounted per route/toggle) so init+login survive navigation.
- Manage the selected conversation/user/group in host state and pass it to the message components. Fetch the exact selection props from the component's `.md` twin (`../cometchat-react-v7-core/references/docs-map.md`).
- Reuse the app's existing routing/layout; add wiring, never rewrite (`RULES.md`).
- **Open an overlay/companion IN the pane its trigger lives in — not full-screen (AUDIT-014).** Search opened from the `CometChatConversations` search bar (`onSearchBarClicked` → `CometChatSearch`) renders **in the conversations list column, over the list** — the message pane stays visible; `onBack`/result-click returns to the list. Do NOT take over the whole screen (it hides the conversation the user was reading). Header search (`onSearchOptionClicked`, scoped by `uid`/`guid`) opens the same way. A full-screen replacement is correct ONLY on a **mobile single-pane** (§ responsive), where the search IS the list-level screen. Same principle for any pane-rooted affordance (thread/profile open in the side panel, not full-screen on desktop).

```tsx
// Wide: the LEFT column shows search when open, else the list — message pane stays.
const listColumn = searchOpen
  ? <CometChatSearch onBack={() => setSearchOpen(false)} onConversationClicked={pick} onMessageClicked={jump} />
  : <CometChatConversations showSearchBar onSearchBarClicked={() => setSearchOpen(true)} onItemClick={pick} />;
// <aside className="list-column">{listColumn}</aside> <main>{messagePane}</main>
// Mobile (single-pane): if (searchOpen) render <CometChatSearch/> full-screen (it's the list screen).
```

## Common pitfalls (BAKED)
- Remounting `CometChatProvider` on every route/toggle (re-triggers init/login). Rendering the message pane before a conversation is selected. Nesting multiple providers.
- **Shipping a fixed side-by-side layout with no small-viewport collapse** — the #1 layout defect. On a phone the list + message panes squash and tapping a conversation does nothing visible. Always add the mobile single-pane branch above and wire the header's built-in `onBack` (AUDIT-011).
- **Not wrapping the surface in `CometChatErrorBoundary`** — a render error in any kit component then blanks the whole page (white screen) instead of showing a localized fallback + retry. Both recipes above wrap the surface; keep it.
- **A surface that grows into place as content loads (load-transition reflow)** — small while the list loads, then jumps to full size. The box is content-driven, not pinned: satisfy `layout.md` (pinned `100dvh`, prepared ancestor chain, `min-height:0` columns) and let the kit's own `loadingView`/`emptyView` fill the pinned box — don't gate the surface behind your own placeholder→chat swap (AUDIT-023).
- **Over-delivering the whole combined app on a plain "add chat"** — the default is the Core-surface recipe (list ↔ message pane); grow to the Combined-app recipe (selector tabs + side panel + incoming call) only when the user asks for the whole app.

## Verify it works
Chat renders in the chosen layout inside a `CometChatErrorBoundary`, and on a narrow viewport it collapses to ONE pane at a time (list → message → back) — no squashed side-by-side panes on a phone. Default "add chat" ⇒ the Core-surface recipe (list ↔ message pane, sized, affordances wired-or-hidden); the whole combined app (tabs + side panel + incoming call) is the grow target for an explicit full-app ask.

**Close (after it builds):** end with the shared 3-option selectable menu and WAIT for the pick — **① add another feature** (suggest a few not-yet-wired) · **② customize theming** · **③ test it manually** (stop; let the user check). Same contract as the `cometchat-react-v7-core` close (`RULES.md` §19).
