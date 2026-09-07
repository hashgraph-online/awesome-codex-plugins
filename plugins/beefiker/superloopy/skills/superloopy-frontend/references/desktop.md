# Desktop Application Contract

Use this after the shared UX contract for native, custom, or hybrid desktop UI. A desktop label is not enough: resolve the actual OS and version, desktop environment and session, toolkit and runtime, package format and update channel, window ownership, supported input methods, and available native validation.

## Platform ownership

Keep system or platform chrome as the default. Custom chrome is a platform integration project, not a visual upgrade:

- Windows supported titlebar customization may extend content into the titlebar while system caption buttons are retained; record which hit-test regions and drag behavior the application owns and which caption, snap, accessibility, and window-state behavior remains system-owned. A fully custom non-client frame transfers caption hit testing, resize, snap, system menu, caption-button semantics, accessibility, high contrast, and window-state responsibilities to the application.
- GNOME commonly uses application-owned header bars and client-side decoration, but the supported compositor and session still determine behavior.
- KDE commonly leaves decoration to the compositor; do not copy GNOME ownership assumptions.
- Apple APIs may customize supported titlebar regions while retaining native window behavior. Preserve traffic-light controls, full screen, tabs, accessibility, and system interaction.

Name the menu/command owner, keyboard conventions, focus and selection model, file/font/account discovery, clipboard and drag behavior, notifications, permissions, and multi-window or document lifecycle. Native-adaptive values from the current palette, font, metrics, accessibility settings, and input method (IME) remain authoritative unless the product explicitly owns a branded alternative.

## State and distribution

Separate application defaults, user settings, document/model data, sensitive credentials, and scene/window restoration. Scope persistence and migration claims to the concrete installer, sandbox, package identity, update channel, and supported version path. A development launch does not prove an installed upgrade; a local settings API does not prove uninstall/reinstall retention.

Handle bootstrap and dependency failures before the main surface depends on them. Preserve user input and state through recoverable failures, and expose a specific recovery path rather than an endless loading state.

## Desktop evidence

Keep a **minimum regression floor** on each changed target: configure/build or package as applicable, launch, the affected core journey, and its closest regression path. Add install or unpack, first run, permission prompts, restart, supported update, and recovery only when that lifecycle is affected, explicitly claimed, release-critical, or selected by risk. Exercise supported mouse, keyboard, IME, screen reader, scaling, high-contrast/theme, and multi-window paths according to the same risk model. Inspect the native accessibility tree and packaged lifecycle when those claims apply; browser screenshots or offscreen widget renders cannot substitute for either.

For custom chrome, capture real native behavior for move, resize, snap/tile, maximize, minimize, close, full screen, system menu, focus, and accessibility on the named OS/session. Mark unsupported environments explicitly instead of presenting one universal desktop checklist.
