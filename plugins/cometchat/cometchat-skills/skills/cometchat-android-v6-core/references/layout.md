# layout — the reflow-free chat surface (the ONE mobile sizing standard, Android v6)

> Ground truth: `ui-kit/android/conversation-message-view.md` (both tabs, snippets verbatim) + `getting-started-*` (`enableEdgeToEdge`), cross-checked against the kit's sample-app manifests (`windowSoftInputMode="adjustResize"`), verified 2026-08-20.

The single source of truth for how a CometChat surface is SIZED on Android so it renders
full-size from the first frame, stays clear of system bars and the keyboard, and never
reflows. `core`, `placement`, and `calls` POINT here — change the rule once, here.

> **The kit is NOT the problem.** Every UI Kit component fills its parent by design and
> ships its OWN loading/empty/error state. A chat surface that collapses, hides the
> composer under the keyboard, or slides under the status bar is a HOST layout defect.

## The five invariants (a correct surface satisfies ALL)

**(1) Fill the parent — never `wrap_content` for the chat surface.**
The conversations screen and the message screen each own their window: Views →
`match_parent` (in a constraint layout, `0dp` + constraints, as the docs guide does);
Compose → `Modifier.fillMaxSize()`. `wrap_content` on a list-shaped component collapses to
~0dp before content loads and grows into place after — both broken. The composer/header
are the exception: they are bars — `wrap_content` height (Views) / intrinsic height
(Compose) by design.

**(2) Edge-to-edge WITH insets.** The docs call `enableEdgeToEdge()` in every Activity
`onCreate` — once you do, YOU own the status/nav-bar insets, or the header renders under
the status bar and the composer under the gesture bar. Compose: the guide's exact recipe —
```kotlin
Scaffold(contentWindowInsets = WindowInsets.statusBars) { paddingValues ->
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(paddingValues)
            .consumeWindowInsets(paddingValues)
            .navigationBarsPadding()
            .imePadding()
    ) { /* header / list / composer */ }
}
```
Views: apply insets to the root (e.g. `ViewCompat.setOnApplyWindowInsetsListener` padding
the root with `systemBars()` insets), or skip `enableEdgeToEdge()` entirely and let the
system fit the window — never edge-to-edge WITHOUT inset handling.

**(3) IME/keyboard-aware — the composer stays visible while typing.**
- **Views:** the chat Activity needs `android:windowSoftInputMode="adjustResize"` in
  `AndroidManifest.xml` (the kit's own sample apps set it on every chat activity). Without
  it the keyboard overlays the composer.
- **Compose:** `Modifier.imePadding()` on the column that holds the composer (guide recipe
  above) — and make sure inset consumption (`consumeWindowInsets`) precedes it so padding
  isn't applied twice. `adjustResize` in the manifest also helps Compose apps on older
  inset paths; the samples set both.

**(4) Loading states render INSIDE the full-size surface — no placeholder→chat jump.**
The components ship their own loading/empty/error states and render them within the sized
surface. Mount the sized surface immediately after the gate unlocks and let each component
show its own state — do NOT swap a small "Loading…" layout for the chat layout (that IS
the reflow). The only gate ABOVE the surface is init/login (`lifecycle.md`), and the docs'
gate renders its spinner `fillMaxSize`, so even that swap is full-size → full-size.

**(5) List scroll containment — the message list scrolls internally.**
`CometChatMessageList` (and `CometChatConversations`) contain their own scrolling.
- **Views:** never nest them in a `ScrollView`/`NestedScrollView`; in the vertical
  `LinearLayout` the list takes `layout_height="0dp"` + `layout_weight="1"` between the
  header and composer bars (docs guide, verbatim below).
- **Compose:** never place them inside a `verticalScroll` or another `LazyColumn`
  (nested unbounded-height measurement crashes/collapses); give the list `weight(1f)`
  in the `Column` so it gets a bounded height and scrolls inside it.

## The message-screen recipe (docs guide, verbatim shapes)

**Views — `activity_message.xml`:**
```xml
<LinearLayout android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical">
    <com.cometchat.uikit.kotlin.presentation.messageheader.ui.CometChatMessageHeader
        android:id="@+id/message_header"
        android:layout_width="match_parent" android:layout_height="wrap_content" />
    <com.cometchat.uikit.kotlin.presentation.messagelist.ui.CometChatMessageList
        android:id="@+id/message_list"
        android:layout_width="match_parent" android:layout_height="0dp"
        android:layout_weight="1" />
    <com.cometchat.uikit.kotlin.presentation.messagecomposer.ui.CometChatMessageComposer
        android:id="@+id/message_composer"
        android:layout_width="match_parent" android:layout_height="wrap_content" />
</LinearLayout>
```
plus manifest: `<activity android:name=".MessageActivity" android:windowSoftInputMode="adjustResize" />`.

**Compose — `MessageScreen`:** the Scaffold recipe in invariant (2) with, inside the Column:
```kotlin
CometChatMessageHeader(modifier = Modifier.fillMaxWidth(), user = user, group = group,
    hideBackButton = false, onBackPress = onBack)
CometChatMessageList(modifier = Modifier.fillMaxWidth().weight(1f), user = user, group = group)
CometChatMessageComposer(modifier = Modifier.fillMaxWidth(), user = user, group = group)
```

The conversations screen is the same standard, one component:
Views full-bleed `CometChatConversations` at `match_parent`/`0dp`+constraints; Compose
`CometChatConversations(modifier = Modifier.fillMaxSize(), ...)`.

> ⚠️ **The list and search routes need insets too, not just the message route.** `fillMaxSize()` under `enableEdgeToEdge()` draws the title under the status-bar clock (verified on device). Wrap every full-screen route in `Scaffold(contentWindowInsets = WindowInsets.statusBars)` — the same recipe this file reserves for the message screen. Skipping it here contradicts layout invariant (2): never edge-to-edge WITHOUT inset handling.

## Embedded (not full-screen)
Same invariants against the embedding cell: give the chat region a bounded height (a sized
fragment container / a `weight`ed cell / a fixed `Modifier.height(...)`) — never
`wrap_content`/unbounded — and keep (3)–(5) unchanged. Bottom-nav/tab shells: size the tab
content pane, not the component (`cometchat-android-v6-{kotlin,compose}-placement`).

## Verify (advisory, human check)
Full-size from the first frame (the kit's own loading state fills the screen, no small box
that grows); header below the status bar and composer above the gesture/nav bar with
edge-to-edge on; open the keyboard → the composer rides above it and the list shrinks (no
overlay); the message list scrolls internally with header/composer pinned; rotate → no
collapse, no re-init (`lifecycle.md`).
