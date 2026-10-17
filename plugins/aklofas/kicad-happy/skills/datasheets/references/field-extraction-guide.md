# Field Extraction Guide

How to find each schema field in a typical datasheet PDF. Covers section naming conventions by vendor, what language to look for, and common mistakes.

The extraction workflow starts with `datasheet_page_selector.py` identifying the relevant pages (pin table, absolute maximum ratings, operating conditions, electrical characteristics, application circuit). This guide describes what to look for once you have those pages.

Use `null` for any field the datasheet does not specify. Do not guess or interpolate.

---

## Page Selection Overview

The page selector uses a three-strategy approach:

1. **TOC present** — scans the first 1–3 pages for section headings with page numbers. TOC references to "Pin Configuration", "Absolute Maximum Ratings", "Electrical Characteristics", and "Typical Application" are automatically resolved to target pages.
2. **No TOC** — scores every page by keyword density. Pages containing "absolute maximum", "pin configuration", "electrical characteristics", and "application circuit" score highest.
3. **No pdftotext** — returns pages 1–5 plus evenly distributed pages.

Default page budget: 10 pages (15 for microcontrollers, FPGAs, SoCs). Always includes page 1 and the last page.

---

## Vendor Section Naming

Different manufacturers use different section titles for the same content. Recognizing these saves time.

### Texas Instruments (TI)

| Content | Typical Section |
|---------|----------------|
| Pin table | §6 "Pin Configuration and Functions" or §7 |
| Absolute maximum ratings | §7.1 "Absolute Maximum Ratings" |
| Operating conditions | §7.2 "ESD Ratings" / §7.3 "Recommended Operating Conditions" |
| Electrical characteristics | §7.4 or §7.5 "Electrical Characteristics" |
| Application circuit | §9 "Application and Implementation" → §9.1 "Typical Application" |

### STMicroelectronics (ST)

| Content | Typical Section |
|---------|----------------|
| Pin table | §4 "Pinouts" or "Pin definition" |
| Absolute maximum ratings | §5 or §6 "Absolute maximum ratings" |
| Operating conditions | Embedded in electrical characteristics table |
| Electrical characteristics | §6 or §7 "Electrical characteristics" |
| Application circuit | "Application schematics" or "Reference circuit" (late in doc) |

### NXP / Freescale

| Content | Typical Section |
|---------|----------------|
| Pin table | §7 "Pinning information" |
| Absolute maximum ratings | §11 "Limiting values" or "Absolute maximum ratings" |
| Operating conditions | §12 "Recommended operating conditions" or "Characteristics" |
| Electrical characteristics | §12 "Characteristics" |
| Application circuit | "Application diagram" or "Typical application circuit" |

### Microchip / Atmel

| Content | Typical Section |
|---------|----------------|
| Pin table | "Pin Diagrams" + "Pin Description" (separate pages) |
| Absolute maximum ratings | "Absolute Maximum Ratings*" (with footnote) |
| Operating conditions | Embedded in DC characteristics tables |
| Electrical characteristics | "DC Characteristics" / "AC Characteristics" |
| Application circuit | "Typical Application Circuit" or "Demo Board Schematic" |

### Espressif

| Content | Typical Section |
|---------|----------------|
| Pin table | Pin description tables in early sections (often §2 or §3) |
| Absolute maximum ratings | "Absolute Maximum Ratings" — often a brief table |
| Operating conditions | "Recommended Operating Conditions" |
| Electrical characteristics | Peripheral-specific tables scattered through the document |
| Application circuit | "Typical Application Schematic" or hardware design guidelines doc |

Note: Espressif often separates the datasheet (pin specs, electrical) from a hardware design guidelines document (application circuit, decoupling). If the PDF is the datasheet only, the application circuit section may be minimal.

### Analog Devices / Maxim

| Content | Typical Section |
|---------|----------------|
| Pin table | "PIN CONFIGURATION" + "PIN DESCRIPTION" (often on page 2) |
| Absolute maximum ratings | "ABSOLUTE MAXIMUM RATINGS" (all caps, early in doc) |
| Operating conditions | Part of main specifications table |
| Electrical characteristics | "ELECTRICAL CHARACTERISTICS" or "DC Specifications" |
| Application circuit | "Typical Application Circuit" or "Applications Information" |

---

## Field-by-Field Guidance

### `mpn`

Use the exact part number from the datasheet's title or ordering information page, including the package and temperature suffix (e.g., `TPS61023DRLR`, not `TPS61023`). Omit marketing names or family names.

### `manufacturer`

Use the company name as it appears on the datasheet header. For acquisitions (e.g., Maxim by Analog Devices, Linear Technology by Analog Devices), use the name on the datasheet being read, not the current parent company.

### `category`

Match to the category list in extraction-schema.md. The category determines which scoring rules apply. If the part spans categories (e.g., a PMIC with multiple regulators), use the primary function.

### `package`

Format: `"<package_name> (<pin_count>-pin)"`. Examples: `"TSSOP-14 (14-pin)"`, `"SOT-23-6 (6-pin)"`, `"QFN-32 (32-pin, 5x5mm)"`. The pin count is used to validate coverage in the scorer. Found in the ordering information or package outline section.

### `pins[].number`

Copy exactly as printed in the pin description table: `"1"`, `"2"`, `"A1"`, `"EP"` (exposed pad). Do not renumber or convert to integers.

### `pins[].name`

Copy from the pin name column. When the datasheet shows alternative names (e.g., `SW/VOUT`), use the primary name for the operating mode you're documenting.

### `pins[].type`

Map from the datasheet's function column:

| Datasheet language | Schema type |
|-------------------|-------------|
| VDD, VCC, VIN, VSUPPLY | `power` |
| GND, AGND, PGND, VSS | `ground` |
| FB, COMP, VREF, VSET (analog) | `analog` |
| EN, SCL, SDA, TX, RX, CS, INT, ALERT | `digital` |
| NC, No Connect | `no_connect` |
| SDA/SCL (bidirectional bus), IO | `bidirectional` |

### `pins[].voltage_abs_max`

Found in the pin description table (individual pin limits) or the absolute maximum ratings table. Individual pin limits take precedence over the global abs max. Common traps:

- **SW pin on switching regulators**: often has a lower abs max than VIN (e.g., VIN = 6V, SW = 6V, but separate footnote limits SW to 5.6V during startup)
- **ESD clamp pins**: may have a negative lower limit (e.g., `-0.3V to 6V`) — store only the upper limit in this field
- **I/O pins on MCUs**: often have a separate `VDDIO` limit distinct from the main supply

### `pins[].threshold_high_v` / `pins[].threshold_low_v`

Look in the electrical characteristics table under "Logic Input Threshold" or similar. Common naming:

- `V_IH`, `VIH`, `V_IL`, `VIL` — standard logic threshold names
- `V_EN(H)`, `V_EN(L)` — enable pin thresholds (device-specific naming)
- `V_IN(H)`, `V_IN(L)` — input pin thresholds

Trap: Do not confuse `V_IH` (recommended minimum high input) with `V_OL`/`V_OH` (output levels). The extraction wants input thresholds — what the pin recognizes as logic high or low.

Trap: Some datasheets list thresholds as fractions of VDD (e.g., "0.7 × VDD"). Record the fraction notation in the description, and store the absolute value calculated at the nominal operating voltage in the field.

### `pins[].required_external`

This is the most important field for design review automation. Sources:

1. Pin description "External components required" columns
2. Application circuit notes referencing specific pins
3. Recommended operating conditions footnotes (e.g., "Bypass VIN to GND with 100nF")
4. Absolute maximum ratings notes (e.g., "Place clamp diode on boot pin for inductive loads")

Write in the datasheet's own language when possible. Include values and placement constraints where specified.

---

### `absolute_maximum_ratings`

Found in the "Absolute Maximum Ratings" table, usually near the front of the datasheet. Key naming conventions:

| Datasheet label | Suggested key | Unit |
|----------------|---------------|------|
| VIN(max), Input Voltage | `vin_max_v` | V |
| VOUT(max), Output Voltage | `vout_max_v` | V |
| TJ(max), Junction Temperature | `junction_temp_max_c` | °C |
| TSTG, Storage Temperature | `storage_temp_min_c`, `storage_temp_max_c` | °C |
| ESD (HBM) | `esd_hbm_v` | V |
| ESD (CDM) | `esd_cdm_v` | V |

Trap: **Absolute maximum ratings are not operating conditions**. Exposing a pin to its abs max continuously will shorten device lifetime. Do not use abs max values as operating targets.

Trap: Some datasheets list separate abs max for each pin in the pin description table. Capture those in `pins[].voltage_abs_max`, not here. The top-level absolute_maximum_ratings covers supply voltage and temperature.

---

### `recommended_operating_conditions`

Found in the "Recommended Operating Conditions" or "Operating Conditions" table. This is the range where the device is guaranteed to perform per the electrical characteristics.

Key traps:

- **VIN vs VOUT vs VDD**: multi-rail devices may have separate operating ranges for each supply. Use the most restrictive or the primary input.
- **Temperature grades**: datasheets may show industrial (−40 to +85°C) and commercial (0 to +70°C) variants in the same table. Extract for the grade you are using.
- **"Conditions" column**: some electrical characteristics tables embed operating conditions as conditions on specific rows. These are test conditions for that row, not the device operating range.

---

### `electrical_characteristics.*`

Found in the "Electrical Characteristics" table. This table is usually organized with columns: Parameter, Min, Typ, Max, Unit, Test Conditions.

Which value to record:

- Use **Typ** for `vref_v`, `switching_frequency_khz` (nominal specs)
- Use **Max** for threshold voltages, quiescent current limits, propagation delay
- Use **Min** for `dropout_mv` (worst case is what matters for design margin)
- Use **Typ** for SPICE model parameters (behavioral accuracy)

Key field lookup:

| Field | What to find in the table |
|-------|--------------------------|
| `vref_v` | Reference voltage or feedback threshold; labeled "VREF", "VFB", "Feedback Voltage" |
| `switching_frequency_khz` | "Oscillator frequency", "Switching frequency", "fSW" |
| `quiescent_current_ua` | "IQ", "IDD (quiescent)", "Supply current (no load)" — exclude gate drive and switching losses |
| `dropout_mv` | "Dropout voltage" at rated output current; labeled "VDO", "VIN-VOUT" |
| `gbw_hz` | "Gain Bandwidth Product", "GBW", "Unity gain frequency" |
| `slew_vus` | "Slew rate", "SR" — use the slower of rising/falling |
| `prop_delay_ns` | "Propagation delay", "tPD" — use the worst case across all measurement conditions |
| `clamping_voltage_v` | "VC", "Clamping voltage" at the specified IEC 61000-4-2 test current |

Trap: **Gain Bandwidth vs Unity Gain Bandwidth**. Some datasheets list both. Use the unity-gain stable bandwidth for `gbw_hz`.

Trap: **Quiescent vs active supply current**. Record the quiescent (no-load, static) current, not the active switching current, unless the datasheet doesn't distinguish.

---

### `application_circuit.*`

Found in the typical application circuit section. This section often spans multiple pages with a reference schematic, a component table, and layout notes.

**topology**: Look for how the circuit is described in the section title or opening sentence: "boost converter", "buck converter", "buck-boost", "flyback", "SEPIC", "inverting buck-boost", "LDO". Use lowercase.

**inductor_recommended**: Usually in a "Inductor Selection" subsection or a component table. Capture value, saturation current requirement, and DCR guidance if given.

**input_cap_recommended / output_cap_recommended**: Labeled in the component table or application notes. Common format: `"10µF, X5R or X7R, 10V rating"`. Include dielectric and voltage rating if specified.

**vout_formula**: Look for a formula in the "Setting the Output Voltage" or "Programming Output Voltage" section. Record the exact formula; do not simplify.

**notes**: Capture layout-critical guidance: copper pour requirements, trace width recommendations, component placement distance constraints, feedback routing warnings.

Trap: Some datasheets have minimal application sections and instead reference an application note (SLVA XXXX, AN1234, etc.). If the datasheet itself has no circuit recommendations, set `application_circuit` to null and note the reference in `extraction_metadata`.

---

### `spice_specs.*`

SPICE specs come from the same electrical characteristics table as `electrical_characteristics`. The difference is that `spice_specs` uses the exact key names from `spice_part_library.py` for direct model generation.

For opamps: `gbw_hz`, `slew_vus`, `vos_mv`, `aol_db`, `rin_ohms` come from the electrical characteristics table. `supply_min`/`supply_max` come from recommended operating conditions. `rro`/`rri` come from the features list or the output swing specification (if the output swings within a few mV of the rail, `rro = true`).

For regulators: `vref` comes from the reference voltage spec. `dropout_mv` from the dropout table. `iq_ua` from quiescent current. `iout_max_ma` from the maximum output current rating.

---

## Common Mistakes

**Mixing abs max with operating conditions.** The schematic verifier compares pin voltages against `voltage_abs_max`; an incorrectly low value will generate false positives.

**Using the wrong table row.** Electrical characteristics tables often have multiple rows for the same parameter under different test conditions (temperature range, load current, VIN). Pick the row matching typical operation, not the extreme test condition.

**Leaving required fields null when the datasheet has them.** If the pin table has a voltage limit column, populate `voltage_abs_max` for every pin — not just the ones that look interesting. The scorer deducts points for name-only pins.

**Truncating the MPN.** `TPS61023` and `TPS61023DRLR` may have different specs (package parasitics, temperature grade). Extract from the correct datasheet and record the full part number.

**Copying from a different variant's table.** Datasheets often cover a family. Check that the table row applies to the specific part number you are extracting.
