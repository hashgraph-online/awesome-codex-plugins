# Rendered Verification

Read this rule before declaring any frontend work delivered, and for the whole of `verify` mode. Source that looks right is not evidence that the page is right. This rule decides what is checked in a real browser, how it is read, and how a missing browser is reported.

## Contents

1. Evidence Labels
2. Capture Matrix
3. What to Read
4. Build-Time Accessibility Checks
5. Performance Checks
6. When No Browser Is Available
7. Fix Mode

## 1. Evidence Labels

Label every claim in the report with one of three labels, and never upgrade one by wording:

- `static`: read from source or from a build or type-check result.
- `rendered`: observed in a real browser at a stated viewport, theme, and state.
- `not verified`: no observation was possible; the reason is stated.

## 2. Capture Matrix

Pick the smallest matrix that covers the change, and state it in the report:

| Axis | Values |
|---|---|
| Width | 320 (reflow floor), 390 (phone), 1440 (desktop); add 768 when the layout changes between them |
| Theme | Light and dark when the project ships both |
| State | Every row of the state matrix the change touches ([layout-and-states.md](layout-and-states.md) §6) |
| Content | Real or realistic: empty, long label, unbroken string, many items |
| Input | Pointer, then keyboard only (Tab, Shift+Tab, Enter, Space, Escape) |
| Preferences | `prefers-reduced-motion: reduce`; optionally forced colors |

A small edit to one component needs the states and widths that component can reach, not the whole product.

## 3. What to Read

- Read computed values (`getComputedStyle`, layout rectangles), not source, for sizes, spacing, contrast, and line length.
- Compare dimensions of one control across its states; they must be equal ([layout-and-states.md](layout-and-states.md) §5).
- Read the console: an error or a failed request is a finding even when the page looks right.
- Look at the screenshot of each captured state; a measurement can pass while the picture is wrong.
- Keyboard pass: every action reachable, order matches the reading order, focus always visible and never hidden behind a sticky element, no trap.

## 4. Build-Time Accessibility Checks

These are the checks that implementation decides. A full conformance table for a design-system deliverable is a different job.

| Item | Pass condition |
|---|---|
| Reflow (1.4.10) | No sideways scroll of primary content at 320 CSS px |
| Contrast (1.4.3, 1.4.11) | Text 4.5:1 (large text 3:1); control edges and icons 3:1; both themes; placeholders included |
| Target size (2.5.8) | Pointer targets at least 24 by 24 CSS px |
| Focus (2.4.7, 2.4.11) | Focus ring visible on every surface; not fully hidden by a sticky or overlay element |
| Keyboard (2.1.1, 2.1.2) | Every action reachable; no keyboard trap |
| Names | Every control has an accessible name; images carry meaningful alt text or are marked decorative |

Report each as pass, fail, or not applicable with the observation behind it.

## 5. Performance Checks

Run these only when the request or the project asks for performance, or when the change is plausibly a regression (a large image, a new dependency, a long list):

- Targets for a good user experience at the 75th percentile: LCP within 2.5 seconds, INP of 200 milliseconds or less, CLS of 0.1 or less.
- Measure in a real browser against a production build when one exists. A development server is reported as such.
- A score or timing that was not measured is `not verified`. Never invent a number, and never trade away behavior, content, or motion to move a score.

## 6. When No Browser Is Available

When no browser capability can open the page, run every static check, state `static` on each claim, and end as `delivered_unverified` with the exact capability that was missing. Do not install a browser, a driver, or a test dependency to make a check run. Do not describe a visual outcome as confirmed from source alone.

## 7. Fix Mode

For a reported defect:

1. Reproduce it first, at the viewport, theme, and state the report names, and keep the evidence. A user's observation is ground truth; reproduce to find the cause, not to doubt the report.
2. State the broken relationship in one sentence: which constraint, state, or ownership is wrong.
3. Make the smallest change that corrects that relationship in the project's own style.
4. Re-run the same capture, then the adjacent states and widths, and record before and after.
5. After two failed repair passes, stop and report `blocked` with the evidence.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| Contrast, target size, focus, keyboard, and reflow success criteria | <https://www.w3.org/TR/WCAG22/> |
| Reflow at 320 CSS px | <https://www.w3.org/WAI/WCAG22/Understanding/reflow.html> |
| Target Size (Minimum) is 24 by 24 CSS px | <https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html> |
| Good thresholds for LCP (2.5 s), INP (200 ms), and CLS (0.1) | <https://web.dev/articles/vitals> |
| Computed styles are read from the rendered page | <https://developer.mozilla.org/en-US/docs/Web/API/Window/getComputedStyle> |
| The three evidence labels, the capture matrix, and the fix-mode order | `dbc-hbin/omp-ulw@74df40f frontend` verification and perfection guidance (mechanism reference, re-authored) |

### Evidence grade

`LOCAL` for the labels, the capture matrix, and the fix-mode order. The WCAG criteria and the Core Web Vitals thresholds are `PRIMARY` and dated above; thresholds change, so recheck them before a release gate.
