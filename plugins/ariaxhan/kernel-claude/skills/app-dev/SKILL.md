---
name: app-dev
description: "Mobile/web app build pipeline: fastlane-first local builds, store submission, pre-submission checklists. Triggers: app, mobile, store submission, build, deploy app, fastlane, expo, react native, flutter."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task
kernel:
  kind: methodology
  version: 1
  side_effects: none
  confirmation: none
---

# POLICY: fastlane, never EAS

Local fastlane builds (gym/gradle + deliver/supply) are the default for all native
build + store submission. EAS/cloud builders are a deliberate, *stated* exception —
never a silent reach (rule: CodingVault/.claude/CLAUDE.md "Mobile builds").
If the project ships its own build CLI (e.g. modelmind's `./mm`), extend that — don't
bolt on a second pipeline.

# FLOW

1. **Load source files** — Read `fastlane/Fastfile`, project build config (`build.gradle`,
   `*.xcodeproj`, `app.config.*`), any project build CLI, CI config. If no fastlane setup
   exists, `fastlane init` and commit the scaffold. (gate: build tooling identified)
2. **Identify environment** — dev / staging / production. API endpoints, signing creds,
   feature flags are environment-specific. Signing material lives in keychain or
   gitignored `_meta/keys/` listed in the secrets-backup manifest — never in the tree.
   (gate: no hardcoded keys or shared signing certs)
3. **Build locally** — iOS: `fastlane gym` (or project lane). Android: `fastlane` lane
   wrapping `gradle bundleRelease` → signed AAB. (gate: build completes without error)
4. **JS-only vs native change** — JS-only updates may use the project's own OTA mechanism
   if one exists; any native change requires a full store build. (gate: OTA never used
   for native changes)
5. **Run pre-submission checklist** (gate: all items pass before submitting):
   - [ ] Privacy manifests (iOS): all required API reasons declared
   - [ ] Permissions: only what you use, with clear usage descriptions
   - [ ] Metadata: screenshots current, descriptions accurate (`fastlane/metadata/`)
   - [ ] Version/build numbers: incremented correctly
   - [ ] Physical device testing: tested on real device (not simulator)
   - [ ] Deep links: universal links / app links verified
   - [ ] Push notifications: working in production config
   - [ ] Crash-free rate: > 99% on staging before promoting
   - [ ] Bundle size: within limits, no large accidental assets
   - [ ] Offline behavior: handles no-network gracefully
6. **iOS submission** — `fastlane deliver`/`pilot`: TestFlight (internal → external) →
   App Store review. (gate: metadata complete; privacy manifests present)
7. **Android submission** — `fastlane supply` with a Play service-account JSON:
   internal → closed/open beta → staged production rollout starting at 5-10%.
   (gate: data safety form complete; crash rate stable)
8. **Monitor rollout** — watch crash rates before expanding staged rollout. Rollback:
   halt rollout in console; OTA rollback via the project's own mechanism if present.
   (gate: crash-free rate holds > 99%)

# ANTI-PATTERNS (block on detection)

- Reaching for EAS / cloud builders without a stated, justified exception
- Hardcoded API keys in builds → keychain or env injection at build time
- OTA update for native changes → must be a store build
- Skipping physical device testing → simulators miss real-world issues
- 0-to-100% rollout on Android → start at 5-10%
- Shared signing certs across environments → separate keystores

# REFERENCE

Deep rationale, environment config patterns, iOS/Android submission detail:
`skills/app-dev/reference/app-dev-research.md`

# ON COMPLETE

agentdb write-end '{"skill":"app-dev","platform":"ios|android|both","gate":"submitted|built|blocked","store_ready":true}'
