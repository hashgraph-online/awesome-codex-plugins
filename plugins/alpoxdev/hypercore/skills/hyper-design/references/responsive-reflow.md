# Responsive Reflow

Read when a write mode builds or edits a layout that must hold from phone to desktop, and when an audit finding concerns breakpoints, overflow, tap targets, or mobile navigation. The principle: a mobile layout is a different layout, not the desktop layout at a smaller size. It re-stacks, rescales, and re-orders with intent.

## Contents

- 1. Breakpoints and states
- 2. Scale and sizing
- 3. Grids and stacking
- 4. Overflow
- 5. Tap targets
- 6. Mobile navigation
- 7. Verification

## 1. Breakpoints and States

| Tell | Why | Fix |
|---|---|---|
| One layout for every width; the phone view is the desktop squeezed | Cards collide and text written for a wide canvas crowds a narrow one | Define a real mobile state where the content stops working: columns stack, sizes drop, order changes where needed |
| Breakpoints named after device widths (375, 414, 768) | Devices change every year; the layout follows a spec sheet instead of the content | Narrow the viewport, watch where the content breaks, and put the breakpoint there |
| Mobile rules bolted on as a trailing override | A patch fixes the reported symptom and leaves the next one | Give the narrow width its own deliberate sizes and stacking, and check the whole page there |
| Exactly two states: a phone stack and a wide grid | Tablet and small-laptop widths (about 600-1024px) inherit a stretched stack or a crammed grid | As many states as the content needs, typically single column, two columns, then the full grid |

## 2. Scale and Sizing

| Tell | Why | Fix |
|---|---|---|
| Desktop padding, gaps, hero heights, and card sizes kept on a phone | What reads as confident at 1440px dominates at 375px | A smaller mobile step for type, padding, and gaps; tap targets keep their minimum |
| Font sizes in fixed px that never change | Headings span the whole phone; body lines are tuned for a wide screen | Fluid type with `clamp()` or a smaller type step at the breakpoint |
| Sections at `100vh` | Includes the browser chrome on mobile, overflows the visible area, and pushes content below the fold | Size to content, or `100dvh` where a full-height section is intended |
| Desktop section padding (96-128px) kept on mobile | The page scrolls through empty space | Roughly half or less at the mobile step |

## 3. Grids and Stacking

| Tell | Why | Fix |
|---|---|---|
| Side-by-side columns stay side by side on a phone | Each column becomes a sliver; text wraps badly and cards overlap | Collapse to one column at the breakpoint |
| `grid-template-columns` in fixed px | Tracks keep their width and force overflow | `minmax()` with `auto-fit` or `auto-fill`; grid areas that collapse |
| A 12-column grid forced onto one-column content | Spans become arbitrary fractions of an invisible grid | Let columns follow the content: one, or two at most, on a phone |

## 4. Overflow

| Tell | Why | Fix |
|---|---|---|
| The page scrolls sideways because a table, code block, image, or long string is wider than the viewport | The user cannot see where the page ends; it is invisible in the desktop preview | Find the wide element: `max-width: 100%` on media, wrapping code, a reflowed or scroll-contained table; zero horizontal scroll at the narrowest width |
| `overflow: hidden` clips text or controls at narrow widths or at 200% zoom | Hides a failure and removes content | Let the container grow, wrap, or collapse; clip only deliberate crops such as thumbnails |
| Flex or grid children with fixed px `width` or `min-width` | The child keeps its desktop size and bursts out | Relative widths, `flex-wrap`, and `min-width: 0` on grid and flex children |

## 5. Tap Targets

| Tell | Why | Fix |
|---|---|---|
| Controls smaller than the touch floor | A thumb is not a cursor | WCAG 2.2 AA requires 24×24 CSS px; on touch surfaces aim for 44×44 (Apple default, WCAG AAA) or 48×48 dp on Android, using padding or a larger hit box when the visual is smaller |
| Large targets packed with no gap | Two touching controls behave like one | A clear gap so the press area of one never covers the next |
| Menus, reveals, and tooltips that exist only on hover | There is no hover on a touchscreen | A tap equivalent for every hover interaction, with visible `:active` feedback |

## 6. Mobile Navigation

| Tell | Why | Fix |
|---|---|---|
| The desktop row of links kept on a phone | Links crowd, wrap, or spill past the edge | Collapse at the breakpoint: a bottom bar for a handful of primary destinations, a menu for the rest |
| A bare hamburger icon hides everything | The user may not know a menu exists or what it holds | Label it ("Menu"), or keep primary destinations visible and hide only the secondary ones |
| A fixed bottom bar covers the last items or the final button | Content scrolls under the bar and becomes unreachable | Reserve the bar's height with padding and `env(safe-area-inset-bottom)` |
| A tall sticky header takes a large slice of the screen | The content becomes a letterbox | Keep fixed chrome compact; shrink or hide it on scroll where suitable |

## 7. Verification

Drag the viewport through the whole range, not two sample widths. Record the widths checked, the horizontal-scroll result at the narrowest width, and the last reachable item under any fixed bar. Without a rendered capture, these items are `static_only`.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The reflow principle and every Tell / Why / Fix row in §1-§6 | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop-layoutmobile/SKILL.md`; MIT, Copyright 2026 Miqdad Badjuber), rewritten for this package |
| Target size 24×24 CSS px (AA) and 44×44 CSS px (AAA); reflow at 320px | <https://www.w3.org/TR/2024/REC-WCAG22-20241212/> (SC 2.5.8, 2.5.5, 1.4.10). The source states 44px as the minimum; this package keeps the AA and AAA levels apart. |
| Apple 44×44 pt default control size; Android 48×48 dp | <https://developer.apple.com/design/human-interface-guidelines/accessibility>, <https://developer.android.com/guide/topics/ui/accessibility/apps> |

### Evidence grade

The WCAG rows are normative. The rest is a practitioner rule set; the source gives no measurements.
