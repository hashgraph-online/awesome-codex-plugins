# Datasheet Cache Layout (v1.4)

Reference doc describing the on-disk convention for datasheet extractions.
Consolidates details scattered across Tracks 2.1–2.6 so Phase 3 extraction
implementers and future category-schema authors have a single place to
check.

## Directory Structure

```
<project>/
  datasheets/
    manifest.json                       # Tier 1 PDF SHA dedup (Track 2.1 schema).
    LM2596-ADJ.pdf                      # Source PDFs — one per unique SHA.
    yageo-rc0603.pdf
    extracted/                          # Per-MPN extraction cache.
      LM2596-ADJ.json                   # Per-MPN fact envelope (Track 2.1).
      LM2596-ADJ.plan.json              # Orchestration plan audit (Phase 3).
      LM2596-ADJ.scout.json             # Scout subagent output (Phase 3).
      RC0603FR-071KL.variant.json       # Per-MPN variant overrides (v1.5).
      RC0603FR-0750KL.variant.json
      _families/                        # Reserved for v1.5 Tier 2 dedup (spec §14).
        yageo-rc0603.family.json        # Canonical family extraction (v1.5).
```

## File Naming

### Per-MPN cache files: `<sanitized_mpn>.json`

`lookup(mpn, cache_dir=...)` resolves to `cache_dir / f"{sanitize_mpn(mpn)}.json"`.
Sanitization rules (`skills/datasheets/scripts/datasheet_lookup.py`):

- Strip leading/trailing whitespace.
- Replace any character NOT in `[A-Za-z0-9_-]` with `_`.
- No hash suffix. Two MPNs that sanitize to the same string collide; this
  is acceptably rare in practice given real MPN character sets.

Examples:
- `LM2596-ADJ` → `LM2596-ADJ.json`
- `STM32F103C8T6` → `STM32F103C8T6.json`
- `STM32/F103` → `STM32_F103.json`
- `LM 2596` → `LM_2596.json`

### Source PDFs: `<part_or_family>.pdf`

Lives at `datasheets/<filename>.pdf`. The per-MPN cache file's
`source.local_path` stores the filename relative to `datasheets/`. A
`datasheets/` prefix in `local_path` is tolerated for v1.3 legacy caches
(see Track 2.3's `_resolve_pdf_path`) — new extractions write without
the prefix.

### Manifest (`datasheets/manifest.json`)

Single file at the `datasheets/` level. Two sections:

1. **`pdfs`** — keyed by `sha256:<hex>`, values are `{path, mpns[], source_url, is_family}`. Tier 1 SHA dedup: when a PDF is downloaded, the downloader checks if its SHA is already a key; if so, the new MPN is appended to the existing entry's `mpns[]` instead of duplicating the PDF.
2. **`extractions`** — legacy v1.3 cache index, retained for `datasheet_features.py` dual-cache-read fallback (Track 2.5). New v1.4 extractions don't write to this section — they write directly to `<MPN>.json` under `extracted/` and reference the PDF via the `pdfs` section.

Full schema: `skills/datasheets/schemas/manifest.schema.json`. Required `pdfs` entry fields: `path`, `mpns`. Optional: `source_url`, `is_family`.

### Orchestration audit files (Phase 3)

`<MPN>.plan.json` and `<MPN>.scout.json` are written by the Phase 3
`datasheets sync` extraction pipeline alongside the main `<MPN>.json`.
They persist the scout subagent output and the per-task orchestration
plan for audit and replay.

`<MPN>.json` references these side-files via `extraction.plan_ref`
(relative filename). A missing plan or scout file does not invalidate
the cache — those files are audit metadata, not required for
consumption by `lookup()`.

### `_families/` subdirectory (reserved for v1.5)

Reserved for v1.5 Tier 2 family extraction (spec §14). In v1.4 this
directory is **not written to by any code path**. Its presence — if a
v1.5 corpus is mixed with v1.4 readers — does not interfere with
`lookup()` or any other v1.4 tooling.

**Why the leading underscore:** distinguishes the reserved directory
from per-MPN files that could theoretically sanitize to the same name.
`_families` is NOT a valid sanitized MPN output (sanitizer preserves
underscore, so `_families` could in principle be produced by an MPN
literally named `_families`; the underscore prefix is a soft-social
reservation, not a structural guarantee). The Track 2.6 regression
test `test_lookup_ignores_families_subdirectory_coexisting_with_cache_files`
locks the invariant that this edge case does not break `lookup()`.

**v1.5 layout preview:**

```
extracted/
  _families/
    yageo-rc0603.family.json        # Canonical family extraction.
  RC0603FR-071KL.variant.json       # Per-MPN variant overrides.
  RC0603FR-0750KL.variant.json
```

A v1.5 `lookup()` call for `RC0603FR-071KL` will:
1. Read `RC0603FR-071KL.variant.json`.
2. Follow `source.family_ref` (currently always null in v1.4) to locate the family file in `_families/`.
3. Merge the family facts with the variant overrides.
4. Return a single merged `DatasheetFacts`.

v1.4 has no merging logic — `source.family_ref` is always `None` in
every v1.4 extraction. Future extraction pipelines must preserve this
until v1.5 ships the Tier 2 reader.

## Cache Invalidation

A per-MPN cache entry is considered **stale** when any of these hold
(paraphrased from spec §8 + Track 2.3 `lookup()` staleness logic):

1. **PDF sha256 mismatch** — `source.sha256` in the cache JSON does not
   match the sha256 of the PDF at `datasheets/<local_path>`. Detected by
   `lookup()`'s `CacheContext.stale_reason = "pdf_hash_mismatch"`.
2. **PDF missing** — `source.local_path` is null, OR the referenced PDF
   doesn't exist on disk. Detected by `lookup()`'s
   `CacheContext.stale_reason = "pdf_missing"`.
3. **Schema version major-bumped** — when `base.schema.json` or a
   category extension's major version changes, cached extractions of
   that section become stale. v1.4 does not enforce this at read time
   (consumers opt in via `min_schema` per spec §13); Phase 3 extraction
   will re-run when it detects a mismatch.
4. **Quality score below threshold** — extraction-act-time check
   (`extraction.quality_score` < project-configured threshold).
   v1.4 does not enforce at read time.
5. **Manual `--force`** — Phase 3 `datasheets sync --force` re-extracts
   ignoring staleness.

`lookup()` in v1.4 only surfaces PDF-related staleness (#1, #2). The
other triggers are extraction-lifecycle concerns for Phase 3.

## Stale Cache Handling

`lookup()` does **not** automatically purge or regenerate stale caches.
Staleness is an advisory signal exposed via `DatasheetFacts.stale`;
consumers decide what to do:

- Phase 4 detectors: consult `ds.stale` and downgrade finding confidence
  accordingly.
- Phase 3 `datasheets sync`: treat staleness as a trigger for
  re-extraction.
- v1.3 compat wrappers (`datasheet_features.py`, Track 2.5): ignore
  staleness — v1.3 API returns the dict either way; consumers got this
  from v1.3 too.

## Static Examples vs Runtime Cache

Two distinct directories that look similar but serve different purposes:

- **`skills/datasheets/examples/<mpn>.json`** (in this repo) — static
  schema documentation, one canonical merged extraction per Phase 3b
  category (regulator, crystal, transistor, opamp, mcu, diode). These
  files are **not read by `lookup()`** at runtime — they exist solely
  to make the v1.4 schemas self-documenting via concrete instances.
  Six MPNs: `lm2596-adj`, `abm8g-106-12.000mhz-t`, `irlml6344`,
  `lm358`, `stm32f103c8t6`, `mbrs540t3g`.
- **`<user-project>/datasheets/extracted/<MPN>.json`** — runtime cache,
  populated by users running `datasheets sync` against their own
  schematics. `lookup(mpn, cache_dir=<user-project>/datasheets/extracted)`
  reads from here.

The Phase 3a/3b extraction audit trail (per-stage `.scout.*`,
`.base.*`, `.<category>.*`, `.pinout.*`, `.plan.*` files for the six
canonical MPNs) lives in the harness repo
(`kicad-happy-testharness`) as test fixtures, not in this product
repo. This product repo only ships the final merged JSONs as static
examples.

## Related Tracks

- **Track 2.1** — JSON Schema contracts for per-MPN files, pinout,
  spec_value, base, regulator, extraction envelope, manifest.
- **Track 2.2** — Typed Python dataclasses matching Track 2.1 schemas.
- **Track 2.3** — `lookup(mpn, cache_dir=...)` facade + MPN sanitization
  + staleness detection.
- **Track 2.5** — Dual-cache-read layer in `datasheet_features.py`
  preserving v1.3 API compatibility.
- **Phase 3 (planned)** — Extraction pipeline writes new entries; reads
  `manifest.json` for dedup; populates `<MPN>.plan.json` /
  `<MPN>.scout.json` audit trail.
- **v1.5 (planned)** — Tier 2 family extraction consumes `_families/`.
