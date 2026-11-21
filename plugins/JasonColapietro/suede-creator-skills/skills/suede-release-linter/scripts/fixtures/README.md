# Release-lint fixtures

Two synthetic release folders that sanity-check whether `scripts/lint_release.py`
still categorizes correctly after any change to it. All names, contributors, and
metadata in both fixtures are fake: no real personal data. This is maintainer
documentation: an agent linting a real user folder never needs it.

- `sample-clean-project/`: a small release folder (metadata declaring no AI
  involvement, a WAV master, square 1600x1600 artwork, a lyrics file, three
  stems) shaped to score cleanly
  against `references/lint-rules.md`.
- `sample-blocked-project/`: a release folder deliberately missing title,
  artist, primary media, artwork, ownership confirmation, and valid split
  totals, with samples indicated but clearance unconfirmed: it triggers real
  `error`-severity findings.
- `sample-clean-project.expected.md` / `.expected.json` and
  `sample-blocked-project.expected.md` / `.expected.json`: the actual
  `release-lint-report.md` / `.json` output produced by running the script
  against each fixture, committed as a regression baseline.

## Re-checking the linter

Run it from the skill folder and diff against the committed expected output:

```bash
python3 scripts/lint_release.py scripts/fixtures/sample-clean-project \
  --output /tmp/suede-lint-check-clean
diff scripts/fixtures/sample-clean-project.expected.md \
  /tmp/suede-lint-check-clean/release-lint-report.md

python3 scripts/lint_release.py scripts/fixtures/sample-blocked-project \
  --output /tmp/suede-lint-check-blocked
diff scripts/fixtures/sample-blocked-project.expected.md \
  /tmp/suede-lint-check-blocked/release-lint-report.md
```

## Expected results

The clean fixture should score `99` with `0` errors, `0` warnings, and the
status `strong` (the single unavoidable `info` finding is the
`rights-passport-candidate` note the script always appends), exiting `0`. The
blocked fixture should score `0` with `7` errors, `11` warnings, `3` info
findings, and the status `blocked`, exiting `1`.

The `.md` reports diff byte-for-byte on a clean re-run. The `.json` reports
differ only in the `generated_at` timestamp line, since that field is set to the
current time on every run.
