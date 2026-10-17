# Consumer API Reference

How to consume structured datasheet extractions in analyzer code. Covers the `datasheet_features.py` helper, the raw cache access functions from `datasheet_extract_cache.py`, and the skip-with-INFO pattern for detectors that require extraction data.

---

## datasheet_features.py

This module provides typed accessors that abstract cache lookup, null safety, and field path traversal.

### `get_regulator_features(mpn, *, extract_dir=None, analysis_json=None, project_dir=None) -> dict | None`

Returns a dict of regulator-relevant fields from the extraction, or `None` if no extraction is available.

Returns `None` when:
- No extraction is cached for the MPN
- Extraction is stale (below `EXTRACTION_VERSION`)
- Extraction score is below `MIN_SCORE` (6.0)
- Extraction topology is not one of: `'boost'`, `'buck'`, `'ldo'`

```python
from datasheet_features import get_regulator_features

feat = get_regulator_features('TPS61023DRLR')
# Returns:
# {
#     'topology': 'boost',
#     'has_pg': False,           # None if unknown
#     'has_soft_start': True,    # None if unknown
#     'iss_time_us': 12.5,       # None if unknown
#     'en_v_ih_max': 0.96,       # None if not in extraction
#     'en_v_il_min': 0.4,        # None if not in extraction
#     'vin_pin': '2',            # Pin number (str) or None
#     'vout_pin': '3',           # Pin number (str) or None
#     'en_pin': '1',             # Pin number (str) or None
#     'pg_pin': None,            # Pin number (str) or None
# }
# or None if no extraction exists for this MPN
```

Returned dict fields:

| Field | Type | Description |
|-------|------|-------------|
| `topology` | `'boost' \| 'buck' \| 'ldo'` | Circuit topology |
| `has_pg` | `bool \| None` | Part has a power-good output pin |
| `has_soft_start` | `bool \| None` | Integrated soft-start circuit |
| `iss_time_us` | `float \| None` | Soft-start time in microseconds |
| `en_v_ih_max` | `float \| None` | EN pin logic-high threshold (V) |
| `en_v_il_min` | `float \| None` | EN pin logic-low threshold (V) |
| `vin_pin` | `str \| None` | Pin number of VIN pin |
| `vout_pin` | `str \| None` | Pin number of VOUT pin |
| `en_pin` | `str \| None` | Pin number of EN pin |
| `pg_pin` | `str \| None` | Pin number of PG pin |

### `get_mcu_features(mpn, *, extract_dir=None, analysis_json=None, project_dir=None) -> dict | None`

Returns MCU-relevant fields, or `None` if no extraction is available.

Returns `None` when:
- No extraction is cached for the MPN
- Extraction is stale or below `MIN_SCORE`
- Extraction topology is not `'mcu'`

```python
from datasheet_features import get_mcu_features

mcu = get_mcu_features('ESP32-S3')
# Returns:
# {
#     'usb_speed': 'FS',          # 'FS' | 'HS' | 'SS' | None
#     'has_native_usb_phy': True, # None if unknown
#     'usb_series_r_required': True,
# }
# or None if no extraction exists
```

Returned dict fields:

| Field | Type | Description |
|-------|------|-------------|
| `usb_speed` | `'FS' \| 'HS' \| 'SS' \| None` | USB device speed |
| `has_native_usb_phy` | `bool \| None` | Native USB PHY present |
| `usb_series_r_required` | `bool \| None` | Series termination resistors required |

### `get_pin_function(mpn, pin_identifier, *, extract_dir=None, analysis_json=None, project_dir=None) -> str | None`

Returns the functional category of a pin, or `None` if not found or extraction unavailable.

`pin_identifier` matches against `pins[].number` (exact match, string) or `pins[].name` (case-insensitive).

```python
from datasheet_features import get_pin_function

fn = get_pin_function('TPS61023DRLR', 'EN')
# Returns: 'EN' (the pin's function field)
# or None if extraction missing or pin not found
```

Possible return values: `'VIN'`, `'VOUT'`, `'EN'`, `'PG'`, `'SW'`, `'FB'`, `'GND'`, `'IO'`, `'CLK'`, `'RESET'`, `'OTHER'`, or `None`.

### `is_extraction_available(mpn, *, extract_dir=None, analysis_json=None, project_dir=None) -> bool`

Returns `True` iff a v2+, sufficiently-scored extraction exists for the MPN.

```python
from datasheet_features import is_extraction_available

if is_extraction_available('TPS61023DRLR'):
    # Safe to call get_regulator_features()
    pass
```

---

## None Contract

The contract for all helper functions: individual fields within a returned dict may be `None`, distinct from `False` or `0`.

| Value | Meaning | Detector action |
|-------|---------|----------------|
| `None` (whole return) | No extraction cached, stale, or low score | Skip the check; emit INFO |
| `None` (field within dict) | Datasheet didn't specify this field | Treat as unknown; do not fire checks based on this field |
| `False` | Datasheet explicitly says feature is absent | Fire relevant checks if configured |
| `0` / `0.0` | Datasheet specifies zero | Treat as numeric zero |

Detectors must distinguish `None` (unknown) from `False` (explicitly no). Example: `has_pg=None` means unknown; `has_pg=False` means confirmed absent.

---

## Skip Pattern for Detectors

When a detector needs extraction data and the helper function returns `None` (whole function return), emit an INFO-level finding and return — do not fire the rule.

```python
feat = get_regulator_features(mpn)
if feat is None:
    findings.append({
        "severity": "INFO",
        "rule_id": "SS-004",
        "summary": (
            f"Check SS-004 skipped for {ref}: no datasheet extraction for {mpn}. "
            f"Run sync_datasheets to download and extract."
        ),
        "detector": "audit_soft_start",
    })
    return findings

# Now safe to use feat['has_soft_start'], etc.
if feat['has_soft_start'] is None:
    # Field not in extraction; skip this particular sub-check
    pass
elif feat['has_soft_start']:
    # Feature present; run the check
    pass
```

Format for the skip message:
```
Check <rule_id> skipped for <ref>: no datasheet extraction for <mpn>. Run sync_datasheets to download and extract.
```

Do not emit a warning or error for a missing extraction — INFO is the correct severity. The extraction is optional; its absence means the check cannot run, not that there is a design problem.

---

## Direct Cache Access

For cases where the helper functions do not cover the needed field, use the cache functions directly.

### `get_cached_extraction(extract_dir, mpn) -> dict | None`

Returns the full extraction dict, or `None` if not cached.

```python
from datasheet_extract_cache import get_cached_extraction, resolve_extract_dir

extract_dir = resolve_extract_dir(analysis_json=analysis)
extraction = get_cached_extraction(extract_dir, mpn)
if extraction is None:
    # no cached data — skip checks that need it
    pass
```

### `resolve_extract_dir(analysis_json=None, project_dir=None, override_dir=None) -> Path`

Resolves the `datasheets/extracted/` directory for a project:

1. If `override_dir` is set, use it directly.
2. If `project_dir` is set, use `<project_dir>/datasheets/extracted/`.
3. If `analysis_json` is provided, use the `"file"` field to find the project root.
4. Fallback: system temp directory.

```python
extract_dir = resolve_extract_dir(project_dir="/path/to/project")
```

---

## Resolving extract_dir in Detectors

Detectors called from `analyze_schematic.py` receive an `AnalysisContext` object. The extraction directory is resolved once at the top of the analysis run and passed through context.

```python
# In analyze_schematic.py (caller side)
from datasheet_extract_cache import resolve_extract_dir
ctx.extract_dir = resolve_extract_dir(analysis_json=analysis_data)

# In a detector (receiver side)
extract_dir = ctx.extract_dir  # Path or None
if not extract_dir or not extract_dir.exists():
    return []  # skip silently — no extraction infrastructure set up
```

If `extract_dir` does not exist, skip silently (no INFO finding) — this is the normal state for projects that have not run the extraction pipeline.

---

## Quality Gate

The helper functions (`get_regulator_features()`, `get_mcu_features()`, etc.) apply a quality gate transparently:
- Extractions with `extraction_metadata.extraction_score < MIN_SCORE` (6.0) are treated as unavailable.
- Extractions with `extraction_metadata.extraction_version < EXTRACTION_VERSION` are stale and treated as unavailable.

This means a `None` return from a helper does not require the detector to check the score separately. For direct cache access, apply the same gate:

```python
from datasheet_extract_cache import get_cached_extraction, EXTRACTION_VERSION, MIN_SCORE

ext = get_cached_extraction(extract_dir, mpn)
if not ext:
    return []  # skip

meta = ext.get('extraction_metadata') or {}
if (meta.get('extraction_version') or 0) < EXTRACTION_VERSION:
    return []  # stale, skip

if (meta.get('extraction_score') or 0) < MIN_SCORE:
    return []  # low quality, skip
```
