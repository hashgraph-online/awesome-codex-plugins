# Layer 07 — Operational

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Run-time concerns: incidents, retention sweeps, monitoring, vendor reviews. Universal across stacks; specific deadlines vary by jurisdiction (see active `jurisdictions/<code>/obligations/06-breach-notification.md`).

## Incident response

**Primary document:** an incident-response runbook that lives in the project repo, owned by the DPO. Template at `templates/INCIDENT_RESPONSE.md.template` — copy and customise for your stack and contacts.

The runbook must be specific enough to act on at 2am. Generic content ("notify the regulator") is useless during an incident; specific content ("file via [portal URL] using the saved template at [path]") is what matters.

### Quick reference (do not substitute for the runbook)

| Step | When |
|---|---|
| Detect / become aware | Happens by chance until observability is in place |
| Contain (rotate keys, revoke endpoints, sign out users) | First hour |
| Assess notifiability per the active jurisdiction's threshold | "Reasonable + expeditious" — most regulators target ≤ 30 days from awareness |
| Notify regulator if notifiable | **Jurisdiction-specific deadline — see active `jurisdictions/<code>/obligations/06-breach-notification.md`** |
| Notify affected individuals if significant harm likely | Concurrent or shortly after regulator notification |
| Post-mortem | Within 30 days of resolution |

### Notifiability shortcuts (use the active jurisdiction's actual rules)

Most PDP-family statutes treat as notifiable:

- A breach affecting at least N individuals (the "significant scale" threshold; varies by jurisdiction)
- A breach involving sensitive categories at any scale (auth credentials, health, location-with-identity, children's data, financial info, private communications)
- An internal-only access (e.g. curious admin) is typically NOT notifiable as a breach but IS a personal offence under the individual-criminal-liability provisions

## Retention sweeps

A canonical "PDP cleanup" job that runs daily at off-peak (e.g. 03:00 local time):

1. Soft- or hard-deletes data past its retention period
2. Cleans up associated storage (files, blobs)
3. Logs what was removed (counts, not content)

**Verify the job is alive (recommended monthly):**
- Check the cron / scheduler dashboard for the last successful run
- Alert if the last run is more than ~25 hours old (one cycle missed)

If your platform supports it, expose a manual "run now" trigger in admin tooling so the job can be invoked outside its normal schedule for testing or after a recovery.

## Log retention

| Log source | Retention | Why |
|---|---|---|
| Admin audit log (table) | 7 years (defensible); indefinite (debatable when challenged) | Accountability evidence |
| Consent log (table) | Indefinite or per consent-record retention rule | Consent evidence |
| Operational rate-limit ledgers | Hours to days | Operational only, not PII |
| Deletion audit (email hashes etc.) | 7 years (defensible) | Deletion-request evidence |
| Application server logs | Whatever your platform default is (typically days–weeks) | Operational debugging |
| Database query logs | Same as application logs | Operational |
| Crash / error reporting | 30–90 days typical | Incident investigation |

**PII in logs:** apply the redaction patterns from [layer 04](04-controls-and-processes.md) at every log site. Verify periodically by sampling production logs for raw email addresses, full UUIDs, or token-shaped strings.

## Backups

Most managed databases offer point-in-time recovery (PITR) with a configurable retention window (typically 7–30 days). Backups inherit:
- Same encryption-at-rest as primary
- Same regional placement
- Same access controls on restore

When a user deletes their account, their data persists in backups for the backup retention window. Disclose this in the privacy policy: *"Some data may be retained longer in encrypted backups, which are purged on a rolling schedule."*

PDP-family statutes generally accept backup retention as long as the schedule is documented and bounded.

## Vendor reviews

When adding a new sub-processor: see [`checklists/new-vendor.md`](../checklists/new-vendor.md).

**Quarterly** (when scaling past beta / first 100 users):
- Walk through the sub-processor table in the privacy policy and verify each entry against actual code paths (any new external-domain calls?).
- Confirm DPAs are still in force.
- Check vendor status pages for incidents during the quarter.
- Note any pending vendor changes (deprecations, region migrations) that need privacy-policy updates.

## Monitoring and breach detection

Without monitoring, breach detection is luck. Minimum signals to set up before scaling past beta:

| Signal | Why |
|---|---|
| Failed-auth volume alarm | Credential-stuffing or brute-force attempts |
| Mass-export rate-limit alert | Abuse of the data-export endpoint, or compromise via legitimate sessions |
| Storage egress anomaly | Bulk download of user files |
| Repository secret scanning | Leaked API keys / credentials in commits |
| External monitoring of key user-facing endpoints | Detect outages and misconfigurations |
| Quarterly admin audit log review | Detect unauthorised access by authorised people |

These feed the breach-detection capability that the regulatory clock depends on. Without them, "detection" means "a user complains" — and the clock has been ticking for an unknown period before that.

## Admin audit log review (when multi-admin)

Once more than one person has admin access:

**Quarterly schedule:**
1. Pull the past 90 days of admin audit log entries
2. Spot-check unusual patterns:
   - One admin viewing many distinct users in a short time
   - Off-hours activity
   - Repeat views of the same record
   - Actions on accounts the admin had no reason to touch
3. Document findings in the staff access log
4. Adjust AUP or training as needed

While solo: this is a self-discipline check — useful but not load-bearing. The moment a second person has the role, it becomes structurally necessary.

## Insurance

Cyber-liability insurance is increasingly available for small organisations. Premiums depend on:
- Number of records held
- Categories of data (sensitive categories raise premiums)
- Existing controls (MFA, encryption, audit logging, breach response capability)
- Industry sector

Worth a conversation with a broker once you have meaningful numbers of users. Not a substitute for compliance, but a backstop.

## Documentation discipline

Compliance posture in an audit is judged in large part on what you can show. Keep:

- A dated **compliance evidence bundle** per major release (snapshot of policies, vendor list, audit log review, etc.)
- **Incident logs** for every incident, even minor ones — pattern visibility matters more than individual severity
- **Decision logs** for compliance-relevant choices ("we decided X because Y, accepting risk Z")
- **Training records** if more than one person has access

Solo founders often skip this. Don't — the cost of writing it down is small; the cost of not having it during an enforcement action is large.
