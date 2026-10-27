# BabelDOC 0.6.4 compatibility patch

Compatibility ID: `0.6.4-pdftranslate.math-integrity.3`. Modified on 2026-10-18 for this repository.

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
from splitting across physical lines. It also preserves connected mathematical
glyphs/curves as two-dimensional formula objects in detected table fallback
lines, instead of reflowing their separately parsed italic variables. The CLI
version gains `+pdftranslate.math-integrity.3`;
distribution metadata remains unchanged.

The math-integrity revisions retain inline operator/argument and accent/base
objects. Revision 3 also bounds prose horizontally by its visible glyphs after
adjacent math is grouped. Extracted spaces inside the formula must not pull the
translated prose into that formula. Source glyphs, curves, spaces and vertical
metrics are retained; untouched prose keeps its original boundaries. The rule
uses source geometry and has no paper coordinates.

The Windows revision also explicitly closes both PDFs after watermark merging,
including error paths. It accepts the immediately previous math-integrity.2 hashes only
with a verified original rollback copy and creates a new backup even for
unchanged files. Unvalidated Windows geometry prototypes are not folded into
this six-file runtime patch.

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

Upgrading from `0.6.4-pdftranslate.1` requires rolling back with the previous
bundle's `repair_runtime.py` and manifest first, while keeping its verified
backups. Then apply/check this six-file bundle. Do not replace a patched runtime
in place or use the new manifest to guess the old patch's state. A fresh isolated
0.6.4 environment is also suitable. The R1 sample and inline-equation repair
boundaries and current acceptance are documented in
[the Windows review report](../../references/windows-stability-review.md).
