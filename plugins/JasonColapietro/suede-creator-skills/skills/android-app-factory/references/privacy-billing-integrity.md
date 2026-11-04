# Privacy, Billing, and Integrity Controls

These controls are part of product correctness. A build that opens but exposes
data, loses an entitlement, or blocks legitimate users from an unreviewed
integrity signal is not release-grade.

## Privacy and Data Inventory

Create one row per first-party flow, SDK, service, and app-controlled WebView:

| Component | Data | Source | Destination | Purpose | Required/optional | Retention/deletion | User control | Data Safety answer | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Verify with source/config inspection, dependency graph, SDK/vendor documents,
runtime network observation on a release-like build, backend behavior, and
Play Console answers. A privacy policy copied from another app is not evidence.

Rules:

- Collect the minimum data required for an explicit purpose.
- Request a runtime permission in context, explain the user benefit, handle
  denial and "don't ask again," and preserve a usable fallback when possible.
- Do not request a restricted permission when a system picker, Storage Access
  Framework, photo picker, or narrower API meets the need.
- Define retention and deletion across app storage, backend, logs, analytics,
  support systems, backups, and service providers.
- Make consent, opt-out, and deletion behavior real in the release build.
- Reconcile Data Safety whenever code, remote config, SDK versions, or backend
  data use changes.

Primary references:

- Data Safety: <https://support.google.com/googleplay/android-developer/answer/10787469>
- Permissions best practices:
  <https://developer.android.com/training/permissions/usage-notes>
- Google Play SDK Index: <https://play.google.com/sdks>

## Account Deletion

When the app offers account creation, implement and test:

1. discoverable in-app deletion initiation (or an in-app link to the web
   resource);
2. a public web deletion resource that does not require reinstalling the app;
3. authentication/re-authentication proportionate to account risk;
4. clear scope, consequences, expected timing, and narrow retained-data notice;
5. deletion of associated user data and requests to service providers;
6. entitlement/subscription guidance without falsely implying that deleting an
   account automatically cancels a Play subscription;
7. completion/error/retry/audit behavior that does not expose sensitive data;
8. Play Console Data Safety deletion answers and URL matching the live flow.

Test signed-in, expired session, federated identity, offline/failure, active
subscription, pending deletion, completion, and repeat-request paths.

Primary reference:
<https://support.google.com/googleplay/android-developer/answer/13327111>

## Play Billing State Machine

Use the current supported Billing Library and official integration patterns.
Treat the purchase token as sensitive. Do not trust a client-only boolean as
the entitlement source of truth for a valuable product.

```text
product queried
  -> billing flow launched
  -> PENDING | PURCHASED | canceled/error
  -> token verified (prefer secure backend)
  -> entitlement granted idempotently
  -> purchase acknowledged or consumed as appropriate
  -> lifecycle reconciled by app query + backend notifications/API
```

Controls:

- Establish/re-establish `BillingClient` connection and handle service
  unavailability.
- Query live product details; never hardcode display price/currency from a
  developer assumption.
- Enable and visibly represent pending purchases. Do not grant or acknowledge
  while the purchase is still `PENDING`.
- Verify package, product, purchase token, purchase state, account binding, and
  replay/idempotency on a secure backend when available.
- Grant entitlement exactly once, but make processing safely retryable.
- Acknowledge/consume within the required window after verified purchase and
  entitlement handling; alert on unacknowledged purchases.
- Query purchases on connection/resume so reinstall, device change, out-of-app
  completion, and missed callbacks recover.
- Reconcile subscription lifecycle and one-time-product changes using Real-time
  Developer Notifications and the Google Play Developer API for server-backed
  systems.
- Define grace, account hold, pause, resubscribe, upgrade/downgrade, expiry,
  cancellation, refund, chargeback, and revocation behavior where applicable.
- Provide a restore/manage-subscription route and accurate support copy.

Test with Play license testers and test products on a Play test track:

- success, user cancellation, service disconnect, duplicate callback;
- pending then completed, pending then canceled;
- already owned, restore after reinstall, multiple devices;
- acknowledgement/consumption retry;
- subscription renewal, grace/hold, cancellation, expiry, refund/revocation;
- backend or notification delay/outage.

Primary references:

- Billing integration:
  <https://developer.android.com/google/play/billing/integrate>
- Backend integration:
  <https://developer.android.com/google/play/billing/backend>
- Test Billing:
  <https://developer.android.com/google/play/billing/test>

## Play Integrity

Use Play Integrity only for abuse-sensitive actions whose risk justifies the
latency, operational burden, false-positive handling, and quota. Examples can
include high-value entitlement redemption, competitive abuse, automated fraud,
or protected server operations.

Production pattern:

1. App requests a verdict close to the protected action using the current
   recommended request type.
2. Request binds the relevant action/account/nonce or request hash according to
   official guidance.
3. Backend decodes/verifies the verdict and checks freshness, package/app
   recognition, device/account/licensing signals as relevant.
4. Backend combines the verdict with authentication, authorization, rate
   limits, behavioral risk, and transaction context.
5. Policy maps uncertainty to proportionate responses: allow, monitor,
   step-up, limit, delay, or deny. A legitimate recovery/appeal path exists.
6. Metrics track verdict errors, latency, quota, false positives, and business
   harm before enforcement is tightened.

Never:

- decode or make the final authorization decision only on-device;
- treat Integrity as user authentication or payment verification;
- permanently ban solely from one missing/negative verdict;
- log raw tokens or sensitive verdict-linked identifiers;
- make every low-risk screen depend on an Integrity round trip;
- ship enforcement without outage, quota, old-device, sideload, and accessibility
  recovery behavior.

Test valid Play install, internal/closed track, unrecognized build, token/replay
failure, timeout, quota/error, stale verdict, backend outage, and each policy
response. Start in observe-only mode for a new rule when risk allows.

Primary references:

- Play Integrity overview:
  <https://developer.android.com/google/play/integrity/overview>
- Standard requests:
  <https://developer.android.com/google/play/integrity/standard>

## Release Reconciliation

Before the release gate closes, reconcile one row per trust surface:

```text
source implementation -> runtime evidence -> backend behavior -> policy/listing answer -> test -> owner
```

Any unexplained disagreement is a `hold`, even if the Console accepts the AAB.
