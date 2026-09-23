# Avoiding AI Slop

Improve clarity, appropriateness and craft. Do not use a supposed AI fingerprint as a substitute for understanding the product. SKILL.md governs scope and authority. Existing brand decisions remain valid unless the user authorizes changing them.

## Separate defects from preferences

**Defects and violated requirements:** broken interactions or assets, inaccessible controls, misleading content, missing requested behavior, unreadable content, accidental overflow, and departures from an explicitly adopted project contract. These require evidence and repair or an explicit unresolved finding.

**Context-dependent warnings:** weak hierarchy, repetition, crowded composition, unhelpful decoration, unnecessary motion or unexplained inconsistency. Describe the user-visible consequence and inspect the rendered result before proposing a change.

**Aesthetic preferences:** font popularity, white or black backgrounds, cream or purple palettes, card count, sidebars, corner radii, punctuation and illustration style. None is a universal defect. Preserve deliberate choices. A static source match cannot determine whether a design is tasteful or whether AI made it.

The detector's historical `slop` category is advisory by default. Project owners may adopt specific additional blocking rule IDs. The static gate separately requires review of selected accessibility and broken-output findings; it cannot certify rendered readiness.

## Review questions

Can the intended user identify the primary task? Does the hierarchy explain what matters? Is density appropriate for the task? Are interaction states recognizable and recovery paths available? Does the interface fit neighboring product flows and the approved identity?

For a genuinely new brand direction, comparing alternatives or using an inverse test can reveal an unexamined default. These are optional exercises, not binary proof. Familiarity is often valuable in product navigation, forms and transactions. Do not redesign a conventional control solely to make it unusual.

Use real references to explain specific decisions. Do not copy a page or claim a reference was inspected when it was not. A physical-scene exercise can inform context; it must not force every application into a light/dark aesthetic.

## Truthful content and assets

Use sourced production metrics, customer logos, endorsements, prices and specifications. Do not replace obviously round invented numbers with more plausible invented numbers. Do not invent people or customer relationships for social proof.

Preview fixtures must be visibly labeled as sample or demonstration content. A hidden HTML comment is not sufficient. Mark placeholders in the task report and do not present them as production-ready data. Use licensed, approved assets; verify an asset exists instead of guessing a URL. Do not contact external asset services or upload private material without authorization.

Meaningful images need useful alternatives. Decorative images should not generate screen-reader noise. Do not outlaw every empty alt attribute or insist on imagery when the brief and available assets do not justify it.

## Output completeness and safe limits

Deliver requested implementation without omitted function bodies or disguised placeholder sections. Preserve legitimate code syntax such as spread operators and meaningful tracked TODOs; a blanket token blacklist is not a completeness validator.

Map requirements to files, tests and findings. When a capability or environmental dependency is missing, report the exact gap. Honest partial completion is better than fabricated success. Do not attribute incompleteness to speculative claims about model training, seasons, token budgets or safety tuning.

If a task cannot finish within its repair budget, stop mutation and record attempts, remaining failures and the next concrete action. Never erase unrelated work to manufacture a clean state.

## Evidence-based completion

Run relevant static and functional checks. Inspect rendered states for UI changes using the available browser/native harness. Automated accessibility tests are useful but cannot establish complete conformance by themselves.

A static pass means only that the executed static check passed on its recorded scope. Missing or ignored-only inputs cannot establish success. Record unavailable checks as NOT_RUN. Task completion and UI readiness are independent: an audit can be complete while its subject fails.

The legacy 85-point aesthetic threshold is retired. A score cannot compensate for failed behavior, accessibility or missing evidence. Never call unrendered output production-ready merely because no source pattern matched.

## Primary verification references

- [Playwright accessibility limitations and testing](https://playwright.dev/docs/accessibility-testing)
- [Playwright visual-comparison controls](https://playwright.dev/docs/test-snapshots)
