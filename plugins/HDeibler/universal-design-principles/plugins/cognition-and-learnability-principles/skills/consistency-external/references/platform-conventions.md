# External consistency — platform conventions

A survey of conventions from major platforms and contexts, with notes on what to honor and where conventions diverge.

## iOS

iOS users expect:

- A navigation bar at the top with the back button at the upper-left (chevron + previous-screen title) and a single action button at the upper-right.
- A tab bar at the bottom for primary navigation in apps with 2–5 main sections.
- The system swipe-from-left-edge gesture to go back.
- The system share sheet for sharing.
- The system context menu (long-press) for additional actions on items.
- Sheet-style modals (sliding up from the bottom) for detail flows.
- The system keyboard with platform-native autocorrect and dictation.
- Adherence to the "Done" / "Cancel" / "Edit" terminology in navigation actions.

Apple's Human Interface Guidelines codify these. iOS users notice deviations even when they can't articulate them; the app feels "off" if it uses an Android-style hamburger menu, a custom share dialog, or a web-style top-level button bar.

## Android

Android users expect:

- A top app bar with the navigation icon (drawer or back) on the left.
- A bottom navigation bar or navigation drawer for primary navigation.
- The system back button (gesture or hardware) to go back.
- Material Design components (Floating Action Button for primary action, Cards for content blocks, Snackbars for transient feedback).
- The system share intent for sharing.
- Long-press for selection mode (entering multi-select).
- The system text-selection toolbar.
- Adherence to material elevation (cards casting shadows, FABs floating above content).

Material Design documentation codifies these. Android is somewhat more tolerant of deviation than iOS because the platform is more diverse, but apps that diverge significantly from Material still feel out of place.

## Web

Web users expect:

- The browser's back button works correctly. Single-page apps that break the back button are a notorious source of user frustration.
- Underlined or differently-colored text is a link.
- Hover states reveal interactivity.
- Forms submit on Enter.
- Tab traverses focus.
- Cmd-F (Ctrl-F) opens browser find.
- The browser's zoom controls work.
- Right-click opens the browser context menu (with possible app additions).
- Standard keyboard shortcuts work where their meaning carries over (Cmd-S for save, Cmd-Z for undo, Cmd-A for select all).

The web's affordances are weaker than native platforms', so following conventions is more important — there's less platform polish to fall back on if you depart.

## macOS

macOS users expect:

- The menu bar at the top of the screen (not in the window).
- The window has traffic lights (close, minimize, zoom) at the upper-left.
- Cmd as the primary modifier key (not Ctrl).
- Standard keyboard shortcuts: Cmd-S, Cmd-Z, Cmd-W, Cmd-Q, Cmd-,
- Right-click or Ctrl-click for context menu.
- The system text-input controls with built-in spell-check.
- Drag and drop between apps.
- The system file open/save dialog.

macOS conventions are deeply ingrained; users notice when an app forces Windows-style behavior (Ctrl modifier, in-window menu bar). Cross-platform desktop apps need to adapt their chrome per platform.

## Windows

Windows users expect:

- An in-window menu bar (or ribbon, in some apps) and toolbar.
- Standard keyboard shortcuts with Ctrl as the primary modifier.
- The window-management chrome (close, maximize, minimize) at the upper-right.
- Right-click for context menu.
- The system file open/save dialog.
- The system text-input controls.
- Notifications via the system notification area.

Windows is more tolerant of cross-platform UI because the platform itself is heterogeneous (desktop, tablet, surface, traditional), but native conventions still matter.

## Web app SaaS conventions

Within the world of SaaS web apps, additional conventions have emerged:

- Top-bar navigation with logo on the left, primary nav in the center, account/notifications on the right.
- A sidebar navigation pattern for products with many sections.
- The Cmd-K (Ctrl-K) command palette for power-user navigation.
- The "/" shortcut to focus a search box.
- Avatar-and-menu in the upper-right for account access.
- A help button (often a chat bubble or "?") in the lower-right.

These conventions are softer than platform conventions, but they're now strong enough that products following them feel familiar to anyone who's used a SaaS tool in the last decade.

## Category conventions: calendar

Calendar apps follow strong category conventions:

- Month, week, and day views available.
- The month view shows a grid with days as cells and events as bars or text within cells.
- The week view shows days as columns with hours as rows; events are positioned at their start time and sized to their duration.
- "Today" is visually highlighted.
- Click/tap on a date or time creates a new event.
- Drag to move; resize at the bottom edge to extend.

Departing from these conventions requires either a strong reframing or a niche audience.

## Category conventions: email

Email apps follow:

- Inbox as a list of conversations; each row shows sender, subject, preview, time.
- Click/tap to open; a reading pane (in dual-pane layouts) or full screen (in single-pane).
- Reply, Reply All, Forward as primary actions on a message.
- The trash, archive, and spam destinations.
- The compose-window pattern with To/Cc/Bcc, Subject, Body.

Email is one of the strongest category conventions; users have been using mail clients for decades. Even radical reinventions (Superhuman, Hey, Front) keep the core conventions and innovate around the edges.

## Category conventions: file management

File managers follow:

- Hierarchical folder navigation with breadcrumbs or a tree.
- List, grid, or column views toggle-able.
- Right-click (or long-press on touch) for context menu with file operations.
- Drag and drop to move; Cmd/Ctrl-drag to copy.
- Cmd/Ctrl+C, X, V for copy, cut, paste.
- The trash/recycle bin.

File management has been stable since the 1980s; departing from these conventions is rarely worthwhile.

## Domain conventions: code editors

Code editors follow:

- Monospace font for code.
- Syntax highlighting with color conventions: keywords blue or purple, strings green or red, comments gray or italic.
- Line numbers in the gutter.
- Find and replace with Cmd-F (Ctrl-F) and Cmd-H (Ctrl-H).
- "Go to line" with Cmd-G or Cmd-L.
- Tab to indent (or smart auto-indent).
- Bracket matching and auto-pairing.

Programmers transferring between editors expect these conventions. Innovating in editor design happens around the edges (LSP integration, AI assistance) but rarely on the core conventions.

## Domain conventions: design tools

Design tools follow:

- A canvas with infinite scroll/zoom.
- Layers panel on one side.
- Properties panel on the other.
- The shape, text, and pen tools as primary creation tools.
- Cmd-D for duplicate; Cmd-G for group.
- Boolean operations (union, subtract, intersect).

Figma, Sketch, Illustrator, and successors all follow these. Departing from them in a serious design tool is a strong claim.

## Cross-cultural and accessibility caveats

Some conventions don't transfer cleanly:

- Reading direction (left-to-right vs. right-to-left) affects many spatial conventions: progress bars, slider directions, even icon orientations.
- Color conventions (red = stop, green = go) are widely shared in industrialized cultures but have local variations.
- Currency, date format, address format, name format all need localization.
- Accessibility conventions (focus states, ARIA roles, keyboard equivalents) are universal — don't sacrifice them for visual coherence.

For globally deployed products, verify each convention with the actual audience rather than assuming it transfers.

## Decision framework

When facing a design decision that touches a convention, ask:

1. **Is there a dominant convention for this in my user's context?** Platform, category, web. If yes, default to it.
2. **Do I have a strong reason to deviate?** "It would look better" is not strong enough. "We're reframing the category" might be.
3. **If I deviate, am I framing it explicitly so users know to expect new patterns?** Without framing, deviation reads as broken.
4. **Am I deviating in chrome, in substance, or both?** Substance can be product-specific; chrome should usually be platform-native.

## Cross-reference

For internal consistency within your product, see `consistency-internal`. For specific patterns of mimicking established conventions, see `mimicry`.
