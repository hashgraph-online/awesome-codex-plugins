# App Store Requirements Baseline

Checked on **2026-10-23**. Apple changes these on its own schedule. Re-open the
primary sources before a submission and record the check date in
`SITE_TO_IOS_PLAN.md`. If a live Apple page and this file disagree, Apple wins.

## Build toolchain

Since April 28, 2026, new apps and updates uploaded to App Store Connect must
be built with Xcode 26 or later against the iOS 26 SDK (or the matching iPadOS,
tvOS, visionOS, or watchOS 26 SDK). Apps already live keep working; the rule
bites on the next upload. Capacitor builds with Xcode 26 without code changes;
the requirement lands on the Mac or CI runner doing the build.

Source: <https://developer.apple.com/news/upcoming-requirements/>

## Privacy manifest

Apps and listed third-party SDKs must declare collected data and the approved
reasons for "required reason" APIs (file timestamps, system boot time, disk
space, user defaults, active keyboards) in `PrivacyInfo.xcprivacy`. Listed SDKs
must ship their own manifest and signature. Missing declarations trigger an
App Store Connect rejection email on upload.

For a wrapper, inventory the Capacitor core, every plugin, and every native SDK.
Web analytics running inside the WebView still count toward the privacy
nutrition label even though they do not appear in the manifest.

Source: <https://developer.apple.com/documentation/bundleresources/privacy-manifest-files>

## Age rating

Apple's age ratings are 4+, 9+, 13+, 16+, and 18+. Developers had to answer the
updated age rating questionnaire in App Store Connect by January 31, 2026, and
every new app answers it before submission. Answer for the real content,
including user-generated and AI-generated content and any in-app web content
the shell can reach.

Source: <https://developer.apple.com/help/app-store-connect/manage-app-information/set-an-app-age-rating/>

## Account deletion

An app that lets users create an account must let them start account deletion
inside the app (Guideline 5.1.1(v)). Find the web product's deletion path during
the audit. It usually needs server work, not app work, and its absence blocks
submission.

Source: <https://developer.apple.com/app-store/review/guidelines/#data-collection-and-storage>

## Login services

Guideline 4.8 no longer requires Sign in with Apple by name. An app that uses a
third-party or social login (Google, Facebook, and similar) as its primary login
must also offer an equivalent login service that limits collection to name and
email, lets the user keep their email private, and does not track for
advertising without consent. Sign in with Apple meets that bar; another
qualifying service can too. Apps using only their own account system are
exempt.

Source: <https://developer.apple.com/app-store/review/guidelines/#login-services>

## Payments

Digital goods and subscriptions sold for use inside the app fall under Guideline
3.1. The rules for linking out to web checkout differ by storefront and, in the
United States, have changed repeatedly through the Epic v. Apple litigation
since 2025. Do not write review notes about Stripe or web checkout from memory:
read the live 3.1.1, 3.1.1(a), and 3.1.3 text, check which storefronts the app
ships to, and state in the plan which flow the app exposes in each.

Source: <https://developer.apple.com/app-store/review/guidelines/#payments>

## Minimum functionality (4.2)

Apps that are a repackaged website, a bookmark, or a content mirror with no
lasting native value get rejected under 4.2. This is the gate in `SKILL.md`.

Source: <https://developer.apple.com/app-store/review/guidelines/#minimum-functionality>

## Kids Category and children's data

For StoryBeam-style reading, story, and lesson apps aimed at children:

- Kids Category apps must not include third-party analytics or advertising
  (Guideline 1.3), must put a parental gate in front of links out of the app,
  purchases, and other engagement that takes a child away from the app, and
  must follow 5.1.4 on children's data.
- Under the amended COPPA Rule, with full compliance required from April 22,
  2026, a service directed to children under 13 in the US needs verifiable
  parental consent before collecting personal information, separate consent
  for disclosure to third parties, a written data retention policy, and a
  written security program. The simplest compliant design for a kids' content
  app collects none: no child accounts, no free-text input that can capture a
  name, school, or location, no voice or photo capture, no persistent
  identifiers sent to third parties.
- AI-generated stories, illustrations, and narration must be screened for the
  declared age band before display. Record the screening step in the plan.
- State and platform age-assurance rules (Apple's Declared Age Range API,
  US state app-store age laws) are moving. Check the live status before
  submission rather than relying on this file.

Sources:

- <https://developer.apple.com/app-store/review/guidelines/#kids-category>
- <https://developer.apple.com/app-store/review/guidelines/#kids>
- Amended COPPA Rule, 90 FR 16918 (April 22, 2025):
  <https://www.federalregister.gov/documents/2025/04/22/2025-05904/childrens-online-privacy-protection-rule>

Legal questions about a specific kids' app go to counsel. This file tells the
agent what to check, not what the law requires of a particular product.
