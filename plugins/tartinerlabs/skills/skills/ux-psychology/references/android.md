# Android (Jetpack Compose)

Material Design 3 and Android's system behaviours are what Android users have learned. This guide covers what most often goes wrong — native Compose apps and React Native/Expo apps running on Android alike. Prefer Material 3 components: they bring the expected behaviour and accessibility for free.

## Targets and Layout

- Minimum touch target **48×48 dp** (Material). A small icon keeps a 48 dp touch area; Material 3 components enforce it via minimum interactive size
- Draw edge-to-edge and handle window insets (status bar, navigation bar, display cutouts) — edge-to-edge is enforced for apps targeting Android 15 (API 35)
- Respect the user's font scale: sizes in `sp`, layouts that grow rather than clip

## Back Behaviour

The system back gesture/button is the most important Android convention, and the one cross-platform apps most often break.

- Every screen must respond correctly to system back: close the sheet or dialog, go up one level, or leave the app from the start destination
- Support predictive back so users see where back will take them before committing
- Never trap back to force a flow; for unsaved input, confirm once ("Discard draft?") and then let the user go
- The top app bar's up arrow and the system back should lead to the same place in normal flows

## Navigation

| Need | Material pattern |
|---|---|
| 3–5 top-level destinations, phone | Navigation bar (bottom) |
| Top-level destinations, tablet/foldable | Navigation rail or drawer |
| Many destinations or rarely switched | Navigation drawer |
| Drill-down | Top app bar with up navigation |

## Actions and Feedback

- Brief confirmations with an optional action ("Archived — Undo"): **Snackbar**, not a Toast — it can carry Undo, which beats a confirmation dialog (`rules/error-prevention.md`)
- The single most important action of a screen: Floating Action Button, at most one per screen (`rules/von-restorff.md`)
- Dialogs for decisions that must interrupt; bottom sheets for options and secondary content
- Touch feedback: ripple comes with Material components — keep it on custom clickable elements via `Modifier.clickable`
- Haptics: `HapticFeedbackType` / `View.performHapticFeedback` for confirmations and selection changes, sparingly

## Text Input

- Set `KeyboardOptions(keyboardType = …)` and autofill hints so the system fills known data (`rules/defaults.md`)
- `ImeAction.Next` / `ImeAction.Done` to move through a form without touching the screen

## Permissions

After the user denies a permission repeatedly, Android stops showing the prompt and the app must send them to Settings. Ask in context and explain first (`references/mobile.md`); handle "denied" as a normal state.
