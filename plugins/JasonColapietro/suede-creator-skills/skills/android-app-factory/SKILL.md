---
name: android-app-factory
description: "Suede AI Android App Factory Skills. Use when asked to \"build an Android app\" or modernize a Kotlin/Compose product: architecture, policy, privacy, billing, tests and a Play-ready release evidence package. NOT FOR: Play uploads or rollout (suede-play-release), website-to-iOS conversion (site-to-ios-app), review-only work (suede-code), or store listing strategy (suede-aso)."
metadata:
  display-name: "Suede AI Android App Factory Skills"
---

# Suede AI Android App Factory Skills

Read [the worked delivery contract](references/worked-contract.md) for a concrete
input, expected artifact, failure response and validation example.

## Compatibility

Agent with repo read/write and shell access; Android SDK/JDK and project Gradle toolchain for builds, emulator/device for runtime proof, web access for current official Play policy.

```
Iron Law: no release-ready claim without a signed `bundleRelease` plus a live
Play Console check, not a debug build, screenshot, source read, or upload.
```

## Gate policy

Every check and verdict here is advice to the user, not a control on the agent.
Run the checks, report results honestly, and complete what the user asked. A
failed gate changes the report, never the work. The one exception: a finding
that risks data loss, credential exposure, a legal or rights violation, a
payment mistake, or irreversible public damage. Pause, name the risk, give the
options, and let the user choose.

## Principle

Build the product, policy evidence, and Play listing together. A successful
release is an installable and usable app whose claims, disclosures,
entitlements, privacy behavior, and store configuration agree.

## Source Truth and Freshness

At the start of every release-oriented run:

1. Identify the exact repo, package/application ID, branch, Play app, target
   track, and whether the checkout is dirty.
2. Read `references/play-policy-baseline.md`.
3. Re-open the linked official Google sources for any submission-sensitive
   requirement. Record the URL, observed requirement, and check time in
   `assets/android-release-gate.template.md`.
4. Treat current repo code and the live Play Console as source truth for the
   app. Treat the reference date as a baseline, not permanent policy.

Take the target-SDK default and enforcement dates from the baseline file, never
from memory. As of the 2026-10-23 baseline, phone and tablet submissions must
target API 36 (extensions end 2026-11-01) and use Play Billing Library 8 or
later. Recheck every run: form-factor exceptions and dates differ, and Google
announces the next year's level each spring.

## Delivery Contract

Lock these before implementation:

- user and one core outcome;
- supported form factors, devices, locales, minimum SDK, and offline behavior;
- application ID, ownership, signing model, Play app/track, and release owner;
- data inventory, third-party SDKs, permissions, account model, deletion path,
  privacy policy owner, and Data Safety owner;
- monetization and entitlement source truth, or an explicit free-v1 decision;
- architecture and migration constraints;
- acceptance devices/API levels, tests, performance/accessibility targets,
  store artifacts, and release evidence;
- external mutations requiring confirmation: product creation, credential use,
  Play upload, track promotion, staged rollout, or production release.

Unknowns stay unknown. Never invent a package name, product ID, policy answer,
privacy URL, customer claim, or Play Console state.

## Production Pipeline

1. **Validate the product**: define the user outcome and evidence of demand.
   Treat keyword research as one input, not proof of product-market fit.
2. **Verify policy**: capture current target-SDK and form-factor rules, app
   access requirements, Data Safety scope, content rating, account deletion,
   billing policy, and any permission-specific declarations.
3. **Design architecture and risk**: use the smallest maintainable architecture
   that preserves unidirectional state, lifecycle safety, offline/error/loading
   states, test seams, and a least-data/least-permission posture.
4. **Scaffold**: native Kotlin + Jetpack Compose by default. Resolve current
   stable Android/Jetpack versions from official sources, lock them in a version
   catalog, and prove a debug build before feature work.
5. **Build the core loop**: implement one complete user outcome with real or
   deterministic demo data. Add history, saved state, sync, or accounts only
   when the product contract requires them.
6. **Prove quality**: unit, repository, ViewModel, Compose UI/instrumented,
   accessibility, and end-to-end core-loop tests as applicable; static analysis,
   release build, device/API matrix, baseline profile, and Macrobenchmark.
7. **Add monetization safely**: use Play Billing for covered digital goods,
   process pending purchases, verify and acknowledge purchases after entitlement
   handling, restore ownership, and keep secrets/server verification off-device.
8. **Complete trust surfaces**: privacy policy, Data Safety, SDK data behavior,
   permission rationale, in-app and web account deletion when accounts exist,
   content rating, ads declarations, app access instructions, and Play Integrity
   only where abuse risk justifies it.
9. **Build store artifacts**: truthful listing, icon/feature graphic,
   screenshots for every declared form factor, localization, support contact,
   release notes, and reviewer instructions. Route title, short description,
   keyword coverage, and screenshot sequencing to `suede-aso`; a listing that
   passes review but cannot be found ships nothing.
10. **Hand off to release**: signed AAB, Play App Signing, completed release
    gate, then `suede-play-release` for credential preflight, testing-track
    upload, promotion, staged rollout, and the live track readback.

Read these before building:

- `references/android-factory-pipeline.md`: phase artifacts and release flow;
- `references/architecture-and-quality.md`: architecture, tests,
  accessibility, performance, and build checks;
- `references/privacy-billing-integrity.md`: privacy, Data Safety, account
  deletion, Billing, and Integrity controls;
- `references/play-policy-baseline.md`: dated official-policy baseline;
- `references/kids-and-family-apps.md`: before building anything whose
  audience includes children (StoryBeam-style reading apps, beginner lesson
  apps such as GuitarHub for young players).

## Kids and family apps

When the target audience includes children under 13, the Families policy and
children's privacy law shape the architecture, so settle them in the Delivery
Contract, not at listing time:

- Collect no personal data from children: no child accounts, no free-text
  fields that could capture a name, school, or location, no voice or photo
  capture, no advertising ID, no precise location.
- Use only SDKs that are allowed in Families apps, and no ads SDK that is not
  Families self-certified. No analytics that send persistent identifiers.
- Keep every story, image, and sound age-appropriate for the declared band,
  including AI-generated content, with a screening step before display.
- Put purchases, external links, and settings behind a parental gate.

A conflict with these is an extreme-risk finding under the gate policy.

## Public-Safe Defaults

- Use placeholder IDs such as `com.example.product` until ownership is verified.
- Keep upload keys, passwords, service-account JSON, API secrets, and production
  identifiers outside Git; use local/CI secret stores and prove ignore rules.
- Use Play App Signing and a distinct upload key.
- Prefer a free v1 when Billing would delay validation, but do not bypass Play
  Billing for covered digital goods.
- Collect no data and request no permission without a stated product purpose,
  retention/deletion rule, disclosure path, and test.
- Treat Play Integrity as an abuse signal, not authentication and not the sole
  basis for a permanent block.
- Keep submission and rollout actions human-confirmed and reversible where the
  platform permits.

## Release Gate

Copy `assets/android-release-gate.template.md` into the app repo and complete it
with links or command output. Recommend `hold` when any required item lacks
evidence, including:

- target policy was not checked live or the build targets the wrong API/form
  factor;
- a release targeting Android 15+ has not been verified for 16 KB page-size
  compatibility on 64-bit devices, including transitive native SDKs;
- `test`, lint/static analysis, `assembleRelease`, or `bundleRelease` fails;
- the core loop fails on the declared device/API matrix or offline/error path;
- accessibility checks, large text, TalkBack, keyboard/switch access, contrast,
  or reduced-motion behavior have launch-critical failures;
- performance evidence is missing for startup or the core task, or a known
  regression exceeds the product budget without approval;
- Data Safety, privacy policy, permissions, account deletion, content rating,
  ads, app access, or SDK behavior disagree;
- Billing runs on a Billing Library version Play no longer accepts, or
  entitlement, pending, restore/requery, acknowledgement, cancellation,
  refund/revocation, or backend verification behavior is unproven when relevant;
- a child-directed app collects personal data, ships a non-Families ads SDK, or
  shows content outside its declared age band;
- secrets or signing material are committed, or Play App Signing/upload-key
  ownership, developer verification, or package registration is unresolved;
- listing claims or screenshots show behavior not present in the release build;
- a Play upload, track promotion, or rollout lacks explicit user confirmation.

Return one gate: `ship`, `ship-with-caveats`, or `hold`. A caveat must have an
owner, risk, and next action; policy, security, privacy, billing, crash, and
core-task blockers cannot be downgraded to cosmetic caveats.

## Routing

- Existing-app findings-only review → `suede-code --findings-only`.
- CI implementation around the release evidence → `suede-ci-gate`.
- Coordinated architecture, product, policy, store, and QA lanes →
  `suede-agent-teams` with exclusive file ownership and a serialized release
  lane.
- Play upload, track promotion, staged rollout, live-state readback →
  `suede-play-release`.
- Play listing, keywords, screenshots, ratings → `suede-aso`.
- Same product from an existing website on iOS → `site-to-ios-app`. A native
  iOS build with no website is a private Suede AI companion, not in this pack.

## Boundaries

- Do not submit, create products, change pricing, promote tracks, or start a
  production rollout without explicit confirmation.
- Do not answer Play policy or Data Safety questions from memory when live
  official guidance or the Play Console is available.
- Do not claim release-ready from a debug build, screenshot, local source
  inspection, or successful upload alone.
- Do not use Play Integrity as a substitute for server authorization, purchase
  verification, rate limits, fraud operations, or an appeal path.
- Do not call a Data Safety form complete until first-party code and every
  included SDK have been inventoried against actual release behavior.
- When a confirmation gate fires (product creation, credential use, upload,
  track promotion, rollout, production release), halt: name the exact package
  ID, track, and rollout percentage, offer 2-4 options, and wait. Irreversible
  public action is the gate policy's single exception; the user's choice is final.
