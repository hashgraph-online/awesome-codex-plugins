# anti-patterns — what breaks a CometChat React Native integration

Every entry here is a failure **observed in this codebase**, not a generic warning. Ordered by how
often it bites and how misleading its error is.

## The meta-pattern: RN errors name the wrong culprit
Three properties make RN bugs hard to read, and all of them appear below:
- **native modules fail at MOUNT, not build** — the app starts, then a screen explodes
- **the error names a peer dependency**, not CometChat — `gesture-handler`, `svg`, Ruby, generated C++
- **an unknown prop is silently ignored** — no error, nothing renders

So "the error doesn't mention CometChat" is evidence of nothing.

---

## 1. Porting React code
The React UI Kit is a **different package with a different API**. These do not exist on RN:

| React | React Native |
|---|---|
| `new UIKitSettingsBuilder()…build()` | a plain `CometChatSettings` object |
| `CometChatUIKit.login(uid)` | `login({ uid })` — an **object** |
| `onItemClick` · `onThreadRepliesClick` | `onItemPress` · `onThreadRepliesPress` |
| `itemView` · `trailingView` (camelCase) | `ItemView` · `TrailingView` (**PascalCase**) |
| `CometChatMessagePlugin` / `PluginRegistry` | `ChatConfigurator` + `DataSourceDecorator` |
| `CometChatErrorBoundary` | none — use a plain React error boundary |
| `setCallingEnabled(true)` | **nothing** — installing the calls package IS the switch |
| CSS variables / `className` | `CometChatThemeProvider` + `useTheme()` |

**The PascalCase one is the nastiest**: an unknown prop throws nothing and renders nothing, so the
custom UI just never appears.

## 2. Same prop name, opposite default
`showSearchBar` is **`true` on React** and **`false` on React Native**. Wiring
`onSearchBarClicked` without `showSearchBar={true}` ships a surface where search can never be
reached — and it compiles, and every symbol exists. See `component-props.md`.

## 3. Missing `GestureHandlerRootView`
Gestures silently stop working. No error. It must be **outermost** and carry `flex: 1`.
On bare RN, `import 'react-native-gesture-handler'` must also be the **first line of `index.js`** —
wrong ordering often works in debug and **crashes in release**.

## 4. Rendering before `login()` resolves
Blank screen, no exception. Gate the render; cache the boot **promise**, not a boolean
(`lifecycle.md`).

## 5. Fixed heights
Breaks the moment the soft keyboard opens. `flex: 1` everywhere, `minHeight: 0` on scrolling
columns (`layout.md`).

## 6. Web-shaped layout
Side panels, two panes side by side, state-toggled views. On a phone every surface is its own
**screen** on a stack navigator with the OS back button (`placement`).

## 7. Two headers
The navigator's header plus `CometChatMessageHeader`. Set `headerShown: false` on that screen.

## 8. Hand-rolling what the kit ships
A `TextInput` composer, a `FlatList` of messages, a `react-native-image-picker` flow. All exist as
drop-ins. Custom UI goes **in a view slot**, never as a sibling above the component.

## 9. Shipping the Auth Key
No client-side hiding works. Production mints an auth token server-side (`setup-credentials.md`).

## 10. Leaking listeners
Every `add*Listener(id, …)` needs `remove*Listener(id)` on teardown. The **SDK** holds the
listener, not React, so it survives unmount — the top cause of duplicate messages, and it worsens
the longer the app runs.

## 11. Ban without unban
`CometChatGroupMembers` lists **active** members only, and v5 ships no banned-members UI. An app
that can ban but not view or unban is an unclosed round trip.

## 12. Believing a simulator
Calls need camera and mic; push needs delivery to a backgrounded or killed app. **Neither works on
a simulator.** A green simulator run proves the screens render, not that the feature works.

## 13. Reloading after a native change
Metro reload only refreshes JavaScript. New native module, Gradle edit or plist change ⇒ **rebuild**.
