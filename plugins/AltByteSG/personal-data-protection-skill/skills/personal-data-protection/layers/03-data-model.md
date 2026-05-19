# Layer 03 — Data Model

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Tables, columns, fields, and constraints that exist specifically because PDP-family obligations require them. Universal patterns across stacks.

## Consent record

Statutes require organisations to be able to demonstrate that consent was given (where consent is the lawful basis). Keep a per-user, append-only record of consent grants and revocations.

**Recommended shape:**

| Field | Purpose |
|---|---|
| `id` (auto) | Primary key |
| `user_id` | Who the consent belongs to. **Do NOT add a foreign key to your users table** — the consent record must survive account deletion as accountability evidence. |
| `consent_type` | What was consented to. Enum: `push_notifications`, `email_marketing`, `email_transactional`, `location_processing`, `crash_reporting`, etc. — be specific. |
| `action` | Enum: `granted`, `revoked`, `pending` (for soft consents not yet confirmed by the OS / provider). |
| `created_at` | When the action happened. |
| `metadata` (optional) | JSON: source (signup, settings, in-app prompt), client version, IP / user-agent if relevant. |

**Append-only:** access controls must allow inserts but block updates and deletes. The integrity of the record is the whole point.

**Care with timing:** the timestamp must reflect when the user actually consented, not when you happened to write the row. If you auto-seed a consent row at signup before the user has actually been asked (e.g. for an OS-level permission), use the `pending` action and only flip to `granted` when the user genuinely consents — otherwise you have false consent evidence.

## Audit record (admin actions on user data)

When admin / support / internal tooling can read or modify user data, every such action should be logged.

**Recommended shape:**

| Field | Purpose |
|---|---|
| `id` (auto) | Primary key |
| `actor_user_id` | Who performed the action |
| `action` | What was done (`view_user`, `update_profile`, `delete_post`, `reset_mfa`, etc.) |
| `resource_type` | What kind of thing was acted on (`user`, `post`, `report`, `feedback`, etc.) |
| `resource_id` | The specific resource (NULL for list/aggregate actions) |
| `details` | JSON with action-specific context |
| `created_at` | When |

**Mutation logging:** every admin write goes here, no exceptions.

**Read logging:** every admin read of personal data also goes here, **with deduplication** (otherwise dashboard refreshes flood the log). A 5-minute throttle per `(actor, action, resource)` tuple is a reasonable default.

**Aggregate-only reads** (dashboards, KPIs, growth charts, retention metrics) don't need audit rows — they don't expose individual personal data. Document the exclusion in code comments so reviewers can verify.

## Deletion audit record

When an account is deleted, retain proof of the deletion request even after the rest of the account data is gone.

**Recommended shape:**

| Field | Purpose |
|---|---|
| `id` (auto) | Primary key |
| `user_id` (no FK) | Who was deleted |
| `email_hash` | SHA-256 of lowercased email — proves deletion without retaining the email |
| `deleted_at` | When |
| `requested_by` | `user` (self-deletion) or `admin` (forced) |

This is accountability evidence. The retention period is debatable — 7 years (typical statute of limitations) is conservative; indefinite is harder to defend if challenged.

## Terms-of-service version tracking

Add a column on the user record (e.g. `tos_version_accepted`) that records which version of the T&C the user agreed to.

When publishing material changes:
1. Bump the column default in a migration.
2. Decide whether existing users at the prior version must re-accept (depends on what changed; usually material changes warrant re-acceptance).
3. If yes, add an in-app prompt that gates access until they accept the new version.

## Notification preferences

A boolean per channel — typically:

- `push_notifications_enabled`
- `email_notifications_enabled`
- (Add channels as you add them: SMS, in-app, etc.)

**Defaults:**
- `true` is acceptable IF the channel is **transactional only** (account verification, security alerts, content directly requested by the user).
- `false` is required if the channel includes **marketing / promotional** content.

**Mixing transactional and marketing on the same channel is a problem.** Either segregate (e.g. `email_transactional_enabled` + `email_marketing_enabled`) or default the combined flag to `false`.

When a user is required to provide a valid contact (e.g. email for OTP verification at signup), defaulting transactional notifications to `true` for that channel is defensible — accepting the T&C with a working contact constitutes consent for transactional use of that contact.

## Cascade conventions for account deletion

When a user is deleted, decide for each related table:

| Pattern | When to use |
|---|---|
| **CASCADE** (delete the related rows) | The data has no meaning without the owner — pets, owned posts, friend requests, OAuth tokens, push tokens |
| **SET NULL** (orphan the row, blank the FK) | The data is shared with other users and they still need it — chat messages, conversations, group memberships, reports filed about other users |
| **RESTRICT** (prevent deletion) | Almost never appropriate for user-deletion cascades; suggests a missing migration step |

For SET NULL paths: also decide how the now-anonymous data displays. Standard pattern is "Deleted User" attribution with a suppressed avatar.

## Retention markers

Columns that gate retention sweeps:

- `last_data_export_at` — when the user last invoked their data export. Used to rate-limit (e.g. once per 7 days).
- `deleted_at` (soft-delete column) — when a row was tombstoned. Hard-delete sweeps reference this.
- `removed_at` — same idea for content moderation tombstones.
- `event_date` / similar temporal columns — used by event-end retention rules.

Each gated column needs a corresponding sweep job (see [layer 04](04-controls-and-processes.md)) and a documented rule in the privacy policy.

## File / storage path conventions

If your application uploads user-owned files (avatars, photos, documents) to object storage, **encode the owner identity in the path**:

| Pattern | Example | Owner |
|---|---|---|
| `{userId}/...` | `feed/abc-123/post-456.webp` | the user |
| `{containerId}/...` for shared content | `chat-media/conv-abc/msg-def.webp` | the conversation |

Why this matters: when a user is deleted, the orphan-cleanup job needs a way to identify which files belong to whom. A flat namespace makes this impossible.

**Conversation-keyed storage** (group chat photos, group avatars) typically should NOT be deleted when an individual member's account is deleted — those files are part of a shared context that other members still need. Document this in the privacy policy and follow the prevailing platform convention (WhatsApp, Discord, Slack all retain shared content after individual account deletion).

## Personal-data inventory

Maintain a written inventory of every column, field, JSON path, and storage path in the system that holds personal data. The inventory feeds:

- The data-export implementation (see [layer 04](04-controls-and-processes.md))
- The privacy policy disclosure section
- The retention schedule
- The breach assessment matrix (knowing what data was exposed determines notifiability)

The inventory does not need to be a separate system — a markdown file or a tagged comment scheme in your migrations is enough. The discipline of maintaining it matters more than the format.

## Rules when adding a new column or field that holds personal data

See [`checklists/new-data-field.md`](../checklists/new-data-field.md). Briefly:

1. Decide if it needs to be in the data-export response.
2. Decide if it needs disclosure in the privacy policy data-categories section.
3. Decide its retention rule.
4. Decide its FK / cascade behaviour.
5. Add it to the orphan-cleanup paths if it references storage.
6. Verify logging won't capture it in plaintext.
