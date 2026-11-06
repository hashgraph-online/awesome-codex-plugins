# Transfer-package fixtures

Two reference example packages, generated end-to-end by
`create_transfer_package.py` against synthetic (non-real) creator projects. All
names, contributors, splits, and metadata in both are fake: no real personal
data. They exist to sanity-check `create_transfer_package.py` and
`validate_transfer_package.py` after any change, and to show both ends of the
risk range.

## sample-complete-package/

Confirmed ownership, confirmed contributors with matching split percentages, no
samples. Zero risk flags, zero open missing-information items, validates
cleanly.

## sample-blocked-package/

Disputed ownership, unconfirmed contributors and splits, an uncleared sample.
Three high-severity and one medium-severity risk flag, four open
missing-information items: still structurally valid, but clearly not ready for
registry, licensing, or royalty routing.

## The point

Both fixtures pass `validate_transfer_package.py`; only their risk posture
differs. That is the design, not a validator bug: structural validity and
rights confirmation are two independent checks, and `risk_flags[]` and
`missing_information[]` are exactly where unresolved rights questions are
supposed to live.

```bash
python3 ../validate_transfer_package.py ./sample-complete-package
python3 ../validate_transfer_package.py ./sample-blocked-package
```

Both fixtures use the legacy 0.1 manifest, so they pass without
`--strict-current` and fail with it by design (`tests/test_rights_passport_schema.py`
asserts exactly that). New packages from `create_transfer_package.py` are 0.2.0
and pass `--strict-current`.
