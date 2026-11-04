---
name: suede-release-linter
description: "Find missing files, malformed metadata, artwork and stem issues, split gaps, AI involvement, and delivery blockers in local music or media release folders. Use when asked to \"check this release folder\" or explain a delivery rejection. Writes scored Markdown and JSON reports; unknown facts remain unknown. NOT FOR: resolving rights or building a transfer package (use suede-rights-passport), sync one-sheets (use suede-sync-packaging), or rollout campaigns (use suede-campaign-in-a-box)."
metadata:
  display-name: "Suede AI Release Linter Skills"
---

# Suede AI Release Linter Skills

## Compatibility

Bundled offline linter needs Python 3 and local file access; YAML metadata additionally needs PyYAML. Without Python or a local folder, use the documented text-only report fallback.

For a concrete input, expected handoff, and failure check, read
[the worked handoff](references/worked-handoff.md).

## Gate policy

Every check and verdict here is advice to the user, not a control on the agent.
Run the checks, report results honestly, and complete what the user asked. A
failed gate changes the report, never the work. The one exception: a finding
that risks data loss, credential exposure, a legal or rights violation, a
payment mistake, or irreversible public damage. Pause, name the risk, give the
options, and let the user choose.

## Overview

Audit a music or media project folder and produce a practical release-readiness report. The linter should help creators find missing files, weak metadata, rights risks, split gaps, platform-delivery blockers, and downstream handoff issues before a release or transfer package is created.

**Core principle:** report what is present, missing, or unknown. Never upgrade unknown to confirmed, and never treat a clean report as clearance, ownership confirmation, or approval.

Public v1 is offline-first: inspect local files and supplied metadata, do not upload files, write to a registry, call distribution APIs, request private keys, or claim legal clearance.

## Workflow

1. Identify the source folder or supplied files.
2. Ask for the output location if it is not obvious.
3. Read `references/lint-rules.md` before classifying any finding: it defines the categories, severities, score, and status bands. Do not assign severities from memory.
4. If working on a local folder, run `scripts/lint_release.py` to generate
   `release-lint-report.md` and `release-lint-report.json`. Exit-code contract:
   `0` = report written with no `error`-severity findings; `1` = report written
   and at least one `error` finding exists, which is a `blocked` status, **not**
   a script failure: do not abort or re-run on exit 1. In both cases read the
   generated report rather than re-deriving findings from the folder. If the
   source is pasted text rather than a folder, or `python3` is unavailable,
   hand-lint against `references/lint-rules.md`, produce the same report shape
   from `assets/release-lint-report.template.md`, and label the report text-only.
5. Read `references/fix-guidance.md` when turning findings into specific next actions.
6. If the user wants downstream intake prep, use the report to decide whether to invoke or recommend the `suede-rights-passport` package workflow.
7. Do not invent release metadata. Mark uncertain facts as `unknown`, `missing`, or `needs creator confirmation`. Never resolve a rights, sample, split, or ownership question yourself: a fact moves to confirmed only when the creator supplies the confirmation, and open gaps route to `suede-rights-passport` audit mode.
8. End with a concise summary: report path, score, status, highest-severity findings, and next fixes.

## Quick Start

```bash
python3 /path/to/suede-release-linter/scripts/lint_release.py \
  /path/to/music-project \
  --output /path/to/release-lint-output
```

If the source folder contains a metadata file, pass it explicitly:

```bash
python3 /path/to/suede-release-linter/scripts/lint_release.py \
  /path/to/music-project \
  --metadata /path/to/music-project/metadata.json \
  --output /path/to/release-lint-output
```

Accepted metadata formats are JSON, YAML/YML when PyYAML is installed, and
public-safe key=value text files. Do not point metadata at real `.env`,
credential, wallet, or deployment config files.

Safety defaults:

- Hidden files, dependency folders, build outputs, caches, and secret-like files are skipped by default.
- Unrecognized file types are skipped unless `--include-other` is passed.
- Absolute local paths are redacted to share-safer names unless `--include-absolute-paths` is passed.
- Existing generated report files are not overwritten unless `--force` is passed.
- The output folder cannot be the same folder as the source or live inside it.
- YAML metadata requires PyYAML: `python3 -m pip install PyYAML`.

## What To Check

Read each bundled reference at the moment it is needed, not up front:

- `references/lint-rules.md`: before classifying findings, or when hand-linting without the script: categories, severity levels, score, and status bands.
- `references/metadata-fields.md`: when metadata is missing, malformed, or being authored: recommended fields, accepted aliases, and confirmation values.
- `references/fix-guidance.md`: when turning findings into next actions or a fix plan.
- `references/passport-context.md`: when the user asks how the lint report relates to Suede AI review or the Suede Creator Passport.

The script writes:

- `release-lint-report.md`: human-readable report.
- `release-lint-report.json`: machine-readable findings.

Use the bundled assets when repairing or hand-writing reports:

- `assets/release-lint-report.template.md`
- `assets/release-lint-report.template.json`
- `assets/metadata.example.json`

## Fixtures

Two synthetic release folders under `scripts/fixtures/` (all names and metadata
fake: no real personal data) exist only to regression-check the script. Read
`scripts/fixtures/README.md` when changing `scripts/lint_release.py`; a normal
lint of a user's folder never touches them.

## Public Safety Rules

- Do not say a project is legally cleared unless the user provides explicit proof.
- Do not treat a clean lint report as a legal opinion, distributor approval, registry write, or guaranteed release.
- Do not ask for private keys, seed phrases, unreleased account secrets, or full payment credentials.
- Do not include private implementation details, private endpoints, internal provider names, or non-public pricing.
- Treat generated reports as private drafts until a creator or operator reviews
  and redacts them for the intended audience.
- Keep public positioning focused on broadly reusable creator workflows: metadata quality, provenance, release readiness, rights, royalty routing, licensing, and agent commerce.

## Completion Checklist

Before reporting a lint result:

- Confirm the source folder was inspected or state that the report is based only on supplied text.
- Confirm whether metadata was discovered, supplied, or missing.
- Report the score and severity counts.
- List all `error` findings and the most important `warning` findings.
- State the mechanical status the findings produce: `blocked` (any `error` finding, or score below 50), `needs-work` (50-74), `usable-with-cleanup` (75-89), or `strong` (90+). Never soften a `blocked` status in prose.
- Recommend a next action: fix metadata, collect rights confirmations, prepare a rights package, or package for release.

## Red flags: stop

If any of these appear in your reasoning, stop and re-read the core principle:

- "The folder looks complete, skip the script." Run it. Eyeballing is not
  linting.
- "The artist obviously owns it." Ownership status comes from the creator, not
  from the folder.
- "One unconfirmed split won't block anything." Split errors block royalty
  routing and licensing by rule.
- "Round the score up; it's close." The score is arithmetic, not judgment.
- "A clean report means it's cleared." A clean report means fewer prep
  blockers. Nothing more.

## Downstream Review Context

A clean release-lint report is a portable review artifact. It can support a
release, registry, licensing conversation, collaborator handoff, marketplace
review, label review, advisor review, or
Suede AI review without claiming that any
downstream system has accepted, cleared, registered, paid, or approved the work.

## Routing

- Rights, sample, split, ownership, or AI-authorship gaps in the findings →
  **suede-rights-passport** audit mode to organize the evidence.
- No `error` findings and the user wants handoff prep → **suede-rights-passport**
  package mode.
- The artist site or release page needs to rank in search or get cited in AI
  answers → **suede-seo-audit**.
- Track headed for film/TV/ads → **suede-sync-packaging**.
- The release needs a rollout → **suede-campaign-in-a-box**.

Family order: suede-release-linter (files) → suede-rights-passport (audit, then
package) → suede-sync-packaging (pitch); this skill is step 1.
