---
name: cometchat-compliance
description: "Data governance & compliance for CometChat — pick the data-residency region, satisfy GDPR/CCPA (right-to-erasure and data export), plan message retention & purge, and produce audit / eDiscovery records. Cross-family: all server/REST/dashboard-side. Triggers: 'is cometchat GDPR compliant', 'delete a user and their data', 'right to be forgotten', 'export a user's data', 'data residency EU', 'which region', 'message retention policy', 'audit log', 'eDiscovery', 'HIPAA/SOC2 chat', 'compliance review'."
license: "MIT"
compatibility: "CometChat REST API v3 (users · messages · conversations) + dashboard (regions, moderation records). Server-side over HTTPS."
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat compliance gdpr ccpa hipaa data-residency retention audit ediscovery erasure region"
---

> **Ground truth:** REST shapes are FETCHED from the live docs — `{DOCS_BASE}/rest-api/users/delete` (erasure), `/rest-api/messages`, `/rest-api/conversations` (access/export), `/articles/properties-and-constraints` (regions, retention behaviour), `/moderation/reviewed-messages` (audit). `DOCS_BASE = https://www.cometchat.com/docs`; append `.md`. Where a control is a **dashboard setting or a sales/plan item** (a managed retention policy, a signed BAA, certifications), this skill says so plainly rather than inventing an API. Certification status (SOC 2, ISO 27001, HIPAA) is a business fact — confirm current scope at `{DOCS_BASE}`/the trust page, don't assert it from here.

## Use this skill when
A privacy/security/compliance review, a data-subject request (delete/export), choosing where data lives, or planning retention and audit. All actions here are server-side; there is no client code to write.

## 1. Data residency — choose the region up front
CometChat hosts each app in one region: **`us`, `eu`, or `in`** (`{DOCS_BASE}/rest-api/chat-apis` → Data Center Hosting — re-fetch before quoting to a customer; regions can be added). The region is fixed to the app and is part of every API/SDK endpoint (`https://{APP_ID}.api-{REGION}.cometchat.io/v3`, and the SDK init `region`). To keep EU data in the EU (GDPR) or meet a residency clause, **create the app in that region** — you cannot silently move an app's region afterward; migrating regions means a new app + a data migration (`cometchat-migrate-from-*` machinery / CometChat support). For full data sovereignty (your own infrastructure), see `cometchat-self-host`.

## 2. Right to erasure (GDPR Art. 17 / CCPA delete)
Call the REST **Delete User** endpoint (`DELETE https://{APP_ID}.api-{REGION}.cometchat.io/v3/users/{uid}`; see the docs at `{DOCS_BASE}/rest-api/users`) with the **REST API Key**:
- **Default** (no body) → **deactivates** the user (recoverable; keeps data).
- **`{ "permanent": true }`** → **permanently deletes the user with all their messages, conversations and associated data. Irreversible.**

```http
DELETE https://{APP_ID}.api-{REGION}.cometchat.io/v3/users/{uid}
apikey: {REST_API_KEY}
content-type: application/json

{ "permanent": true }
```
Wire this to your account-deletion flow so a "delete my account" request erases the user in CometChat too. Also flush their auth tokens (`cometchat-security`) so no session lingers.

## 3. Right of access / portability (data export)
To answer a data-subject *access* request, export the user's data server-side via REST and hand it over in a portable format:
- their messages — the Messages REST collection (`{DOCS_BASE}/rest-api/messages`, filtered by the user);
- their conversations — `{DOCS_BASE}/rest-api/conversations`;
- their profile — the Users API.
Run it with the REST API Key from a server job; never expose these to the client. Fetch the exact filter params from the docs before writing the exporter.

## 4. Retention & purge
CometChat keeps messages until they are deleted. Behaviour to know (`/articles/properties-and-constraints`): **soft-deleted** messages are retained; messages **permanently deleted via the API are not**. To enforce a retention window:
- run a scheduled server job that deletes messages/conversations older than your policy via the REST APIs (delete-message / delete-conversation / user permanent-delete);
- a **managed/automatic retention policy** (auto-purge at N days) is a dashboard/plan capability — confirm availability and configure it with CometChat rather than assuming an API. Do not invent a retention endpoint.
- **on-prem** gives you full control of storage lifecycle and backups (`cometchat-self-host`).

## 5. Audit & eDiscovery
- **Moderation audit trail:** the dashboard's **Moderation → Reviewed Messages** records moderator activity and decisions for compliance (`{DOCS_BASE}/moderation/reviewed-messages`); pair with `cometchat-moderation`.
- **eDiscovery / legal hold:** export the relevant conversations and messages via the REST collections above (by user, group, or time range) — that is the supported way to produce chat records; there is no separate "eDiscovery API." For a legal hold, export before any retention purge runs.
- **Webhooks** (`{DOCS_BASE}/rest-api/management-apis/webhooks/overview`) can stream message/user events to your own immutable audit store in real time if you need a tamper-evident log outside CometChat.

## 6. Certifications & agreements (business, not code)
SOC 2, ISO 27001, HIPAA (with a BAA), GDPR/CCPA posture, and pen-test reports are handled through CometChat's trust/compliance process, not the API. Point the reviewer to the current trust page and get agreements in writing; encryption in transit (TLS) is standard, and at-rest/e2e options + key management vary by plan/deployment — confirm the specifics for the customer's plan.

## Common pitfalls
1. **Region chosen by accident** — the default is `us`; an EU customer needs the app created in `eu` from day one.
2. **"Delete" that only deactivates** — omitting `permanent: true` leaves the data; erasure requests need the flag.
3. **Deleting the user but leaving live sessions** — also flush auth tokens (`cometchat-security`).
4. **Assuming an automatic retention policy exists** — implement purge via REST/on-prem, or confirm the managed setting; don't invent it.
5. **Asserting a certification from memory** — verify current SOC 2 / HIPAA / ISO scope with CometChat.

## Verify it works
A test user permanently deleted returns success and their messages/conversations are gone · an access-request export produces the user's profile + messages + conversations · the app's region matches the customer's residency requirement · a retention job (or the confirmed managed policy) removes data past the window · moderation decisions appear in Reviewed Messages · webhooks (if used) land audit events in your store.
