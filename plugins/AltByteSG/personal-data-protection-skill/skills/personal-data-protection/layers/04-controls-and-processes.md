# Layer 04 — Controls and Processes

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Server-side and pipeline code that enforces the obligations. Universal patterns across stacks.

## User-rights endpoints

Every PDP-family statute requires support for at least:

- **Access** — the user can request a copy of all personal data the organisation holds about them.
- **Correction** — the user can request rectification of inaccurate or incomplete data.
- **Deletion** — the user can request deletion of their personal data.
- **Withdrawal of consent** — the user can revoke any consent previously given.

Implementation suggestions:

| Right | Common implementation |
|---|---|
| Access | A function or endpoint that returns the user's complete personal-data set as a structured payload (typically JSON), delivered to the user via in-app share-sheet or download link. Rate-limit to prevent abuse (e.g. once per 7 days). |
| Correction | Self-service edit screens for fields the user can correct themselves, plus a contact channel for fields under admin control. |
| Deletion | Hard-delete cascade for owned data; SET NULL or "Deleted User" attribution for shared content. Triple-confirm in the UI to prevent accidents. Re-authenticate before delete. |
| Withdrawal | The same toggles used to grant consent must allow revocation, with equal effort. |

**Access endpoint completeness** is critical and frequently fails audits. The implementation must return *all* personal data the org holds — not just the most-used fields. See [`checklists/new-data-field.md`](../checklists/new-data-field.md) for the discipline of keeping the export in sync as new fields are added.

## Admin endpoint pattern

Every admin endpoint (read or write) should follow the same shape:

1. **Verify the caller has the admin role** at the start of the function. Don't trust middleware alone — check inside the function too. Defence in depth.
2. **Mutations** call the audit-log helper at the end, recording action, resource type, resource ID, and a JSON details blob.
3. **Reads of single-user PII or PII lists** call a throttled audit-log helper at the end (5-minute deduplication per actor + resource).
4. **Reads of pure aggregates** (dashboard, KPIs, charts) skip the audit log — document the exclusion in a code comment.

Why throttle reads but not writes: every mutation is unique state change. Reads can repeat (page refreshes, polling). Without throttling, a user-detail page refresh produces dozens of identical audit rows that drown the signal.

## Retention sweeps

Statutes require ceasing to retain personal data once the purpose is no longer served. For most categories this means scheduled background cleanup.

**Pattern:**
- One canonical "PDP cleanup" function that runs daily at off-peak hours.
- Each retention rule lives as a separate sub-function called from the canonical one (`cleanup_expired_messages()`, `cleanup_expired_events()`, `cleanup_orphan_storage()`, etc.).
- The schedule is registered with whatever cron / scheduler your platform offers.
- Each sub-function is idempotent — safe to run again if a previous run failed mid-way.

**When adding a new retention rule:**
1. Write the cleanup sub-function (parameterised by the retention period).
2. Add a call to it from the canonical sweep.
3. Document the rule in the privacy policy retention table.
4. Don't create a new schedule — reuse the existing one.

**File / object storage cleanup** has a special caveat on most platforms: deleting database rows does NOT automatically delete object-storage files. Cleanup must explicitly call the storage API for each file, in addition to the database delete.

## Storage cleanup orchestration

When deleting account-owned files from object storage:

1. Use the storage platform's REST API or SDK with service credentials.
2. Batch deletes (most APIs accept a list per call).
3. Tolerate partial failures — the next sweep run should re-attempt.
4. **Do not** rely on client-side cleanup as the primary path. The server is authoritative; client cleanup is at most a UX optimisation.

For orphan reaping (files whose owner no longer exists in the database):
- Periodic full scan of bucket prefixes.
- For each file, extract the owner identifier from the path.
- LEFT JOIN against the users table; delete files whose owner is NULL.
- Skip prefixes that are conversation-keyed or otherwise not owned by an individual user (group chat media, shared content).

**Shared containers need different cleanup logic than user-owned files.** If a file lives in a shared path (group chat media, collaborative documents, event galleries), deleting it on individual account deletion would erase data the *other* members are still entitled to view. Pattern: re-attribute ownership to a system "Deleted User" pseudo-account on account deletion; reap the file itself only when *all* referencing members are gone or when the parent container (the conversation, the event, the document) is itself deleted. The trade-off: a deleted user's content lingers in shared spaces — name them in the privacy policy if you want this to be defensible.

## Sub-processor dispatch (push / email / webhooks)

When your system dispatches data to a sub-processor (push notification provider, email service, analytics, webhooks):

- **Authenticate** with credentials from your secret store, never hard-coded.
- **Sanitise the payload** so it contains the minimum data needed — the destination provider sees what you send.
- **Cache short-lived auth tokens** with sensible expiry; don't re-acquire on every call.
- **Handle stale credentials** (expired tokens, revoked keys) gracefully — clear them and log without leaking the credential value.
- **Sanitise the response** before logging — sub-processors notoriously echo the value you submitted (email address, push token, OAuth token) back in error responses.

## Logging hygiene patterns

For every `console.error` / `console.log` / `print` / equivalent in server-side code that includes a variable, the variable must be sanitised first. Suggested helpers (translate to your language):

```
// Pseudocode — adapt to your language
function safeError(e) {
  // Extract code + message; never dump full object
  return e.code ? `${e.code}: ${e.message}` : e.message || String(e);
}

function redactId(uuid) {
  // First 8 chars + ellipsis. Enough to correlate, not enough to identify
  return uuid ? `${uuid.slice(0, 8)}…` : '<none>';
}

function redactPII(s) {
  // Multi-pass: named token fields, emails, then long token-shaped substrings
  let out = s.slice(0, 300);
  out = out.replace(/(token|access_token|refresh_token|authorization|api_key)\s*[:=]\s*['"]?([^'",\s}]{8,})/gi, '$1: <redacted>');
  out = out.replace(/[\w.+-]+@[\w.-]+\.\w+/g, '<email>');
  out = out.replace(/\b[A-Za-z0-9][A-Za-z0-9._:/=+-]{39,}\b/g, '<redacted>');
  return out;
}
```

Apply at every call site that logs a variable. Plain string literals are fine.

## Breach detection signals

Without some kind of detection, you only learn about breaches when something visible breaks. For the regulatory clock to start (PDP-family typically 3–72 hours after assessment), someone has to notice. Minimum signals to consider:

- **Failed-auth spike alarm** (sudden surge in 4xx auth responses)
- **Mass-export detector** (rate-limit alert on data-export endpoint per hour)
- **Storage egress anomaly** (unusual download volume)
- **Repository secret-scanning** (your VCS provider almost certainly offers it; turn it on)
- **Log review schedule** (quarterly skim of admin audit log for unfamiliar actions)

These are operational signals, not user-facing features — owned by [layer 07](07-operational.md).

## Session and credential rotation

When a user changes their password, deletes their account, or revokes a session: existing sessions on other devices should be invalidated. Most auth platforms expose a "sign out everywhere" or "revoke refresh tokens" function — wire it into your account-management flows.

For admin sessions: shorter session lifetimes than user sessions, plus periodic forced re-authentication. The blast radius of an admin-session leak is much higher.

## Backwards compatibility for personal-data changes

When modifying any function that user clients call:

- Adding new fields to a JSON return shape: safe (older clients ignore them).
- Adding new optional parameters with defaults: safe.
- Removing or renaming fields: breaking. Coordinate with client version pinning / force-update.
- Tightening validation: silently breaks older clients. Coordinate.

For internal admin functions: backwards compatibility doesn't apply to client versions, but admin console must be redeployed in the same release.

See also CLAUDE.md golden rule #12 in your project (or whatever its equivalent is) for project-specific backwards-compat policy.
