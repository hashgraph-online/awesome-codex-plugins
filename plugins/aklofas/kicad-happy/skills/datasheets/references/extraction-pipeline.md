# Extraction Pipeline — Full Procedure

Full extraction-pipeline procedure. The SKILL.md main flow points here; scripts do the orchestration — this is depth-on-demand, not a required read.

---

## Extraction workflow

**v1.4 pipeline (current, used for all new extractions):**
1. A scout subagent reads the PDF (TOC, headings) for the requested MPN; its schema-valid, unwrapped output, with the PDF's `pdf_sha256` added, is saved as `<cache_dir>/<sanitized_mpn>.scout.json` (the MPN with every character outside `[A-Za-z0-9_.-]` replaced by `_`: `LM317/NOPB` → `LM317_NOPB`).
2. `plan_extraction.py <mpn> <pdf_path> --use-cached-scout --cache-dir <cache_dir>` builds the orchestration plan JSON. A scout `skip` verdict writes an empty plan and exits 1; stop extraction for that part.
3. Category extractor prompts (base, pinout, regulator, …) run per `dispatch-claude-code.md` and `dispatcher-contract.md`.
4. `merge_results.py` validates per-task result files against schemas and merges into `<project>/datasheets/extracted/<sanitized_mpn>.json`.
5. Three-dimension quality score lives at `facts.extraction.quality_score`.
6. Consumers query via `lookup(mpn, cache_dir=…)` or via the v1.3 compat helpers in `datasheet_features.py`.

**v1.3 legacy pipeline (read-only in v1.4):**
1. User runs an analyzer or requests extraction.
2. Skill checks the cache (`<project>/datasheets/extracted/<sanitized_mpn>.json`).
3. On cache miss / stale / low score: Claude reads selected PDF pages and extracts structured data.
4. Extraction is scored; if score ≥ 6.0, cached.
5. Consumers query via `datasheet_features.py`.

For dispatcher dispatch recipes and subagent recipes, see `references/dispatch-claude-code.md` and `references/dispatcher-contract.md`.
