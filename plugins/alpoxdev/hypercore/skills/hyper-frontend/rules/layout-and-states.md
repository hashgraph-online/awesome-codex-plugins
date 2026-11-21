# Layout and States

Read this rule before writing or changing markup or styles. It decides how an interface is built to hold real content and to keep one shape in every state. It sets no color, type, or mood; those come from the project's design language.

## Contents

1. Scroll Ownership
2. Two Contracts That Fail Silently
3. Responsiveness
4. Content Stress
5. State-Stable Controls
6. State Matrix

## 1. Scroll Ownership

Name these three answers before writing layout styles, in the report or the change description:

- Which one element owns vertical scroll in this region.
- Which regions stay fixed (header, sidebar, toolbar, footer).
- Where the height of the scroll container is bounded.

Rules:

- One scroll container per region unless every extra one has a named job. Nested scrollbars with no declared job make the next gesture unpredictable.
- A full-height shell is bounded with a dynamic viewport unit (`100dvh`), not `100vh`, which ignores mobile browser chrome.
- Do not mix document scroll (`position: sticky`) and a shell region that owns its scroll inside one region without a reason.

## 2. Two Contracts That Fail Silently

Both look correct until real content arrives.

**A scroll body inside a fixed shell.** A grid or flex child defaults to `min-height: auto` and refuses to shrink below its content, so the body pushes the footer away instead of scrolling. Give the scrolling child `min-height: 0` and `overflow: auto`, and bound the shell.

```css
.shell { display: grid; grid-template-rows: auto minmax(0, 1fr) auto; height: 100dvh; }
.shell__body { min-height: 0; overflow: auto; }
```

**A grid that adapts without a media query.** A plain `minmax(16rem, 1fr)` forces a 16rem track even in a 12rem container. Cap the floor with `min()` so the track can collapse.

```css
.grid { display: grid; gap: var(--gap); grid-template-columns: repeat(auto-fit, minmax(min(16rem, 100%), 1fr)); }
```

## 3. Responsiveness

- Ask what the component responds to. A card that is wide in the main column and narrow in a rail responds to its own width: use a container query. Only a change of the page frame (a sidebar collapses, columns drop) is a viewport query.
- Prefer intrinsic adaptation (wrapping flex, the grid above, `clamp()`) over a breakpoint; name a breakpoint for the layout state it switches, never for a device.
- Use logical properties (`margin-inline`, `inset-inline-start`) when the product supports right-to-left text, so the layout mirrors.
- Korean and other CJK text breaks inside words by default; set `word-break: keep-all` with `overflow-wrap: anywhere` on prose containers when the project's text is Korean, then check the rendered line breaks.

## 4. Content Stress

A layout is not done until every region survives this list with real or realistic content, not the happy-path mock:

| Stress | Failure to look for |
|---|---|
| Empty (no rows, no avatar, no value) | A broken frame, a collapsed region, a lonely heading |
| Long label (a 40-character name in a 12-character slot) | Overflow, or a truncation nobody chose |
| Long paragraph | A line measure far beyond a readable length |
| Unbroken string (a URL or token) | Horizontal scroll; needs `overflow-wrap: anywhere` and `min-width: 0` on the flex child |
| 320 CSS px wide | Sideways scrolling of primary content (WCAG 1.4.10), except genuinely two-dimensional content |
| User text-spacing overrides | Clipped text in fixed-height boxes (WCAG 1.4.12) |
| Many items (hundreds of rows) | Layout cost or an unvirtualized list that stalls input |

## 5. State-Stable Controls

A control keeps one box in every state. Width, height, and padding never change when the state does.

- Reserve the space for the longest label before it appears: size a slot to the longest state label, or overlay the spinner on the hidden label instead of replacing it.
- Reserve space for content that arrives later (images with intrinsic size or an aspect ratio, a skeleton the same size as the loaded content, a line for a validation message). This is also what keeps cumulative layout shift low.
- A numeric value that changes or aligns uses tabular numerals so the digits do not shift neighbors.
- Hover, focus, and active states change paint (color, outline, shadow), not geometry. A focus ring uses `outline` or a shadow, never a border that resizes the box.

## 6. State Matrix

Before calling a component or screen built, list every state it can be in and give each a defined look and behavior:

- Component: default, hover, focus-visible, active, disabled, loading, error, success, selected.
- Data-driven screen: loading, empty, error with a way to retry, partial, stale, and the happy path with long content.
- Form: pristine, dirty, validating, invalid with a message that does not move the layout, submitting, submitted. A failed submit keeps what the user typed.

A state that exists in the product but not in the matrix is a finding. Record any state intentionally left out, with the reason.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| A flex or grid item does not shrink below its content unless `min-height` is set | <https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/min-height> |
| Long strings wrap with `overflow-wrap: anywhere` | <https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/overflow-wrap> |
| A component can respond to its container's width | <https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Containment/Container_queries> |
| Content reflows at 320 CSS px without two-dimensional scrolling | <https://www.w3.org/WAI/WCAG22/Understanding/reflow.html> |
| Reserved space for late content keeps cumulative layout shift low | <https://web.dev/articles/optimize-cls> |
| Text-spacing overrides must not clip content (1.4.12) | <https://www.w3.org/TR/WCAG22/> |
| Ownership naming, the stress list, the state matrix, and the state-stable control rule | `dbc-hbin/omp-ulw@74df40f frontend` layout and build-floor guidance (mechanism reference, re-authored) |

### Evidence grade

`LOCAL` for the ownership questions, the stress list, and the state matrix, which are this package's chosen checklist. The CSS and WCAG facts are `PRIMARY` and dated above. The source repository has no license file at the pinned commit, so nothing was copied.
