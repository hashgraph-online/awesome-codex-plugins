# Layout & sizing — why the chat pane collapses

## The rule
Every kit component fills its container. If any ancestor has no resolved height, the component computes to **0px** and you get a blank pane with no error. This is the second most common failure after a missing `imports` entry.

## The prepared ancestor chain
```css
/* styles.css — global, required */
html, body { height: 100%; margin: 0; }
```
Then the shell:
```css
.cc-shell { display: flex; height: 100dvh; width: 100%; min-height: 0; overflow: hidden; }
.cc-side  { width: 320px; min-height: 0; overflow: hidden; }
.cc-main  { flex: 1; display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
```
`100dvh` (not `100vh`) so mobile browser chrome does not clip the composer.

## `overflow: hidden` is what makes each pane scroll ITSELF
`min-height: 0` lets a child shrink; **`overflow: hidden` on the shell and on each column is what keeps its scrolling inside it.** Omit it and the panes grow the page instead: scrolling the conversation list scrolls the WHOLE window, message pane and all, and the header scrolls away with it. The height chain looks right, nothing errors, and the app feels broken.

Both are required, and they do different jobs:
- `min-height: 0` — the column may shrink below its content
- `overflow: hidden` — the overflow is contained, so the kit's own list scrolls internally

The kit's lists manage their own scrolling. Your job is to give them a **fixed-size box to scroll inside**; the moment the box can grow, they stop scrolling and the document does.

## `min-height: 0` on every flex column
A flex item defaults to `min-height: auto`, which refuses to shrink below its content. Nested scrollable lists then overflow the viewport instead of scrolling internally. Every column in the chain needs `min-height: 0`.

## Ancestors that break it
- `transform`, `filter` or `backdrop-filter` on an ancestor creates a containing block that breaks the height chain and can trap `position: fixed` overlays.
- `overflow: hidden` on a mid-level wrapper clips the composer.
- A host element with no display set: kit components are custom elements, so give the host `display: block` or `display: flex` where you control it.

## No reflow between loading and loaded
The pane must not change size when data arrives. Give the pinned box its height up front so the kit's loading and empty views occupy the same box as the loaded list. If the layout jumps, an ancestor is sizing to content rather than to the viewport.

## Thread and search panels
Both are additional columns in the same shell, not overlays:
```css
.cc-thread { width: 360px; min-height: 0; border-left: 1px solid var(--cometchat-border-color-default); }
```
Opening a thread must not resize the message list — reserve the column or animate width, never remount the list. Closing must return to the exact prior layout (the panel-close round-trip).

## Responsive — one pane on mobile
Below ~768px, show a single pane: the list, or the conversation, never both squeezed.
```css
@media (max-width: 768px) {
  .cc-shell { flex-direction: column; }
  .cc-side  { width: 100%; }
  .cc-side[hidden], .cc-main[hidden] { display: none; }
}
```
Drive `hidden` from the same selection state that drives the message components, and give the mobile conversation view a back control that clears the selection.

## Quick diagnosis
| Symptom | Cause |
| --- | --- |
| Blank pane, no error | an ancestor has no height — check `html, body` |
| List overflows the page | a flex column is missing `min-height: 0` |
| Composer off-screen on mobile | `100vh` instead of `100dvh`, or `overflow: hidden` on a wrapper |
| Layout jumps when data loads | the box is sizing to content, not the viewport |
| Dropdown clipped | an ancestor has `overflow: hidden` or a `transform` |
