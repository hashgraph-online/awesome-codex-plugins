# lifecycle — init, login, provider (React v7)

## Init must happen once (StrictMode double-init)
Init is async and must complete before any `CometChat*` component renders. React 18 StrictMode runs effects twice in dev, so guard by caching the init **PROMISE — NOT a boolean**. A boolean set BEFORE `await init()` lets StrictMode's second call see `true` and return BEFORE init has actually resolved → the app renders / logs in against an un-initialized SDK and throws **"CometChatUIKit: Not initialized"** on first load (AUDIT-047). Cache the promise so every concurrent caller awaits the SAME init (mirrors the login in-flight promise below):
```typescript
// initFromSettings resolves to CometChat.User | null (a resumed session or null), so type the cached
// promise as Promise<unknown> — assigning it into Promise<void> is a TS2322 error under strict TS.
let initPromise: Promise<unknown> | null = null;
function initCometChat(): Promise<unknown> {
  if (!APP_ID || !REGION || !AUTH_KEY) throw new Error("CometChat credentials empty — check .env + prefix (VITE_/NEXT_PUBLIC_/PUBLIC_) and restart the dev server.");
  if (!initPromise) {
    // initFromSettings sets integrationSource="ai-agent" for telemetry attribution (routes the Calls SDK too) — AUDIT-084.
    initPromise = CometChatUIKit.initFromSettings({   // cache the PROMISE (never a boolean flipped before the await)
      appId: APP_ID, region: REGION,
      credentials: { authKey: AUTH_KEY },                        // dev only — prod: server-minted auth token (login below)
      chatSDK: { presenceSubscription: { type: "ALL_USERS" } },  // = subscribePresenceForAllUsers()
    });
  }
  return initPromise;                              // 2nd StrictMode call awaits the SAME init → never early-returns before ready
}
```
Call init in `useEffect` (Next.js/Astro/React Router SSR) or at the entry file before `createRoot` (Vite/CRA — `main.tsx` only runs in the browser). Never call init during render (infinite re-render).

## Login — safe SEQUENTIALLY, not CONCURRENTLY
Sequential: a second `login()` after the first completes returns the cached user. Concurrent: a second `login()` while the first is in-flight throws **"Please wait until the previous login request ends."** — exactly what StrictMode's double-effect triggers. Guard with a module-level in-flight promise:
```typescript
let loginInFlight: Promise<unknown> | null = null;
async function ensureLoggedIn(uid: string, authToken?: string) {
  const existing = CometChatUIKit.getLoggedInUser();   // SYNC getter, capital "In" — no await (see the note below)
  if (existing && existing.getUid?.() === uid) return;         // same user → done
  if (existing) await CometChatUIKit.logout();                 // switching accounts needs explicit logout
  if (loginInFlight) { await loginInFlight; return; }          // concurrent → reuse pending promise
  loginInFlight = authToken ? CometChatUIKit.loginWithAuthToken(authToken) : CometChatUIKit.login(uid);
  try { await loginInFlight; } finally { loginInFlight = null; }
}
```
Call `ensureLoggedIn()` from the provider/effect, not `login()` directly. A cached promise (not a boolean) lets all callers `await` the same request.

## Dev-only: `ensureDevUser` — create-if-missing a sample user, then log in (a guaranteed valid session)
For a fast dev start you can't reliably pre-check whether `cometchat-uid-1` exists (`getUser` needs a session, and you only have the Auth Key — not the REST key for a server-side lookup). So **create-if-missing then login** — one deterministic path, valid on any app (fresh/sample/empty/custom), no 5-way probe. **DEV-ONLY** — prod uses a real user + a server-minted token via `loginWithAuthToken`.
```typescript
import { CometChat } from "@cometchat/chat-sdk-javascript";   // for CometChat.User
// CometChatUIKit.createUser(user) uses the Auth Key configured in init — verified vs 7.1.0.
async function ensureDevUser(uid = "cometchat-uid-1", name = "Demo User") {
  try {
    const u = new CometChat.User(uid);
    u.setName(name);
    await CometChatUIKit.createUser(u);          // creates it if missing (dev; uses the init Auth Key)
  } catch {
    // already-exists is EXPECTED and fine — the user is there; fall through to login.
  }
  await ensureLoggedIn(uid);                      // now guaranteed to succeed
}
```

## Get the current logged-in UID (never hardcode)
```typescript
import { CometChatUIKit } from "@cometchat/chat-uikit-react";
import { CometChat } from "@cometchat/chat-sdk-javascript";
// preferred — sync, after login completes (most app code):
const myUid = CometChatUIKit.getLoggedInUser()?.getUid();      // UI Kit, capital "In" → CometChat.User | null (sync)
// fallback — async, when the SDK was initialized directly / session may still be restoring:
const myUid2 = (await CometChat.getLoggedinUser())?.getUid();  // SDK namespace, lowercase "in" → Promise<CometChat.User | null>
```
> Two DIFFERENT methods on two DIFFERENT owners: the **sync** getter is `CometChatUIKit.getLogged**In**User()` (UI Kit, capital "In"); the **async** getter is `CometChat.getLogged**in**User()` (SDK namespace, lowercase "in"). `CometChatUIKit` has NO async `getLoggedinUser` — that was a v6 assumption. Verified against installed 7.1.0 (`index.d.ts` line 617 + the kit's own doc note).

## Production login
Fetch a per-user token from YOUR backend (CometChat REST API with your server AUTH_TOKEN), then `await CometChatUIKit.loginWithAuthToken(token)`. Never hardcode auth keys in shipped source.

## Logout
`await CometChatUIKit.logout();` — clears the local session; call on app sign-out.

## Reusable provider
Wrap init + login + ready-gate in a `CometChatProvider` so components mount only after login resolves; keep the module-level `initPromise`/`loginInFlight` promises (cache the PROMISE, not a boolean — AUDIT-047) so StrictMode doesn't double-fire or race ahead of a not-yet-resolved init. Mount the provider at a STABLE ancestor (not remounted per route/toggle) so init/login survive navigation. (Pretty-print errors — don't `String(error)` raw; surface the code/message.)
