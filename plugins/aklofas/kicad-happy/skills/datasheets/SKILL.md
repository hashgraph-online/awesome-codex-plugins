---
name: datasheets
description: Extract structured specifications from electronic component datasheet PDFs — pinouts, electrical characteristics, peripherals, topology, and features. Cache extractions per project for consumption by schematic and PCB analyzers. Primary consumer infrastructure for `kicad`, `emc`, `spice`, and `thermal` analyzers. Use this skill whenever the user asks to extract, verify, or read specs from a component datasheet; when analyzers need verified IC knowledge (EN pin thresholds, PG presence, USB peripheral speed); or when a review mentions datasheet coverage, extraction quality, or per-MPN specifications. Also triggers on "extract this datasheet", "what are the specs for MPN X", "verify datasheet extraction", or "check pin functions for part Y".
---

# Datasheets Skill

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `digikey` / `mouser` / `lcsc` / `element14` | **Producers** — download the PDFs under `<project>/datasheets/` that this skill extracts from |
| `kicad` | **Primary consumer** — VM-001/PU-001/FS-001/PP-001/LR-001/XT-001 + the datasheet-backed lookup detectors (AM-001/OV-001/TJ-001/FT-001/EX-001/PM-001) query extractions via `lookup(mpn)` for verified-IC knowledge |
| `emc` | **Consumer** — switching-frequency, package-Rθ_JA, and operating-voltage data sharpen EMC heuristics |
| `spice` | **Consumer (limited)** — the model resolver reads legacy `spice_specs` fields only; v1.4 typed facts are not used |
| `thermal` | **Consumer** — package Rθ_JA + junction temperature limits drive Tj estimates (TS-001..TJ-001) |
| `bom` | **Indirect** — coverage of structured extractions affects BOM verification confidence |

**Handoff guidance:** This skill is consumer infrastructure. The typical flow is `distributor skill downloads PDF → datasheets skill extracts → analyzer skill queries`. Use this skill directly when (a) the user asks to extract or verify a specific MPN, (b) an analyzer reports `trust_level: low` and the gap is per-MPN extraction quality, or (c) a new MPN was added to the BOM and downstream detectors should pick up its verified specs. Don't run this skill in isolation if the user just wants a design review — call it from the kicad workflow at the "Sync datasheets" step instead.

## Purpose

Extract structured, machine-readable specifications from component datasheet PDFs and make them available to analyzer skills. Works on whatever PDFs are downloaded under `<project>/datasheets/` (downloads are owned by distributor skills like `digikey`, `mouser`, `lcsc`, `element14`).

## Scope

This skill owns:
- **Extraction schemas** — canonical JSON structures for per-MPN specs. v1.4 ships 6 JSON Schema Draft 2020-12 schemas under `schemas/` (`base`, `pinout`, `spec_value`, `regulator`, `extraction`, `manifest`) plus 5 v1.4 category extensions (diode, transistor, opamp, mcu, crystal). v1.3 cache format (`EXTRACTION_VERSION` in `scripts/datasheet_extract_cache.py`) is still read for compat.
- **Typed access layer (v1.4)** — `datasheet_types/` package exposes `DatasheetFacts`, `SpecValue`, `Pin`, `Pinout`, `lookup()`, `best()`, `trusted()`, `has_data()`. Recommended for all new consumers.
- **PDF page selection** — heuristics to pick pages most likely to contain pinouts, e-chars, applications, SPICE models.
- **Quality scoring** — v1.4 scores 0–100 on pinout completeness (20 %), base completeness (25 %) and category-extension completeness (25 %), plus a reserved 30 % awarded in full. v1.3 5-dimension weighted rubric still applies to legacy caches.
- **Consumer APIs** — `datasheet_types.cache_reader` (`from datasheet_types import lookup`) for v1.4 typed access; `scripts/datasheet_features.py` for the v1.3 dict-shaped helpers (`get_regulator_features`, `get_mcu_features`, `get_pin_function`) — the v1.3 helpers dual-read v1.4 caches and translate to v1.3 dict shape for legacy detector code.
- **Verification** — `datasheet_verify.py` (v1.3, schema-vs-usage cross-check) plus `verify_v14_extraction` (v1.4, power_domain references resolve, recommended ≤ absolute, regulator pin references exist).

## Non-goals

- **No PDF downloading.** That is owned by distributor skills (`digikey`, `mouser`, `lcsc`, `element14`).
- **No global library.** Each project's extractions live in `<project>/datasheets/extracted/`. There is no shared cross-project cache.

## Cache location

```
<project>/
  design.kicad_sch
  datasheets/
    TPS61023DRLR.pdf        # downloaded by distributor skills
    extracted/
      manifest.json         # extraction manifest (legacy name: index.json)
      TPS61023DRLR.json     # structured extraction (this skill's output)
```

## Reference guides

- `references/extraction-schema.md` — legacy v1.3 cache fields; the current v1.4 contracts are `schemas/extraction.schema.json`, `schemas/base.schema.json` and the category schemas, with extraction instructions under `prompts/`
- `references/field-extraction-guide.md` — how to find each field in datasheets from common vendors (TI, ST, NXP, Espressif, Microchip)
- `references/quality-scoring.md` — legacy v1.3 0–10 rubric; the current 0–100 score is summarised at its top
- `references/consumer-api.md` — how kicad/emc/spice/thermal consume extractions
- `references/cache-layout.md` — v1.4 cache directory convention (per-MPN files, `_families/` reservation, staleness rules)

## Entry-point scripts

- `scripts/datasheet_extract_cache.py` — v1.3 cache manager, resolver, indexer
- `scripts/datasheet_page_selector.py` — page selection heuristics (manual helper; no pipeline script imports it)
- `scripts/datasheet_score.py` — v1.3 extraction quality scoring
- `scripts/datasheet_verify.py` — cross-check extraction vs schematic usage (v1.3 + v1.4 `verify_v14_extraction` mode)
- `scripts/datasheet_features.py` — v1.3 consumer helper API (dual-reads v1.4 caches via `_derive_*_v14` translators)
- `scripts/plan_extraction.py` — **v1.4** orchestration plan generator (extraction pipeline)
- `scripts/merge_results.py` — **v1.4** per-task result validator + merger
- `datasheet_types/` — **v1.4** typed access layer package (`DatasheetFacts`, `SpecValue`, `Pin`, `Pinout`, `lookup`, `best`, `trusted`, `has_data`)
- `distributor_core/` — shared sync/fetch plumbing for the four distributor skills (BOM projection, `manifest.json`, download, verification, the sync driver); not an entry point of this skill

## Extraction workflow

Run the scout first: dispatch `prompts/scout.md` for the MPN and PDF and save its schema-valid, unwrapped output, with the PDF's `"pdf_sha256": "sha256:<hex>"` added, as `<cache_dir>/<sanitized_mpn>.scout.json` (the MPN with every character outside `[A-Za-z0-9_.-]` replaced by `_`: `LM317/NOPB` → `LM317_NOPB`) (`references/dispatch-claude-code.md` Step 1). Then run `python3 <skill-path>/scripts/plan_extraction.py <mpn> <pdf_path> --use-cached-scout --cache-dir <cache_dir>` (`<skill-path>` is this skill's directory) to write the plan, dispatch its tasks, and run `merge_results.py <mpn> --cache-dir <cache_dir>` to validate and merge their results. Without `--use-cached-scout` it exits 2 (it cannot run the scout itself); with the flag and no saved scout it stops with a FileNotFoundError. `merge_results.py` and `validate_extraction_result.py` need the `jsonschema` package (`pip install jsonschema`); everything else here is stdlib-only. Full scout→plan→dispatch→merge procedure: [`references/extraction-pipeline.md`](references/extraction-pipeline.md).

## Consuming extractions (v1.4 typed API)

The recommended consumer surface is the typed `lookup(mpn, cache_dir=...)` facade plus the trust-gating helpers from `datasheet_types`. Import like:

```python
import sys, pathlib
sys.path.insert(0, "<datasheets-skill-path>")
from datasheet_types import lookup, has_data, best, trusted

# Returns Optional[DatasheetFacts]. None on cache miss or unreadable cache; quality is reported on the object, not gated.
facts = lookup("TPS61023DRLR", cache_dir=pathlib.Path("datasheets/extracted"))
if facts is None:
    return  # heuristic-only path; no datasheet evidence available

# Field-level trust gating — every SpecValue list runs through has_data() / best() / trusted().
vin = facts.base.recommended_operating.get("VIN")  # Optional[list[SpecValue]]; recommended_operating is dict[str, list[SpecValue]]
if has_data(vin):
    # Most-trusted single value (first SpecValue meeting threshold, preserves extractor order).
    rec = best(vin, min_confidence="medium")  # Optional[SpecValue]
    if rec is not None and rec.min is not None:
        ...  # use rec.min, rec.max, rec.typ, rec.unit, rec.evidence.{page,section,confidence}

# All SpecValues at threshold (for multi-value fields like absolute_max).
hi_conf = trusted(facts.base.absolute_max.get("VDD", []), min_confidence="high")
```

**Defensive patterns** (mirrors `kicad/SKILL.md` § "Probing Analyzer JSON"):

- `lookup()` returns `None` on a cache miss or an unreadable cache (malformed, non-UTF-8, symlinked, not a regular file, oversized, not an object); a stale PDF or a low quality score is described on the facts (`facts.stale`, `facts.quality`), never a `None`. Always guard with `if facts is None: return`.
- Category extensions are optional on `DatasheetFacts`. `facts.regulator` is `None` when the part isn't in the `regulator` category — check before dereferencing.
- SpecValue lists can be `None` (field not extracted), `[]` (extracted but empty), or `list[SpecValue]`. `has_data()` collapses the first two to `False`; pair with `best()` / `trusted()` for confidence gating.
- `SpecValue.min` / `.max` / `.typ` are each `Optional[float]`. A SpecValue carrying only `typ` (no range) makes `>` / `<` comparisons against `.min` / `.max` raise `TypeError` — guard with explicit `is not None` chains on every numeric access.
- `confidence` is one of `"low"` / `"medium"` / `"high"`. Calling `best()` / `trusted()` with any other string raises `ValueError`.

## v1.3 compat shim

Legacy detectors still call `get_regulator_features(mpn)` / `get_mcu_features(mpn)` / `get_pin_function(mpn, pin)` from `scripts/datasheet_features.py`. These dual-read v1.4 caches and translate to the v1.3 dict shape. New code should use `lookup()` directly.

## When to trigger this skill

- **Immediately after downloading datasheets** via `sync_datasheets_digikey.py`, `sync_datasheets_lcsc.py`, or equivalent. Without extraction, IC-aware checks (VM-001 rail voltage, PS-001 power-good, PR-004 USB, DP-002 USB speed classification) fall back to heuristics on unknown ICs.
- **Before running analyzers on a new project** where datasheets are present but `datasheets/extracted/` is empty — the analyzers won't produce the extractions themselves.
- **When a review flags low trust level** due to missing manufacturer evidence: extracting the ICs referenced by power regulators, MCUs, and high-speed peripherals typically flips `trust_level: low` → `mixed` or `high`.
- **When a user asks for pin verification** ("verify U1 pin names match datasheet") — this skill's cached extraction is the authoritative source.
