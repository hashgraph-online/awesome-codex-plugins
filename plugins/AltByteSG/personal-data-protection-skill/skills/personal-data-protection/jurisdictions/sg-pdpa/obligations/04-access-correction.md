# Part 5 — Access and Correction (s21–22A)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

## s21(1) — Access right

**Rule (verbatim):** *"On request of an individual, an organisation must, as soon as reasonably possible, provide the individual with — (a) personal data about the individual that is in the possession or under the control of the organisation; and (b) information about the ways in which the personal data... has been or may have been used or disclosed by the organisation within a year before the date of the request."*

**Practical effect:** must support a complete personal-data export AND a "who we shared it with" disclosure.

**Implementation layer:** [04 Controls](../../../layers/04-controls-and-processes.md), [03 Data model](../../../layers/03-data-model.md) (PII inventory).

**Operationalisation:**
- A function or endpoint that returns the user's complete personal-data set as structured data (typically JSON)
- Delivered via in-app share-sheet, download link, or email attachment
- Rate-limit (e.g. once per 7 days) to prevent abuse
- The disclosure section ("ways in which personal data has been used or disclosed") typically lives as a static block in the export, mirroring the privacy policy's sub-processor table

**Critical:** the export must include *all* personal data the org holds — not just the most-used fields. As new columns / fields are added, the export must be updated. Use the [`new-data-field.md` checklist](../../../checklists/new-data-field.md) to enforce this discipline.

## s21(2)–(4) + Fifth Schedule — Permitted exclusions from access

**Rule:** access need not be provided for Fifth Schedule matters (opinion data for evaluative purposes; legal privilege; confidential commercial info; investigation records; frivolous / vexatious / repetitious requests). And **must not** be provided where it could threaten safety/health of another, cause grave harm to the requester, reveal another individual's PD, reveal an informant's identity, or be contrary to national interest.

## s21(3A) — User-activity / user-provided-data carve-out

**Rule:** where an individual requests their own data, the s21(3)(c)/(d) "reveals another individual's data" exception **does not apply** to the requester's own user-provided data or activity data.

**Practical effect:** chat exports must include the requester's outgoing messages even when those messages reference other users. Activity data (likes, RSVPs, posts) must be included even when it implicates other users by association.

**Operationalisation:**
- For chat-history exports: include the requester's sent messages in full
- For "received messages" (other users' messages in conversations the requester was part of): a defensible read of s21 is to include them, since they form the requester's activity history. See [`new-data-field.md`](../../../checklists/new-data-field.md) for the trade-offs.

## s21(6)–(7) — Notify rejection or partial exclusion

**Rule:** if the organisation refuses access under s21(2)/(3), it *"must, within the prescribed time and in accordance with the prescribed requirements, notify the individual of the rejection."* If access is partial, the individual must be notified of the exclusion.

**Operationalisation:**
- Templated refusal email / in-app message
- Include an exclusion notice section in any partial export bundle (e.g. README in the JSON: "this export excludes X for reason Y")

## s22 — Correction right

**Rule (verbatim, key language):** an individual *"may request an organisation to correct an error or omission in the personal data."* Unless reasonable grounds otherwise, the organisation *"must... correct the personal data as soon as practicable"* and *"send the corrected personal data to every other organisation to which the personal data was disclosed by the organisation within a year before the date the correction was made."* If no correction is made, the organisation *"must annotate the personal data... with the correction that was requested but not made."*

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md) (self-service edit screens).

**Operationalisation:**
- Self-service edit for fields the user can correct themselves (display name, email, phone, bio, profile data)
- Channel via the privacy email for fields under admin control (account ID, T&C version, etc.)
- For any downstream system that received the data (CRM, analytics destination, partner integrations), build correction propagation
- Annotation table for cases where a correction is refused

## s22(7) + Sixth Schedule — Permitted exclusions from correction

**Rule:** correction does not apply to opinion data for evaluative purposes; exam scripts/results; private trust beneficiary data; mediation/arbitration records; prosecution documents (proceedings open); **derived personal data**.

**Practical effect:** computed / derived fields (badge counts, scores, computed match suggestions) are not subject to correction — but the underlying inputs are.

**Operationalisation:**
- Identify which fields are derived vs source data
- Document the exempt-as-derived fields in an internal note
- For any user-facing data-quality issue, surface the underlying source field for the user to correct

## s22A — Preservation of refused-access copy

**Rule:** where an access request is refused (in whole or in part), the organisation *"must preserve, for not less than the prescribed period, a copy of the personal data concerned"* and ensure the copy is *"complete and accurate."*

**Practical effect:** refusing access does not let you delete the data; you must snapshot and retain it.

**Operationalisation:**
- On refusal, snapshot the user's data into a preservation table or storage object with a timestamp
- Retain for ≥ the prescribed period (currently 30 days)
- Include the preservation in your retention schedule (out of scope of normal cleanup until the period expires)

## Response time

PDPC guidance: 30 calendar days. Many privacy policies state "30 business days" — this is laxer than guidance and worth tightening.

## What "complete" means in practice

If a user files an access request and the export is missing categories the system actually holds, that's a finding. PDPC reviews access-request responses by comparing against the schema. Use the data-field inventory (see [layer 03](../../../layers/03-data-model.md)) and the new-data-field checklist to keep the export current.
