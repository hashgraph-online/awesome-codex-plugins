# Mobile (shared)

How the rules apply on phones and tablets, whatever the stack. Load the platform guide alongside this one — `apple.md`, `android.md`, or `cross-platform.md` — for conventions specific to each OS.

## The Context Is Different

- **Short, interrupted sessions** — people use phones in queues, while walking, between other things. Every screen must make sense to someone who glances at it for three seconds and may leave mid-task
- **One hand, one thumb, often** — Hoober's field observation (2013, UXmatters) found 49% of people touching their phone's screen held it in one hand, and grips change constantly. Design for the thumb, but never require a single grip
- **No hover, no precise pointer** — affordances must be visible, and targets large (`rules/signifiers.md`, `rules/fitts-law.md`)
- **Small screen** — less fits, so cognitive load and progressive disclosure matter more than on desktop

## Thumb Reach

- Put frequent and primary actions in the lower half: bottom tab bars, bottom sheets, bottom-anchored primary buttons on long forms
- Put rare or destructive actions where they take deliberate reach — top corners, or inside a menu
- Do not stack primary and destructive actions next to each other at the bottom (`rules/fitts-law.md`)
- On tablets and large phones, keep core actions reachable from the edges where hands rest

## Interruptions and State

- Save drafts and progress automatically; returning to the app should land on the same screen with the same input
- Long tasks (uploads, sync) continue in the background and report when done (`rules/system-status.md`)
- Do not rely on the user remembering anything from a previous session — show it (`rules/cognitive-load.md`)

## Permission Requests

The OS permission prompt is often a one-shot chance: iOS shows it once, and Android stops showing it after repeated denials. So:

1. Ask in context — when the user taps the feature that needs it, not at launch
2. Explain first, in your own UI: what the permission enables for *them* (`rules/reciprocity.md`)
3. Then trigger the system prompt
4. If denied, keep the app usable and offer a path to Settings later

A pre-permission screen must be honest: no fake system-style dialogs, no "Allow" as the only button (`rules/deceptive-patterns.md`).

## Notifications

- Ask for notification permission after the user has seen the value of a notification, not on first launch
- Every notification should be something the user would want if asked — volume and irrelevance train people to disable them all
- Let users choose categories rather than all-or-nothing

## Gestures

- Gestures are invisible: every swipe, long-press, or pinch action also needs a visible control (`rules/signifiers.md`)
- Use gestures the OS already teaches (swipe back, pull to refresh, swipe-to-delete in lists) rather than inventing new ones (`rules/jakobs-law.md`)
- Never put a custom gesture where it fights a system gesture (screen edges, bottom home indicator)

## Feedback on Touch

- Every tap gets an immediate visible response — pressed state, highlight, or ripple — within ~0.1 s (`rules/system-status.md`)
- Haptics confirm meaningful moments (success, toggle, selection change, error); used everywhere they become noise. Platform APIs are in the platform guides
- Offline or slow network: show cached content, queue actions, and say clearly what has not synced yet

## Onboarding

- Show the product working before asking for an account where the product allows it (`rules/reciprocity.md`)
- Keep any tour to the few things not obvious from the UI itself; skippable, and never blocking the first real action
- Start with a small first step and count completed steps as progress (`rules/commitment.md`, `rules/goal-gradient.md`)

## Text Input

- Choose the right keyboard (email, number, phone, URL) and autofill hints so the OS fills what it knows (`rules/defaults.md`)
- Avoid typing where a choice works: pickers, segmented controls, recent values
- Keep the focused field and the primary button visible above the keyboard
