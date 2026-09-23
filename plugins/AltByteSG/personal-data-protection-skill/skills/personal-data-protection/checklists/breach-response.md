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
| Philippines DPA | **72 hours** from knowledge / reasonable belief (NPC Circular 16-03 § 12(a)) — **to NPC *and* subjects in parallel**; plus an **annual** Security Incident Report by 31 March | **Same 72 hours**, not sequential (§ 20(f) RA 10173). **§ 30 makes concealment its own offence** (1.5–5y + ₱500k–₱1M) |
| Vietnam PDPL | **72 hours** from **detection of the act** (Điều 23(1)) — no assessment buffer. Trigger is **harm-based**, incl. honour and dignity; no scale threshold. **Form No. 08** via the authority or the national portal (Decree Điều 28(2)) | Not a fixed statutory clock; Điều 23(3) separately makes **purpose-creep and broken rights paths** notifiable in their own right |

For SG the clock starts at **assessment**; for TH / ID / MY / PH it starts at **awareness / discovery / knowledge** — so in a multi-jurisdiction incident one of those, not SG, is the binding deadline. PH is the only regime here where *failing to notify* is itself a criminal offence (§ 30). **VN is tighter still**: the clock runs from *detection of the violating act*, with no assessment step in between. Your runbook has the full assessment matrix per active jurisdiction.

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
| Internal-only access (curious admin) without external disclosure | **Jurisdiction-dependent — do not assume it is exempt.** SG carves it out (s26B(4)); **TH does not** (s37(1) — still a breach, notifiability per risk assessment); ID / MY / PH have no explicit carve-out. Always a personal offence under individual-criminal-liability provisions |
| Loss of device / medium without confirmed access | Notifiable if access is "likely to occur" |

The actual threshold is in the active jurisdiction's `obligations/06-breach-notification.md`.
