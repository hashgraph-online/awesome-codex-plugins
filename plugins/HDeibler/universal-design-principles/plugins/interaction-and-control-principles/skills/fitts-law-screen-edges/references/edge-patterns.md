# Screen edges: pattern reference

A reference complementing `fitts-law-screen-edges` with platform conventions and historical context for edge-anchored UI.

## The classic edge-advantage example

The macOS menu bar has lived at the top edge of the screen since 1984. The Mac team's defense of this choice (vs. Windows's per-window menus) was explicitly Fitts-grounded: a screen-edge menu has *infinite* target height along the vertical axis, because the cursor cannot move past the screen edge. The user can fly the cursor upward without precision and the cursor stops on the menu bar.

This argument is decades old and still wins blind A/B tests where users complete file-menu tasks faster on macOS than on Windows-style UI when conditions are otherwise equal. The cost: only one application's menu can occupy the bar at a time, so the menu changes as you switch apps — a cognitive trade-off that might not be worth the Fitts win for casual users.

## Platform-specific edge use

### macOS
- **Top edge:** menu bar (per-app commands), notch (display cutout), system status (right side).
- **Bottom edge:** Dock by default; can be hidden or moved.
- **Right edge:** notification center / Mission Control if configured.

### Windows
- **Bottom edge:** taskbar (default), Start button (left corner), system tray (right corner).
- **Edge swipe gestures** for snap layouts.

### iOS
- **Top edge:** status bar, dynamic island.
- **Bottom edge:** home indicator (system gesture area, ~25 points reserved).
- **Left edge:** back-swipe gesture.
- **Right edge:** control center swipe (top-right corner specifically).

### Android
- **Top edge:** status bar, notification shade pull-down.
- **Bottom edge:** navigation bar (back/home/recents) or gesture area.
- **Edges:** various gesture targets.

### Web
- The browser owns most of the screen edges; web apps have only the viewport's interior edge to work with.
- Sticky headers and footers are the canonical web equivalents of edge-anchored UI.

## Cross-domain examples

### Television remote controls

The "channel up/down" and "volume up/down" buttons typically occupy the top of the remote's button cluster — easy to find by feel. Power button is often at the very top edge. The arrangement is a tactile equivalent of Fitts's edge advantage: the edges of the remote act as physical targets for the thumb.

### Calculator layout

A calculator's "C" or "AC" (clear) button is typically in a corner — large, distinct color, edge-positioned. Hitting it accidentally costs the user; the corner placement makes finding it deliberate easier and finding it accidental harder.

### Light switches

Standard toggle light switches sit at a fixed wall location (typically near a doorway, ~48 inches from the floor). The position is a "spatial edge" — wall + door frame — that helps the user find the switch by touch in darkness. Same Fitts logic, different domain.

## Things to know about web edges

### Browser chrome

Modern browsers reserve some edge real estate:

- **Top:** URL bar (variable), tabs, system menu.
- **Bottom (mobile):** URL bar (mobile Safari, Chrome) — moves around as you scroll.
- **Edges:** scroll bars on desktop (sometimes hidden until scroll).

Web apps must respect these reservations; the actual usable "edge" is the interior of the viewport.

### Safe-area insets

iOS and modern Android expose `env(safe-area-inset-*)` CSS variables for the screen-edge regions reserved for system UI (notch, home indicator):

```css
.bottom-bar {
  padding-bottom: env(safe-area-inset-bottom);
}
```

Use these for edge-anchored content on mobile — otherwise your content may be hidden under the system UI.

### Edge gestures and content collision

A button placed flush at the bottom edge of an iPhone screen may trigger the system home gesture instead of registering as a tap. Best practice: inset 8–16px from the absolute edge for primary touchable content, while still keeping the visual element close to the edge.

## Anti-patterns

- **The all-margin app.** Modern web design defaults to padded layouts with no element at the screen edge. Easy to over-do.
- **Edge-flush buttons that conflict with system gestures.** Especially mobile.
- **Modal dialogs floating mid-screen.** The X to close is far from any edge; aim is required.
- **Sticky headers without sticky behavior.** A nav that's only sticky on some pages forces the user to relearn its location.

## Resources

- **Apple HIG: Layout** — discussion of safe areas, edge-aligned UI.
- **Material Design: Layout** — Android-side conventions.
- **Bruce Tognazzini, "First Principles of Interaction Design"** — original popularizer of the Fitts-and-edges argument for HCI.

## Closing

The screen edge is the most underused real estate in modern web UI. Designers trained on print conventions instinctively reach for margins; designers trained on Fitts's research instinctively reach for edges. Worth knowing which tradition you're drawing from on a given decision.
