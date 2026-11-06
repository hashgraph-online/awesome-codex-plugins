# Interoperability Crosswalk: DDEX, Identifiers, and C2PA

Use this reference only when a package may be exchanged with a registry,
label, distributor, publisher, PRO/CMO, marketplace, or provenance system.

## Boundary

The package schema is an intake and evidence model. The mappings below are
orientation aids, not a DDEX implementation profile, certified message, legal
opinion, registry submission, or C2PA Content Credential. Do not say a package
is DDEX- or C2PA-compliant merely because similarly named fields exist.

Before an external exchange:

1. identify the receiver and exact standard/profile/version it accepts
   (see "Versions to expect" below);
2. validate identifiers with the responsible issuing or authoritative party;
3. map controlled vocabularies using that receiver's rules;
4. preserve source evidence and unknown/disputed status;
5. validate the exported message or manifest with the receiver's conformance
   tooling; and
6. obtain creator/operator approval before transmission.

## Versions to expect (checked 2026-10-23)

- **DDEX ERN**: DDEX advises implementing the most recent ERN 4.3.x; ERN 4.3.2
  is the latest published. Some receivers may still ingest ERN 3.8.x
  feeds. Ask the receiver which version and release profile it ingests; never
  assume 4.3.
- **C2PA**: the specification is on the 2.x line (2.2 shipped in 2025; later
  2.x revisions followed in 2026). Record the spec version the verifier
  reports alongside each `content_credentials[]` result rather than assuming
  one.
- **AI disclosure at delivery**: Spotify committed in September 2025 to an
  industry AI-disclosure standard for music credits built through DDEX, with
  credits covering vocals, instrumentation, and post-production. Distributors
  roll out the matching delivery fields on their own schedules. Capture AI
  involvement per element in the package (see `package-standard.md`) so it can
  map to whichever field the distributor exposes.

Sources:

- [DDEX ERN knowledge base](https://kb.ddex.net/implementing-each-standard/electronic-release-notification-message-suite-(ern))
- [C2PA specifications](https://spec.c2pa.org/specifications/)
- [Spotify, "Spotify Strengthens AI Protections for Artists, Songwriters, and Producers" (2025-09-25)](https://newsroom.spotify.com/2025-09-25/spotify-strengthens-ai-protections/)

## Object and identifier separation

| Package object | Common identifier | What it identifies | Do not use it for |
| --- | --- | --- | --- |
| `works[]` | ISWC | A musical work/composition | A sound recording or release |
| `recordings[]` | ISRC | A specific sound recording or music video recording | The underlying composition |
| `releases[]` | UPC/EAN | A marketed release/product | Ownership or party identity |
| `parties[]` | IPI/CAE | A party in rights-management systems | A work or recording |
| `parties[]` | ISNI | A public identity for a person or organization | Proof of ownership |
| `releases[]` | Catalog number | A label/distributor catalog reference | A globally unique registry ID |

Every identifier is paired with `status` and `evidence_refs`. A plausible
format is not proof that the identifier is valid or belongs to the object.

## DDEX-oriented mapping

| Package field | DDEX-oriented concept | Export note |
| --- | --- | --- |
| `parties[]` | Party | Map roles and identifiers to the selected DDEX allowed-value sets. |
| `works[]` | Musical work | Preserve writers, publishers, ISWC, and evidence separately. |
| `recordings[]` | Resource / sound recording | Preserve ISRC, performers, master controllers, and asset links. |
| `releases[]` | Release | Map recording membership, release identifiers, label, dates, and territories. |
| `rights_claims[]` | Right share / right-delegation facts | Scope each share by object, right type, territory, and dates. Never force unknown shares to total 100. |
| `licenses[]` | Deal or delegated-use facts | Receiver-specific messages may model these differently; retain source agreements as evidence. |
| `third_party_material[]` | Resource/work dependencies and clearances | Samples, interpolations, covers, loops, and beats need explicit source and clearance state. |

The studio-stage metadata concepts in DDEX Recording Information Notification
(RIN) are useful for contributor, role, session, and resource capture. RIN
orientation does not make this package a valid RIN message.

Primary sources:

- [DDEX Recording Information Notification](https://rin.ddex.net/recording-information-notification/)
- [DDEX studio metadata standards](https://ddex.ddex.net/standards/collection-of-studio-metadata/)
- [DDEX identifier guidance](https://kb.ddex.net/implementing-each-standard/best-practices-for-all-ddex-standards/guidance-on-identifiers%2C-iso-codes-lists-and-dates/communication-of-identifiers-in-ddex-messages)
- [IFPI ISRC Handbook](https://isrc.ifpi.org/isrc-standard/isrc-handbook)
- [ISWC](https://www.iswc.org/iswc)

## C2PA-oriented mapping

`provenance.content_credentials[]` can record that a C2PA manifest was found
or checked. It does not create or sign one.

| Package field | C2PA-oriented concept | Required handling |
| --- | --- | --- |
| `asset_id` | Asset associated with a manifest | Resolve to a hashed asset in `assets[]`. |
| `kind: c2pa` | Content Credential / manifest reference | Store a reference, not private signing material. |
| `verification_status` | Local verification result | Record `verified_at` and evidence from a named verifier. |
| `manifest_reference` | Manifest or sidecar location | Apply privacy classification before sharing. |
| `evidence_refs` | Verification output | Retain the redacted report or digest used for the claim. |

Hashing an asset proves only that the bytes seen later can be compared with
the bytes inventoried. A SHA-256 digest alone does not establish authorship,
ownership, consent, chronology, or C2PA authenticity.

Primary source: [C2PA specifications](https://spec.c2pa.org/specifications/).

## Privacy and synthetic-media consent

- Default packages to `private-draft`.
- Classify contact, wallet/payment, agreement, unreleased-asset, and identity
  fields before external sharing.
- Use `consents[]` for voice, likeness, and AI-use scope. Unknown consent stays
  `unknown`; silence is not consent.
- Never include seed phrases, private keys, account secrets, unredacted IDs,
  or an agreement whose sharing is restricted.
- Export only the minimum fields required by the intended recipient.

## Export gate

An external export is blocked when any required identifier, share, territory,
term, authority, consent, or evidence is disputed or unknown. The package can
still be structurally valid; the blocking condition belongs in
`missing_information[]` and `risk_flags[]`.
