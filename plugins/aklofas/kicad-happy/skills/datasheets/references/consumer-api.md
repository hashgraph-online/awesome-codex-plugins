# Consumer API Reference

How to consume structured datasheet extractions in analyzer code. Covers the `datasheet_features.py` helper, the raw cache access functions from `datasheet_extract_cache.py`, and the skip-with-INFO pattern for detectors that require extraction data.

---

## datasheet_features.py

This module provides typed accessors that abstract cache lookup, null safety, and field path traversal.

### `get_regulator_features(mpn, *, extract_dir=None, analysis_json=None, project_dir=None) -> dict | None`

Returns a dict of regulator-relevant fields from the extraction, or `None` if no extraction is available.

`get_regulator_features` and `get_mcu_features` return `None` only when no extraction is cached for the MPN (`_load`), or when the part is not of the requested kind: topology outside `boost` / `buck` / `ldo` for the regulator helper, topology other than `mcu` for the MCU helper. They also return `None` when no project is named, and `get_mcu_features` returns `None` when only a v1.4 extraction is cached (it falls through to the legacy cache, the only one that carries its fields). Quality is **described, not gated** for these two helpers: the returned dict always carries `quality`, a dict `{score, scale, trusted, reasons}` built by `_quality_v13` (v1.3 caches, scale `0-10`) or `_quality_v14` (v1.4 caches, scale `0-100`), and callers decide. Legacy v1.3 caches (score below `MIN_SCORE`, old `EXTRACTION_VERSION`) are still returned, with `quality.trusted` false and `quality.reasons` such as `low_score (...)` or `stale_version (...)`. `get_pin_function` and `is_extraction_available` gate on `quality.trusted` for legacy caches only (see Quality Gate below).

```python
from datasheet_features import get_regulator_features

feat = get_regulator_features('TPS61023DRLR', project_dir='.')
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
#     'quality': {'score': 8.4, 'scale': '0-10', 'trusted': True, 'reasons': []},
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
| `quality` | `dict` | `{score, scale, trusted, reasons}`; always present |

### `get_mcu_features(mpn, *, extract_dir=None, analysis_json=None, project_dir=None) -> dict | None`

Returns MCU-relevant fields, or `None` if no extraction is available.

Returns `None` when:
- No extraction is cached for the MPN
- Extraction topology is not `'mcu'`
- No project is named (no `project_dir`, `extract_dir` or `analysis_json`)
- Only a v1.4 extraction is cached

```python
from datasheet_features import get_mcu_features

mcu = get_mcu_features('ESP32-S3', project_dir='.')
# Returns:
# {
#     'usb_speed': 'FS',          # 'FS' | 'HS' | 'SS' | None
#     'has_native_usb_phy': True, # None if unknown
#     'usb_series_r_required': True,
#     'quality': {'score': 8.4, 'scale': '0-10', 'trusted': True, 'reasons': []},
# }
# or None if no extraction exists
```

Returned dict fields:

| Field | Type | Description |
|-------|------|-------------|
| `usb_speed` | `'FS' \| 'HS' \| 'SS' \| None` | USB device speed |
| `has_native_usb_phy` | `bool \| None` | Native USB PHY present |
| `usb_series_r_required` | `bool \| None` | Series termination resistors required |
| `quality` | `dict` | `{score, scale, trusted, reasons}`; always present |

### `get_pin_function(mpn, pin_identifier, *, extract_dir=None, analysis_json=None, project_dir=None) -> str | None`

Returns the functional category of a pin, or `None` if not found or extraction unavailable.

`pin_identifier` matches against `pins[].number` (exact match, string) or `pins[].name` (case-insensitive).

```python
from datasheet_features import get_pin_function

fn = get_pin_function('TPS61023DRLR', 'EN', project_dir='.')
# Returns: 'EN' (the pin's function field)
# or None if extraction missing or pin not found
```

Possible return values: `'VIN'`, `'VOUT'`, `'EN'`, `'PG'`, `'SW'`, `'FB'`, `'GND'`, `'IO'`, `'CLK'`, `'RESET'`, `'OTHER'`, or `None`.

### `is_extraction_available(mpn, *, extract_dir=None, analysis_json=None, project_dir=None) -> bool`

Returns `True` iff a v1.4 extraction exists for the MPN, or a v1.3 extraction exists whose `quality.trusted` is true (not stale, score at least `MIN_SCORE`).

```python
from datasheet_features import is_extraction_available

if is_extraction_available('TPS61023DRLR', project_dir='.'):
    # Safe to call get_regulator_features()
    pass
```

---

## None Contract

The contract for all helper functions: individual fields within a returned dict may be `None`, distinct from `False` or `0`.

| Value | Meaning | Detector action |
|-------|---------|----------------|
| `None` (whole return) | No extraction cached, no project named, or the part is not the requested kind (`get_pin_function`: also an untrusted v1.3 extraction or unknown pin) | Skip the check; emit INFO |
| `None` (field within dict) | Datasheet didn't specify this field | Treat as unknown; do not fire checks based on this field |
| `False` | Datasheet explicitly says feature is absent | Fire relevant checks if configured |
| `0` / `0.0` | Datasheet specifies zero | Treat as numeric zero |

Detectors must distinguish `None` (unknown) from `False` (explicitly no). Example: `has_pg=None` means unknown; `has_pg=False` means confirmed absent.

---

## Skip Pattern for Detectors

When a detector needs extraction data and the helper function returns `None` (whole function return), emit an INFO-level finding and return — do not fire the rule.

```python
feat = get_regulator_features(mpn, project_dir=ctx.project_dir)
if feat is None:
    findings.append({
        "severity": "info",
        "rule_id": "SS-004",
        "summary": (
            f"Check SS-004 skipped for {ref}: no datasheet extraction for {mpn}. "
            f"Download the datasheet and run the datasheets extraction pipeline."
        ),
        "detector": "audit_soft_start",
    })
    return findings

# feat may still be untrusted: check feat['quality']['trusted'] before relying on its fields
if feat['has_soft_start'] is None:
    # Field not in extraction; skip this particular sub-check
    pass
elif feat['has_soft_start']:
    # Feature present; run the check
    pass
```

Format for the skip message:
```
Check <rule_id> skipped for <ref>: no datasheet extraction for <mpn>. Download the datasheet and run the datasheets extraction pipeline.
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
extraction = get_cached_extraction(extract_dir, mpn) if extract_dir else None
if extraction is None:
    # no cached data — skip checks that need it
    pass
```

### `resolve_extract_dir(analysis_json=None, project_dir=None, override_dir=None) -> Path | None`

Resolves the `datasheets/extracted/` directory for a project:

1. If `override_dir` is set, use it directly.
2. If `project_dir` is set, use `<project_dir>/datasheets/extracted/`.
3. If `analysis_json` is provided, use the directory of its `"file"` field, else of its first `inputs.source_files` entry.
4. Otherwise return `None`: there is no cache, and the helpers return `None`. There is no shared temp-directory fallback.

In cases 2 and 3 the result is also `None` (with one stderr warning) when the project's `datasheets/` or `datasheets/extracted/` folder is a symlink (`cache_reader.safe_extract_dir`). An `override_dir` is used as given, link or not.

```python
extract_dir = resolve_extract_dir(project_dir="/path/to/project")
```

---

## Resolving extract_dir in Detectors

Detectors called from `analyze_schematic.py` receive an `AnalysisContext` with `ctx.project_dir` (the schematic's folder) and `ctx.cache_dir` (the `datasheets/extracted/` folder used by `lookup()`, or `None`). Pass `project_dir=ctx.project_dir` to the helpers in this file; they return `None` when the project has no cache.

```python
# In a detector
feat = get_regulator_features(mpn, project_dir=ctx.project_dir)
```

If the project has no `datasheets/extracted/` folder, skip silently (no INFO finding) — this is the normal state for projects that have not run the extraction pipeline.

---

## Quality Gate

Quality handling differs by helper (`datasheet_features.py`):

- `get_regulator_features()` and `get_mcu_features()` **describe** quality and do not gate. Any cached extraction of the right kind is returned with `quality = {score, scale, trusted, reasons}`. A detector that needs verified data checks `quality['trusted']` itself and may downgrade confidence or skip.
- `get_pin_function()` and `is_extraction_available()` **gate** on the v1.3 path: an extraction with `quality['trusted']` false (stale `extraction_version` below `EXTRACTION_VERSION`, or `extraction_score` below `MIN_SCORE`, 6.0) yields `None` / `False`. The v1.4 path for these two helpers is not score-gated.

`None` from `get_regulator_features()` or `get_mcu_features()` therefore means "no cached extraction of that kind", not "low quality". For direct cache access, apply the gate explicitly when you need one:

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
