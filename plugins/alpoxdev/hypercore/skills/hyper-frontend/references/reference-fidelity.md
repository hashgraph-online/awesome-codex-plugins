# Reference Fidelity

Read this reference in `match` mode, when the user supplies a concrete visual target: a screenshot, a mockup image, a design export, or a live page to reproduce. The reference is the contract. This file decides how to extract it, build to it, and prove the match.

## Contents

1. Extract the Contract
2. Live Page References
3. Build to the Contract
4. Prove the Match
5. Limits

## 1. Extract the Contract

Before writing code, write down what the reference fixes, from measurement and not from impression:

| Part | What to record |
|---|---|
| Tokens | Colors, font families and sizes, weights, line heights, radii, shadows, spacing steps; each as a value with the element it came from |
| Geometry | Container widths, column counts, gaps, alignment, and sizes of the main elements at the reference width |
| Copy | The visible text exactly, including capitalization and punctuation |
| States | Hover, focus, active, disabled, empty, and error states, when the reference shows or implies them |
| Responsive intent | How the reference behaves at other widths when it shows them; otherwise, a stated assumption |

Record the contract in the project's token file or design document when one exists; otherwise in the report. Mark each unknown as an assumption instead of filling it in silently.

## 2. Live Page References

For a public page the user names:

- Read runtime truth in a browser: computed styles, layout rectangles, transitions, and keyframes, instead of reading minified source.
- Sample the default, hover, focus, and active state of the main controls, and the page at the widths you will capture.
- Take only what the reference needs for the contract. Do not copy another site's logo, brand imagery, fonts without a license, or marketing copy; use the user's own content or labeled placeholders.
- A page that cannot be read with a plain fetch is a different problem from matching it; report that boundary instead of working around a block or a login.

## 3. Build to the Contract

- Build reusable primitives that carry the extracted tokens, not a one-off that matches one screenshot. A second screen using the same primitives must work without new magic numbers.
- Take values from the contract; reuse the project's existing tokens where a contract value equals one, and add a token only for a new value.
- Keep the project's component, routing, and data conventions. The reference decides appearance, not architecture.

## 4. Prove the Match

1. Capture the build at the same viewport as the reference, in the same state, with the same content.
2. Compare side by side and by measurement: token values, element sizes, and positions. A visual compare alone is not enough.
3. List every deviation with its reason. An unexplained deviation is a failure; an accepted one needs the user's agreement or a stated technical reason.
4. Check the states and the other widths the contract covers, then the rest of [rendered-verification.md](../rules/rendered-verification.md).

## 5. Limits

- A static image cannot show behavior, so behavior beyond the shown states is an assumption and is labeled.
- Fonts, images, and icons that are not available or licensed are replaced with the closest available choice, and the substitution is reported.
- The match is for the viewport, theme, and content captured; say so instead of claiming the page matches everywhere.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| Computed styles and layout are read from the rendered page | <https://developer.mozilla.org/en-US/docs/Web/API/Window/getComputedStyle> |
| Treating a concrete reference as a contract, extracting tokens and geometry, and proving the match with a deviation list | `dbc-hbin/omp-ulw@74df40f frontend` reference-fidelity guidance (mechanism reference, re-authored) |

### Evidence grade

`LOCAL`: the contract table, the primitive rule, and the proof order are this package's chosen procedure. The source repository has no license file at the pinned commit, so nothing was copied.
