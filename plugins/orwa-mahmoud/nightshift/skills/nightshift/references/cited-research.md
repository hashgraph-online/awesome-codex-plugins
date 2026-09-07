# Cited research and report

Shared contract for any Nightshift work that reads owner-approved URLs or local files and writes a
cited report. SEO audit, documentation-from-sources, and research-synthesis inherit this file
verbatim. It is not a Hunt catalog entry; those specialized shifts live in `shifts/`.

Use it in repository mode or artifact mode. Artifact mode completes with
`runtime/write-receipt.sh` (native Windows: `runtime/windows/write-receipt.ps1`) into `$NS/receipts/`
against the report and any other output files. Repository mode still makes one conventional commit per item.

## Sources are an explicit list

The owner supplies the URLs and local files. Do not add sources to the search set from memory,
autocomplete, or "what one would usually read." A URL that was not provided may be recorded as
out of scope; it must never be fetched, ranked, or cited as if it had been.

Write a dated source manifest beside the report. One record per source, tab-separated, `#`
comments allowed:

```text
# status<TAB>retrieved<TAB>id<TAB>locator
ok	2026-08-28T08:00:00Z	S1	https://example.com/page
unavailable	2026-08-28T08:00:00Z	S2	https://example.com/gone
ok	2026-08-28T08:00:00Z	S3	file:notes/topic.md
```

- `ok` — the source was actually read. Cite it as `[S1]`.
- `unavailable` — access failed or was refused. Record the locator and why; never invent the
  missing page, ranking, or measurement.
- `locator` is the owner-approved URL or a `file:` path relative to the work target.

Status `ok` requires real retrieval in this shift. Do not copy a citation from another document
and mark it `ok`.

## Citations, observations, inferences

Every important claim in the report names its source with `[ID]` matching the manifest.

**Observations** are what the source states or what a local file contains. **Inferences** are
conclusions drawn from those observations. Keep them in separate sections so a reader can reject
the inference without losing the evidence.

Never fabricate access, rankings, measurements, quotes, or citations. If the evidence is not in
an `ok` source, say so under inferences and limits, or omit the claim.

## Report shape

The report is a non-empty markdown file. These headings are required, in any order after the
title:

- `## Executive summary` — what was asked, what was found, what remains unknown
- `## Sources` — the manifest ids, locators, retrieval times, and unavailable reasons
- `## Observations` — sourced facts only
- `## Inferences` — conclusions, confidence, and limits

Every `ok` id must appear as `[ID]` somewhere in the report. Every `unavailable` id must appear
in `## Sources` with a reason. An `[ID]` that is not in the manifest is a fabricated citation.

## Private material stays off the wire

Do not put private source code, secrets, customer data, credentials, or unpublished material into
an external search query, a public prompt, or a report that will leave the machine. Local `file:`
sources may be quoted in the report only when they are already in the owner-approved set and are
not secret. Lines that look like secrets (`password=`, `api_key=`, embedded basic-auth URLs) are
invalid in both the manifest and the report.

## Verification

Before ticking, run:

```bash
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/check-report.sh" \
  --project "$NIGHTSHIFT_WORKSPACE" \
  --report <report.md> \
  --manifest <sources.tsv> \
  --output <report.md> [--output <other-artifact>...]
```

Native Windows:

```powershell
& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\check-report.ps1" `
  -Project "$NIGHTSHIFT_WORKSPACE" `
  -Report <report.md> `
  -Manifest <sources.tsv> `
  -Output <report.md> [, <other-artifact>...]
```

Exit 0 is a complete cited report. Exit 2 is a contract failure (empty or missing files,
missing headings, uncited `ok` sources, unrecorded unavailable sources, fabricated ids, or
secret lines). Fix the report; do not weaken the checker.

In artifact mode, pass the same output paths to `write-receipt.sh` / `write-receipt.ps1` after
the checker is green. Completion lands in `$NS/receipts/`, not a git log.
