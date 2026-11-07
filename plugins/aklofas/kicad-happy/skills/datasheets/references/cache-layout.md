# Datasheet Cache Layout (v1.4)

Reference doc describing the on-disk convention for datasheet extractions:
where the files live, how they are named, and when `lookup()` reports a
cache entry stale.

## Directory Structure

```
<project>/
  datasheets/
    manifest.json                       # Distributor download manifest (parts).
    LM2596-ADJ.pdf                      # Source PDFs, as downloaded.
    yageo-rc0603.pdf
    extracted/                          # Per-MPN extraction cache.
      LM2596-ADJ.json                   # Per-MPN fact envelope.
      LM2596-ADJ.plan.json              # Orchestration plan audit.
      LM2596-ADJ.scout.json             # Scout subagent output.
      RC0603FR-071KL.variant.json       # Reserved: per-MPN variant overrides.
      RC0603FR-0750KL.variant.json
      _families/                        # Reserved for Tier 2 family dedup.
        yageo-rc0603.family.json        # Reserved: canonical family extraction.
```

## File Naming

### Per-MPN cache files: `<sanitized_mpn>.json`

`lookup(mpn, cache_dir=...)` resolves to `cache_dir / f"{sanitize_mpn(mpn)}.json"`.
Sanitization rules (`skills/datasheets/datasheet_types/cache_reader.py`):

- Strip leading/trailing whitespace.
- Replace any character NOT in `[A-Za-z0-9_.-]` with `_`.
- No hash suffix. Two MPNs that sanitize to the same string collide; this
  is acceptably rare in practice given real MPN character sets.
- A hand-dropped extraction file must use this sanitized name. The dict helpers in
  `datasheet_features.py` look the MPN up in the legacy manifest index first and
  fall back to this sanitized file name.

Examples:
- `LM2596-ADJ` → `LM2596-ADJ.json`
- `STM32F103C8T6` → `STM32F103C8T6.json`
- `STM32/F103` → `STM32_F103.json`
- `LM 2596` → `LM_2596.json`
- `ABM8G-106-12.000MHZ-T` → `ABM8G-106-12.000MHZ-T.json` (dots and hyphens are kept)

### Source PDFs: `<part_or_family>.pdf`

Lives at `datasheets/<filename>.pdf`. The per-MPN cache file's
`source.local_path` stores the filename relative to `datasheets/`.
`merge_results.py` records the `pdf_path` given to the planner; a leading
`datasheets/` is tolerated when the PDF is resolved.

### Manifest (`datasheets/manifest.json`)

The distributor download manifest, written by the sync scripts: `{schematic, last_sync, parts}`, one entry per MPN downloaded. The extraction cache does not read it.

`schemas/manifest.schema.json` also defines a `pdfs` section (keyed by `sha256:<hex>`, values `{path, mpns[], source_url, is_family}`) for PDF SHA dedup. It is defined but not populated by the current scripts. The legacy v1.3 cache keeps its own index at `datasheets/extracted/manifest.json` (`{version, last_updated, extractions}`), written by `datasheet_extract_cache.py`; v1.4 extractions don't write to it.

### Orchestration audit files

`<sanitized_mpn>.plan.json` (written by `plan_extraction.py`) and `<sanitized_mpn>.scout.json`
(the scout subagent's output, saved by the dispatcher per `dispatch-claude-code.md`) sit alongside the
main `<sanitized_mpn>.json`. They persist the scout output and the per-task
orchestration plan for audit and replay.

`<sanitized_mpn>.json` references these side-files via `extraction.plan_ref`
(relative filename). A missing plan or scout file does not invalidate
the cache — those files are audit metadata, not required for
consumption by `lookup()`.

### `_families/` subdirectory (reserved)

Reserved for Tier 2 family extraction. No code reads or writes this
directory, and its presence does not interfere with `lookup()` or any
other tooling.

**Why the leading underscore:** distinguishes the reserved directory
from per-MPN files that could theoretically sanitize to the same name.
The sanitizer keeps underscores, so an MPN literally named `_families`
sanitizes to `_families`; the leading underscore is a naming convention,
not a guarantee. A regression test in the
test harness (`test_lookup_ignores_families_subdirectory_coexisting_with_cache_files`)
locks the invariant that this edge case does not break `lookup()`.

**Reserved layout:**

```
extracted/
  _families/
    yageo-rc0603.family.json        # Canonical family extraction.
  RC0603FR-071KL.variant.json       # Per-MPN variant overrides.
  RC0603FR-0750KL.variant.json
```

A family-aware `lookup()` call for `RC0603FR-071KL` would:
1. Read `RC0603FR-071KL.variant.json`.
2. Follow `source.family_ref` to locate the family file in `_families/`.
3. Merge the family facts with the variant overrides.
4. Return a single merged `DatasheetFacts`.

No such reader exists: `lookup()` has no merging logic, and
`source.family_ref` is always `None` in every extraction `merge_results.py`
writes. Extraction pipelines must preserve this until a family reader
exists.

## Cache Invalidation

`lookup()` reports a per-MPN cache entry as **stale** when either of
these holds:

1. **PDF sha256 mismatch** — `source.sha256` in the cache JSON does not
   match the sha256 of the PDF at `datasheets/<local_path>`. Detected by
   `lookup()`'s `CacheContext.stale_reason = "pdf_hash_mismatch"`.
2. **PDF missing** — `source.local_path` is null, OR the referenced PDF
   doesn't exist on disk. Detected by `lookup()`'s
   `CacheContext.stale_reason = "pdf_missing"`.

The rest of the lifecycle is the caller's job:

3. **Schema and quality checks.** `lookup()` enforces no schema minimum or quality floor, and the planner treats a cache as current when its `source.sha256` matches the PDF.
4. **Manual refresh.** Re-run the scout on the current PDF (its output carries the PDF's `pdf_sha256`), then `plan_extraction.py <mpn> <pdf_path> --use-cached-scout --cache-dir <cache_dir>`, dispatch the tasks and run `merge_results.py <mpn> --cache-dir <cache_dir>`. When the PDF changed, the planner deletes the previous plan's task results. When it did not (for example after a schema bump), pass the planner `--force` and re-run the completed tasks with the dispatcher's `--force`.

## Stale Cache Handling

`lookup()` does **not** automatically purge or regenerate stale caches.
Staleness is an advisory signal exposed via `DatasheetFacts.stale`;
consumers decide what to do:

- Detectors: the regulator detector skips stale or low-score facts; the
  lookup detectors do not read `stale` yet.
- Extraction: nothing re-extracts a stale entry automatically; refresh it
  by hand (Manual refresh, above).
- Dict helpers (`datasheet_features.py`): return the dict either way, with
  `quality.trusted: false` and `stale_pdf` in `quality.reasons`.

## Static Examples vs Runtime Cache

Two distinct directories that look similar but serve different purposes:

- **`skills/datasheets/examples/<mpn>.json`** (in this repo) — static
  schema documentation, one canonical merged extraction per
  category (regulator, crystal, transistor, opamp, mcu, diode). These
  files are **not read by `lookup()`** at runtime — they exist solely
  to make the v1.4 schemas self-documenting via concrete instances.
  Six MPNs: `lm2596-adj`, `abm8g-106-12.000mhz-t`, `irlml6344`,
  `lm358`, `stm32f103c8t6`, `mbrs540t3g`.
- **`<user-project>/datasheets/extracted/<sanitized_mpn>.json`** — runtime cache,
  populated by running the extraction pipeline on the parts of their
  own schematics. `lookup(mpn, cache_dir=<user-project>/datasheets/extracted)`
  reads from here.

The extraction audit trail (per-stage `.scout.*`,
`.base.*`, `.<category>.*`, `.pinout.*`, `.plan.*` files for the six
canonical MPNs) lives in the harness repo
(`kicad-happy-testharness`) as test fixtures, not in this product
repo. This product repo only ships the final merged JSONs as static
examples.

## Related code

- `skills/datasheets/schemas/` — JSON Schema contracts for per-MPN files,
  pinout, spec_value, base, regulator, extraction envelope, manifest.
- `skills/datasheets/datasheet_types/` — typed Python dataclasses, the
  `lookup(mpn, cache_dir=...)` facade, MPN sanitization and staleness
  detection.
- `skills/datasheets/scripts/datasheet_features.py` — the dict helpers,
  which read v1.4 caches first and fall back to v1.3 caches.
- `skills/datasheets/scripts/plan_extraction.py` and `merge_results.py` —
  the extraction pipeline; they write new entries and `<sanitized_mpn>.plan.json`.
  The scout's output, `<sanitized_mpn>.scout.json`, is saved by the dispatcher (the
  agent following `dispatch-claude-code.md`).
