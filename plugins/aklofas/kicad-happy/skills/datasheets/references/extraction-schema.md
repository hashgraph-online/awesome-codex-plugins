# Extraction Schema Reference

Canonical schema for structured datasheet extraction JSON files stored in `datasheets/extracted/`. The extraction itself is performed by the LLM reading selected PDF pages; this document defines what fields the LLM must produce and how the cache manager and verifier interpret them.

Current `EXTRACTION_VERSION`: **2** (in `datasheet_extract_cache.py`). Bump this constant when the schema changes to trigger re-extraction of all cached files.

---

## Top-Level Structure

```json
{
  "mpn": "TPS61023DRLR",
  "manufacturer": "Texas Instruments",
  "category": "switching_regulator",
  "package": "SOT-23-6 (6-pin)",
  "description": "1A, 5V, 1.2MHz boost converter with 0.5V input",
  "topology": "boost",
  "pins": [...],
  "features": {...},
  "peripherals": {...},
  "absolute_maximum_ratings": {...},
  "recommended_operating_conditions": {...},
  "electrical_characteristics": {...},
  "application_circuit": {...},
  "spice_specs": {...},
  "extraction_metadata": {...}
}
```

### Top-Level Fields

| Field | Type | Nullable | Description | Added in v2 |
|-------|------|----------|-------------|-------------|
| `mpn` | string | no | Manufacturer part number, exact including suffix | — |
| `manufacturer` | string | no | Manufacturer name | — |
| `category` | string | no | Component category (see category list below) | — |
| `package` | string | yes | Package name and pin count, e.g. `"SOT-23-6 (6-pin)"` | — |
| `description` | string | yes | One-line description from datasheet | — |
| `topology` | string | yes | Circuit topology: `'boost'`, `'buck'`, `'ldo'`, `'mcu'`, `'sensor'`, `'adc'`, `'mosfet'`, `'bjt'`, `'other'` | yes |
| `pins` | array | no | Per-pin specifications (may be empty if pin table not found) | — |
| `features` | object | yes | Device-specific feature flags (has_pg, has_soft_start, etc.) | yes |
| `peripherals` | object | yes | Peripheral specifications for MCUs (usb, etc.) | yes |
| `absolute_maximum_ratings` | object | yes | Absolute limits; null if section not found | — |
| `recommended_operating_conditions` | object | yes | Operating ranges; null if section not found | — |
| `electrical_characteristics` | object | yes | Category-dependent key specs | — |
| `application_circuit` | object | yes | Reference design and component recommendations | — |
| `spice_specs` | object | yes | SPICE behavioral model parameters | — |
| `extraction_metadata` | object | no | Cache bookkeeping (source PDF, score, version) | — |

---

## Category Values

Use these exact strings — they match `_classify_ic_function()` in `analyze_schematic.py`.

| Category | Typical parts |
|----------|--------------|
| `microcontroller` | STM32, ESP32, ATmega, RP2040 |
| `operational_amplifier` | LM358, OPA340, AD8605 |
| `comparator` | LM393, TLV3501 |
| `linear_regulator` | AMS1117, LM1117, AP2112 |
| `switching_regulator` | TPS61023, LM2596, MP2307 |
| `voltage_reference` | REF3030, LM4040 |
| `esd_protection` | USBLC6-2SC6, PRTR5V0U2X |
| `adc` | ADS1115, MCP3008 |
| `dac` | MCP4725, DAC8552 |
| `interface` | MAX232, SN65HVD230, CP2102 |
| `memory` | AT24C256, W25Q128 |
| `sensor` | BME280, MPU6050 |
| `led_driver` | TLC5940, WS2812B |
| `motor_driver` | DRV8833, A4988 |
| `power_management` | BQ24074, TPS2113 |
| `fpga` | ICE40, XC7A |
| `rf` | CC1101, SX1276 |
| `audio` | MAX98357, PCM5102 |

---

## `pins[]`

Array of pin entries. The schematic verifier joins on `pin.number` (string) to the schematic's `pin_nets` map.

### Pin Entry Fields

| Field | Type | Unit | Nullable | Example | Description | Added in v2 |
|-------|------|------|----------|---------|-------------|-------------|
| `number` | string | — | no | `"1"`, `"A3"`, `"EP"` | Pin number as shown on datasheet | — |
| `name` | string | — | no | `"SW"` | Pin name from datasheet | — |
| `function` | string | — | yes | `"EN"` | Functional category; see values below | yes |
| `type` | string | — | no | `"power"` | Functional type (see values below) | — |
| `direction` | string | — | yes | `"bidirectional"` | Signal direction (see values below) | — |
| `description` | string | — | yes | `"Inductor switch node"` | Brief functional description | — |
| `voltage_abs_max` | float | V | yes | `6.0` | Absolute maximum voltage on this pin | — |
| `voltage_operating_min` | float | V | yes | `0.5` | Minimum recommended operating voltage | — |
| `voltage_operating_max` | float | V | yes | `5.5` | Maximum recommended operating voltage | — |
| `current_max_ma` | float | mA | yes | `3600` | Maximum current through this pin | — |
| `internal_connection` | string | — | yes | `"Power FET drain"` | What this pin connects to internally | — |
| `required_external` | string | — | yes | `"0.47-2.2uH inductor"` | What must be connected — primary field for pin audit | — |
| `threshold_high_v` | float | V | yes | `1.2` | Logic high threshold (digital input pins) | — |
| `threshold_low_v` | float | V | yes | `0.4` | Logic low threshold (digital input pins) | — |
| `has_internal_pullup` | bool | — | yes | `true` | Pin has internal pull-up resistor | — |
| `has_internal_pulldown` | bool | — | yes | `false` | Pin has internal pull-down resistor | — |

### `function` Values (v2)

Canonical pin functional categories, used by `get_pin_function()` in `datasheet_features.py`.

| Value | Description |
|-------|-------------|
| `'VIN'` | Input power supply pin |
| `'VOUT'` | Output voltage or regulated output |
| `'EN'` | Enable control input |
| `'PG'` | Power-good indicator output |
| `'SW'` | Switching node (regulators) |
| `'FB'` | Feedback input (regulators) |
| `'GND'` | Ground pin |
| `'IO'` | General-purpose I/O |
| `'CLK'` | Clock signal |
| `'RESET'` | Reset control |
| `'OTHER'` | Other function not in above list |
| `None` | Function not specified or unknown |

### `type` Values

| Value | Description |
|-------|-------------|
| `power` | Supply voltage input or output |
| `ground` | Ground connection |
| `analog` | Analog signal (feedback, sense, reference) |
| `digital` | Digital signal (logic I/O, enable, clock) |
| `no_connect` | NC pin — must not be connected |
| `bidirectional` | Can be input or output depending on configuration |

### `direction` Values

| Value | Description |
|-------|-------------|
| `input` | Signal flows into the device |
| `output` | Signal driven by the device |
| `bidirectional` | Both input and output |
| `passive` | No inherent direction (power, ground) |

### `required_external` Examples

This field is the primary driver for the missing-external-component check. Use the datasheet's own language where possible.

- `"Connect to inductor (0.47-2.2uH recommended)"`
- `"10K pull-up to VCC required"`
- `"Bypass cap 100nF to GND, place within 3mm"`
- `"Resistor divider from VOUT, Vout = 0.595 * (1 + R1/R2)"`
- `"Do not connect"` (NC pins)
- `"Connect to VIN for always-on, or logic control. Do not float."`

---

## `features` (v2)

Device-specific feature flags. This object is null if not applicable to the device category.

| Key | Type | Nullable | Description |
|-----|------|----------|-------------|
| `has_pg` | bool | yes | Part has a power-good output pin |
| `has_soft_start` | bool | yes | Device has integrated soft-start circuit |
| `iss_time_us` | float | yes | Soft-start time constant in microseconds |

---

## `peripherals` (v2)

Peripheral specifications for MCUs and similar devices. This object is null if not applicable.

### `peripherals.usb`

USB interface specifications. Null if device does not have USB.

| Key | Type | Nullable | Description |
|-----|------|----------|-------------|
| `speed` | string | yes | USB speed: `'FS'` (full-speed), `'HS'` (high-speed), `'SS'` (super-speed), or `None` |
| `native_phy` | bool | yes | Device has native USB PHY (vs external PHY required) |
| `series_r_required` | bool | yes | Series termination resistors required on D+/D- |

---

## `absolute_maximum_ratings`

Use keys with the suffix `_max_v`, `_max_c`, `_max_ma`, or `_v` as appropriate for the physical quantity. Null means the datasheet did not specify the limit.

| Key | Type | Unit | Example | Description |
|-----|------|------|---------|-------------|
| `vin_max_v` | float | V | `6.0` | Input voltage absolute maximum |
| `vout_max_v` | float | V | `6.0` | Output voltage absolute maximum |
| `io_voltage_max` | float | V | `4.0` | I/O pin voltage maximum (MCUs) |
| `junction_temp_max_c` | float | °C | `150` | Maximum junction temperature |
| `storage_temp_min_c` | float | °C | `-65` | Minimum storage temperature |
| `storage_temp_max_c` | float | °C | `150` | Maximum storage temperature |
| `esd_hbm_v` | float | V | `2000` | ESD rating, Human Body Model |
| `esd_cdm_v` | float | V | `500` | ESD rating, Charged Device Model |

Add device-specific keys as needed (e.g., `sw_pin_max_v`, `boot_voltage_max_v`). The scoring check looks for any key ending in `_max_v` to confirm voltage abs max is present.

---

## `recommended_operating_conditions`

| Key | Type | Unit | Example | Description |
|-----|------|------|---------|-------------|
| `vin_min_v` | float | V | `0.5` | Minimum input voltage |
| `vin_max_v` | float | V | `5.5` | Maximum input voltage |
| `vout_min_v` | float | V | `1.8` | Minimum output voltage |
| `vout_max_v` | float | V | `5.5` | Maximum output voltage |
| `temp_min_c` | float | °C | `-40` | Minimum operating temperature |
| `temp_max_c` | float | °C | `85` | Maximum operating temperature |

The scorer checks for `vin_min_v` + `vin_max_v` and `temp_min_c` + `temp_max_c`; missing either pair deducts from the voltage_ratings score.

---

## `electrical_characteristics`

Category-dependent. The scorer checks for category-specific required and optional fields.

### Switching regulators

| Key | Type | Unit | Scoring | Description |
|-----|------|------|---------|-------------|
| `vref_v` | float | V | required | Feedback reference voltage |
| `switching_frequency_khz` | float | kHz | required | Nominal switching frequency |
| `quiescent_current_ua` | float | µA | optional | Quiescent supply current |
| `output_current_max_ma` | float | mA | optional | Maximum output current |
| `vref_accuracy_pct` | float | % | optional | Reference voltage accuracy |
| `efficiency_pct` | float | % | optional | Peak efficiency |
| `shutdown_current_ua` | float | µA | optional | Shutdown/sleep supply current |

### Linear regulators

| Key | Type | Unit | Scoring | Description |
|-----|------|------|---------|-------------|
| `vref_v` | float | V | required | Reference / output voltage |
| `quiescent_current_ua` | float | µA | required | Quiescent supply current |
| `dropout_mv` | float | mV | optional | Dropout voltage at rated current |
| `output_current_max_ma` | float | mA | optional | Maximum output current |

### Operational amplifiers

| Key | Type | Unit | Scoring | Description |
|-----|------|------|---------|-------------|
| `gbw_hz` | float | Hz | required | Gain-bandwidth product |
| `slew_vus` | float | V/µs | required | Slew rate |
| `vos_mv` | float | mV | optional | Input offset voltage |
| `aol_db` | float | dB | optional | Open-loop gain |
| `rin_ohms` | float | Ω | optional | Input impedance |
| `cmrr_db` | float | dB | optional | Common-mode rejection ratio |

### Comparators

| Key | Type | Unit | Scoring | Description |
|-----|------|------|---------|-------------|
| `prop_delay_ns` | float | ns | required | Propagation delay |
| `vos_mv` | float | mV | optional | Input offset voltage |
| `aol_db` | float | dB | optional | Open-loop gain |

### Voltage references

| Key | Type | Unit | Scoring | Description |
|-----|------|------|---------|-------------|
| `vref_v` | float | V | required | Reference output voltage |
| `vref_accuracy_pct` | float | % | required | Initial accuracy |
| `temp_coefficient_ppmk` | float | ppm/°C | optional | Temperature coefficient |

### ESD protection

| Key | Type | Unit | Scoring | Description |
|-----|------|------|---------|-------------|
| `clamping_voltage_v` | float | V | required | Clamping voltage at rated surge current |
| `leakage_current_na` | float | nA | optional | Reverse leakage current |
| `capacitance_pf` | float | pF | optional | Line capacitance |

### Microcontrollers

No universally required fields (MCU characteristics vary too widely). Optional fields include `quiescent_current_ua` and `io_voltage_max`. Include whatever the datasheet provides.

---

## `application_circuit`

| Key | Type | Nullable | Example | Description |
|-----|------|----------|---------|-------------|
| `topology` | string | yes | `"boost"` | Circuit topology |
| `inductor_recommended` | string | yes | `"1uH, Isat > 3.6A"` | Recommended inductor |
| `input_cap_recommended` | string | yes | `"10uF ceramic, X5R or X7R"` | Input capacitor recommendation |
| `output_cap_recommended` | string | yes | `"22uF ceramic x2"` | Output capacitor recommendation |
| `feedback_resistor_top_ohm` | float | yes | `1000000` | Top feedback resistor value (Ω) |
| `feedback_resistor_bottom_ohm` | float | yes | `845000` | Bottom feedback resistor value (Ω) |
| `compensation_cap` | string | yes | `"22pF"` | Compensation capacitor |
| `bootstrap_cap` | string | yes | `"100nF"` | Bootstrap capacitor |
| `decoupling_cap` | string | yes | `"100nF per VDD pin"` | Decoupling recommendation |
| `vout_formula` | string | yes | `"Vout = 0.595 * (1 + R1/R2)"` | Output voltage formula |
| `notes` | array | yes | `["Place input cap close to IC", ...]` | Layout and application notes |

The scoring check counts fields matching `_recommended` or in the set `{inductor_recommended, input_cap_recommended, output_cap_recommended, feedback_resistor_top_ohm, feedback_resistor_bottom_ohm, compensation_cap, bootstrap_cap, decoupling_cap}`. Two or more populated fields scores full marks; zero scores 0.

Additional `_recommended`-suffixed keys are also counted. Add device-specific keys freely.

---

## `spice_specs`

Uses the same key names as `spice_part_library.py` to allow direct consumption by the SPICE model generator without field mapping.

| Key | Type | Unit | Nullable | Description |
|-----|------|------|----------|-------------|
| `gbw_hz` | float | Hz | yes | Gain-bandwidth product (opamps) |
| `slew_vus` | float | V/µs | yes | Slew rate (opamps) |
| `vos_mv` | float | mV | yes | Input offset voltage (opamps) |
| `aol_db` | float | dB | yes | Open-loop gain (opamps) |
| `rin_ohms` | float | Ω | yes | Input impedance (opamps) |
| `supply_min` | float | V | yes | Minimum supply voltage |
| `supply_max` | float | V | yes | Maximum supply voltage |
| `rro` | bool | — | yes | Rail-to-rail output |
| `rri` | bool | — | yes | Rail-to-rail input |
| `swing_v` | float | V | yes | Output swing from rail (non-RRO) |
| `dropout_mv` | float | mV | yes | Dropout voltage (LDOs) |
| `iq_ua` | float | µA | yes | Quiescent current |
| `iout_max_ma` | float | mA | yes | Maximum output current |
| `vref` | float | V | yes | Reference voltage |

Populate only the fields relevant to the component category. Null means the value was not found in the datasheet — do not guess.

---

## `extraction_metadata`

The extractor populates `source_pdf` and `extracted_from_pages`. The cache manager fills the remaining fields automatically.

| Key | Type | Nullable | Description |
|-----|------|----------|-------------|
| `source_pdf` | string | yes | Filename of the source PDF (relative to `datasheets/`) |
| `source_pdf_hash` | string | yes | `"sha256:<hex>"` — set by cache manager |
| `extracted_from_pages` | array | yes | Page numbers read during extraction |
| `total_pdf_pages` | int | yes | Total pages in the source PDF |
| `extraction_date` | string | no | ISO 8601 UTC timestamp — set by cache manager |
| `extraction_score` | float | no | Total score 0.0–10.0 — set after scoring |
| `score_breakdown` | object | yes | Per-dimension scores (see quality-scoring.md) |
| `extraction_version` | int | no | Schema version — set by cache manager (`EXTRACTION_VERSION`) |
| `retry_count` | int | no | How many extraction attempts have been made |

---

## Manifest File

`datasheets/extracted/manifest.json` (legacy name: `index.json`) tracks all cached extractions. The cache manager reads and writes this file; extraction code does not need to update it directly.

```json
{
  "version": 1,
  "last_updated": "2026-04-15T12:00:00+00:00",
  "extractions": {
    "TPS61023DRLR_a1b2c3": {
      "file": "TPS61023DRLR_a1b2c3.json",
      "mpn": "TPS61023DRLR",
      "category": "switching_regulator",
      "source_pdf": "TPS61023DRLR.pdf",
      "source_pdf_hash": "sha256:...",
      "extraction_date": "2026-04-15T12:00:00+00:00",
      "extraction_score": 9.1,
      "extraction_version": 1,
      "pin_count": 6
    }
  }
}
```

Index keys are MPN strings sanitized by `_sanitize_mpn()`: non-alphanumeric characters replaced with underscores, with a 6-character MD5 suffix appended to avoid collisions (e.g., `TPS61023DRLR_a1b2c3`). The suffix is derived from the raw MPN.

---

## Schema Versioning

`EXTRACTION_VERSION` is an integer in `datasheet_extract_cache.py`. When the schema changes in a backward-incompatible way, bump this constant. Helper functions in `datasheet_features.py` check the stored `extraction_version` against the current constant; any extraction with an older version is treated as unavailable.

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 2 | 2026-04-15 | Added `topology` (top-level), `features` object (has_pg, has_soft_start, iss_time_us), `peripherals.usb` object (speed, native_phy, series_r_required), `pins[].function` (canonical pin category) |
| 1 | (original) | Base schema with pins, electrical_characteristics, application_circuit, spice_specs, etc. |
