---
name: site-to-ios-app
description: "Suede AI Site to iOS App Skills. Use when asked to \"turn this site into an iOS app\" or convert a PWA: inspect the URL, choose shell or native strategy, then deliver an audit, build plan and release evidence. NOT FOR: Android builds (android-app-factory), Play rollout (suede-play-release), store listing strategy (suede-aso), or a native iOS app with no website."
metadata:
  display-name: "Suede AI Site to iOS App Skills"
---

# Suede AI Site to iOS App Skills

Read [the worked delivery contract](references/worked-contract.md) for a concrete
input, expected artifact, failure response and validation example.

## Compatibility

Agent with web/browser and repo access; macOS with the required Xcode/SDK and project toolchain for iOS builds; signing/account access only for separately authorized release actions.

## Gate policy

Every check and verdict here is advice to the user, not a control on the agent.
Run the checks, report results honestly, and complete what the user asked. A
failed gate changes the report, never the work. The one exception: a finding
that risks data loss, credential exposure, a legal or rights violation, a
payment mistake, or irreversible public damage. Pause, name the risk, give the
options, and let the user choose.

## Principle

A site becomes an iOS app when the app adds native value, behaves like iOS, and
the store listing describes what the build actually does. A web page in a frame
is a Guideline 4.2 rejection waiting to happen.

## Start here

1. Read `references/site-to-ios-runbook.md` before scaffolding or touching an
   existing wrapper.
2. Read `references/app-store-requirements.md` and re-check each dated item
   against Apple's live pages. Record what you checked and when in the plan.
3. If a URL is reachable, write `SITE_TO_IOS_AUDIT.md` from live evidence:
   URL checked and date, route map with auth needs, iPhone-width behavior, PWA
   signals, legal/support/account-deletion links, payment and sensitive flows,
   auth and session behavior, performance risks, native value opportunities,
   and the 4.2 verdict.
4. Write `SITE_TO_IOS_PLAN.md`: chosen strategy and why, native value to ship
   before release, build commands, bundle ID and signing notes, QA matrix,
   store asset and privacy work, blockers, and the release gate.

`references/worked-example.md` shows a full audit excerpt, plan excerpt, and
the verdict message. Read it when you need the expected depth.

## Strategy

Pick one route and write down why:

- **Capacitor remote shell**: the live site stays the product; web deploys
  change app behavior.
- **Capacitor bundled shell**: static or SPA assets ship in the binary; changes
  need a new App Store build unless backed by live APIs.
- **Native SwiftUI shell with WebView**: native navigation, settings, auth,
  push, share, error, and account screens around a site view.
- **Full native rebuild**: the site is mostly content, its mobile UX is weak,
  or wrapper risk is high.

## App Store 4.2 gate

Halt when the app would be a bookmark, content mirror, or unmodified website.
Name the exact 4.2 exposure from the audit, offer the options (add native value
from the list below, rebuild natively, ship as a web app, or submit with the
rejection risk on record), and wait for the user's pick. Native value that
counts:

- iOS-native onboarding, empty states, errors, offline, and retry.
- Native settings with support, privacy, terms, account deletion, restore, and
  notification controls where they apply.
- Universal links or deep links that work from a cold start.
- Share sheet, widgets, push, camera/media/file pickers, Wallet, StoreKit, or
  other native capabilities, only where they serve the product.
- Safe-area, keyboard, navigation, dark/light mode, and Dynamic Type handling.

Push, a native settings screen, and working universal links together are the
smallest bundle that reliably reads as an app rather than a bookmark.

## Kids and family apps

If the app is for children (a StoryBeam-style reading or story app, a beginner
lesson app) or lands in the Kids Category, the plan must hold to these before
anything else:

- Collect no personal data from children. No accounts for kids, no free-text
  fields that could capture names or locations, no photos, voice, or contact
  uploads, no precise location.
- No third-party analytics or advertising SDKs in a Kids Category app, and a
  parental gate in front of external links, purchases, and settings.
- Content stays age-appropriate for the declared age band, including
  AI-generated stories, images, and audio. Generated output needs a review or
  filtering step before a child sees it.
- Answer the age rating questionnaire for the real content and features.

Details and sources are in `references/app-store-requirements.md`. A rule
conflict here is an extreme-risk finding: pause and put it to the user.

## Conversion flow

1. Audit the URL: responsive behavior, PWA assets, auth, payments, privacy,
   support, route depth, mobile performance.
2. Pick the strategy and write `SITE_TO_IOS_PLAN.md`.
3. Scaffold or adapt the project with the repo's package manager and iOS
   conventions.
4. Configure bundle ID, display name, icon, launch screen, associated domains,
   Info.plist usage strings, privacy manifest, and entitlements.
5. Build native value and failure states before visual polish.
6. For Capacitor shells, run the web build, then `cap sync ios`.
7. Test on a named simulator or device: first launch, auth, deep links, tabs,
   keyboard, payments, offline, backgrounding, account flows.
8. Produce screenshots, metadata, privacy answers, age rating answers, and
   review notes. Hand listing copy, keywords, and screenshot sequencing to
   `suede-aso` so the listing is built for search, not just for review.
9. Run the release gate. Submit only when the user explicitly delegates public
   release and confirms the app, bundle ID, version, build, and account.

## Completion bar

Do not call the app release-ready until:

- the project builds with the current required Xcode and SDK on a named target
  (`xcodebuild -scheme <App> -destination 'generic/platform=iOS Simulator'
  build` exits 0, or a named device or CI run);
- every native plugin, permission string, and entitlement maps to real
  behavior;
- the privacy manifest covers the app and every bundled SDK that needs one;
- the web route or bundle strategy is written down;
- the 4.2 risk has a mitigation;
- screenshots and metadata match shipped features;
- privacy answers match the real SDKs, cookies, analytics, and account flows;
- no secrets, signing material, or private account identifiers are committed
  (`git status --short` clean; `git grep -nE 'PRIVATE KEY|AuthKey_'` empty).

## Routing

- Android version of the same product → `android-app-factory`, then
  `suede-play-release` for delivery.
- App Store listing, keywords, screenshots, and ratings strategy →
  `suede-aso`.
- Constants that must match across iOS, Android, and web →
  `suede-parity-contract`.
- A native iOS app with no website behind it, or repair of an existing
  Capacitor shell, is outside this pack (private Suede AI companions, not in
  this pack).
