---
name: mouser
description: Search Mouser Electronics for electronic components — secondary source for prototype orders. Find parts, check pricing/stock, download datasheets, analyze specifications. Use with KiCad for BOM creation and part selection. Also supports batch MPN-list seeding (`--mpn-list`) for bulk datasheet workflows without a KiCad project. Use this skill when the user specifically mentions Mouser, when DigiKey is out of stock or has worse pricing, when comparing prices across distributors, or when searching for parts that DigiKey doesn't carry. For package cross-reference tables and BOM workflow, see the `bom` skill.
---

# Mouser Electronics Parts Search & Analysis

## Related Skills

| Skill | Purpose |
|-------|---------|
| `kicad` | Schematic analysis — extracts MPNs for part lookup |
| `bom` | BOM management — orchestrates sourcing across distributors |
| `digikey` | Primary prototype source (prefer for datasheets — direct PDF links) |
| `spice` | Uses Mouser parametric data for behavioral SPICE models |

Mouser is the **secondary source for prototype orders** — use when DigiKey is out of stock or has worse pricing. For production orders, see `lcsc`/`jlcpcb`. For BOM management and export workflows, see `bom`. For datasheets, prefer DigiKey's API (direct PDF links) — Mouser blocks automated PDF downloads.

## API Credential Setup

Mouser uses **simple API key authentication** — no OAuth, no tokens, no callback URLs. The Search API key is a UUID passed as a query parameter.

### Getting Your API Key

1. Go to [mouser.com](https://www.mouser.com) → My Mouser → My Account
2. Under "APIs" section, click "Manage"
3. Register for **Search API** key — this is the one needed for part lookups and datasheet downloads
4. Search API keys may require approval (status shows "pending authorization" initially)

### Setting Credentials

Set the environment variable before running the scripts:
```bash
export MOUSER_SEARCH_API_KEY=your-search-api-key-uuid
```

If credentials are stored in a central secrets file (e.g., `~/.config/secrets.env`), load them first:
```bash
export $(grep -v '^#' ~/.config/secrets.env | grep -v '^$' | xargs)
```

## Mouser Search API Reference

All search endpoints use the Search API key as a query parameter: `?apiKey=<key>`. Content-Type is `application/json` for all POST requests.

### V1 Endpoints

#### Keyword Search
```
POST /api/v1/search/keyword?apiKey=<key>
```
```json
{
  "SearchByKeywordRequest": {
    "keyword": "100nF 0402 ceramic capacitor",
    "records": 50,
    "startingRecord": 0,
    "searchOptions": "InStock"
  }
}
```
- `searchOptions`: `"None"` | `"Rohs"` | `"InStock"` | `"RohsAndInStock"`
- `records`: max 50 per request
- `startingRecord`: offset for pagination

#### Part Number Search
```
POST /api/v1/search/partnumber?apiKey=<key>
```
```json
{
  "SearchByPartRequest": {
    "mouserPartNumber": "GRM155R71C104KA88D|RC0402FR-0710KL",
    "partSearchOptions": "Exact"
  }
}
```
- Up to **10 part numbers**, pipe-separated (`|`)
- Works with both Mouser part numbers AND manufacturer part numbers (MPNs)
- `partSearchOptions`: `"Exact"` | `"BeginsWith"` | `"Contains"`

### V2 Endpoints

V2 adds manufacturer filtering and pagination by page number.

#### Keyword + Manufacturer Search
```
POST /api/v2/search/keywordandmanufacturer?apiKey=<key>
```
```json
{
  "SearchByKeywordMfrNameRequest": {
    "keyword": "LMR51450",
    "manufacturerName": "Texas Instruments",
    "records": 25,
    "pageNumber": 1,
    "searchOptions": "InStock"
  }
}
```
Note: the wrapper object name is `SearchByKeywordMfrNameRequest` (not `SearchByKeywordMfrRequest` — the V1 name is deprecated).

#### Part Number + Manufacturer Search
```
POST /api/v2/search/partnumberandmanufacturer?apiKey=<key>
```

#### Manufacturer List
```
GET /api/v2/search/manufacturerlist?apiKey=<key>
```
Returns the full list of manufacturer names for use in filtered searches.

### V1 Deprecated Endpoints

These still work but V2 equivalents are preferred:
- `POST /api/v1/search/keywordandmanufacturer` → use V2
- `POST /api/v1/search/partnumberandmanufacturer` → use V2
- `GET /api/v1/search/manufacturerlist` → use V2

## Search Response Structure

All search endpoints return the same response format:

```json
{
  "Errors": [],
  "SearchResults": {
    "NumberOfResult": 142,
    "Parts": [...]
  }
}
```

### Key Part Fields

| Field | Type | Description |
|-------|------|-------------|
| `MouserPartNumber` | string | Mouser's internal part number (prefixed, e.g., `81-GRM155R71C104KA88`) |
| `ManufacturerPartNumber` | string | Manufacturer's part number (MPN) — use for cross-distributor matching |
| `Manufacturer` | string | Manufacturer name |
| `Description` | string | Product description |
| `Category` | string | Product category |
| `DataSheetUrl` | string | URL to datasheet PDF (Mouser-hosted — see Datasheet section) |
| `ProductDetailUrl` | string | URL to Mouser product page |
| `ImagePath` | string | Product image URL |
| `Availability` | string | Human-readable stock text (e.g., "2648712 In Stock") |
| `AvailabilityInStock` | string | Numeric stock quantity (as string) |
| `AvailabilityOnOrder` | array | Incoming stock: `[{Quantity, Date}]` |
| `LeadTime` | string | Factory lead time (e.g., "84 Days") |
| `LifecycleStatus` | string\|null | "New Product", "End of Life", etc. |
| `IsDiscontinued` | string | "true" or "false" (string, not boolean) |
| `SuggestedReplacement` | string | Replacement MPN if discontinued |
| `Min` | string | Minimum order quantity (as string) |
| `Mult` | string | Order multiple (as string) |
| `Reeling` | bool | Tape-and-reel packaging available |
| `ROHSStatus` | string | RoHS compliance status |
| `PriceBreaks` | array | Tiered pricing: `[{Quantity, Price, Currency}]` |
| `ProductAttributes` | array | Parametric specs: `[{AttributeName, AttributeValue}]` |
| `AlternatePackagings` | array\|null | Alternate packaging MPNs: `[{APMfrPN}]` |
| `SurchargeMessages` | array | Tariff/surcharge info: `[{code, message}]` |
| `ProductCompliance` | array | HTS codes, ECCN: `[{ComplianceName, ComplianceValue}]` |
| `UnitWeightKg` | object | `{UnitWeight: <float>}` in kg |

### Quirks and Gotchas

- **Price is a string** with currency symbol: `"$0.10"`, not a float. Parse it before comparing.
- **Stock is a string**: `AvailabilityInStock` returns `"2648712"` not `2648712`.
- **IsDiscontinued is a string**: `"true"` or `"false"`, not boolean.
- **Mouser part numbers have prefixes**: `81-GRM155R71C104KA88` — the prefix is Mouser-specific. Use `ManufacturerPartNumber` for cross-referencing.
- **V2 wrapper names differ from V1**: V2 uses `SearchByKeywordMfrNameRequest`, not `SearchByKeywordMfrRequest`.
- **Tariff info**: `SurchargeMessages` may contain US tariff percentages — useful for cost estimation.
- **On-order data**: `AvailabilityOnOrder` shows incoming stock quantities and expected dates.

## Datasheet Download & Sync

Mouser's `DataSheetUrl` field points to Mouser-hosted URLs (`mouser.com/datasheet/...`). These URLs **block automated downloads** — they return an HTML "Access denied" page when fetched with Python/curl/wget, even with browser User-Agent headers. The download scripts handle this with a multi-strategy approach:

1. Try the Mouser datasheet URL directly (works for some parts)
2. Scrape the Mouser product page HTML for alternative datasheet links
3. Try manufacturer-specific alternative URL patterns

Note: Mouser's product pages return 403 for most automated requests, so strategy 2 has limited success. DigiKey and LCSC are more reliable datasheet sources.

### Datasheet Directory Sync

Use `sync_datasheets_mouser.py` to maintain a `datasheets/` directory alongside a KiCad project. Same workflow and `manifest.json` format as the DigiKey skill.

```bash
# Sync datasheets for a KiCad project
python3 <skill-path>/scripts/sync_datasheets_mouser.py <file.kicad_sch>

# Preview what would be downloaded
python3 <skill-path>/scripts/sync_datasheets_mouser.py <file.kicad_sch> --dry-run

# Retry previously failed downloads
python3 <skill-path>/scripts/sync_datasheets_mouser.py <file.kicad_sch> --force

# Custom output directory
python3 <skill-path>/scripts/sync_datasheets_mouser.py <file.kicad_sch> -o ./my-datasheets

# Parallel downloads (3 workers)
python3 <skill-path>/scripts/sync_datasheets_mouser.py <file.kicad_sch> --parallel 3

# Batch mode — sync from a plain MPN list (no KiCad project required)
python3 <skill-path>/scripts/sync_datasheets_mouser.py --mpn-list mpns.txt --output ./datasheets
```

**MPN-list batch mode** (KH-312) — when you have a list of MPNs but no
KiCad project to point at (harness datasheet seeding, bulk part-library
seeding). One MPN per line; blank lines and `#` comments (full-line and
inline) are skipped; generic values (`100nF`, `DNP`) are filtered via
`is_real_mpn()` and de-duplicated. Output defaults to `./datasheets/` in
the current working directory when `--output` is omitted.

**Rate limiting** — the script paces API calls with a 1.0s delay between
requests by default (Mouser's Search API allows 30 calls/min on the free
tier; 1.0s stays comfortably under). Override with `--delay <seconds>` if
you have a higher-tier key or want to slow things down further.

### Single Datasheet Download

Use `fetch_datasheet_mouser.py` for one-off downloads.

```bash
# Search by MPN (uses Mouser API)
python3 <skill-path>/scripts/fetch_datasheet_mouser.py --search "TPS61023DRLR" -o datasheet.pdf

# Direct URL download
python3 <skill-path>/scripts/fetch_datasheet_mouser.py "https://example.com/datasheet.pdf" -o datasheet.pdf

# JSON output
python3 <skill-path>/scripts/fetch_datasheet_mouser.py --search "ADP1706" --json
```

### Download Strategy

The scripts try multiple sources in order:
1. **Schematic URL** — uses the datasheet URL embedded in the KiCad symbol (sync only)
2. **Mouser API search** — gets the `DataSheetUrl` from the API response
3. **Alternative manufacturer sources** — tries known URL patterns for major manufacturers (TI, Microchip, etc.) when the Mouser URL is blocked
4. **Headless browser fallback** — if `playwright` is installed, uses headless Chromium as a last resort

When all methods fail, provide the `ProductDetailUrl` to the user so they can download from the Mouser product page in their browser.

## Web Search Fallback

If no API key is available, search Mouser by fetching product pages directly:

- Search URL: `https://www.mouser.com/c/?q=<query>`
- Product pages contain full specs, pricing tiers, stock, datasheets
- Results from Mouser can be noisy (JS-heavy pages)

Include key parameters in the query:
- **Passives**: value, package (0402/0603/0805), tolerance, voltage/power rating, dielectric (C0G/X7R)
- **ICs**: part number or function, package (QFN/SOIC/TSSOP), key specs (voltage, current, interface)
- **Connectors**: type (USB-C, JST-PH), pin count, pitch, mounting (SMD/THT), orientation

## Tips

- Pipe-separate up to 10 part numbers in a single PartNumber search for batch lookups
- `Min` and `Mult` fields matter — some parts have minimum order qty or must be ordered in multiples
- `SurchargeMessages` may include US tariff percentages — factor into cost estimates
- `AvailabilityOnOrder` shows incoming stock with expected dates
- Check `IsDiscontinued` and `LifecycleStatus` before selecting parts
