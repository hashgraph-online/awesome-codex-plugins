# Quality Scoring Reference

The scorer (`datasheet_score.py`) evaluates a completed extraction against a five-dimension completeness rubric and returns a total score from 0.0 to 10.0. The score determines whether the extraction is good enough to cache and use for design review.

---

## Thresholds

| Constant | Value | Source |
|----------|-------|--------|
| `MIN_SCORE` | 6.0 | `datasheet_extract_cache.py` |
| `MAX_RETRIES` | 3 | `datasheet_extract_cache.py` |
| `DEFAULT_MAX_AGE_DAYS` | 90 | `datasheet_extract_cache.py` |

An extraction with `total >= 6.0` is considered sufficient. An extraction with `total < 6.0` is retried if `retry_count < MAX_RETRIES`. Keep the highest-scoring extraction across retries (the cache manager overwrites with each new attempt; stop when sufficient).

---

## Five-Dimension Rubric

| Dimension | Weight | Score Function |
|-----------|--------|---------------|
| Pin coverage | 35% | `_score_pin_coverage()` |
| Voltage ratings | 25% | `_score_voltage_ratings()` |
| Application info | 20% | `_score_application_info()` |
| Electrical characteristics | 10% | `_score_electrical_chars()` |
| SPICE specs | 10% | `_score_spice_specs()` |

**Total** = sum of (dimension score × weight), rounded to one decimal place. Weights sum to 1.0.

---

## Dimension Scoring Rules

### Pin Coverage (35%)

Starting score: 10.0.

| Condition | Deduction |
|-----------|-----------|
| No pins in extraction | Score = 0.0 immediately |
| Fewer than 50% of expected pins present | Score = 0.0 immediately |
| Each missing pin (vs expected count) | -2.0 |
| Each pin with name only (no specs, no description, no `required_external`) | -1.0 |

A pin "has specs" if any of these fields is non-null: `voltage_abs_max`, `voltage_operating_min`, `voltage_operating_max`, `current_max_ma`, `threshold_high_v`, `threshold_low_v`. A pin with only `description` or `required_external` (no numeric specs) still avoids the name-only deduction.

If no `expected_pin_count` is passed to `score_extraction()`, the expected count defaults to the number of pins in the extraction (no missing-pin deduction).

Issues list is capped at 5 entries for readability.

### Voltage Ratings (25%)

Starting score: 10.0.

| Condition | Deduction |
|-----------|-----------|
| `absolute_maximum_ratings` dict missing or empty | -3.0 |
| No key ending in `_max_v` with a non-null value | -2.0 |
| `junction_temp_max_c` missing | -1.0 |
| `recommended_operating_conditions` dict missing or empty | -3.0 |
| `vin_min_v` or `vin_max_v` missing | -1.5 |
| `temp_min_c` or `temp_max_c` missing | -1.0 |

### Application Info (20%)

Starting score: 10.0. If `application_circuit` dict is missing or empty: score = 0.0 immediately.

| Condition | Deduction |
|-----------|-----------|
| `topology` missing | -2.0 |
| Zero component recommendation fields populated | -3.0 |
| Only 1 recommendation field populated (expect 2+) | -1.5 |
| Neither `vout_formula` nor `notes` populated | -2.0 |
| `notes` missing (but `vout_formula` present) | -1.0 |

Recommendation fields counted: `inductor_recommended`, `input_cap_recommended`, `output_cap_recommended`, `feedback_resistor_top_ohm`, `feedback_resistor_bottom_ohm`, `compensation_cap`, `bootstrap_cap`, `decoupling_cap`, and any other key ending in `_recommended`.

### Electrical Characteristics (10%)

Category-dependent. Starting score: 10.0.

If `electrical_characteristics` dict is missing:
- Categories with required fields → score = 0.0
- Categories without required fields → score = 5.0

| Condition | Deduction |
|-----------|-----------|
| Each missing required field for category | -3.0 |
| Each missing optional (nice-to-have) field | -1.0 |

Required and optional fields by category:

| Category | Required | Optional |
|----------|----------|---------|
| `operational_amplifier` | `gbw_hz`, `slew_vus` | `vos_mv`, `aol_db`, `rin_ohms` |
| `comparator` | `prop_delay_ns` | `vos_mv`, `aol_db` |
| `linear_regulator` | `vref_v`, `quiescent_current_ua` | `dropout_mv`, `output_current_max_ma` |
| `switching_regulator` | `vref_v`, `switching_frequency_khz` | `quiescent_current_ua`, `output_current_max_ma` |
| `voltage_reference` | `vref_v`, `vref_accuracy_pct` | `temp_coefficient_ppmk` |
| `microcontroller` | (none) | `quiescent_current_ua`, `io_voltage_max` |
| `esd_protection` | `clamping_voltage_v` | `leakage_current_na`, `capacitance_pf` |
| all others | (none) | (none) |

For categories with no required and no optional fields: if 3+ fields are populated, score = 10.0; if 1–2 fields, score = 7.0; if 0 fields, score = 5.0.

Issues list is capped at 5 entries.

### SPICE Specs (10%)

Starting score: 10.0.

| Condition | Score / Deduction |
|-----------|-------------------|
| `spice_specs` dict missing, but `electrical_characteristics` present | Score = 5.0 |
| `spice_specs` dict missing, no electrical chars either | Score = 0.0 |
| `spice_specs` section is empty (all values null) | Score = 0.0 |
| Each missing required SPICE field for category | -4.0 |
| 1–2 fields populated, no required fields for category | Score capped at 6.0 |

Required SPICE fields by category:

| Category | Required SPICE fields |
|----------|----------------------|
| `operational_amplifier` | `gbw_hz` |
| `linear_regulator` | `vref`, `dropout_mv` |
| `switching_regulator` | `vref` |
| `voltage_reference` | `vref` |
| `comparator` | (none) |
| all others | (none) |

---

## Score Interpretation

| Score | Meaning |
|-------|---------|
| >= 8.0 | All critical fields present; high confidence for automated pin audit |
| 6.0 – 7.9 | Sufficient for design review; some optional specs missing |
| < 6.0 | Insufficient; cache manager will retry up to `MAX_RETRIES` times |

An extraction at 5.9 from a part with a minimal datasheet (no application circuit section, no SPICE specs) is not the same as 5.9 from a part whose datasheet has everything but was incompletely extracted. Check the `issues` list to distinguish.

---

## Calling the Scorer

```python
from datasheet_score import score_extraction

result = score_extraction(extraction, expected_pin_count=6)
```

Returns:

```python
{
    "total": 8.2,
    "pin_coverage": 9.0,
    "voltage_ratings": 8.5,
    "application_info": 7.0,
    "electrical_characteristics": 8.0,
    "spice_specs": 8.5,
    "issues": ["Pin 3 (BOOT): name only, no specs", ...],
    "sufficient": True   # True if total >= 6.0
}
```

The `issues` list is the union of per-dimension issue strings (capped per dimension). Use it to guide retry attempts — if the issues show "No application circuit information", re-read the application section pages.

---

## Cache Index Entry

When an extraction is cached via `cache_extraction()`, the `manifest.json` records a summary:

```json
{
  "file": "TPS61023DRLR_a1b2c3.json",
  "mpn": "TPS61023DRLR",
  "category": "switching_regulator",
  "source_pdf": "TPS61023DRLR.pdf",
  "source_pdf_hash": "sha256:...",
  "extraction_date": "2026-04-15T12:00:00+00:00",
  "extraction_score": 8.2,
  "extraction_version": 1,
  "pin_count": 6
}
```

The `extraction_score` in the index is the `total` from `score_extraction()`, stored in `extraction_metadata.extraction_score` inside the full JSON. An entry with `extraction_score < 6.0` may still be present if `retry_count >= MAX_RETRIES` (retries exhausted).

---

## Staleness Check

`is_extraction_stale()` in `datasheet_extract_cache.py` returns `(True, reason)` if any of:

1. Extraction not found in cache (`"not_cached"`)
2. `extraction_version < EXTRACTION_VERSION` (`"schema_upgrade"`)
3. Source PDF hash changed (`"pdf_changed"`)
4. Score below `MIN_SCORE` and retries not exhausted (`"low_score (X.X < 6.0, retry N/3)"`)
5. Extraction older than 90 days (`"age (N days > 90)"`)

A stale extraction can still be returned by `get_extraction_for_review()` along with the stale status; the caller decides whether to use the old data or wait for a refresh.
