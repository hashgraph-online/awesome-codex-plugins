# Checklist — Responding to a Suspected Security Incident

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

**This checklist is a pointer, not the runbook.** The authoritative incident-response document is your project's `docs/INCIDENT_RESPONSE.md` (built from `templates/INCIDENT_RESPONSE.md.template`). Open it now.

## Why this checklist is separate from the runbook

The runbook lives in your project's `docs/` so non-Claude tools and on-call humans can reach it without going through the skill directory. This checklist is the bridge from a Claude session into that runbook.

## When to open the runbook

Open it the moment you suspect any of:

- A secret leaked (database credentials, API keys, OAuth keys, encryption keys, vault contents)
- An access-control rule was discovered to return data the caller shouldn't see (RLS bypass, IAM misconfig, privileged-function leak)
- An admin / developer accessed user data outside their role (potential s48D / s48E offence)
- A device with admin session / production credentials was lost
- An email with PII was sent to the wrong recipient
- Anomalous traffic (mass downloads, scraping, unusual auth-failure spikes)
- A user reports their account was accessed by someone else
- A vendor notifies you of an incident on their side
- Storage or database was exposed publicly (misconfiguration)

**Doubt = open the runbook.** Cheap to log + assess; expensive to miss the regulatory clock.

## Critical timer (jurisdiction-specific)

Once you assess an incident as "notifiable" per your active jurisdiction's threshold:

| Jurisdiction | Notification deadline to authority | Subject notification |
|---|---|---|
| Singapore PDPA | **3 calendar days** (s26D(1)) — clock starts at **assessment** | On or after authority notification, where significant harm |
| Indonesia UU PDP | **72 hours** from awareness (Pasal 46(1)) | All breaches notify subject; "certain circumstances" trigger public notification |
| Thailand PDPA | **72 hours** from awareness (s37(4)) | If "high risk to rights and freedoms" |
| Malaysia PDPA | **72 hours** from discovery (s12B(1) + JPDP Guideline 25 Feb 2025) | **Within 7 days** of Commissioner notification, where significant harm (s12B(2)) |

For SG the clock starts at **assessment**; for TH / ID / MY it starts at **awareness / discovery**. Your runbook has the full assessment matrix per active jurisdiction.

## Do not use Claude to:

- Submit the regulatory notification (use the official portal — DPO submits manually)
- Send the user notification email (templates in the runbook — DPO sends from your privacy contact address)
- Make legal calls about whether something is "significant harm" or whether a particular breach is notifiable

## Do use Claude to:

- Triage the technical surface (what files, what tables, what users affected)
- Draft containment migrations (revoke access, tighten access-control rules, rotate credentials)
- Search application and platform logs for related events
- Draft the post-mortem
- Cross-reference the incident against the obligation files for the active jurisdiction

## After the incident

- [ ] Post-mortem in `docs/incidents/INCIDENT_YYYY-MM-DD_<slug>.md` per the runbook's section 6.
- [ ] If the incident revealed a structural gap, file a tracking issue and update the project's "Open compliance gaps" list.
- [ ] Update the runbook itself if anything was unclear during the incident — the next responder benefits.
- [ ] Update any layer file in this skill (or your project's overlay of it) if the lesson generalises beyond this project.

## Threshold reference (for the assessment phase)

The runbook contains the per-jurisdiction notifiability matrix. As a starting reference (verify against the active jurisdiction's actual rules):

| Trigger | Notifiable? |
|---|---|
| ≥ 500 affected individuals (Singapore threshold) | Yes |
| Sensitive category leaked at any scale (auth credentials, health, financial, location-with-identity, children's data, private chat content) | Yes |
| Internal-only access (curious admin) without external disclosure | Generally not notifiable as a breach, but IS a personal offence under individual-criminal-liability provisions |
| Loss of device / medium without confirmed access | Notifiable if access is "likely to occur" |

The actual threshold is in the active jurisdiction's `obligations/06-breach-notification.md`.
