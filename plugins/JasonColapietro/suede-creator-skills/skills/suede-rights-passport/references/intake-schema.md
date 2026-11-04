# Suede Intake Manifest Schema 0.2.0

`suede-intake.json` is the agent-readable center of the transfer package.
The canonical machine-readable contract is
`assets/suede-intake.schema.json` (JSON Schema draft 2020-12).

Schema validity establishes structure and referential integrity only. It does
not establish ownership, clearance, registration, identifier validity, DDEX
conformance, C2PA authenticity, consent, or authority to transact.

## Top-level model

```json
{
  "schema_version": "0.2.0",
  "package_type": "suede-transfer-package",
  "generated_at": "ISO-8601 timestamp",
  "metadata_source": "optional source label",
  "project": {},
  "creator": {},
  "parties": [],
  "works": [],
  "recordings": [],
  "releases": [],
  "assets": [],
  "rights": {},
  "rights_claims": [],
  "licenses": [],
  "third_party_material": [],
  "consents": [],
  "provenance": {},
  "privacy": {},
  "optimization": {},
  "missing_information": [],
  "risk_flags": []
}
```

Version 0.2 retains `project`, `creator`, and the compact `rights` summary for
0.1 readers. The normalized arrays are the exchange-oriented source of truth.
Do not infer normalized claims from prose when evidence is absent.

## Evidence state

Every identifier, party, work, recording, release, rights claim, license,
third-party-material record, and consent uses one of:

- `confirmed`: supported by a user-supplied evidence reference;
- `claimed`: asserted by a named party but not independently evidenced;
- `unconfirmed`: recorded but awaiting confirmation;
- `disputed`: conflicting evidence or claims exist;
- `unknown`: not enough information to characterize it.

`confirmed` records must include at least one `evidence_refs[]` item. A filename,
document ID, registry readback, or redacted verification report is acceptable;
an agent's conclusion is not.

## Object model

### `parties[]`

People and organizations. Each party has a stable `party-*` ID, name, roles,
optional IPI/CAE or ISNI identifiers, organization, evidence state, evidence
references, and privacy classification. Roles are descriptive in this schema;
an external DDEX export must map them to the receiver's controlled vocabulary.

### `works[]`

Musical works/compositions. Each `work-*` record has a title, optional ISWC,
writer and publisher party references, evidence state, and evidence references.

### `recordings[]`

Sound recordings. Each `recording-*` record has associated asset IDs, optional
ISRC, performer and master-owner party references, evidence state, and evidence
references. Do not place an ISWC here.

### `releases[]`

Marketed releases/products. Each `release-*` record links recordings, UPC/EAN
or catalog identifiers, label/distributor parties, release date, territories,
evidence state, and evidence references.

### Identifiers

An identifier object contains `scheme`, `value`, `status`, and
`evidence_refs[]`. Supported schemes are `ISRC`, `ISWC`, `IPI_CAE`, `ISNI`,
`UPC_EAN`, `CATALOG_NUMBER`, and `PROPRIETARY`. Format checks do not confirm an
identifier; retain `claimed` or `unknown` until authoritative evidence exists.

## Rights and permission model

### `rights_claims[]`

Each claim includes:

- stable `claim-*` ID;
- `subject_type` and `subject_id` (`work`, `recording`, or `release`);
- `right_type` such as `composition`, `publishing`, `mechanical`,
  `performance`, `synchronization`, `master`, `neighboring`, or `distribution`;
- claimant `party_id`;
- nullable `share_percent` from 0 through 100;
- territories and optional start/end dates;
- evidence state, evidence references, and conflict notes.

The validator rejects a known-share total over 100 for the same subject, right
type, territory set, and term. Distinct territorial or temporal scopes are
counted separately. It does not fill a shortfall. A total below 100 remains a
documented gap unless the creator supplies evidence; potentially overlapping
but non-identical scopes still require human rights review.

### `licenses[]`

Record subjects, licensors/licensees, allowed uses and media, territory, term,
exclusivity, sublicensing, revocability, restrictions, evidence state, and
evidence references. A summary is not a substitute for the governing agreement.

### `third_party_material[]`

Record samples, interpolations, covers, beats, loops, visuals, or other
dependencies; link the affected subjects and supporting license where known.

### `consents[]`

Record scope, media, AI-use permission, voice/likeness permission, status, and
evidence. Unknown or absent consent never becomes permission by inference.

## Assets and provenance

Every `assets[]` item includes a stable ID, relative path, category, role,
media type, byte size, and SHA-256 digest. `provenance.chain_of_custody[]`
records events. `provenance.content_credentials[]` may record hash checks or a
C2PA manifest verification result, but never private signing material.

Hash continuity is not proof of authorship, ownership, chronology, or consent.

## Privacy

`privacy.default_classification` is `private-draft` by default. Per-field rules
use JSON Pointers and classifications:

- `public`
- `shared-with-recipient`
- `private-draft`
- `restricted`
- `do-not-share`

Each rule specifies `keep`, `mask`, `remove`, or `review`. Redaction review is
required before external sharing unless an authorized operator explicitly sets
and verifies a narrower policy.

## Open questions and risk flags

`missing_information[]` records a field, creator question, blocked downstream
steps, and severity. `risk_flags[]` records a factual label, severity, detail,
and recommended action. These arrays are the correct place for incomplete or
conflicting facts; structural validation should not erase them.

## Migration from 0.1.0

The validator accepts 0.1.0 packages as `legacy` by default so existing creator
packages remain inspectable. New packages are generated as 0.2.0. Run the
validator with `--strict-current` to require 0.2.0 before an exchange or release.

Migration steps:

1. keep the original 0.1.0 package immutable;
2. create a 0.2.0 copy and retain its source-package hash/evidence reference;
3. map contributors to `parties[]` without upgrading their confirmation state;
4. separate composition (`works[]`) from master (`recordings[]`) and release;
5. translate splits into scoped `rights_claims[]` without filling gaps;
6. record licenses, third-party material, consent, privacy, and provenance;
7. validate with `--strict-current`; and
8. obtain creator/operator review before external exchange.

See `references/ddex-c2pa-crosswalk.md` before mapping to an external standard.
