# Suede AI Rights Passport Skills: Worked Handoff

## Inputs

Request: “Prepare a rights handoff for this track.” Supply a local track folder,
public-safe metadata, a signed split document if available, known contributors,
sample information, and a new output location outside the source. Synthetic
exercise: two known contributors, one missing split confirmation, and no sample
declaration. The request authorizes inventory, not uploading or copying private
drafts indiscriminately.

## Expected output

Start with audit lane A for the gaps, then use package mode for the requested
handoff. Create the inventory and seven required reports, retain evidence links,
and put the missing split and sample declaration in `missing-info-report.md` and
the manifest's open-question/risk fields. Hash actual assets; never insert
example digests. Validate the new package from this skill directory:

```sh
python3 scripts/validate_transfer_package.py --strict-current /path/to/package
```

A structural pass can coexist with those open rights questions. State the actual
validator result and risk count without calling the track cleared.

## Failure case

A symlink in the source, non-shareable file, oversubscribed share, or missing
evidence for a `confirmed` fact needs its specific response from the main skill
and schema. Do not follow the link, invent the missing share, or relabel a claim
as confirmed to get a pass. Inventory without copying when appropriate.

## Validation

Read validator errors before changing anything. Confirm each asset hash resolves
to the inspected file, every reference ID resolves, and required reports exist.
Check that the missing split and sample question survived every output and that
private paths and unapproved media are absent from the intended shared package.
