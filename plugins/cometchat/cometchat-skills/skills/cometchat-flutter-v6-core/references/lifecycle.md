# lifecycle — init once, login, gate the first frame, log out

Loaded when the task touches startup, session, or "why is it blank / why did it re-init".

## The invariant
`initFromSettings()` → `login(uid)` → **only then** render any `CometChat*` widget. Both are async and
callback-reporting; a widget rendered before login succeeds shows blank or throws.

## Init once — not once per widget, and hot-restart-safe
Do it at app startup (before `runApp`, or in the root widget's `initState`), never inside a screen that
can be re-entered. `initFromSettings` reads `cometchat-settings.json` and persists
`integrationSource="ai-agent"`; calling it twice is wasteful and races the Calls SDK routing.

```dart
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();   // REQUIRED before any plugin/asset access
  runApp(const MyApp());                       // init happens inside the gate widget below
}
```
> `WidgetsFlutterBinding.ensureInitialized()` is mandatory — `initFromSettings` loads an asset through
> `rootBundle`, which needs the binding. Omitting it is a common first-run crash.

## Gate the first frame (the pattern that prevents the blank screen)
Hold the app on a loader until init AND login have both reported success; only then build the chat.
Keep the gate at the ROOT so a hot restart re-runs it cleanly.

```dart
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';
import 'package:flutter/material.dart';

class ChatGate extends StatefulWidget {
  const ChatGate({super.key});
  @override
  State<ChatGate> createState() => _ChatGateState();
}

class _ChatGateState extends State<ChatGate> {
  bool _ready = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _start();
  }

  Future<void> _start() async {
    await CometChatUIKit.initFromSettings(
      onError: (e) => setState(() => _error = e.message),
    );
    if (_error != null) return;
    // Already signed in after a restart? login() no-ops for the same UID.
    await CometChatUIKit.login(
      'cometchat-uid-1',                       // ASK for a real UID — never invent one
      onSuccess: (_) => setState(() => _ready = true),
      onError: (e) => setState(() => _error = e.message),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) return Scaffold(body: Center(child: Text('CometChat: $_error')));
    if (!_ready) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    // Only past this point may a CometChat* widget be built.
    return const Scaffold(body: SafeArea(child: CometChatConversations()));
  }
}
```
> `setState` after an await needs the usual `if (!mounted) return;` guard in real code.

## Who is logged in
`CometChatUIKit.loggedInUser` is the cached `User?` — the sync getter the thread screen needs
(`loggedInUser:` is a REQUIRED param on `CometChatThreadedHeader`). It is populated by `login`, so it is
non-null anywhere behind the gate above. `CometChatUIKit.login` itself calls `getLoggedInUser()` first and
returns early when that UID is already signed in — **no host-side concurrent-login guard is needed.**

## Production auth — the Auth Key is dev-only
`login(uid)` uses the Auth Key from the settings file, which means the key ships inside the app bundle.
That is acceptable for development only. For production:
1. Omit `credentials.authKey` from `cometchat-settings.json`.
2. Mint a per-user **auth token** on your server (CometChat REST API, using the App's REST key).
3. Sign in with `CometChatUIKit.loginWithAuthToken(authToken, onSuccess: …, onError: …)`.
Say this out loud to the user when you wire the dev path — flag dev-only AS dev-only.

## Logout
`CometChatUIKit.logout()` clears the session; send the user back to the gate afterwards so a subsequent
login re-runs cleanly. Do not re-`init` on logout.
