---
name: suede-rights-passport
description: "Audit rights gaps in ownership, contributors, splits, samples, licenses, provenance, and AI involvement, or assemble a hashed offline handoff package with a validated manifest. Use when asked to \"prepare a rights handoff\" or assess release, licensing, or royalty-routing evidence. Keeps confirmed facts separate from open questions. NOT FOR: release file linting (use suede-release-linter), sync pitching (use suede-sync-packaging), or rollout campaigns (use suede-campaign-in-a-box)."
metadata:
  display-name: "Suede AI Rights Passport Skills"
---

# Suede AI Rights Passport Skills

## Compatibility

Audit mode can use supplied text. Offline package creation and validation need Python 3 and local files; YAML metadata needs PyYAML. No registry, wallet, or upload integration is required.

For a concrete input, expected handoff, and failure check, read
[the worked handoff](references/worked-handoff.md).

## Gate policy

Every check and verdict here is advice to the user, not a control on the agent.
Run the checks, report results honestly, and complete what the user asked. A
failed gate changes the report, never the work. The one exception: a finding
that risks data loss, credential exposure, a legal or rights violation, a
payment mistake, or irreversible public damage. Pause, name the risk, give the
options, and let the user choose.

## Core principle

The work carries questions, not answers. Every rights fact is either confirmed
with user-supplied evidence or unknown with a question attached. Nothing here
clears rights, confirms ownership, adjudicates chain of title, grants or
implies a license, approves a payout, moves money, or writes to a registry.
Humans and counsel make those calls.

## Pick the mode

- **Audit mode**: the user wants to know where the gaps are, has no folder yet,
  or is asking "can I release / license / get paid for this?" Read
  `references/audit-lanes.md`, run the lanes that fit (A rights gaps,
  B provenance, C licensing readiness, D royalty-routing readiness), and
  deliver the evidence table and ship gate. No files are written unless asked.
- **Package mode**: the user wants the handoff folder. Follow the Workflow
  below. When gaps are unclear, run audit lane A first and carry its rows into
  `missing-info-report.md`.

A request to "get this rights-ready" with no other signal starts in audit mode
and offers the package as the next step.

## Red flags: stop

If any of these show up in your reasoning, re-read the core principle:

- "The artist says it's cleared." A claim is evidence of a claim. Status:
  `unconfirmed` (or `claimed` in the manifest).
- "Fill in the missing split so the total reaches 100." A guessed split is a
  false rights fact. Record the shortfall and ask.
- "It's obviously their song." Obviousness is inference. Record what the
  evidence shows.
- "Mark it confirmed so routing can move." Blocked means blocked; unblocking is
  the rights holder's job.
- "Nothing seems missing: skip missing-info-report.md." The report ships even
  when empty.
- "Copy all the assets; sorting is the reviewer's problem." Check for draft and
  do-not-share files before any `--copy-assets` run.
- "Call it registered or cleared since the package looks complete." Complete
  means organized, not approved.

## Workflow (package mode)

1. Identify the source folder or supplied files.
2. Ask for the output location if it is not obvious.
3. Read `references/package-standard.md` for the expected transfer package shape.
4. If working on a local folder, run `scripts/create_transfer_package.py` to inventory files, hash assets, and create starter reports.
5. Read `references/creator-questions.md` and ask only for missing information that blocks package quality.
6. Fill or refine the generated package files:
   - `RIGHTS_PASSPORT.md`
   - `suede-intake.json`
   - `provenance.md`
   - `credits-and-splits.md`
   - `license-notes.md`
   - `optimization-brief.md`
   - `missing-info-report.md`
7. Flag uncertainty clearly. Use `unknown`, `unconfirmed`, or `needs creator confirmation` instead of inventing rights facts. Never resolve a rights question while packaging: ownership, split, sample, and license statuses move to confirmed only on user-supplied evidence, and every open gap ships as a question in `missing-info-report.md`.
8. For an external exchange, read `references/ddex-c2pa-crosswalk.md`, identify the receiver's exact profile/version, and keep the mapping labeled as a crosswalk until receiver conformance tooling passes.
9. Run `scripts/validate_transfer_package.py` with `--strict-current` against new output folders. A pass confirms schema, evidence-state, reference, and share-bound structure only: it does not mean rights are confirmed.
10. End with a concise transfer summary: package path, schema version, files found, missing info, risk flags, privacy/redaction posture, and recommended next step.

## Quick Start

For a local project folder:

```bash
python3 /path/to/suede-rights-passport/scripts/create_transfer_package.py \
  /path/to/source-project \
  --output /path/to/transfer-package \
  --metadata /path/to/source-project/metadata.json \
  --project-title "Project Title" \
  --artist "Artist Name"
```

To copy media into the transfer package as well as inventory it:

```bash
python3 /path/to/suede-rights-passport/scripts/create_transfer_package.py \
  /path/to/source-project \
  --output /path/to/transfer-package \
  --copy-assets
```

Safety defaults:

- Hidden files, dependency folders, build outputs, caches, and secret-like files are skipped by default.
- Symlinked sources, metadata, files, and directories are rejected; the builder
  hashes or copies only regular files that resolve inside the declared source tree.
- Unrecognized file types are skipped unless `--include-other` is passed.
- Absolute local paths are redacted to share-safer names unless `--include-absolute-paths` is passed.
- Existing generated package files are not overwritten unless `--force` is passed.
- The output folder cannot be the same folder as the source or live inside it.
- Public-safe JSON, YAML, or key=value text metadata can prefill known project,
  rights, contributor, release, wallet, and provenance facts. Do not point
  metadata at real `.env`, credential, wallet, or deployment config files.
  Unknown facts remain flagged. YAML metadata requires PyYAML.

**Halt format: material that may not be shareable.** Before any `--copy-assets`
run, scan for draft, unreleased, private, or do-not-share files. If any appear:
stop, name the specific files and why each one reads as do-not-share, offer the
options (exclude and proceed / include with a redaction note / inventory without
copying / abort), and wait for the choice. Use the same shape for anything
hitting the gate policy's extreme-risk exception. Never guess which way the
creator would want it.

## Validate A Package

After creating or editing a package, check that it is structurally complete
with `scripts/validate_transfer_package.py`:

```bash
python3 /path/to/suede-rights-passport/scripts/validate_transfer_package.py \
  --strict-current /path/to/transfer-package
```

It is a dependency-free (stdlib-only) check that executes the bundled Draft
2020-12 JSON Schema. It confirms the 7 required report files, that
`suede-intake.json` matches the shape documented in
`references/intake-schema.md`, real 64-hex `sha256` digests on every asset,
unique IDs with resolving references, evidence on every `confirmed` record,
in-range and non-oversubscribed shares, and explicit privacy/redaction posture:
each one mapped to its exact error string in the Completion Checklist below.

It exits non-zero with a specific error list on failure and prints a short pass
summary, including a risk-flag count, on success. Run `--help` for usage, or
`--quiet` to suppress the success summary. Legacy 0.1 packages remain
inspectable without `--strict-current`; new exchanges require 0.2.0.

To migrate an existing 0.1 manifest without modifying it:

```bash
python3 /path/to/suede-rights-passport/scripts/migrate_intake_v1_to_v2.py \
  /path/to/transfer-package/suede-intake.json
```

The migration writes `suede-intake.v0.2.json`, records the source manifest
digest and custody history, preserves open questions and risk flags, maps only
roles stated in source data, and never upgrades evidence state or fills missing
shares. Review it before replacing any current manifest.

**Structural validity is not a rights clearance.** The validator checks that a
package is shaped correctly and complete, not that the rights facts inside it
are confirmed: a project with unconfirmed ownership, unconfirmed splits, or an
uncleared sample still passes, because `risk_flags[]` and
`missing_information[]` are exactly where that uncertainty belongs. Never read a
PASS as clearance, and never expect a risk-flagged package to fail.

`scripts/fixtures/sample-complete-package/` and `sample-blocked-package/` are
worked examples at both ends of that range. Both are legacy 0.1 packages and validate without `--strict-current`. Read
`scripts/fixtures/README.md` when you need a concrete example of what a
risk-flagged but structurally valid package looks like, or when changing
`create_transfer_package.py`.

## Package Standards

Read each bundled reference at the moment it is needed, not up front:

- `references/audit-lanes.md`: in audit mode, or when gaps need investigating before packaging: the evidence table, severity gate, coverage check, and lanes A-D.
- `references/package-standard.md`: before creating or repairing any package: required output files, folder structure, risk labels, and quality bar.
- `references/intake-schema.md`: when filling or validating `suede-intake.json`.
- `references/ddex-c2pa-crosswalk.md`: before external standards mapping or any DDEX/C2PA claim.
- `references/optimization-checklist.md`: when writing `optimization-brief.md`.
- `references/creator-questions.md`: when information is missing: ask only the questions that block package quality.
- `references/passport-context.md`: when the user asks how the package relates to Suede AI review or the Suede Creator Passport.

Use the bundled assets as templates when creating or repairing a package:

- `assets/rights-passport.template.md`
- `assets/suede-intake.template.json`
- `assets/suede-intake.schema.json`
- `assets/provenance.template.md`
- `assets/credits-and-splits.template.md`
- `assets/license-notes.template.md`
- `assets/optimization-brief.template.md`
- `assets/missing-info-report.template.md`

## Public Safety Rules

- Do not say Suede AI owns, controls, or has cleared a work unless the user provides explicit proof.
- Do not call the package a legal contract.
- Do not ask for private keys, seed phrases, unreleased account secrets, or full payment credentials.
- Do not include private implementation details, private endpoints, internal provider names, or non-public pricing.
- Do not upload files or call live services unless the user explicitly asks and provides the relevant authenticated workflow.
- Treat generated reports and transfer packages as private drafts until a
  creator or operator reviews and redacts them for the intended audience.
- Do not call a field crosswalk DDEX conformance, and do not call a hash a C2PA
  Content Credential. Validate the receiver's exact profile separately.
- Keep composition, recording/master, and release identifiers on their proper
  objects. ISWC and ISRC are not interchangeable, and neither proves ownership.
- Unknown voice, likeness, or synthetic-media consent stays unknown; silence is
  not consent.
- Keep public positioning focused on broadly reusable creator workflows: rights packaging, provenance, registry readiness, royalty routing, licensing, and agent commerce.

## Completion Checklist

Run `scripts/validate_transfer_package.py` with `--strict-current` against the output
folder first and report the result: it is the evidence behind most of this
checklist, and every structural gap it names gets fixed before the package is
called ready. Each machine-checked box names the error raised when it is unmet:

- All 7 required files present: *missing required file*.
- Every asset has a stable relative path and a 64-hex SHA-256: *empty or
  non-string sha256 field*.
- Parties, works, recordings, and releases have distinct IDs that resolve:
  *duplicate id* / *references unknown id*.
- Every media/document file is inventoried or intentionally excluded, and
  identifiers (ISWC, ISRC, IPI/CAE, ISNI, UPC/EAN, catalog) sit only on their
  proper objects: *identifiers[…].scheme is unsupported*.
- Claims and licenses are scoped by subject, right/use type, party, territory,
  term, evidence, and restrictions, with no scope over 100%: *share_percent
  must be null or between 0 and 100* / *total … above 100%*. Never force
  unknown shares to total 100.
- Every `confirmed` record carries evidence: *is confirmed but has no
  evidence_refs*.
- Privacy classification and redaction posture are explicit:
  *privacy.default_classification is unsupported*.

Three boxes the validator cannot check: the human-judgment residue, on which a
clean run says nothing:

- **Do-not-share review**: no draft, private, or unreleased material was copied
  in without the user's explicit choice (the halt format above).
- **Redaction review**: someone read the sensitive fields before any external
  share instead of trusting the classification labels.
- **Uncertainty stated**: final clearance requires creator/legal confirmation
  wherever a rights fact is uncertain; contributor, split, license, sample, and
  ownership facts are confirmed only on user-supplied evidence and `unknown`
  when in doubt; `missing-info-report.md` ships even when empty, and
  `optimization-brief.md` ships with concrete next actions.

A validator pass still does not resolve a rights fact.

## Downstream Review Context

Artifacts produced by this skill (`RIGHTS_PASSPORT.md`, `suede-intake.json`,
`provenance.md`, `credits-and-splits.md`, `license-notes.md`) are portable
review materials. They can support a release, registry, licensing conversation,
collaborator handoff, marketplace review, label review, advisor review, or
Suede AI review without claiming that any downstream system has accepted, cleared,
registered, paid, or approved the work.

## Routing

- File, artwork, stem, and metadata lint before packaging →
  **suede-release-linter**.
- Track headed to film, TV, ads, games, or trailers →
  **suede-sync-packaging**, carrying the audit's open clearance questions.
- The release needs a rollout → **suede-campaign-in-a-box**.

Family order: suede-release-linter (files) → suede-rights-passport (audit, then
package) → suede-sync-packaging (pitch).
