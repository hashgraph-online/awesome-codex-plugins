# Suede AI Release Linter Skills: Worked Handoff

## Inputs

Request: “Check this release folder before delivery.” Use a local source folder,
public-safe `metadata.json`, and a new output directory outside the source.
For an offline exercise use one of the synthetic folders documented in
`scripts/fixtures/README.md`; those files are test material, not a real release.

## Expected output

From the skill directory, substitute the real source and output paths:

```sh
python3 scripts/lint_release.py /path/to/release \
  --metadata /path/to/release/metadata.json \
  --output /path/to/new-lint-output
```

Read both generated reports. Return their paths, actual score, mechanical status,
severity counts, every `error`, important warnings, and the next corrective
action. Exit `1` with written reports means findings require attention; it is
not a reason to repeat the same command or discard the report. The score never
establishes ownership or clearance.

## Failure case

An output path inside the source or an existing report can be rejected before
report generation. Report that operational error, select a fresh sibling output
directory, and rerun only after correcting the path. Do not use `--force`
automatically. Missing Python or pasted-only metadata uses the documented
text-only report shape and the same lint rules, with execution stated accurately.

## Validation

Confirm the files exist before quoting their results. Check the rule in
`lint-rules.md` for each reported severity and the status bands. Verify that
unknown splits and sample status remain unknown, absolute local paths are not
exposed in the handoff, and the input files remain unchanged.
