# Native Platforms

Read when the work is an iOS or Android screen — SwiftUI, UIKit, Jetpack Compose, or the platform views — instead of a web page. The platform replaces the web rules in this package: system type styles and Dynamic Type replace CSS type tokens, safe areas replace viewport padding, navigation stacks and tabs replace page routing, and platform colors replace hex tokens. The brief, the tokens, and the delivery gate do not change; only the surface does.

## Contents

- 1. Type and scaling
- 2. Safe areas and insets
- 3. Navigation and structure
- 4. Touch and controls
- 5. Color and appearance
- 6. Evidence for a native screen
- 7. Web rules that transfer only as principles

## 1. Type and scaling

| Tell | Why | Fix |
|---|---|---|
| Fixed text sizes tuned for one device | Users raise or lower the text size; fixed values overflow or crowd at other settings | Start from the platform text styles and let the system scale them; check the smallest and largest sizes before delivery |
| A size list copied from a CSS scale (16/20/24/32px) | The app reads as a web page squeezed into a phone | Map each role to the nearest system style, then break ties with the token plan |
| Text that clips at the largest size | The layout has no room to grow | Let containers grow or wrap; keep lines of text out of fixed-height boxes |

## 2. Safe areas and insets

| Tell | Why | Fix |
|---|---|---|
| Content pinned to the screen edges | The notch, the status bar, the home indicator, or the gesture area covers it | Inset to the safe area; the platform layout primitives do this by default, so never ignore the insets |
| A fixed header that ignores the status bar and home indicator | Text and controls sit under system chrome | Let the platform place its own chrome; add a custom bar below it |
| One layout for phone, tablet, foldable, and split-screen windows | The phone layout stretched looks like a mistake | Treat the compact and regular widths as different layouts, the way `responsive-reflow.md` treats the phone and the desktop |

## 3. Navigation and structure

| Tell | Why | Fix |
|---|---|---|
| A web-style top menu rendered inside the app | The user has to learn the site again | Use the platform containers: navigation stacks for drill-down, tabs for the few primary destinations, a sheet for a bounded task |
| Back buttons that go nowhere or just close the app | The stack was never modeled | The top of the stack is the list; every pushed screen can return to its parent |
| Every screen a modal | Sheets promise a short task and a clear exit | Push for hierarchy, and reserve sheets for bounded tasks |

## 4. Touch and controls

| Tell | Why | Fix |
|---|---|---|
| Controls smaller than the touch floor | A finger is not a cursor | 44pt on iOS and 48dp on Android as the minimum, with padding or a larger hit area when the visual is smaller. The evidence and the reason are in `responsive-reflow.md` §5 |
| Two adjacent targets that read as one | The thumb touches the wrong one | A clear gap so one press area never covers the next |
| Anything that exists only on hover | There is no hover on a touchscreen | A tap equivalent for every hover interaction, with visible pressed feedback |
| Gestures without a visible alternative | Some users cannot perform the gesture | A button or menu path for the same action |

## 5. Color and appearance

| Tell | Why | Fix |
|---|---|---|
| Hard-coded hex colors everywhere | Dark mode, forced colors, and higher-contrast settings break the screen | Semantic platform colors (label, secondary label, background, separators, and the Android equivalents); they carry the light and dark values and the accessibility settings with them |
| Every theme re-tuned by hand after switching | Each value drifted from its role | Name the role once, then resolve it per appearance |
| Dark mode chosen because it "looks tech" | A trend, not a product decision | Both appearances work, unless the brief pins one; verify both before delivery |

## 6. Evidence for a native screen

A CSS token, a Lighthouse report, or a browser screenshot never proves anything about an app. Proof for a native screen is one of:

- A simulator or device capture at the checked size classes, with the text-size setting stated.
- The accessibility inspector output for the screen: labels, roles, and states, not the builder's impression.
- The platform preview or screenshot tests the project already runs, named with their output.

Without a simulator or device, mark the rendered items `static_only` or `unavailable` with the reason, exactly as a missing browser is reported in the web path. Never report a visual or accessibility pass from the source alone.

## 7. Web rules that transfer only as principles

Contrast, the purpose test, honest placeholders, and the delivery gate transfer unchanged — they are about the product, not the medium. What does not transfer: CSS tokens, breakpoint names, hover and cursor behavior, browser chrome, Lighthouse numbers, and any viewport claim. When a web rule and a platform rule disagree, the platform rule wins for the app, and the disagreement is written down in the brief.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| System text styles are the starting point for type on Apple platforms, and the styles scale with the preferred text size | <https://developer.apple.com/design/human-interface-guidelines/typography> |
| The Compose Material 3 type scale, and building app UI in Compose | <https://developer.android.com/develop/ui/compose>, <https://m3.material.io/styles/typography/overview> |
| The idea and the section shape (platform rules replace web rules; proof is a simulator or device capture, not a browser mockup) | `dbc-hbin/omp-ulw @ 74df40f` (2026-11-09), re-authored in this package's own words; the source repository has no license and no text or code was copied |

### Evidence grade

The platform facts come from the vendor guidance above. The rest is a practitioner rule set over this package's existing rules, with no measurements taken.
