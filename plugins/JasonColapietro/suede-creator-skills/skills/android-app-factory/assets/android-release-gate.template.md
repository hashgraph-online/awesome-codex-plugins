# Android Release Gate

Copy this file into the app repository. Replace every `TBD`; use `N/A` only
with a reason. Link command output, CI jobs, screenshots, Play Console evidence,
or dated test notes without copying credentials or private customer data.

## Release Identity

- Gate owner: TBD
- Checked at (UTC): TBD
- Repo / remote: TBD
- Branch / commit: TBD
- Dirty paths or parallel WIP: TBD
- Application ID / Play app: TBD
- Version code / name: TBD
- Artifact checksum: TBD
- Intended track / rollout: TBD
- Rollback or halt owner: TBD

## Live Policy Receipt

- Official target API URL and checked time: TBD
- Observed requirement and effective date: TBD
- Form-factor exception: TBD
- `compileSdk` / `targetSdk` from release artifact: TBD
- Android 16 behavior-change migration evidence: TBD
- 16 KB page-size artifact/tool/device/Console evidence: TBD
- Developer verification and package registration status: TBD
- Other applicable policy URLs/check times: TBD
- Play Console policy status/notices: TBD
- Extension requested/approved: N/A: TBD

## Build and Artifact

- Toolchain/version-lock evidence: TBD
- `test` result: TBD
- lint/static-analysis result: TBD
- `assembleRelease` result: TBD
- `bundleRelease` result: TBD
- AAB validation/inspection: TBD
- Release shrinking/serialization/reflection test: TBD
- Play App Signing/upload-key ownership: TBD
- Secret/signing-material scan: TBD
- Mapping/native-symbol handling: TBD

## Core Task and Device Matrix

| Device/form factor | API | Locale/text scale | Install/update | Core task | Offline/error/restore | Result/evidence |
| --- | --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD | TBD |

- Deep-link/external-input tests: TBD
- Minimum SDK and API 36 coverage: TBD
- Adaptive/resizable/fold/rotation behavior: TBD
- Background/process restoration: TBD

## Accessibility

- Compose semantics and automated checks: TBD
- TalkBack core-flow test: TBD
- Large text/reflow: TBD
- Contrast and non-color cues: TBD
- Target size/focus/keyboard/D-pad/switch behavior as applicable: TBD
- Reduced-motion behavior: TBD
- Launch-critical accessibility issues: TBD

## Performance and Reliability

- Representative device and build type: TBD
- TTID/TTFD and core-task budgets/results: TBD
- Jank/frame timing: TBD
- Memory/ANR/battery/network findings: TBD
- Baseline Profile generated, packaged, and verified: TBD
- Macrobenchmark result: TBD
- Play pre-launch report: TBD
- Crash/ANR/core-task alert owner and halt threshold: TBD

## Privacy, Permissions, and Account Deletion

- Data/SDK/WebView inventory: TBD
- Runtime/network evidence: TBD
- Least-permission and denial-path tests: TBD
- Privacy policy URL/content check: TBD
- Data Safety reconciliation and submission state: TBD
- Retention/deletion/service-provider reconciliation: TBD
- In-app deletion path (if accounts): TBD
- External deletion URL and no-reinstall test: TBD
- Target audience/Families, content rating, ads, app access: TBD
- Child-directed: personal data collected from children (expect none), Families SDK check, parental gates, AI content screening: TBD
- Restricted-permission declarations: TBD

## Billing and Entitlements

- Applicability or free-v1 rationale: TBD
- Billing Library major version (8+ required since 2026-08-31) and check date: TBD
- Product/base-plan/offer IDs and environment: TBD
- License tester / Play test-track evidence: TBD
- Pending-to-purchased behavior: TBD
- Verification, idempotent entitlement, and acknowledgement/consumption: TBD
- Restore/requery and multi-device/reinstall behavior: TBD
- Grace/hold/pause/cancel/expire/refund/revoke behavior as applicable: TBD
- RTDN/Developer API reconciliation or N/A reason: TBD
- Purchase/support/manage-subscription UX: TBD

## Play Integrity and Security

- Threat model and exported component review: TBD
- Integrity applicability/risk decision: TBD
- Server verification/action binding/freshness: TBD
- Layered authorization and proportionate response/appeal: TBD
- Timeout/quota/outage/false-positive tests and monitoring: TBD
- OWASP MASVS risk-based checks: TBD

## Store Listing and Review

- Title/short/full description current-limit checks: TBD
- Claim-to-feature evidence: TBD
- Phone/form-factor screenshots from release candidate: TBD
- Icon/feature graphic/localization: TBD
- Support contact/site: TBD
- Privacy/deletion links: TBD
- Reviewer instructions and least-privileged access: TBD
- Release notes: TBD

## External Mutation Approval

- Play app/product/pricing mutation approved by: TBD
- AAB upload approved by: TBD
- Track promotion approved by: TBD
- Production rollout percentage approved by: TBD
- Approval timestamp/channel or N/A: TBD

## Verdict

- Gate: `hold`
- Blockers: TBD
- Caveats with owner/risk/next action: TBD
- Exact next step: TBD

Allowed gates:

- `ship`: all required evidence passes;
- `ship-with-caveats`: only named non-critical caveats remain;
- `hold`: any policy, security, privacy, billing, crash, core-task,
  accessibility, signing, claim-truth, or confirmation blocker remains.
