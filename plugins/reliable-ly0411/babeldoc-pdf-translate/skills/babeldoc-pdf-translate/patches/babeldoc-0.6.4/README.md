# BabelDOC 0.6.4 compatibility patch

Compatibility ID: `0.6.4-pdftranslate.1`. Modified on 2026-10-11 for this repository.

These unified diffs modify [BabelDOC](https://github.com/funstory-ai/BabelDOC),
Copyright BabelDOC contributors, under AGPL-3.0 (see [LICENSE](LICENSE)). The
repository's MIT license does not relicense these upstream-derived patches.
The full corresponding upstream source is available from the linked project and
the [0.6.4 source distribution](https://pypi.org/project/BabelDOC/0.6.4/#files).
This directory plus that exact upstream source describes the modified runtime.
No upstream binaries, model assets, private PDFs or credentials are included.

The patch fixes first-page watermark typesetting, selected-page indexing,
alternating-page replacement and split-output names; preserves exact Unicode
with PDF ActualText; and prevents recognized signed numbers/decimals/exponents
from splitting across physical lines. The CLI version gains `+pdftranslate.1`;
distribution metadata remains unchanged.

Use the engine virtual environment's Python:

```sh
python scripts/repair_runtime.py --apply
python scripts/repair_runtime.py --check
python scripts/repair_runtime.py --rollback
```

Run from the skill root. No translation may be active during changes. All source
hashes are checked before any source write; backups are verified before reuse.
Unknown versions or altered files fail closed. A rollback retains original
source bytes. An unpatched engine is still callable by the CLI adapter, but its
known defects remain; structural validation rejects incomplete output.
