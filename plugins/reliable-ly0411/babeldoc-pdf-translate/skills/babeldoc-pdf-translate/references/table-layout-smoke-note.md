# Space-aligned rows and real table cells

A PDF can look tabular while storing each row as a single text object separated by spaces. Translating that object may normalize spaces and reflow the row. This differs from a table whose cells are separate text objects.

A bounded synthetic check with adapter 1.3.0 and BabelDOC 0.6.4+pdftranslate.1 found:

- Space-aligned rows lost column spacing after whole-row translation.
- Independent-cell gridded rows retained Chinese cell labels, numbers, units, formulas and all eight grid lines.
- The original half of the bilingual output matched the source rendering at 72 dpi.

These are historical results for the named versions, not validation of the current adapter.

The adapter passed `--translate-table-text`. BabelDOC v0.6.4 retains a compatibility no-op for its retired RapidOCR table detector, so this flag is not a promise of cell reconstruction. Direct engine runs with translation skipped preserved the source positions.

Review table cells and numbers visually. Use independent cell geometry in synthetic regression fixtures; keep a separate whitespace-aligned fixture to disclose that limitation. Do not claim general scanned, complex-table or multi-page acceptance from this one-page check. No user document belongs in a public test fixture.

Source for the engine behavior: https://github.com/funstory-ai/BabelDOC/blob/v0.6.4/babeldoc/docvision/table_detection/rapidocr.py
