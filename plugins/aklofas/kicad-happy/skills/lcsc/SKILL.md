---
name: lcsc
description: Search LCSC Electronics for electronic components — find parts by LCSC number (Cxxxxx) or MPN, check stock/pricing, download datasheets, analyze specifications. Sister company to JLCPCB, same parts library. Sync and maintain a local datasheets directory for a KiCad project, or use batch MPN-list seeding (`--mpn-list`) for bulk workflows without a project. No API key needed — uses the free jlcsearch community API. Use this skill when the user mentions LCSC, JLCPCB parts library, JLCPCB assembly parts, production sourcing, Cxxxxx part numbers, needs to find LCSC equivalents for parts, is preparing a BOM for JLCPCB assembly, or wants to download datasheets and LCSC is available. For package cross-reference tables and BOM workflow, see the `bom` skill.
---

# LCSC Electronics — Component Search, Datasheets & Ordering

## Related Skills

| Skill | Purpose |
|-------|---------|
| `kicad` | Schematic analysis — extracts MPNs for part lookup |
| `bom` | BOM management — orchestrates sourcing across distributors |
| `jlcpcb` | PCB assembly — shares the same parts library |
| `spice` | Uses LCSC parametric data for behavioral SPICE models (no auth needed) |

LCSC is JLCPCB's sister company — they share the same parts library and `Cxxxxx` part numbers. Use LCSC for **production sourcing** (assembled boards from JLCPCB/PCBWay). DigiKey/Mouser are for prototyping. For BOM management and export workflows, see `bom`.

## Key Differences from DigiKey/Mouser

- **No API key needed** — jlcsearch community API is free and open
- **Lower prices** — especially for passives and Chinese-manufactured ICs
- **JLCPCB integration** — same LCSC part numbers used in JLCPCB assembly BOMs
- **Direct PDF downloads** — LCSC's CDN (wmsc.lcsc.com) serves datasheets without bot protection
- **Low MOQ** — many parts available in quantities as low as 1
- **Warehouses** — Shenzhen (JS), Zhuhai (ZH), Hong Kong (HK)
- **Website**: `https://www.lcsc.com`

## LCSC Part Numbers

Format: `Cxxxxx` (e.g., `C14663`). This is the universal identifier across both LCSC and JLCPCB. Use it for:
- Direct ordering on LCSC
- BOM matching in JLCPCB assembly (see `jlcpcb` skill)
- Cross-referencing between platforms

## Component Search

Use `search_lcsc.py` to search LCSC and JLCPCB for electronic components, check live stock, inspect pricing tiers, identify basic vs. extended parts, and fetch parametric attributes. **No API key required.**

```bash
# Search by keyword or description
python3 <skill-path>/scripts/search_lcsc.py "tactile switch"

# Search for basic parts only (no JLCPCB extended loading fees)
python3 <skill-path>/scripts/search_lcsc.py "0805 100R" --basic

# Filter by package/footprint and stock
python3 <skill-path>/scripts/search_lcsc.py "red led" --package 0805 --in-stock

# Inspect full component details (manufacturer, datasheet URL, price breaks, parametric attributes)
python3 <skill-path>/scripts/search_lcsc.py "C318884" --details

# Output machine-readable JSON (for scripts and agent workflows)
python3 <skill-path>/scripts/search_lcsc.py "ME2108" --limit 5 --json

# Sort results by price or stock
python3 <skill-path>/scripts/search_lcsc.py "microcontroller STM32" --sort price

# Parametric category search (rows carry package, stock, price and attributes)
python3 <skill-path>/scripts/search_lcsc.py "STM32" --category microcontrollers
```

The script:
- Queries the free `jlcsearch` community API for the search, then enriches from LCSC's direct product-detail endpoint (manufacturer, datasheet URL, price breaks) for exact `Cxxxxx` queries and for every hit shown with `--details` — one extra request per hit, 0.5s apart. If jlcsearch has no row for a `Cxxxxx` code, the direct lookup is the fallback.
- Formats results into a clean terminal table highlighting `LCSC #`, `MPN`, `Package`, `Basic/Ext` status, `Stock`, `Price`, and `Description`
- Supports `--basic` filtering to optimize PCB assembly BOM costs for JLCPCB manufacturing
- Supports `--json` for automated BOM enrichment and agent workflows

## jlcsearch API Reference

The jlcsearch community API is the recommended way to search LCSC. **No authentication required.**

**Base URL:** `https://jlcsearch.tscircuit.com`

### General Search

```
GET /api/search?q=<query>&limit=20&full=true
```

Parameters:
- `q` — search query (matches MPN, LCSC code, or description keywords)
- `package` — optional footprint filter (e.g., `0402`)
- `limit` — max results (default 100)
- `full` — accepted but no longer adds fields (the former `extra` block is gone, see below)

### Category-Specific Search

```
GET /resistors/list.json?search=10k+0402
GET /capacitors/list.json?search=100nF+0402
GET /microcontrollers/list.json?search=STM32
GET /voltage_regulators/list.json?search=3.3V
```

### Response Format

General search returns `{"components": [...]}`. As of 2026-09 each hit carries only these fields — the `extra` block (manufacturer, datasheet URL, per-warehouse stock, attributes, price breaks) is no longer returned, even with `full=true`:

```json
{
  "lcsc": 318884,
  "mfr": "TS-1187A-B-A-B",
  "package": "SMD-4P,5.1x5.1mm",
  "is_basic": true,
  "is_preferred": false,
  "description": "-30℃~+85℃ 1.5mm 1.6N ... SMD-4P,5.1x5.1mm Tactile Switches ROHS",
  "stock": 1683297,
  "price": 0.0197
}
```

Key fields:
- `lcsc` — numeric LCSC ID (without "C" prefix); prepend `C` for the LCSC code
- `mfr` — manufacturer part number (no manufacturer name)
- `is_basic` — `true` if JLCPCB basic part (no setup fee); `is_preferred` — JLCPCB preferred extended part
- `stock` / `price` — JLCPCB assembly stock and unit price (USD)

Category endpoints return `{"<category>": [...]}` — keyed by the category name, **not** `components`. Rows differ from the general search: `price1` instead of `price`, `in_stock`, an empty `description`, parametric columns (e.g. `resistance`, `cpu_core`), and `attributes` as a JSON **string**:

```json
{"resistors": [{"lcsc": 25804, "mfr": "0603WAF1002T5E", "description": "", "stock": 37165617,
  "price1": 0.000842857, "in_stock": true, "package": "0603", "resistance": 10000,
  "is_basic": true, "is_preferred": false,
  "attributes": "{\"Resistance\":\"10kΩ\",\"Power(Watts)\":\"100mW\",\"Tolerance\":\"±1%\"}"}]}
```

### LCSC Direct Product Detail (enrichment)

For manufacturer, datasheet URL and price breaks, query LCSC's own endpoint by `Cxxxxx` code — no auth, JSON, `code: 200` on success:

```
GET https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=C318884
```

Useful `result` fields: `productModel` (MPN), `brandNameEn` (manufacturer), `pdfUrl` (direct datasheet PDF), `encapStandard` (package), `productIntroEn` / `productDescEn` (description), `stockNumber` (LCSC stock), `productPriceList[]` (`ladder` = min qty, `usdPrice`). `fetch_datasheet_lcsc.search_lcsc_direct()` wraps this and normalizes the result to the jlcsearch dict shape (`extra.number`, `extra.mpn`, `extra.manufacturer.name`, `extra.datasheet.pdf`, ladder list in `price`); `search_lcsc.py` uses it for `Cxxxxx` enrichment and as the fallback when jlcsearch has no row.

### Rate Limits

Neither API documents rate limits, but be respectful — use delays of 0.5s between calls.

## Datasheet Download & Sync

LCSC's CDN serves datasheet PDFs directly — no bot protection, no special headers needed. This makes LCSC a reliable datasheet source alongside DigiKey.

### Datasheet Directory Sync

Use `sync_datasheets_lcsc.py` to maintain a `datasheets/` directory alongside a KiCad project. Same workflow and `manifest.json` format as the DigiKey and Mouser skills. **No API key required.**

```bash
# Sync datasheets for a KiCad project
python3 <skill-path>/scripts/sync_datasheets_lcsc.py <file.kicad_sch>

# Preview what would be downloaded
python3 <skill-path>/scripts/sync_datasheets_lcsc.py <file.kicad_sch> --dry-run

# Retry previously failed downloads
python3 <skill-path>/scripts/sync_datasheets_lcsc.py <file.kicad_sch> --force

# Custom output directory
python3 <skill-path>/scripts/sync_datasheets_lcsc.py <file.kicad_sch> -o ./my-datasheets

# Parallel downloads (3 workers)
python3 <skill-path>/scripts/sync_datasheets_lcsc.py <file.kicad_sch> --parallel 3

# Batch mode — sync from a plain MPN list (no KiCad project required)
python3 <skill-path>/scripts/sync_datasheets_lcsc.py --mpn-list mpns.txt --output ./datasheets
```

**MPN-list batch mode** (KH-312) — when you have a list of MPNs but no
KiCad project to point at. One MPN per line; blank lines and `#`
comments (full-line and inline) are skipped; generic values are filtered
via `is_real_mpn()` and de-duplicated. Output defaults to `./datasheets/`
in the current working directory when `--output` is omitted.

The script:
- **Runs the kicad schematic analyzer** to extract components, MPNs, and LCSC codes
- **Accepts any identifier** — MPN, LCSC code, or other distributor PNs from KiCad symbol properties
- **Prefers LCSC code** for search (exact match) — falls back to MPN keyword search
- **Falls back to wmsc.lcsc.com API** when jlcsearch has no results, or a hit has no datasheet URL, for an LCSC code (Cxxxxx)
- **Downloads from LCSC CDN** — direct PDF URLs, no bot protection
- **Writes `manifest.json` manifest** — same format as DigiKey/Mouser skills
- **Verifies PDF content** — checks MPN, manufacturer, and description keywords
- **Rate-limited** — 0.5s between API calls (configurable with `--delay`)
- **Saves progress incrementally** — safe to interrupt

### Single Datasheet Download

Use `fetch_datasheet_lcsc.py` for one-off downloads.

```bash
# Search by MPN
python3 <skill-path>/scripts/fetch_datasheet_lcsc.py --search "GRM155R71C104KA88D" -o datasheet.pdf

# Search by LCSC code
python3 <skill-path>/scripts/fetch_datasheet_lcsc.py --search "C14663" -o datasheet.pdf

# Direct URL download
python3 <skill-path>/scripts/fetch_datasheet_lcsc.py "https://wmsc.lcsc.com/..." -o datasheet.pdf

# JSON output
python3 <skill-path>/scripts/fetch_datasheet_lcsc.py --search "C14663" --json
```

The script:
- **OS-agnostic** — uses `requests` → `urllib` → `playwright` fallback chain (no wget/curl)
- **Validates PDF headers** — rejects HTML error pages
- **Falls back to alternative manufacturer sources** when LCSC URL fails
- **Exit codes**: 0 = success, 1 = download failed, 2 = search/API error
- **Dependencies**:
  - `pip install requests` (recommended; urllib fallback works fine for LCSC)
  - `pip install playwright && playwright install chromium` (optional; rarely needed for LCSC)

## LCSC Official API (Requires Approval)

**Base URL:** `https://ips.lcsc.com`. Requires API key + signature authentication. Contact `support@lcsc.com` for access. Rarely needed — jlcsearch covers most use cases.

## Web Search Fallback

If the jlcsearch API is unavailable, search LCSC by fetching the website directly:

```
https://www.lcsc.com/search?q=<query>
```

## Cross-Referencing & Missing Equivalents

LCSC part numbers are specific to the LCSC/JLCPCB ecosystem. Use the `mfr` field (MPN) to cross-reference on DigiKey/Mouser.

When an MPN has no exact LCSC match:
1. Search by key parameters (e.g., "100nF 0402 X7R 16V")
2. Look for pin-compatible alternatives from Chinese manufacturers
3. Verify specs and footprint match — pad dimensions can vary even within the same package size
4. As a last resort, mark as "consigned" and source separately

## Tips

- `is_basic` field matters — JLCPCB basic parts have no setup fee; extended parts cost $3 each
- jlcsearch `stock` is JLCPCB assembly stock; the wmsc detail's `stockNumber` is LCSC's own stock — the two differ
- MOQ and order multiples are no longer in the jlcsearch response — check the LCSC product page before ordering
- Datasheet quality varies for Chinese manufacturers — cross-reference MPN on DigiKey for better docs
