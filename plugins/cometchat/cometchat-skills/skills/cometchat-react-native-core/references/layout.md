# layout — the React Native sizing standard

`contracts.rn-v5.json` gates four capabilities on this file: `flex-fill-screen-height` ·
`flex-min-height-0` · `safe-area-ancestor-chain` · `keyboard-avoidance`. The **principle** is the
same as web — the kit fills its container and must not reflow between loading and loaded — but the
**recipe** is entirely different.

## There is no viewport unit, and no CSS
`100dvh`, `min-height`, `vh`, media queries: none exist. Height comes from **flex**, and the frame
resizes when the keyboard opens.

## The four invariants

### 1. Every ancestor is `flex: 1`
A kit component fills its parent. A parent with no height collapses it to **zero** — and on RN a
zero-size view still **exists in the tree**, so it is `toExist` but not `toBeVisible`. That is why
the Detox specs assert visibility, never existence.

```tsx
<View style={{ flex: 1 }}>
  <CometChatMessageList user={user} />
</View>
```

### 2. A scrolling column also needs `minHeight: 0`
Without it the child grows instead of scrolling, and the composer is pushed off-screen.

### 3. The provider chain order is load-bearing
Outermost first — verified against the integration and recipe pages:

```tsx
<GestureHandlerRootView style={{ flex: 1 }}>   {/* OUTERMOST, and flex:1 */}
  <SafeAreaProvider>
    <CometChatI18nProvider>
      <SafeAreaView style={{ flex: 1 }}>
        <CometChatThemeProvider>{/* screens */}</CometChatThemeProvider>
      </SafeAreaView>
    </CometChatI18nProvider>
  </SafeAreaProvider>
</GestureHandlerRootView>
```

**Omit `GestureHandlerRootView` and gestures silently stop working** — no error, no warning. Swipe
and long-press simply do nothing. It is the single most common "renders but doesn't respond" cause.

### 4. The composer must survive the keyboard
A fixed pixel height anywhere in the chain breaks when the soft keyboard opens. Verify with the
keyboard **up**, on a device — a simulator's hardware keyboard can hide the problem.

## No side panels — one screen per route
The web kit toggles panels with state. On a phone every surface is its own screen on a stack
navigator, with the OS back button. Search, threads and members are **pushed screens**. Details in
the `placement` skill.

## Anti-patterns
| Don't | Why |
|---|---|
| `height: 600` on a chat container | breaks on keyboard open and on every other device size |
| a `ScrollView` wrapping `CometChatMessageList` | the list scrolls itself; nesting breaks both |
| `NavigationContainer` outside the providers | screens mount unthemed |
| the message screen inside the tab navigator | the tab bar overlaps the composer |
