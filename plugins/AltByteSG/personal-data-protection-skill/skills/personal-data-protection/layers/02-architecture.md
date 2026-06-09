# Layer 02 — Architecture & Infrastructure

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Cross-cutting technical decisions that protect personal data at the system level. Universal across PDP-family jurisdictions; the principles apply regardless of cloud, database, or framework.

## Data residency

**Decide where your primary data store physically lives, and disclose it.**

Most PDP-family statutes treat cross-border transfers as a separate obligation requiring "comparable protection" in the destination. Keeping the primary store in the same jurisdiction as your users simplifies the transfer story. Where that's impractical, rely on contractual binding clauses in your vendor DPAs.

**Disclose** the storage location in your privacy policy. Don't change region without (a) updating the policy, (b) documenting the transfer-comparable-protection basis, (c) notifying users if the change is material.

## Cross-border processing (sub-processors)

Even when the primary store is local, individual data points typically flow to sub-processors hosted globally (push tokens to a notification provider, OAuth tokens to an identity provider, anonymised crash reports to a monitoring service). Each is a cross-border transfer requiring its own basis.

**What belongs in your sub-processor list (privacy policy disclosure):**
- Anything that processes user personal data on your behalf
- Authentication providers (Sign in with Apple, Google, etc.)
- Push notification providers
- Email/SMS delivery providers (when sending content involving user PII)
- Crash and error reporting services (if anonymisation isn't perfect)
- Any analytics service that receives identifiers

**What does NOT belong in the sub-processor list:**
- Pure transit infrastructure (CDN, edge cache) — they don't process at rest
- Source-code hosting and CI — they don't see production user data
- Internal developer tooling
- Vendors integrated but not yet activated (add at activation)

The line is "do they receive a value that maps to an individual user." If yes, list them.

## Encryption

Three places:

- **In transit:** TLS 1.2+ (1.3 preferred). Enforced for all client–server and server–server traffic.
- **At rest:** disk-level encryption on database, file storage, and backups. Most managed cloud providers offer this by default; verify it's on.
- **Passwords:** never stored in plaintext or with reversible encryption. Use a memory-hard hashing algorithm (bcrypt, scrypt, Argon2) — be precise about which one in the privacy policy.

If you describe encryption in your privacy policy, **be accurate about the algorithm**. Claiming bcrypt when you actually use scrypt is a factual misstatement in a legal document.

## Access isolation (per-user data scoping)

The default in any system that holds personal data must be: **no user can read another user's data unless explicitly authorised.**

Patterns to implement this depend on the stack:
- Database-level row isolation (e.g. row-level security in Postgres, IAM policies in DynamoDB, scoped queries enforced server-side)
- Application-level access control (every read filters by current-user ID)
- Service-account separation (the credentials your app uses on behalf of a user differ from the credentials your background jobs use)

The principle: **defence in depth**. Even if one layer fails, the next should still block unauthorised access. Don't rely on a single check.

## Privileged-function discipline

When your application has functions that execute with elevated privileges (e.g. SECURITY DEFINER in Postgres, sudoers in shell, AWS service roles, an admin RPC layer):

- **Document them** — keep an inventory of which functions can read/write which data with which credentials.
- **Tighten search paths and namespaces** — don't let a privileged function be tricked into running against a malicious schema or table (relevant for SQL stored procedures specifically).
- **Audit-log invocations** — at least the mutations; ideally also the reads of personal data.
- **Limit who can call them** — explicit grants to the right role or service, never to the broadest role.

## Service / role separation

Your system likely needs at least three identity layers:
- **Anonymous / pre-auth** — used during signup, login, and other public flows
- **Authenticated user** — the role most application traffic uses
- **Service / admin** — used by background jobs, cron, internal tooling, and admin consoles

The service / admin role should never be exposed to client code. Service credentials live in:
- Environment variables (for server processes)
- A secrets manager (for production secrets that need rotation, sharing, or audit)
- Never in source control (gitignore enforced; pre-commit hooks if needed)

## Secret management

Long-lived secrets that server-side code needs:

- **Database credentials**: managed by the platform (e.g. cloud-managed DB) or in a secrets manager.
- **API keys for sub-processors**: secrets manager. Rotate on a schedule.
- **OAuth client secrets**: secrets manager. Rotate when staff with access leaves.
- **Webhook signing secrets**: secrets manager.

When a secret is suspected compromised: rotate immediately, verify dependent systems still work after rotation, document in the incident log.

For database functions or scheduled jobs that need secrets: most platforms offer an in-database vault or secret table that keeps secrets out of the function source. Use it.

## Logging hygiene at the architecture level

Application logs, error tracking, request logs, and database query logs are all places where personal data can leak unintentionally. The architecture-level principle: **don't include personal data in operational logs unless necessary, and when included, reduce to the minimum that preserves the operational signal.**

Practical measures:
- Sanitise IDs before logging (truncate UUIDs, hash emails).
- Strip raw external API response bodies that may echo submitted PII (sub-processor errors are notorious for echoing the offending value).
- Avoid logging full request/response bodies on read endpoints that return PII.
- Configure database query log redaction where supported.

See [layer 04](04-controls-and-processes.md) for concrete patterns and templates.

## Defence in depth

No single control should be the only thing standing between an attacker and user data. Every personal-data-protection finding worth taking seriously involves multiple controls failing simultaneously. When designing:

- Assume any single control can fail or be bypassed.
- Layer access controls so a missed check at one layer is caught at another.
- Make the audit trail comprehensive enough that even silent failures are detectable.
- When the platform offers a defence (RLS, IAM policy, network ACL, WAF, etc.), use it — even if your application code already enforces the same rule.

## Backwards compatibility (when changing personal-data handling)

If your application has live users, schema and behavioural changes that affect personal data must remain compatible with the lowest deployed version still in field use.

- Adding new optional fields and JSON keys is safe (older clients ignore them).
- Removing or renaming fields is breaking — coordinate with the lowest-permitted client version (force-update gate, version pinning, etc.) before shipping.
- Tightening validation in an existing function (e.g. rejecting a value that was previously accepted) silently breaks older clients. Coordinate.

For purely server-side or admin-only changes: backwards compatibility doesn't apply to client versions, but the admin tooling using the function must be re-deployed in the same release.
