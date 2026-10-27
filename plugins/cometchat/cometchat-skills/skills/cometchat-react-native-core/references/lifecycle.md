# lifecycle — init → login → render on React Native

## The invariant
**`init()` must resolve before `login()`. `login()` must resolve before any component renders.**
Out of order fails **silently** — a blank screen, no exception.

## Init with `initFromSettings` (not the classic init)
`initFromSettings` persists `integrationSource="ai-agent"` for telemetry attribution; the classic
`init` does not (AUDIT-084), and a machine gate enforces this.

```tsx
import { CometChatUIKit } from "@cometchat/chat-uikit-react-native";
import { CometChat } from "@cometchat/chat-sdk-react-native";

const settings: CometChat.CometChatSettings = {
  appId: APP_ID,
  region: REGION,
  credentials: { authKey: AUTH_KEY },       // dev only
  chatSDK: {
    presenceSubscription: { type: "ALL_USERS" },
    autoEstablishSocketConnection: true,
  },
};
```

Presence lives **inside** `chatSDK.presenceSubscription.type` — not a top-level field, and not a
builder call. There is no `UIKitSettingsBuilder` in RN.

## Guard the boot so it runs once
React re-renders, remounts and Fast Refresh can all fire the effect again. Two `login()` calls race
and the second can reject. Cache the **promise**, not a boolean:

```tsx
let boot: Promise<void> | null = null;

export function ensureReady() {
  if (!boot) {
    boot = (async () => {
      await CometChatUIKit.initFromSettings(settings);
      await CometChatUIKit.login({ uid: UID });   // ({ authToken }) in production
    })();
  }
  return boot;
}
```

A boolean flag does **not** work: the second caller sees `false` while the first is still awaiting.

## Gate the render
```tsx
const [ready, setReady] = useState(false);
useEffect(() => { ensureReady().then(() => setReady(true)).catch(console.error); }, []);
if (!ready) return null;   // or your own splash
```

Rendering before `ready` gives the blank screen above.

## Logout order
**Unregister the push token first**, then `CometChatUIKit.logout()`. Reversed, the device keeps
receiving the previous user's notifications — a privacy incident on a shared device, not a bug.

## `login` is untyped — TypeScript will not help
`login(...args: any)` in the `.d.ts`. The two real shapes are `login({ uid })` and
`login({ authToken })`. A wrong call compiles and fails at runtime.
