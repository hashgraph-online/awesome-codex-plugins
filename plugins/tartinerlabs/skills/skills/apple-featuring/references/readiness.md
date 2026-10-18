# Readiness Review

Checks to run before nominating. Mark each finding **Blocking** (would undermine a nomination) or **Strengthen** (raises the odds). For UX depth, use the `ux-psychology` skill when it is available.

## First Launch

Whoever evaluates the app at Apple installs it fresh. An app that only shines after weeks of use shows them an empty screen.

- **Blocking:** the first screens show nothing of value without long setup, an account, or accumulated data
- Offer an immediate taste of the app's value — a clearly labelled demo or sample content, a guided first task, or a meaningful empty state with one action that fills it
- Sign-up and permission requests come after the user has seen value, not before
- The signature interaction is reachable within the first minute

## Platform Fit

"Perfectly tailored to their platform" is an ADA category in itself.

- System components and current platform design (Liquid Glass on the OS 26 releases) rather than custom imitations
- iPad is not a stretched iPhone layout: sidebars, resizable windows, pointer and keyboard support
- Mac apps have a complete menu bar and standard keyboard shortcuts
- Each supported platform feels native to it; cutting a weak platform beats shipping it

## Accessibility

Two featuring considerations and the Inclusivity category depend on it. Check every primary workflow — and when the `accessibility` skill is available, run its audit for the full picture:

- **VoiceOver:** every control labelled; visual content (charts, maps, images) has a meaningful spoken alternative
- **Dynamic Type:** layouts work up to the largest accessibility sizes
- **Reduce Motion:** animations have a calmer alternative
- **Contrast and colour:** text readable; nothing conveyed by colour alone
- Touch targets at least 44×44 pt on iPhone and iPad

## Localization

- Every user-facing string comes from a String Catalog (or `.strings`), with no hard-coded text
- Dates, numbers, currencies, and units use locale-aware formatters
- Layouts survive longer languages and right-to-left scripts
- Localized App Store metadata and screenshots for each supported language
- Content that is culturally relevant, not only translated

## Quality

Editors expect it to work beyond a prepared demo.

- No known crashes in primary flows; check Xcode Organizer crash and energy reports
- Smooth scrolling and transitions on the oldest supported device
- Fast launch; no long blocking spinners
- Works offline or degrades gracefully where the app's purpose allows
- Battery and data use proportionate to what the app does

## App Store Product Page

When the metadata is in the repo (for example `fastlane/metadata/`) or provided:

- Screenshots show the real app and lead with the signature interaction — not a feature list over stock imagery
- An app preview video demonstrates it in the first seconds
- The description opens with what the app does and for whom
- Ratings and reviews come from real users — never incentivised or fabricated (App Store Review Guidelines)

## Category Fit

For the chosen ADA category, ask: is this app the best in its genre at that category's description? If the honest answer is "not yet", the report says what would get it there — or recommends a better-fitting category.
