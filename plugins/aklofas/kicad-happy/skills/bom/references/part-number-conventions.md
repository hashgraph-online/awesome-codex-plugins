# Part Number Conventions in KiCad Projects

This reference documents how real-world KiCad projects track part numbers. The `bom_manager.py` script handles the most common patterns automatically, but many projects use unconventional approaches. When the script doesn't detect a project's convention, use this guide to understand what you're looking at and adapt.

## Table of Contents

1. [The Spectrum of Approaches](#the-spectrum-of-approaches)
2. [Symbol Property Patterns](#symbol-property-patterns)
3. [External File Patterns](#external-file-patterns)
4. [Detecting the Approach](#detecting-the-approach)
5. [Field Name Variants](#field-name-variants)
6. [Part Number Pattern Recognition](#part-number-pattern-recognition)
7. [Edge Cases and Gotchas](#edge-cases-and-gotchas)
8. [Working with Unknown Conventions](#working-with-unknown-conventions)

---

## The Spectrum of Approaches

Projects fall on a spectrum from "no tracking at all" to "full multi-distributor BOM in schematic properties":

### Level 0: No Part Numbers

The schematic has only Reference, Value, Footprint, and maybe Datasheet. No MPNs, no distributor PNs, no manufacturer info. Common in tutorials, student projects, hobby boards, and early-stage designs.

**What to do:** This is the cleanest starting point. Add fields from scratch using canonical names (`MPN`, `Manufacturer`, `DigiKey`, etc.). Use KiCad's Field Name Templates (KiCad 9+) to add them to all symbols at once, or use `edit_properties.py` to batch-add.

### Level 1: MPN Only

Symbols have a manufacturer part number field (under any of a dozen possible names) but no distributor-specific fields. The MPN is the universal cross-reference key — search any distributor with it.

### Level 2: Single Distributor

One distributor's part numbers are tracked alongside (or instead of) MPNs. Often DigiKey or LCSC, depending on whether the project is prototype-focused or production-focused.

### Level 3: Multi-Distributor

Multiple distributor fields populated. Rare in open-source projects (only ~5% of projects examined). Usually production-ready commercial designs.

### Level 4: External BOM File

Part tracking happens outside the schematic entirely — in a CSV, spreadsheet, text file, or BOM management tool. The schematic may have no custom fields at all, or may have a "Key" or "ID" field that cross-references to the external file.

### Level 5: Hybrid

Some parts tracked in symbol properties, others in external files. Or different revisions use different approaches. Or the project migrated conventions partway through.

---

## Symbol Property Patterns

### Pattern A: Direct Named Fields (most common)

Each distributor gets its own property field on every symbol.

```
(property "MPN" "GRM155R71C104KA88D" ...)
(property "DigiKey" "490-10698-1-ND" ...)
(property "Mouser" "81-GRM155R71C104KA8D" ...)
(property "LCSC" "C14663" ...)
```

The `bom_manager.py` script handles this pattern and recognizes 50+ field name variants.

### Pattern B: Supplier Slot Fields

Generic numbered supplier slots where the supplier name is in one field and the PN in another.

```
(property "Supplier 1" "Digikey" ...)
(property "Supplier 1 Part #" "490-10698-1-ND" ...)
(property "Supplier 1 Link" "https://www.digikey.com/..." ...)
(property "Supplier 2" "Mouser" ...)
(property "Supplier 2 Part #" "81-GRM155R71C104KA8D" ...)
```

Used by some projects and KiCad BOM export templates. The `bom_manager.py` script detects this pattern by reading the supplier name value and mapping it to a canonical distributor.

Variants: `Vendor` / `Vendor Part Number`, `Source` / `Source Part Number`, `Distributor 1` / `Distributor 1 PN`.

### Pattern C: Internal Key System

A project-internal identifier (slug, database ID, or custom code) instead of or alongside MPNs.

```
(property "Key" "cap-cer-0402-100n" ...)
(property "UST_ID" "UST-CAP-0042" ...)
(property "PartID" "P00123" ...)
```

Some projects use `Key` fields with slugs like `ic-cy7c68013a-56`, or custom IDs like `UST_ID`. These IDs cross-reference to an external database or spreadsheet, not to a distributor.

**What to do:** The internal key is NOT an MPN. Look for a separate MPN field (might be named `MFN`, `MFPN`, `Part Number`, etc.). If there's no MPN, the internal key might be the only identifier — ask the user how they want to proceed.

### Pattern D: Parametric Properties

Component specifications stored as individual fields rather than relying on the Value field alone.

```
(property "Value" "100n" ...)
(property "Tolerance" "10%" ...)
(property "Voltage" "16V" ...)
(property "TempCoef" "X7R" ...)
(property "Power" "0.1W" ...)
(property "Package" "0402" ...)
```

These are parametric search criteria, not part numbers. Useful for finding the right part when no MPN exists.

**What to do:** Use these parametric values to build a search query (e.g., "100nF 0402 X7R 16V ceramic capacitor") and search distributor APIs by keyword. Don't confuse parametric fields with part number fields.

### Pattern E: EasyEDA/LCSC Catalog Dump

Full LCSC catalog metadata embedded from EasyEDA imports, including stock counts, pricing, process type, and category.

```
(property "LCSC" "C14663" ...)
(property "Part" "100nF ±10% 16V X7R 0402 MLCC" ...)
(property "Category" "Capacitors,Multilayer Ceramic Capacitors MLCC - SMD/SMT" ...)
(property "Stock" "2648712" ...)
(property "Price" "0.0017" ...)
(property "Class" "Basic Component" ...)
```

Stock and price values are stale the moment they're saved. Don't use them for ordering decisions — always query current data from the distributor API.

### Pattern F: SnapEDA/SamacSys Import Fields

Symbols downloaded from SnapEDA or SamacSys inject a distinctive set of metadata fields.

```
(property "Manufacturer_Part_Number" "TPS61023DRLR" ...)
(property "Manufacturer_Name" "Texas Instruments" ...)
(property "Mouser Part Number" "595-TPS63020DSJR" ...)
(property "Mouser Price/Stock" "https://www.mouser.com/..." ...)
(property "STANDARD" "IPC 7351B" ...)
(property "PARTREV" "1.0" ...)
(property "MAXIMUM_PACKAGE_HEIGHT" "1.45mm" ...)
```

These often coexist with the project's own field naming convention, creating inconsistency. `Manufacturer_Part_Number` (SnapEDA) might be on some symbols while `MPN` (project convention) is on others.

**What to do:** Recognize both naming conventions. When writing new fields, use whichever convention the project uses more consistently. If the project has both, prefer the simpler/more canonical name.

### Pattern G: Description-as-MPN

Some projects (especially for commodity passives) put what looks like a part number in the Value or Description field, not in a dedicated MPN field.

```
(property "Value" "EEEFK1V470P" ...)     # This is actually an MPN
(property "Value" "RC0805FR-071ML" ...)   # This too
(property "Value" "100n" ...)             # This is a value, not an MPN
```

**What to do:** If a Value field contains something that looks like an MPN (alphanumeric with manufacturer-specific patterns, not a simple value like "100n" or "10K"), it might be the MPN. Check by searching a distributor. But don't change it — the Value field is displayed on the schematic, so the user chose to show the MPN there deliberately.

---

## External File Patterns

Not all projects track BOM data in schematic properties. Some use external files.

### CSV/TSV BOM Files

A CSV or TSV with columns for reference designators, values, and part numbers.

```csv
Reference,Value,Footprint,MPN,DigiKey,Qty
"C1,C2,C5",100nF,0402,GRM155R71C104KA88D,490-10698-1-ND,3
R1,10K,0805,RC0805FR-0710KL,311-10.0KCRCT-ND,1
```

Common locations: `bom/`, `docs/`, `exports/`, project root. File names: `bom.csv`, `BOM.csv`, `parts.csv`, `partlist.csv`, `<project>_bom.csv`.

**What to do:** Read the CSV, match reference designators to schematic symbols, and optionally write the data back into symbol properties using `edit_properties.py`. Ask the user which direction they want the data to flow.

### Spreadsheet BOM (XLS/XLSX/ODS)

Same as CSV but in a spreadsheet format. May have multiple sheets (e.g., one per board revision, or separate sheets for different distributors).

**What to do:** Use Python (`openpyxl` for xlsx, `xlrd` for xls) to read the spreadsheet. The structure varies too much to automate — look at the column headers and ask the user to confirm the mapping.

### KiCad Symbol Fields CSV (Edit Symbol Fields export)

KiCad can export all symbol fields to CSV via Tools > Edit Symbol Fields > Export. This CSV has one row per symbol instance with all properties as columns.

```csv
Reference,Value,Footprint,Datasheet,MPN,DigiKey,...
C1,100nF,Capacitor_SMD:C_0402_1005Metric,~,GRM155R71C104KA88D,490-10698-1-ND,...
```

This is a round-trip format — the user can export, edit in a spreadsheet, and re-import. If you find one of these CSVs, it represents the definitive BOM state at the time of export.

### KiCad BOM Export Plugins

KiCad has BOM export plugins (Tools > Generate Bill of Materials) that produce various formats. Common outputs:

- `<project>_bom.xml` — KiCad's native XML BOM format
- `<project>_bom.csv` — CSV from built-in or third-party BOM plugin
- `ibom.html` — Interactive HTML BOM (visual, not for editing)

These are generated outputs, not source-of-truth files. Don't edit them — edit the schematic properties instead and regenerate.

### Plain Text / Markdown Notes

Some projects keep freeform notes about parts in README, docs, or text files.

```
## Parts List
- U1: ESP32-S3-WROOM-1-N4 (DigiKey: 1965-ESP32-S3-WROOM-1-N4CT-ND)
- All 0402 caps: Murata GRM series, LCSC C14663 or equivalent
- Connectors from Samtec, order via Samtec.com directly
```

**What to do:** Extract the part numbers and offer to add them to the schematic properties for proper tracking. This is often a sign the project started without BOM management and the user added notes ad-hoc.

---

## Detecting the Approach

When encountering a new project, check in this order:

1. **Run `bom_manager.py`** — it will detect most symbol property patterns automatically
2. **Check for unrecognized fields** — the JSON output includes `unrecognized_fields` with values that look like part numbers in unknown field names
3. **Look for external BOM files:**
   ```
   *.csv, *.tsv, *.xlsx, *.xls, *.ods in the project directory
   bom/, docs/, exports/ subdirectories
   README or docs mentioning parts/sourcing
   ```
4. **Read a few symbols manually** — if the script shows no custom fields, read 3-5 symbols from the .kicad_sch to see if there are fields the script didn't recognize
5. **Ask the user** — "I see your project doesn't have part numbers in the schematic properties. Do you track them somewhere else, or would you like to start adding them?"

---

## Field Name Variants

Comprehensive list of every field name variant observed across 56 open-source KiCad projects, grouped by canonical name. `bom_manager.py` reads every name below except those marked *not read*.

### MPN (Manufacturer Part Number)

| Field Name | Notes |
|---|---|
| `MPN` | Most common, canonical name |
| `PartNumber` | Common in older projects |
| `Part Number` | Space-separated variant |
| `Manufacturer_Part_Number` | SnapEDA imports |
| `Manufacturer Part Number` | Verbose variant |
| `Manufacturer Part #` | Hash-suffixed variant |
| `Manf#` / `manf#` | Older KiCad convention |
| `Mfr No.` | Abbreviated variant |
| `MFN` | Rare abbreviation |
| `MFPN` | Rare abbreviation |
| `Partno` | Rare variant |
| `PN` | *Not read* (ambiguous; see note below) |
| `MP` | SnapEDA imports |
| `Mfg Part` / `MfgPart` | Various |

**Note:** `PN` is ambiguous — it could be MPN or a distributor PN. If a project uses `PN` alongside a separate `Manufacturer` field, it's likely an MPN. If used alone, check the values.

### Manufacturer

| Field Name | Notes |
|---|---|
| `Manufacturer` | Most common |
| `Manufacturer_Name` | SnapEDA imports |
| `MF` | Abbreviated |
| `MFR` | Abbreviated |
| `Mfr` | Abbreviated |
| `Mfg` | Abbreviated |

### DigiKey

| Field Name | Notes |
|---|---|
| `DigiKey` | Common short form |
| `Digi-Key Part Number` | Verbose variant |
| `Digi-Key_PN` | Underscore variant |
| `Digi-Key PN` | Space variant |
| `DigiKey_Part_Number` | Underscore verbose |
| `Digikey Part Number` | No hyphen variant |
| `DK` | Short abbreviation |
| `Vendor Part Number` | *Not read*; only `Supplier N` slots are read (next row) |
| `Supplier 1 Part #` | When `Supplier 1` = "Digikey" (slot pattern) |

### Mouser

| Field Name | Notes |
|---|---|
| `Mouser` | Common short form |
| `Mouser Part Number` | Verbose variant |
| `Mouser Part` | Space variant |
| `Mouser_PN` | Underscore variant |

### LCSC / JLCPCB

| Field Name | Notes |
|---|---|
| `LCSC` | Most common |
| `LCSCStockCode` | Rare variant |
| `LCSC Part #` | Hash-suffixed |
| `LCSC Part Number` | Verbose variant |
| `LCSC_PN` | Underscore variant |
| `LCSC PN` | Space variant |
| `JLCPCB` | Common for JLCPCB assembly |
| `JLCPCB Part` | Verbose variant |
| `JLC` | Short abbreviation |

### Newark / Farnell / element14

| Field Name | Notes |
|---|---|
| `Newark` | Newark (US) |
| `Farnell` | Farnell (UK/EU) |
| `element14` | element14 (APAC) |
| Various `_PN` / `Part Number` suffixed variants | Same pattern as other distributors |

### Other Distributors

Listed for reference; `bom_manager.py` does not read these fields.

| Field Name | Notes |
|---|---|
| `TME` | Transfer Multisort Elektronik (European) |
| `Adafruit PN` | Adafruit |
| `Arrow` | Arrow Electronics (rare) |

### DNP (Do Not Populate)

| Field Name | Meaning |
|---|---|
| `DNP` | KiCad 7+ built-in attribute |
| `(dnp yes)` | KiCad 7+ S-expression flag |
| `DONOTPLACE` | Boolean "TRUE" |
| `DNM` | Do Not Mount |
| `POPULATE` | "0" / "no" / "false" / "DNP" = DNP, "1" / "yes" / "true" / empty = populate |
| `Do Not Populate` | Verbose variant |

---

## Part Number Pattern Recognition

When a value is found in an ambiguous field (like `PN` or `Part Number`), these patterns help classify it:

| Pattern | Likely Distributor | Examples |
|---|---|---|
| Ends with `-ND` | DigiKey | `490-10698-1-ND`, `296-TPS61023DRLRCT-ND` |
| `C` + 3-8 digits | LCSC | `C14663`, `C2913202` |
| 2-3 digits + `-` + alphanum | Mouser | `81-GRM155R71C104KA8D`, `595-TPS63020DSJR` |
| Alphanumeric 8+ chars, no hyphens | Often MPN | `GRM155R71C104KA88D`, `TPS61023DRLR` |
| URL | Not a PN — datasheet or product link | `https://www.digikey.com/...` |
| Simple value (digits + unit) | Not a PN — component value | `100nF`, `10K`, `4.7uH` |
| Slug with hyphens | Internal key | `cap-cer-0402-100n`, `ic-stm32f407` |

These are heuristics, not guarantees. A Mouser-pattern string could be an MPN. Always verify by searching the distributor.

---

## Edge Cases and Gotchas

### Typos in Field Names

Real projects contain typos: `Manufactuer`, `MAXIMUM_PACKAGE_HIEGHT`, `LCSC Parrt #`. When you see a field name that's close to a known alias but not an exact match, it's probably a typo. Search by the value to verify, and consider mentioning the typo to the user.

### Multiple Fields for the Same Thing

Some projects have both `LCSC` and `LCSC Part #` on different symbols, or both `Digi-Key_PN` and `DigiKey` from different symbol sources. The `bom_manager.py` picks the most common variant, but individual symbols might use the other. Always check both when extracting values.

### Empty Fields as Placeholders

Projects using KiCad's Field Name Templates often have empty fields on every symbol (the template added them but the user hasn't filled them in yet). This is different from a field not existing at all — it means the project intends to use that distributor but hasn't populated it yet.

### Fields with Unexpected Content

- `Digi-Key Part Number` containing "LCSC" as a value — meaning "source this from LCSC instead"
- `LCSC link` containing full URLs instead of LCSC codes
- `Mouser Price/Stock` containing a Mouser URL, not a price
- `Source` = "ANY" meaning any distributor is acceptable
- `Alt MPN` or `Substitution` containing alternative parts, not the primary MPN
- `Notes` containing distributor info in free text: "Digikey: USB4105-GF-A"
- `Remarks` containing color info, mating connector references, or errata
- `BOM Comments` / `Notes` / `Remarks` containing ordering/assembly quirks: "Proto only", "shares cable with board X", "hand-solder", "order 10% extra", variant-specific population rules
- `Assembly` or `Assembly Notes` containing post-reflow instructions or orientation notes
- `Variant` / `Config` / `SKU` containing conditional population rules for multi-variant designs

### Multi-Unit Symbols

A dual op-amp (e.g., LM358) has one reference (U1) but two units (U1A, U1B). In KiCad, both units share the same symbol properties. Editing U1's properties affects both units. The `edit_properties.py` script handles this by finding all symbol blocks with the same reference.

### Hierarchical Schematics

Properties are on the symbol instances in each sheet, not on the sheet reference. When a project uses hierarchical design (root + sub-sheets), `bom_manager.py --recursive` finds all symbols across all sheets, with each sheet instance's own reference (a sheet used twice lists both sets). The `edit_properties.py` script needs to be pointed at the specific `.kicad_sch` file containing the symbol to edit, and finds a symbol by the `Reference` property stored in that file, which for a repeated sheet is the reference of only one of its instances.

### KiCad 5 vs KiCad 6+ Format

KiCad 5 used `.sch` files (different text format). KiCad 6+ uses `.kicad_sch` (S-expression format). `bom_manager.py analyze` and `export` read KiCad 5 `.sch` projects (read only, through the schematic analyzer's legacy reader). `edit_properties.py` and `sync_datasheet_urls.py` write symbol properties and need `.kicad_sch`: open and save a KiCad 5 project in KiCad 6+ first (KiCad converts on open). The KiCad analyzer (`kicad` skill) reads both formats.

---

## Working with Unknown Conventions

When you encounter a project that doesn't match any known pattern:

1. **Don't assume** — read actual symbol properties from the file before deciding on an approach
2. **Look at all custom fields** — not just the ones you recognize. Unknown fields often contain valuable BOM data under project-specific names
3. **Check for external files** — CSV, spreadsheet, or text files in the project directory
4. **Ask the user** what convention they want to use going forward, especially if the current state is messy or inconsistent
5. **Match existing style** — if the project uses `Digi-Key_PN`, don't introduce `DigiKey` as a new field. Use whatever names already exist, even if they're not canonical
6. **MPN is non-negotiable** — regardless of what other fields exist, always ensure MPN is populated. It's the universal cross-reference key and should be present on every real component (not test points, mounting holes, or power symbols)
7. **Be conservative with edits** — don't "fix" field names to canonical unless the user asks. A project with `Manf#` on 200 symbols should keep using `Manf#`, not suddenly switch to `MPN` on the 201st
8. **Preserve what exists** — never delete or overwrite a user's existing data. If a field has a value, update it only if you have better data and the user agrees
