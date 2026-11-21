# Worked Example: SaaS Dashboard to iOS

A synthetic run showing the depth expected from the audit, the plan, and the
verdict. The product and URL are invented.

## Prompt

```
Audit https://app.shiftly.example and plan its conversion into an iOS app.
It is a shift-scheduling SaaS for restaurant managers.
```

## Excerpt from `SITE_TO_IOS_AUDIT.md`

```markdown
# Site to iOS Audit: Shiftly

URL checked: https://app.shiftly.example (2026-10-20)
Target user: restaurant shift managers and hourly staff
Core job: publish a weekly schedule, claim and swap shifts

## Route map
| Route | Auth | Notes |
| --- | --- | --- |
| /login | public | email + Google OAuth |
| /schedule | required | primary surface, drag-and-drop grid |
| /shifts/:id | required | deep-link target, no canonical URL yet |
| /billing | required | Stripe Checkout redirect, web only |
| /help | public | support articles |
| /legal/privacy, /legal/terms | public | present |
| account deletion | MISSING | no self-serve delete path found |

## Responsive behavior at iPhone widths
- 390pt: schedule grid overflows horizontally, no momentum scrolling.
- Bottom action bar sits under the home indicator (no safe-area padding).
- Shift chips measure about 28pt tall, below the 44pt touch target guidance.

## PWA signals
- manifest.webmanifest present with 192 and 512 icons.
- apple-touch-icon and theme-color set. Service worker caches assets only;
  no offline route.

## Auth and session
- Google OAuth redirects out and back to /schedule.
- Session cookie SameSite=Lax, 30-day persistence.
- Google is the primary social login, so Guideline 4.8 needs an equivalent
  privacy-limited login option alongside it (Sign in with Apple qualifies).

## Sensitive flows
- Payments: Stripe Checkout subscription for managers, web redirect.
- Personal data: names, phone numbers, shift availability.

## App Store 4.2 wrapper risk: HIGH
A shell over /schedule with no native surfaces is a repackaged website:
no native settings, no offline or retry state, no push, no deep-link
handling, and no account deletion path (also a 5.1.1(v) blocker).
```

## Excerpt from `SITE_TO_IOS_PLAN.md`

```markdown
## Strategy: Capacitor remote shell
/schedule is the product and ships web changes weekly. A full native rebuild
of the drag-and-drop grid is a quarter of work, not a conversion.

## Native value before release (4.2 mitigation)
1. Native onboarding: 3 screens, no web content.
2. Native settings: support, privacy, terms, notification toggles, restore,
   and self-serve account deletion.
3. Push for shift published, swap requested, shift claimed. This is the
   strongest 4.2 argument the app has.
4. Universal links for /shifts/:id from cold and warm start.
5. Native offline state and retry for schedule fetch failures.
6. Safe-area, keyboard, and Dynamic Type handling in the shell chrome.

## Requirements checked (2026-10-20)
- Xcode 26 / iOS 26 SDK on the CI runner.
- PrivacyInfo.xcprivacy for the app plus Capacitor core and each plugin.
- Age rating questionnaire answered: no UGC visible to other users.

## Blockers
- BLOCKED: account deletion does not exist on the web product either.
  Ships server-side before submission.
- OPEN: Guideline 4.8 login option alongside Google OAuth.
- OPEN: which purchase flow the app exposes in each storefront. Read the live
  3.1 rules for the target storefronts before writing review notes.

## Build
xcodebuild -scheme Shiftly \
  -destination 'generic/platform=iOS Simulator' build

## Release gate
HOLD. Native value items 1-5 incomplete, account deletion missing, 4.8 login
option missing.
```

## Verdict returned to the user

```
App Store 4.2 verdict: HIGH risk, gate held.
As specified, this is a bookmark to /schedule. Options:
  1. Add the native value in the plan (push, settings, and deep links are
     the minimum worth submitting).
  2. Rebuild the schedule grid natively in SwiftUI.
  3. Ship it as a PWA and skip the App Store.
  4. Submit as-is with the rejection risk on record.
Two items block submission on any route: account deletion and the 4.8 login
option. Pick an option and I will write the build.
```

## Tips that change outcomes

- Run the audit before anyone writes code. The 4.2 verdict changes the budget,
  and learning it from a rejection costs a review cycle per attempt.
- Request only the entitlements and plugins the app uses. An unjustified
  permission string is both a review risk and a privacy-label mismatch.
- Write the update route into the plan. A remote shell means web deploys change
  shipped app behavior; a bundled shell means every change is a new binary.
- Make privacy answers match the SDKs, cookies, and analytics the web surface
  actually loads, not the ones the team meant to keep.
- Test deep links from a cold start. Warm-start handling passes far more often.
