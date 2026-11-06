# Google Play Policy Baseline

Checked against official Google sources on **2026-10-23**. This file is a dated
starting point, not a substitute for a release-day check. Record the live result
and timestamp in the release-gate artifact.

## Target API Requirements

Phone and tablet apps:

| Scope | Requirement | Since |
| --- | --- | --- |
| New apps and updates | Android 16 / API 36 or higher | 2026-08-31 (extensions end 2026-11-01) |
| Existing apps, to stay available to new users on newer Android versions | Android 15 / API 35 or higher | 2026-08-31 |

Form factors, new apps and updates:

- Wear OS and Android Automotive OS: API 35 or higher (since 2026-08-31).
- Android XR: API 34 or higher (since 2026-08-31).
- Android TV: API 34 or higher (since 2025-08-31).

Permanently private apps restricted to one organization are exempt. The
extension window closes 2026-11-01; after that a phone/tablet update below API
36 is rejected. Do not assume an extension applies; inspect the app's Policy
status page in Play Console.

Factory default: `compileSdk = 36`, `targetSdk = 36`. Google has moved the bar
up one level every August; check the page below for the 2027 level before
planning a release past mid-2027. Raise `targetSdk`
only after testing the Android behavior changes for that level; changing the
integer without migration testing is not compliance.

Primary sources:

- <https://developer.android.com/google/play/requirements/target-sdk>
- <https://support.google.com/googleplay/android-developer/answer/11926878>

## Policy and Console Checks

Complete for the exact release build:

- target API and any form-factor exception;
- 16 KB memory page-size compatibility for 64-bit devices when targeting
  Android 15+; inspect direct and transitive native libraries and test the
  release in a 16 KB environment;
- developer identity verification and package registration status in Play
  Console (enforced in Brazil, Indonesia, Singapore, and Thailand since
  2026-09-30; global in 2027);
- app category, target audience, Families applicability, ads, and content
  rating;
- restricted permissions and declaration forms;
- app access/reviewer credentials for gated functionality;
- privacy policy and Data Safety answers;
- account deletion when an app account can be created in-app or through an
  out-of-app flow initiated by the app;
- payments policy and Play Billing applicability;
- health, financial, VPN, accessibility service, background location, media,
  generative-AI, news, or other category-specific rules when applicable;
- SDK policy status using the Google Play SDK Index and the actual release
  dependency graph;
- Play Console policy status, pre-launch report, device catalog exclusions,
  and unresolved review notices.

Do not infer a Console answer from source alone. Installed SDK configuration,
remote flags, backend flows, WebViews, and the Play listing can change the
answer.

## 16 KB Page-Size Baseline

In force for new apps and updates targeting Android 15+ submitted to Play: the
release must support 16 KB page sizes on 64-bit devices.
Pure Java/Kotlin code is compatible by default, but an app can inherit native
code through an SDK. Inspect the final artifact, rebuild/update incompatible
native libraries, run Android Studio/lint alignment checks, and test in a 16 KB
environment. Confirm Play Console's release detail rather than relying only on
the source tree.

Primary source:
<https://developer.android.com/guide/practices/page-sizes>

## Developer Verification Baseline

Since 2026-09-30, certified Android devices in Brazil, Indonesia, Singapore,
and Thailand install and update only apps registered by verified developers,
across participating stores and sideloading. Google expands this globally in
2027. Play auto-registers eligible apps once the developer account passes
identity verification; apps that fail auto-registration use the manual claim
flow. Check the verification page in Play Console for each package. Apps
distributed only outside Play register through the Android Developer Console.
Never collect identity documents or private signing material in the project
artifact.

Primary sources:

- <https://developer.android.com/developer-verification>
- <https://developer.android.com/blog/posts/android-developer-verification-rolling-out-to-all-developers-on-play-console-and-android-developer-console>

## Data Safety Baseline

Inventory first-party code, libraries/SDKs, and app-controlled WebViews. Google
defines off-device transmission by included libraries/SDKs as collection even
when the data goes directly to a third party. Locally processed data can be out
of scope for Data Safety, but it can still be sensitive and must be secured.

For every data type, record:

- collection and sharing status;
- required versus optional;
- purpose;
- ephemeral processing, retention, deletion, and user controls;
- transport encryption and any end-to-end-encryption claim;
- SDK/service-provider role and contract;
- evidence from runtime traffic, configuration, vendor documentation, and code.

Primary source:
<https://support.google.com/googleplay/android-developer/answer/10787469>

## Account Deletion Baseline

If the app offers account creation anywhere in its experience, provide:

1. an in-app path to initiate deletion, which may link to a deletion web
   resource; and
2. a functional web deletion resource declared in Play Console that works for
   users who no longer have the app.

Deletion covers the account and associated user data, including relevant data
held by service providers. Document narrowly required retention, reason, and
duration. The web resource must not force the user to reinstall the app.

Primary source:
<https://support.google.com/googleplay/android-developer/answer/13327111>

## Billing Baseline

For Play-distributed apps selling covered digital goods or subscriptions, use
the current required Play Billing path. Google's deprecation schedule:

| Billing Library | New apps and updates must move off it by | Extension until |
| --- | --- | --- |
| 7 | 2026-08-31 | 2026-11-01 |
| 8 | 2027-08-31 | 2027-11-01 |
| 9 | 2028-08-31 | 2028-11-01 |

So a release today ships on Billing Library 8 or later, and a new build should
start on the newest stable major. Version 8 removed APIs that 7 still had
(including purchase history queries); budget a migration, not a version bump.
Recheck the table live before each release.

Primary source:
<https://developer.android.com/google/play/billing/deprecation-faq>

Release evidence must cover:

- product/base-plan/offer IDs and environment;
- purchase connection and reconnect behavior;
- pending purchases and transition from `PENDING` to `PURCHASED`;
- purchase-token verification and entitlement idempotency;
- acknowledgement/consumption only in the correct state;
- restore/requery behavior across reinstall/device changes;
- cancellation, expiry, grace, hold, pause, refund, and revocation as relevant;
- Real-time Developer Notifications and Developer API reconciliation for a
  server-backed entitlement system;
- license testers and Play test tracks, not only local mocks.

Google's integration guidance says not to acknowledge a purchase in `PENDING`;
acknowledge after it becomes `PURCHASED`. Prefer secure-backend verification and
acknowledgement when a backend exists.

Primary source:
<https://developer.android.com/google/play/billing/integrate>

## Release-Day Verification Receipt

```text
checked_at_utc:
checker:
package_id:
play_app:
track:
release_version_code:
target_api_source_url:
observed_target_requirement:
build_compile_sdk:
build_target_sdk:
form_factor_exception:
supports_16kb_page_sizes_evidence:
developer_verification_and_package_registration:
billing_library_version:
families_and_target_audience:
data_safety_source_url:
account_deletion_source_url:
billing_source_url_and_library_status:
other_policy_urls:
play_console_status_and_evidence:
caveats:
```

If an official source and this baseline differ, follow the current official
source and update the copied project gate. Do not quietly rewrite history in a
completed release record.
