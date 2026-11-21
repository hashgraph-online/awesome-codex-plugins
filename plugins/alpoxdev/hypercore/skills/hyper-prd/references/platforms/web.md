# Web Platform Checklist

Load this file only when the PRD's decided platforms include web. It owns the items that fill the platform requirements block and its release gate table: supported browsers, responsive layout, accessibility conformance, Core Web Vitals, session handling, and search visibility.

## Contents

- How to use
- Supported browsers
- Responsive layout
- Accessibility
- Core Web Vitals
- Sessions and re-authentication
- Search visibility
- Release gate rule
- Sources

## How to use

- Copy the items into the platform requirements block and answer each one in the PRD's own words. Do not paste this table into the PRD.
- The grade decides what the release gate table must contain: every `[M]` and `[M-조건]` item gets a conclusion (applies / not applicable with a reason / `[확인 필요]`). A `[G]` item is written only when it is relevant to the product.
- `[M-조건]` items carry their condition in the sentence. When the condition is false, write "not applicable" and the reason in the gate table instead of deleting the row.
- An item that cannot be verified as written is not a requirement. "Follow the accessibility guidelines" is forbidden; name the success criterion and the observable state.
- Every numeric target carries a threshold, a measurement method, and a percentile. "Fast enough" is not a target.
- The check date is 2026-11-07 for every row. Standards revisions, browser support windows, and metric thresholds change; re-check each row every quarter and update the date.

## Supported browsers

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| W1 | `[G]` | Baseline floor: write which Baseline tier the support promise uses, `newly available` or `widely available`, and the browser and version set that tier resolves to on the release date. Record where the tier is checked for each web platform feature the build relies on. | https://web-platform-dx.github.io/baseline/ | 2026-11-07 |
| W2 | `[G]` | Behavior below the floor: write what a visitor on an older browser sees (a message naming the required version, or a reduced read-only view) and the check that detects the shortfall. | https://web-platform-dx.github.io/baseline/ | 2026-11-07 |

## Responsive layout

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| W3 | `[G]` | Content-based breakpoints: state each breakpoint as a content width in CSS pixels and what in the content needs it. "Don't define breakpoints based on device classes": a device name in a breakpoint is a defect. | https://web.dev/articles/responsive-web-design-basics | 2026-11-07 |
| W4 | `[G]` | Supported width range: write the minimum and maximum viewport width in CSS pixels that the layout serves, and what the page does outside that range. Measurement: resize one continuous window across the range and record every point where the layout changes. | https://web.dev/articles/responsive-web-design-basics | 2026-11-07 |

## Accessibility

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| W5 | `[M-조건]` | Condition: a law, a regulation, a public procurement rule, or a customer contract requires WCAG 2.2 AA conformance. Write the conformance level, the pages in scope, and the audit record: one pass or fail per AA success criterion. | https://www.w3.org/TR/WCAG22/ (5.2.1 Conformance Level) | 2026-11-07 |
| W6 | `[M-조건]` | Condition: a law, a regulation, a procurement rule, or a contract requires WCAG 2.2 AA conformance. Pointer targets measure at least 24 by 24 CSS pixels at 100% zoom. Where a target is smaller, record which of the five exceptions applies: Spacing (a 24 CSS pixel diameter circle centred on each undersized target's bounding box does not intersect another target or another undersized target's circle), Equivalent (the function can be achieved through a different control on the same page that meets the criterion), Inline (the target is in a sentence or its size is otherwise constrained by the line-height of non-target text), User Agent Control (the size is determined by the user agent and is not modified by the author), Essential (a particular presentation of the target is essential or is legally required for the information being conveyed). Threshold: 24×24 CSS px. Measurement: measure the rendered box of each interactive target. | https://www.w3.org/TR/WCAG22/ (2.5.8 Target Size (Minimum)) | 2026-11-07 |
| W7 | `[M-조건]` | Condition: the same WCAG 2.2 AA obligation. Each of the five other new criteria at Level A or AA gets its own conclusion: 2.4.11 Focus Not Obscured (Minimum) AA, 2.5.7 Dragging Movements AA, 3.2.6 Consistent Help A, 3.3.7 Redundant Entry A, 3.3.8 Accessible Authentication (Minimum) AA. | https://www.w3.org/TR/WCAG22/ | 2026-11-07 |

## Core Web Vitals

Field data for the page group, reported separately for mobile and desktop. Report each value at the 75th percentile (p75) of page loads, from first-party real-user monitoring or the CrUX dataset. The PRD states the reporting window of the field-data source it uses. Lab measurements are a build-time check, not the gate value.

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| W8 | `[G]` | Largest Contentful Paint: threshold LCP ≤ 2.5s @p75, mobile and desktop separately. Measurement: field data for the page group, p75 of page loads, over the reporting window the PRD names. | https://web.dev/articles/vitals | 2026-11-07 |
| W9 | `[G]` | Interaction to Next Paint: threshold INP ≤ 200ms @p75, mobile and desktop separately. Measurement: field data for the page group, p75 of page loads, over the reporting window the PRD names. | https://web.dev/articles/vitals | 2026-11-07 |
| W10 | `[G]` | Cumulative Layout Shift: threshold CLS ≤ 0.1 @p75, mobile and desktop separately, as a unitless score. Measurement: field data for the page group, p75 of page loads, over the reporting window the PRD names. | https://web.dev/articles/vitals | 2026-11-07 |

## Sessions and re-authentication

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| W11 | `[G]` | Timeouts: write the idle timeout in minutes and the absolute timeout in hours, chosen by the risk of what the session can reach, and list the actions that force re-authentication (changing a password, changing an email address, a payment, an administrative action). Measurement: leave a test session idle past the idle timeout and confirm the re-authentication prompt; run one sensitive action after the absolute timeout and confirm it is refused. | https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html (Idle Timeout, Absolute Timeout) | 2026-11-07 |
| W12 | `[G]` | Renewal and invalidation: the session identifier changes at sign-in and at a privilege change, and sign-out invalidates the session on the server, not only in the browser. Measurement: capture the identifier before and after sign-in and after the privilege change, confirm it changed each time, and confirm the pre-sign-out value is rejected afterwards. | https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html (Renew the Session ID, Logout) | 2026-11-07 |

## Search visibility

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| W13 | `[G]` | Crawlable and indexable: each indexable page template returns 200, carries its primary content in the served HTML, is reachable by a link, and is not blocked by `robots.txt` or a `noindex` directive. Measurement: fetch one URL per template as a crawler and record the status, the directive, and the rendered text. | https://developers.google.com/search/docs/essentials | 2026-11-07 |
| W14 | `[G]` | Metadata and discovery: every indexable template has a unique title and description, one canonical URL, and one entry in the submitted sitemap. Measurement: list the templates, one URL each, and record the title, the description, the canonical, and the sitemap entry. | https://developers.google.com/search/docs/essentials | 2026-11-07 |

## Release gate rule

Every `[M]` and `[M-조건]` row above appears in the PRD release gate table with one conclusion:

| Conclusion | When to write it |
|---|---|
| applies | The obligation holds and the PRD states the observable state that satisfies it. |
| not applicable + reason | The condition is false (no accessibility obligation, another channel), and the reason names the decision. |
| `[확인 필요]` | The answer is not in the repository or the conversation; name who answers it. |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Pointer target minimum for WCAG 2.2 AA | [WCAG 2.2](https://www.w3.org/TR/WCAG22/) - "The size of the target for pointer inputs is at least 24 by 24 CSS pixels" |
| The five 2.5.8 exceptions | [WCAG 2.2](https://www.w3.org/TR/WCAG22/) - "The size of the target for pointer inputs is at least 24 by 24 CSS pixels, except when:" followed by Spacing, Equivalent, Inline, User Agent Control, and Essential |
| Breakpoints follow the content, not device classes | [Responsive web design basics](https://web.dev/articles/responsive-web-design-basics) - "Don't define breakpoints based on device classes" |
| Core Web Vitals thresholds and the p75 field measurement | [Web Vitals](https://web.dev/articles/vitals) - "a good threshold to measure is the 75th percentile of page loads, segmented across mobile and desktop devices" |
| Baseline tiers and the browser set behind each tier | [Baseline](https://web-platform-dx.github.io/baseline/) |
| Session timeout, renewal, and invalidation | [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) |
| Crawlability, indexability, and page metadata | [Google Search Essentials](https://developers.google.com/search/docs/essentials) |

### Evidence grade

`LOCAL` - the id scheme, the grades, and the release gate rule are this package's design assembled from the sources above. The WCAG sentence and the breakpoint sentence are quoted verbatim from the pages listed; the metric thresholds follow the Web Vitals page. Standards revisions and metric thresholds change, so the quotes and the 2026-11-07 check date must be re-verified every quarter before a release gate is signed off.
