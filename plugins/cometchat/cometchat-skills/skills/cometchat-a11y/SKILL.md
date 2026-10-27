---
name: cometchat-a11y
description: "Keep a CometChat integration accessible — the UI Kit is designed targeting WCAG 2.1 AA with keyboard navigation (verify per component in its docs; full conformance still needs manual testing), and this skill makes sure the HOST app doesn't break that, covering contrast, focus, screen-reader context, reduced motion, RTL, and calls accessibility. Cross-family. Triggers: 'is cometchat accessible', 'WCAG / 508 / ADA compliance', 'screen reader support', 'keyboard navigation', 'a11y audit', 'accessible chat', 'contrast/focus issues in chat'."
license: "MIT"
compatibility: "CometChat UI Kits (React v7 · Angular v5 · React Native v5 · iOS v5 · Android v6 · Flutter v6). Kit components are designed targeting WCAG 2.1 AA + keyboard navigation (the Angular docs state this explicitly; other families are not individually documented, and full conformance needs manual testing / a VPAT). Host wiring is per platform."
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat a11y accessibility wcag screen-reader keyboard focus contrast rtl section508"
---

> **Ground truth:** the UI Kit components are documented as **designed targeting WCAG 2.1 Level AA** with **keyboard navigation** built in (the Angular component docs state this most explicitly; note the docs' own caveat that full conformance still requires manual testing — do not assert a blanket AA/VPAT claim to the user without it). Treat AA as the design target, not a certified guarantee. Accessibility failures in a CometChat app are almost always **host-side regressions** — global CSS, a broken focus order, a container with no accessible name, or motion that ignores the user's preference. Verify component-level a11y claims against the component's own docs page (`cometchat-<family>-components` → docs-map); this skill owns the host-side discipline the kit can't control.

## Use this skill when
An accessibility review (WCAG / Section 508 / ADA / EN 301 549), a screen-reader or keyboard complaint, or "make our chat accessible." Procurement for public-sector, education, healthcare and large enterprises requires this.

## Start from what the kit gives you
The kit ships accessible components: keyboard-operable lists/composer, focus handling, and semantics **designed targeting** AA (the design target — not a certified guarantee; see above). On web it sets ARIA roles and names itself — the conversation/user rosters render as a labelled `listbox` and manage roving focus — so don't override or strip them. Your job is to **not break it** and to make the surrounding app equally accessible. Two rules first:
1. **Don't let global CSS leak into the `.cometchat` subtree** (web) — a global `outline:none`, a low-contrast override, a `text-align`/flex reset, or a Tailwind base can strip focus rings or break contrast the kit set correctly. Scope your resets away from the kit (`RULES.md` → CSS isolation).
2. **Give the chat container a real, labelled home** — a sized region (a11y needs a visible, non-collapsed surface too) with an accessible name (e.g. an `aria-label`/landmark on web, an accessibility label on native) so screen-reader users can find and enter it.

## The checklist (host-side)
- **Keyboard:** every path reachable and operable by keyboard — open a conversation, type, send, open thread, close. Don't trap focus; return focus sensibly when a panel/dialog closes. Don't remove focus outlines; if you restyle them, keep a visible focus indicator.
- **Screen reader:** the surface and its regions have accessible names; your own buttons around the kit have labels (not icon-only with no `aria-label`/accessibility label). New-message announcements: verify the kit's live-region behavior on your target reader (VoiceOver/NVDA/TalkBack) and don't suppress it with `aria-hidden` on an ancestor.
- **Contrast:** if you theme the kit (`cometchat-<family>-customization`), keep text/UI contrast at **AA** (4.5:1 text, 3:1 large text/UI). Check both light and dark themes — a brand color that passes on light can fail on dark.
- **Reduced motion:** honor `prefers-reduced-motion` (web) / the OS "reduce motion" setting (native) in any animation you add around the chat; don't force motion the user opted out of.
- **Text scaling / zoom:** the surface must remain usable at 200% zoom / large Dynamic Type — don't cap font sizes or clip at large text.
- **RTL:** direction-correct for RTL locales (pairs with `cometchat-i18n`).
- **Targets:** your custom controls meet the minimum touch-target size; don't shrink the kit's.

## Calls accessibility (if you use calling)
- Request camera/mic with clear, user-visible prompts and reasons.
- Provide accessible labels for call controls you add (mute, end, camera).
- Where available, surface captions/transcription; ensure incoming-call UI is announced and keyboard/AT-operable.

## Test it
- **Automated (web):** run `axe`/Lighthouse on the chat screen — fix contrast, missing names, and ARIA misuse it flags. (Automated tools catch ~a third of issues; do the manual pass too.)
- **Manual:** tab through the whole flow with the mouse unplugged; drive it with VoiceOver / NVDA / TalkBack; zoom to 200%; toggle reduced motion; switch to dark. Fix what breaks in YOUR wiring; if a genuine kit-component gap appears, verify against the component docs and report it (don't hand-patch kit internals).

## Common pitfalls
1. **Global CSS stripping focus rings or contrast** inside `.cometchat` — scope resets away.
2. **Icon-only custom buttons with no label** — add accessible names.
3. **Unlabelled, collapsed, or unreachable chat container** — size it and name it.
4. **Animations ignoring reduced-motion.**
5. **Contrast checked in one theme only** — check light and dark.
6. **Assuming automated tools are enough** — they miss keyboard/reader flow; test manually.

## Verify it works
The chat flow is fully keyboard-operable with a visible focus indicator · a screen reader announces the surface, messages, and your controls · contrast passes AA in light and dark · the UI holds at 200% zoom / large type · reduced-motion is honored · RTL mirrors correctly · axe/Lighthouse on the chat screen is clean of contrast/name/ARIA errors.
