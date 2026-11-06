# Transfer Package Standard

## Goal

Prepare a creator project for clean downstream review. The package should let an operator, collaborator, label, or agent quickly understand what the work is, where the files are, what rights data is known, what is missing, and what optimization should happen next.

## Required Folder Shape

```text
suede-transfer-package/
  RIGHTS_PASSPORT.md
  suede-intake.json
  provenance.md
  credits-and-splits.md
  license-notes.md
  optimization-brief.md
  missing-info-report.md
  assets/
    audio/
    stems/
    lyrics/
    artwork/
    docs/
```

`assets/` may be empty when the package is manifest-only. A manifest-only package is acceptable if files remain in their original location and `suede-intake.json` records their relative source paths and hashes.

## Required Reports

`RIGHTS_PASSPORT.md`: Human-readable summary of the work, creator, rights posture, ownership confidence, known contributors, known releases, and review readiness.

`suede-intake.json`: Agent-readable manifest. New packages use schema 0.2.0,
the machine contract in `assets/suede-intake.schema.json`, and the field guide
in `references/intake-schema.md`.

`provenance.md`: Chain-of-custody notes, creation history, source folder, file hashes, upload/export history, and registry/readiness notes.

`credits-and-splits.md`: Contributors, roles, publishers, labels, managers, split percentages, wallet/payment details if provided, and confirmation status.

`license-notes.md`: Samples, interpolations, covers, beat leases, sync/master licenses, platform releases, takedown risks, and usage restrictions.

`optimization-brief.md`: Recommended next actions, such as mastering, stems, lyric sync, metadata cleanup, artwork polish, rights registration, licensing setup, or agent commerce packaging.

`missing-info-report.md`: Blockers and unresolved questions. Include this even when there are no blockers.

## Risk Labels

Use plain labels consistently:

- `low`: information is complete enough for intake and no obvious rights blockers are visible.
- `medium`: package can move forward, but some contributor, file, metadata, or release facts need confirmation.
- `high`: do not optimize/register/license until the user resolves a rights, sample, collaborator, or ownership issue.
- `unknown`: not enough information to rate.

## Language Rules

Say "transfer package" or "prepared for downstream review." Avoid saying "ownership transfer" unless the user is explicitly discussing legal assignment. The skill prepares materials for review; it does not perform legal transfer or rights clearance.

Use "needs creator confirmation" instead of guessing.

## Intake Quality Bar

A strong package answers:

- What is the project or work?
- Who created it?
- Which files are originals, masters, stems, lyrics, artwork, and documents?
- Who contributed and what are their roles?
- What rights are confirmed, disputed, licensed, or unknown?
- What release history exists?
- What should be optimized first?
- What facts must be confirmed before registry, licensing, royalty routing, or agent commerce?

It also keeps unlike industry objects separate:

- musical work/composition and its ISWC, writers, publishers, and composition shares;
- sound recording/master and its ISRC, performers, master controllers, and master shares;
- release/product and its UPC/EAN or catalog number, recordings, label, distributor, date, and territories;
- parties and their roles, IPI/CAE or ISNI identifiers, evidence, and privacy state;
- licenses, third-party material, voice/likeness or AI-use consent, and chain-of-title evidence;
- AI involvement per element (vocals, instrumentation, composition, lyrics, post-production), the tools used, and the evidence of human authorship, since distributors and DSPs now ask for AI disclosure at delivery.

Before an external exchange, run the current validator in strict mode and read
`references/ddex-c2pa-crosswalk.md`. A crosswalk is not receiver conformance.
