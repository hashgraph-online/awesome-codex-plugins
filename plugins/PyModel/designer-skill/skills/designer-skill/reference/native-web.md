# Native Web

Small platform mismatches make a web app feel foreign on a phone. Every fix below is standard platform behavior, not preference. After fixing, verify on a real device or credible emulation — a desktop browser resized narrow does not reproduce touch, viewport, or safe-area behavior. None of these fixes require device sniffing: use media queries, CSS environment values, and viewport configuration.

## Symptom → cause → fix

| Symptom | Cause | Fix |
| --- | --- | --- |
| Hover styles stick after tapping | Touch devices report `:hover` on first tap; no hover exists to leave | Gate hover effects behind `@media (hover: hover)`; provide `:active` feedback for touch |
| Gray/colored flash when tapping | `-webkit-tap-highlight-color` default | Set `-webkit-tap-highlight-color: transparent` *and* provide your own pressed state (color alone is not feedback) |
| Content hidden under the URL bar, or gap at the bottom | `100vh` ignores dynamic browser chrome | Size to the viewport with `100dvh` (or `100svh` when chrome-stable layout matters); keep a fallback height for old browsers |
| Page zooms when focusing an input | iOS Safari zooms to fonts under 16px | Set input font-size to ≥16px; never disable user zoom |
| ~300ms tap delay | Missing/`user-scalable=no` viewport historically, or double-tap-zoom ambiguity | Declare `<meta name="viewport" content="width=device-width, initial-scale=1">`; keep zoom enabled; use `touch-action` to disambiguate gestures, not to block zoom |
| Controls clipped by the notch or home indicator | Hardware insets overlay the viewport | Pad with `env(safe-area-inset-*)` (via `viewport-fit=cover` when needed) for edge-attached bars and controls |
| Browser pull-to-refresh fires during custom drags | Default overscroll behavior | `overscroll-behavior-y: contain` on the scrolling container that owns the gesture; preserve pull-to-refresh where the app expects it |
| Scroll chaining scrolls the page behind a modal | Default overscroll propagation | `overscroll-behavior: contain` on the modal's scroll area |
| Momentum scrolling missing on legacy overflow panes | Old `-webkit-overflow-scrolling` requirement | Modern iOS/Android scroll fine by default; only legacy webviews need the prefix — check the project's support policy first |
| Text selection UI appears during custom drag/UI | Default selection on long-press/drag | `user-select: none` on controls only; never on content users may copy |
| Double-firing on pointer handlers | Click synthesized after touch; both handlers run | Use pointer events consistently (`pointerdown`/`click`), or guard touch-then-click synthesis |
| Keyboard covers the focused field | Visual viewport shrinks; layout viewport does not | Scroll the field into view on focus (`scrollIntoView({ block: "nearest" })`); test with the software keyboard open |
| 404s/hard reload lose app state | Full page loads in an app-like SPA | Keep client routing healthy; test cold start and resume paths |

## Rules that outrank the table

- **Never disable zoom** (`user-scalable=no`, `maximum-scale=1`): it breaks accessibility and modern mobile browsers ignore it anyway.
- **Touch targets** follow the interaction-design reference (24 CSS px minimum per WCAG 2.2 AA; comfortable is larger) — thumb reach guidance lives in `ux/08-mobile-ux`.
- Prefer **media and feature queries** (`hover`, `pointer`, `display-mode`) over user-agent or device sniffing; capabilities, not devices, drive behavior.
- `position: fixed` bars interact with keyboard and chrome resizing: verify the bar's behavior when the keyboard opens and the address bar collapses, not just at rest.
- Installed-app feel is mostly *state* correctness (resume, back, offline, focus), not visual chrome; pair this reference with the state-coverage rules in SKILL.md Step 5.
