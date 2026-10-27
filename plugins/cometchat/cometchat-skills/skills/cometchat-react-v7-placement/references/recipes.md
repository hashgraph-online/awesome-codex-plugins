# Placement recipes — `cometchat-react-v7-placement`

The two production placement recipes for the React v7 UI Kit, loaded on demand (the SKILL entry carries the pattern matrix + invariants; this file carries the full code). Every symbol is catalog-verified vs installed 7.1.0 and the compositions compile against 7.1.0. Both recipes use the `useIsMobile` hook from the **Responsive / mobile** section of `../SKILL.md`.

## Core-surface recipe (BAKED) — THE DEFAULT for an unscoped "add chat" (production-ready, lean)
`CometChatErrorBoundary` wraps the surface; one `CometChatProvider` at a stable ancestor; a small state object drives a `CometChatConversations` LIST ↔ a MESSAGE pane; the **thread-replies panel is wired by DEFAULT** (opt-out only) and the search affordance is wired-or-hidden; it collapses to one pane on mobile. No selector tabs, no details/search side panel, no incoming call — those are the GROWTHS (see the Combined-app recipe below); the thread panel, however, is part of the default surface. Uses the same `useIsMobile` hook + column CSS defined further down.

```tsx
import { useReducer } from "react";
import {
  CometChatErrorBoundary,
  CometChatConversations, CometChatMessageHeader, CometChatMessageList,
  CometChatMessageComposer, CometChatThreadHeader, CometChatSearch,
} from "@cometchat/chat-uikit-react";
import { CometChat } from "@cometchat/chat-sdk-javascript";

// ONE small state object: the selected conversation + which side view is open.
type Side = "none" | "thread" | "search" | "chat-search";  // "search"=GLOBAL (over the list column); "chat-search"=IN-CHAT search SCOPED to the open chat (side panel) — never one shared state (AUDIT-041/044)
type S = { user?: CometChat.User; group?: CometChat.Group; thread?: CometChat.BaseMessage; side: Side };
type A =
  | { t: "user"; v?: CometChat.User } | { t: "group"; v?: CometChat.Group }
  | { t: "thread"; v?: CometChat.BaseMessage } | { t: "side"; v: Side };
function reducer(s: S, a: A): S {
  switch (a.t) {
    case "user": return { ...s, user: a.v, group: undefined, side: "none", thread: undefined };
    case "group": return { ...s, group: a.v, user: undefined, side: "none", thread: undefined };
    case "thread": return { ...s, thread: a.v, side: "thread" };
    case "side": return { ...s, side: a.v };
  }
}

function CoreChatSurface() {
  const isMobile = useIsMobile();                 // the SSR-guarded breakpoint hook below
  const [s, dispatch] = useReducer(reducer, { side: "none" });
  const target = s.user ? { user: s.user } : s.group ? { group: s.group } : undefined;
  const hasChat = !!target;

  const list = (
    <aside className="list-column">
      {s.side === "search" ? (
        // GLOBAL search — OVER the list column (AUDIT-014), NO uid/guid; wire the round-trip (AUDIT-017)
        <CometChatSearch
          onBack={() => dispatch({ t: "side", v: "none" })}
          onConversationClicked={(e) => {
            const w = e.conversation.getConversationWith();
            if (w instanceof CometChat.User) dispatch({ t: "user", v: w });
            else if (w instanceof CometChat.Group) dispatch({ t: "group", v: w });
          }}
          onMessageClicked={(e) => {/* select the conversation of e.message, then jump to it */}}
        />
      ) : (
        <CometChatConversations
          onItemClick={(c) => {
            const e = c.getConversationWith();
            if (e instanceof CometChat.User) dispatch({ t: "user", v: e });
            else if (e instanceof CometChat.Group) dispatch({ t: "group", v: e });
          }}
          onSearchBarClicked={() => dispatch({ t: "side", v: "search" })}   // GLOBAL search → OVER this column (or set showSearchBar={false})
        />
      )}
    </aside>
  );

  const messagePane = target && (
    <main className="message-pane">
      <CometChatMessageHeader
        {...target}
        hideBackButton={!isMobile}
        onBack={() => dispatch({ t: "user", v: undefined })}
        showSearchOption
        onSearchOptionClicked={() => dispatch({ t: "side", v: "chat-search" })}  // IN-CHAT search → SCOPED (side panel), NOT global
      />
      <CometChatMessageList {...target} onThreadRepliesClick={(m) => dispatch({ t: "thread", v: m })} />
      <CometChatMessageComposer {...target} />
      {/* call buttons (header) + attach/emoji/voice (composer) are built-in defaults — pass nothing */}
    </main>
  );

  // thread + in-chat (scoped) search → side panel; GLOBAL search → over the list column (desktop) / full-screen (mobile single pane)
  const sidePanel = hasChat && s.side !== "none" && s.side !== "search" && (   // "search" (GLOBAL) lives in the list column, not here
    <aside className="side-column">
      {s.side === "thread" && s.thread && (
        <>
          <CometChatThreadHeader parentMessage={s.thread} onClose={() => dispatch({ t: "side", v: "none" })} />
          <CometChatMessageList {...target!} parentMessageId={s.thread.getId()} />
          <CometChatMessageComposer {...target!} parentMessageId={s.thread.getId()} />
        </>
      )}
      {s.side === "chat-search" && (   // IN-CHAT search — SCOPED to the open conversation (uid/guid + searchIn), NOT global (AUDIT-041)
        <CometChatSearch
          uid={s.user?.getUid()}
          guid={s.group?.getGuid()}
          searchIn={["messages"]}
          onBack={() => dispatch({ t: "side", v: "none" })}
          onMessageClicked={(e) => {/* jump to e.message in the open chat */}}
        />
      )}
    </aside>
  );

  // wide → list + message (+ side); mobile → ONE pane at a time
  return (
    <CometChatErrorBoundary>
      <div className="cc-app" style={{ height: "100dvh", width: "100%", display: "flex", overflow: "hidden" }}>
        {(!isMobile || !hasChat) && list}
        {(!isMobile || hasChat) && (isMobile && s.side !== "none" ? sidePanel : messagePane)}
        {!isMobile && sidePanel}
      </div>
    </CometChatErrorBoundary>
  );
}
```
Mount `<CoreChatSurface/>` inside your `CometChatProvider` (kept at a stable ancestor). **Ship the same column CSS below** — the root sizing alone leaves the columns collapsed. Every symbol is catalog-verified and the composition compiles against 7.1.0. To GROW this into the whole app (selector tabs + details/thread/search side panel + incoming call), see the Combined-app recipe next.

## Combined-app recipe (BAKED) — the GROW target (load on request, when the user wants the whole app)
Grow the core surface into the whole app. One `CometChatProvider` at a stable ancestor, wrapped in `CometChatErrorBoundary`; one state object drives three columns; every affordance sits on the component's built-in trigger (never a hand-rolled button); the side panel is a single mutually-exclusive slot. (For a plain "add chat", emit the leaner Core-surface recipe above instead.)
> **Selection has THREE obligations, not one (AUDIT-079) — a selection that only opens a pane is a composition dead-end:** (1) **render** the target pane; (2) **REFLECT** it in the list as the active item — pass `activeConversation` / `activeUser` / `activeGroup` back to the list so the selected row highlights (the kit ships these props; without them the user can't tell what's selected); (3) make every opened side panel **CLOSEABLE** — wire `onBack`/`onClose` AND make sure a close CONTROL actually renders. Most components render their own back/close button (thread header `onClose`, search `onBack`), but **do NOT assume it** — `CometChatGroupMembers` in 7.2.0 renders NO default back button (only the "Members" title), so the host must supply the close via `headerView` (AUDIT-203). An opened panel with no *reachable* close is the SAME defect as an unwired trigger — §12 round-trip. All three are in the recipe below.
> **A list-header action ("New chat" / "Create group") goes in the list's `headerView`, NOT a sibling above it — and re-render the title (AUDIT-083).** `CometChatConversations`/`CometChatGroups`/`CometChatUsers` only expose `headerView`, which REPLACES the whole default header (including the "Chats"/"Groups"/"Users" title) — so render the title AND your button together inside it. Placing the button ABOVE the list is the sibling-on-top defect (§13 / `../cometchat-react-v7-core/references/component-props.md` → "List-header actions" for the exact pattern).
> **A Calls tab must be GATED ON REAL AVAILABILITY, not baked-always-on (AUDIT-162).** `CometChatCallLogs` shows the kit's raw "OOPS!" screen when call-logs are unavailable — and, verified live, it renders that from its OWN INTERNAL error state WITHOUT throwing, so a host `CometChatErrorBoundary`/`fallbackView` CANNOT override it. A fallbackView is NOT the remedy. The recipe therefore gates the Calls TAB on a `callLogsAvailable` flag and omits the tab unless call-logs is CONFIRMED available. Two INDEPENDENT gates: `callingEnabled` (`uiKit:{callsSDK:{}}`) governs the header call BUTTONS; `callLogsAvailable` (a SEPARATE plan/capability gate — enabled ≠ available; proven live) governs the Calls-logs tab. Confirm availability with a one-time SDK probe you own (CallLogRequestBuilder → fetchNext()) or your known plan; default the tab OFF.

```tsx
import { useReducer } from "react";
import {
  CometChatErrorBoundary,
  CometChatConversations, CometChatUsers, CometChatGroups, CometChatCallLogs,
  CometChatMessageHeader, CometChatMessageList, CometChatMessageComposer,
  CometChatThreadHeader, CometChatSearch, CometChatGroupMembers, CometChatIncomingCall,
} from "@cometchat/chat-uikit-react";
import { CometChat } from "@cometchat/chat-sdk-javascript";

// ONE state object coordinates the whole app (tab · selection · thread · side panel).
type Side = "none" | "details" | "thread" | "search" | "chat-search";  // "search"=GLOBAL (over the list column); "chat-search"=IN-CHAT search SCOPED to the open chat (side panel) — NEVER one shared state (AUDIT-041/044)
// `conversation` is kept ALONGSIDE user/group so the Conversations list can REFLECT the selection
// (activeConversation) — selection has 3 obligations: render the pane, HIGHLIGHT the active item, and
// make every opened panel CLOSEABLE (RULES §12; AUDIT-079).
type S = { tab: "chats"|"users"|"groups"|"calls"; user?: CometChat.User; group?: CometChat.Group; conversation?: CometChat.Conversation; thread?: CometChat.BaseMessage; side: Side };
type A =
  | { t: "tab"; v: S["tab"] } | { t: "user"; v?: CometChat.User; conv?: CometChat.Conversation } | { t: "group"; v?: CometChat.Group; conv?: CometChat.Conversation }
  | { t: "thread"; v?: CometChat.BaseMessage } | { t: "side"; v: Side };
function reducer(s: S, a: A): S {
  switch (a.t) {
    case "tab": return { ...s, tab: a.v };
    case "user": return { ...s, user: a.v, group: undefined, conversation: a.conv, side: "none", thread: undefined };
    case "group": return { ...s, group: a.v, user: undefined, conversation: a.conv, side: "none", thread: undefined };
    case "thread": return { ...s, thread: a.v, side: "thread" };
    case "side": return { ...s, side: a.v };
  }
}

// `callLogsAvailable` = is the CALL-LOGS capability actually available on this app's PLAN? Compute it in
// the app shell and pass it in. It is SEPARATE from "calling enabled": enabling calling
// (`uiKit:{callsSDK:{}}`, which surfaces the header call buttons — that happens at init, NOT here) does
// NOT imply call-logs is available (proven live). The Calls-logs TAB is gated on THIS flag because
// `CometChatCallLogs` shows the kit's internal "OOPS!" (which no host fallbackView can override) when
// call-logs is unavailable. Compute it with a one-time SDK probe you own (CallLogRequestBuilder with the
// logged-in USER's auth token → fetchNext(); see `useCallLogsAvailable` below) or your known plan; default
// false so a plain app never ships a dead-ending Calls tab.
function CombinedChatApp({ callLogsAvailable = false }: { callLogsAvailable?: boolean }) {
  const isMobile = useIsMobile();                 // the SSR-guarded breakpoint hook below
  const [s, dispatch] = useReducer(reducer, { tab: "chats", side: "none" });
  const target = s.user ? { user: s.user } : s.group ? { group: s.group } : undefined;
  const hasChat = !!target;
  // The tabs to render — Calls is included ONLY when call-logs is CONFIRMED AVAILABLE (a real gate, not a
  // comment, and NOT merely "calling enabled" — enabled ≠ available).
  const tabs: S["tab"][] = callLogsAvailable
    ? ["chats", "users", "groups", "calls"]
    : ["chats", "users", "groups"];

  const selector = (
    <aside className="list-column">
      {s.side === "search" ? (
        // GLOBAL search (all conversations + messages) — renders OVER the list column (AUDIT-014), NO uid/guid;
        // wire the FULL round-trip (AUDIT-017): onBack + result clicks close it and select the hit.
        <CometChatSearch
          onBack={() => dispatch({ t: "side", v: "none" })}
          onConversationClicked={(e) => {
            const w = e.conversation.getConversationWith();
            if (w instanceof CometChat.User) dispatch({ t: "user", v: w });
            else if (w instanceof CometChat.Group) dispatch({ t: "group", v: w });
          }}
          onMessageClicked={(e) => {/* select the conversation of e.message, then jump to it */}}
        />
      ) : (
        <>
          {/* Tab bar — render the GATED `tabs` (Calls absent unless calling is enabled). This is the
              real wiring, not a TODO: a button per tab that dispatches the tab change. */}
          <nav className="cc-tabbar">
            {tabs.map((t) => (
              <button
                key={t}
                className={s.tab === t ? "cc-tab cc-tab--active" : "cc-tab"}
                onClick={() => dispatch({ t: "tab", v: t })}
              >
                {t}
              </button>
            ))}
          </nav>
          {s.tab === "chats" && (
            <CometChatConversations
              activeConversation={s.conversation}   /* REFLECT the selection — highlights the open chat in the list (AUDIT-079) */
              onItemClick={(c) => {
                const e = c.getConversationWith();
                if (e instanceof CometChat.User) dispatch({ t: "user", v: e, conv: c });
                else if (e instanceof CometChat.Group) dispatch({ t: "group", v: e, conv: c });
              }}
              onSearchBarClicked={() => dispatch({ t: "side", v: "search" })}   // GLOBAL search → OVER this column
            />
          )}
          {s.tab === "users" && <CometChatUsers activeUser={s.user} onItemClick={(u) => dispatch({ t: "user", v: u })} />}
          {s.tab === "groups" && <CometChatGroups activeGroup={s.group} onItemClick={(g) => dispatch({ t: "group", v: g })} />}
          {/* Calls tab — GATE ON REAL AVAILABILITY, not merely "calling enabled" (AUDIT-063 + AUDIT-162).
              `CometChatCallLogs` renders the kit's raw "OOPS! …" screen whenever call-logs are unavailable,
              and — verified live — it does so from its OWN INTERNAL error state WITHOUT THROWING, so an
              outer `CometChatErrorBoundary`/`fallbackView` CANNOT override it (fallbackView never fires).
              A `fallbackView` is therefore NOT the remedy here. Two facts to design around:
                (1) Calling being ENABLED (the calls skill's `uiKit:{callsSDK:{}}`, which surfaces the header
                    Voice/Video buttons) is NECESSARY to offer the tab but NOT SUFFICIENT — call-logs is a
                    SEPARATE plan/capability gate (proven live: header call buttons present, tab still "OOPS").
                (2) There is NO host-side way to replace the internal "OOPS!". So the ONLY reliable
                    protection is to NOT surface the Calls tab until call-logs is confirmed AVAILABLE.
              So gate `callLogsAvailable` on an actual availability check (a one-time SDK probe you own —
              build a CallLogRequestBuilder with the logged-in USER's auth token (NOT a generateToken()
              call token) → fetchNext(), and only flip the flag on success), or on your known
              plan. Compute it in the app shell and pass it down as `callLogsAvailable`. */}
          {callLogsAvailable && s.tab === "calls" && <CometChatCallLogs />}
        </>
      )}
    </aside>
  );

  const messagePane = target && (
    <main className="message-pane">
      <CometChatMessageHeader
        {...target}
        hideBackButton={!isMobile}
        onBack={() => dispatch({ t: "user", v: undefined })}
        onItemClick={() => dispatch({ t: "side", v: "details" })}       // header → details side panel
        showSearchOption
        onSearchOptionClicked={() => dispatch({ t: "side", v: "chat-search" })}  // IN-CHAT search → SCOPED to THIS chat (side panel), NOT global
      />
      <CometChatMessageList {...target} onThreadRepliesClick={(m) => dispatch({ t: "thread", v: m })} />
      <CometChatMessageComposer {...target} />
      {/* call buttons (header) + attach/emoji/voice (composer) are built-in defaults — pass nothing */}
    </main>
  );

  const sidePanel = hasChat && s.side !== "none" && s.side !== "search" && (   // "search" (GLOBAL) lives in the selector column, not here
    <aside className="side-column">
      {s.side === "thread" && s.thread && (
        <>
          <CometChatThreadHeader parentMessage={s.thread} onClose={() => dispatch({ t: "side", v: "none" })} />
          <CometChatMessageList {...target!} parentMessageId={s.thread.getId()} />
          <CometChatMessageComposer {...target!} parentMessageId={s.thread.getId()} />
        </>
      )}
      {s.side === "chat-search" && (   // IN-CHAT search — SCOPED to the open conversation (uid/guid + searchIn), NOT global (AUDIT-041)
        <CometChatSearch
          uid={s.user?.getUid()}
          guid={s.group?.getGuid()}
          searchIn={["messages"]}
          onBack={() => dispatch({ t: "side", v: "none" })}
          onMessageClicked={(e) => {/* jump to e.message in the open chat */}}
        />
      )}
      {s.side === "details" && s.group && (
        // WIRE THE CLOSE — the HOST OWNS IT with its OWN chrome bar, as a SIBLING ABOVE the component
        // (AUDIT-203). Verified vs installed 7.2.0: CometChatGroupMembers renders NO default back button
        // (its default header is title-only; `CometChatGroupMembersRootProps` has `onBack?` but NO
        // hideBackButton/showBackButton) AND it does NOT honor a `headerView` slot at runtime — it renders
        // only `__search-bar` + `__list`, so a `headerView` back button never appears (re-verified live).
        // Therefore the ONLY reliable close is a HOST SIBLING chrome bar, not the component's slot. Keep
        // `onBack` too (harmless; fires if a future kit renders its own back button).
        <>
          <div className="cc-side-header" style={{ display: "flex", alignItems: "center", gap: 8, padding: "0 12px", height: 56, flex: "0 0 auto" }}>
            <button aria-label="Back" onClick={() => dispatch({ t: "side", v: "none" })}>←</button>
            <h3 style={{ margin: 0 }}>Members</h3>
          </div>
          <div style={{ flex: "1 1 0", minHeight: 0 }}>
            <CometChatGroupMembers group={s.group} onBack={() => dispatch({ t: "side", v: "none" })} />
          </div>
        </>
      )}
      {/* user details = host-composed from CometChatAvatar + SDK (no single kit drop-in) — it MUST include
          its OWN close control that dispatches side:"none" (same round-trip rule; don't leave it dead-ending). */}
    </aside>
  );

  // wide → 3 columns; mobile → ONE pane at a time (side replaces message replaces list)
  return (
    <CometChatErrorBoundary>
      <div className="cc-app" style={{ height: "100dvh", width: "100%", display: "flex", overflow: "hidden" }}>
        {(!isMobile || !hasChat) && selector}
        {(!isMobile || hasChat) && (isMobile && s.side !== "none" ? sidePanel : messagePane)}
        {!isMobile && sidePanel}
        <CometChatIncomingCall />
      </div>
    </CometChatErrorBoundary>
  );
}
```
**Ship this CSS too — the 3-column layout is NOT complete without it, and it must satisfy the reflow-free-surface standard (`../cometchat-react-v7-core/references/layout.md`: prepared ancestor chain · pinned `100dvh` · `min-height:0` columns).** Sizing the root alone leaves the columns collapsing to content and growing as it loads. Values proven from the official sample app (`styles/App.css`):
```css
/* (a) prepare/reset the ancestor chain FIRST — see layout.md */
html, body, #root { height: 100%; margin: 0; padding: 0; }
#root { max-width: none; text-align: left; display: block; }
body { display: block; place-items: normal; }
.cc-app { overflow: hidden; }              /* (b) cap to the pinned 100dvh on the wrapper */
.cc-app * { box-sizing: border-box; }
/* (c) selector + side panel: fixed-ish width, full height, min-height:0 = scroll not grow */
.cc-app .list-column,
.cc-app .side-column { display: flex; flex-direction: column; height: 100%; width: 30%; max-width: 420px; flex-shrink: 0; min-height: 0; }
.cc-app .message-pane { display: flex; flex-direction: column; height: 100%; flex: 1; min-width: 0; min-height: 0; overflow: hidden; }
/* let the kit list fill the column below your tab bar */
.cc-app .list-column .cometchat-list__body,
.cc-app .side-column .cometchat-list__body { flex: 1; min-height: 0; }
/* host tab bar (your chrome, not the kit) */
.cc-tabbar { display: flex; gap: 2px; padding: 6px; flex: 0 0 auto; }
.cc-tab { flex: 1; text-transform: capitalize; padding: 8px 4px; border: 0; border-radius: 6px; background: transparent; cursor: pointer; font: inherit; }
.cc-tab--active { background: var(--cometchat-primary-color, #6851d6); color: #fff; }
/* friendly "unavailable" fallback for a capability-gated surface (e.g. call-logs) — NOT the raw kit "OOPS!" */
.cc-unavailable { padding: 24px; text-align: center; color: var(--cometchat-text-color-secondary, #727272); }
```
Mount `<CombinedChatApp callLogsAvailable={/* call-logs confirmed available */} />` inside your `CometChatProvider` (kept at a stable ancestor). It defaults `false`: the header call buttons are enabled at INIT (`uiKit:{callsSDK:{}}` in the calls skill), not via a prop here; `callLogsAvailable` (a SEPARATE plan gate — calling-enabled ≠ call-logs-available) governs the Calls-logs tab, which is omitted unless confirmed available so a plain app never ships a dead-ending "OOPS!" tab. A host `CometChatErrorBoundary`/`fallbackView` does NOT help for `CometChatCallLogs` — it renders its own internal "OOPS!" without throwing (verified live), so gating is the only reliable protection. Every symbol above is catalog-verified and the composition compiles against 7.1.0. Full composition rationale + the complete placement map: the factory's `FULL-APP-BLUEPRINT.md`.

### The `callLogsAvailable` probe (BAKED — with the EXACT imports, AUDIT-204)
Compute `callLogsAvailable` with a one-time SDK probe you own, then pass it into `<CombinedChatApp>`. **Import discipline: `CallLogRequestBuilder` is NOT a named export of `@cometchat/calls-sdk-javascript` — it is a STATIC on the `CometChatCalls` default-export class** (verified vs calls-sdk 5.0.5 `dist/index.d.ts`: `static CallLogRequestBuilder: typeof CallLogRequestBuilder`; the package default-exports the `CometChatCalls` namespace). A naive `import { CallLogRequestBuilder } from "@cometchat/calls-sdk-javascript"` FAILS to compile (TS2614). Use the static. **`setAuthToken` takes the logged-in USER's auth token** — the call-log request sends it as the `authToken` header, exactly as the kit's own `CometChatCallLogs` does (`loggedInUser.getAuthToken()`); a `generateToken()` CALL/session token is the wrong credential, so a probe built on it always fails and the tab never shows. And on a RESTORED session `initFromSettings` does not await the Calls-SDK init, so wait (bounded) for `CometChatUIKit.isCallingReady()` before probing:
```tsx
import { useEffect, useState } from "react";
import { CometChatUIKit } from "@cometchat/chat-uikit-react";
import { CometChatCalls } from "@cometchat/calls-sdk-javascript";   // ← CallLogRequestBuilder is a STATIC on this, NOT a named import

export function useCallLogsAvailable(): boolean {
  const [available, setAvailable] = useState(false);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        for (let i = 0; i < 40 && !cancelled && !CometChatUIKit.isCallingReady(); i++) await new Promise((r) => setTimeout(r, 250));
        const me = CometChatUIKit.getLoggedInUser();
        if (cancelled || !me || !CometChatUIKit.isCallingReady()) return;   // calling off / SSR / not ready ⇒ stays OFF
        const req = new CometChatCalls.CallLogRequestBuilder()      // ← static access — the ONLY form that compiles
          .setLimit(1).setAuthToken(me.getAuthToken()).build();     // USER auth token — NOT a generateToken() call token
        await req.fetchNext();                                      // resolves ⇒ call-logs available; throws/402 ⇒ not on plan
        if (!cancelled) setAvailable(true);
      } catch {
        if (!cancelled) setAvailable(false);                        // default OFF ⇒ no dead-ending Calls tab
      }
    })();
    return () => { cancelled = true; };
  }, []);
  return available;
}
// then: const callLogsAvailable = useCallLogsAvailable(); <CombinedChatApp callLogsAvailable={callLogsAvailable} />
```
