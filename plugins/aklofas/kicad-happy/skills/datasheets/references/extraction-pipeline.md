# Extraction Pipeline — Full Procedure

Full extraction-pipeline procedure. The SKILL.md main flow points here; scripts do the orchestration — this is depth-on-demand, not a required read.

---

## Extraction workflow

**v1.4 pipeline (current, used for all new extractions):**
1. `plan_extraction.py` builds an orchestration plan JSON.
2. Scout subagent inspects the PDF (TOC, headings) and emits per-MPN scout audit file.
3. Category extractor prompts (base, pinout, regulator, …) run per Phase 2 dispatcher recipe.
4. `merge_results.py` validates per-task result files against schemas and merges into `<project>/datasheets/extracted/<MPN>.json`.
5. Three-dimension quality score lives at `facts.extraction.quality_score`.
6. Consumers query via `lookup(mpn, cache_dir)` or via the v1.3 compat helpers in `datasheet_features.py`.

**v1.3 legacy pipeline (read-only in v1.4):**
1. User runs an analyzer or requests extraction.
2. Skill checks the cache (`<project>/datasheets/extracted/<MPN>.json`).
3. On cache miss / stale / low score: Claude reads selected PDF pages and extracts structured data.
4. Extraction is scored; if score ≥ 6.0, cached.
5. Consumers query via `datasheet_features.py`.

For dispatcher dispatch recipes and subagent recipes, see `references/dispatch-claude-code.md` and `references/dispatcher-contract.md`.
