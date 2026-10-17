# Datasheet v2 Schemas — CHANGELOG

Per-schema semver-lite versioning. Rules:

- **Additive within minor.** Adding an optional field → minor bump (0.3 → 0.4, 1.0 → 1.1). Consumers tolerate missing optional fields. Cached extractions remain valid.
- **Breaking = major bump.** Renaming, removing, or type-changing an existing field → major bump (0.3 → 1.0, 1.0 → 2.0). Cached extractions for that section flagged stale; re-extraction required for consumers gated on `min_schema >= new_major`.
- **Stale one section ≠ stale whole MPN.** A base→2.0 bump doesn't invalidate the regulator extension's cached values.
- **Pinout is flagged `still-calibrating`** through v1.4. The shape may shift with real-corpus feedback before v1.5 commits to strict additive-only discipline.

---

## crystal.schema.json v1.0 — 2026-04-27

Initial release. Phase 3b (extraction breadth). Final Phase 3b category. Fields cover AT-cut quartz crystals, ceramic resonators, TCXO, VCXO, OCXO. Field union from a single MVP MPN — ABM8G-106-12.000MHZ-T (Abracon 12 MHz AT-cut fundamental SMD crystal, 3.2×2.5×1.0 mm) — per harness Stage 0 coordination.

Required: `crystal_type` (enum: `at_cut | ceramic_resonator | tcxo | vcxo | ocxo`). All other fields nullable. Smallest Phase 3b schema (12 properties); crystals have less parameter spread than active ICs.

`motional_capacitance` and `motional_inductance` are typically published only for AT-cut quartz; ceramic resonators / TCXO / VCXO / OCXO usually omit them. Schema supports null for both.

`aging` uses plain `"ppm"` unit (no new unit needed). The first-year time window goes in the `condition` field (e.g. `"Aging @ 25°C ±3°C, first year"`). This aligns with the harness sanity vector, which stores aging as `{min: -3, max: 3, unit: "ppm"}` with a first-year condition note.

`mode` enum is `fundamental | overtone_3rd | overtone_5th` plus null. Most consumer crystals are fundamental-mode; overtone modes are common in low-noise oscillator applications. Null for ceramic resonators, TCXO, VCXO, OCXO (the term is not meaningful for integrated oscillators).

`package.body_mm` follows the diode/transistor/opamp/mcu convention: nested `{length, width, height}` (no `_mm` suffix on inner keys).

**Phase 3b deferred to v1.5:** The original brainstorm planned 2 MVP MPNs per category for field-union; crystal shipped with only 1 because the harness sanity-vector list (12 MPNs) had no crystal at brainstorm time. v1.5 will add a second crystal extraction (TCXO or low-frequency 32.768 kHz watch crystal preferred) to validate field-union coverage.

**No spec_value.schema.json amendments required.** Aging stores in `"ppm"` with first-year condition. No new units needed.

`thermal_resistance` is intentionally absent — crystals rarely publish thermal resistance figures. v1.5 may add it if TCXO/OCXO datasheets prove otherwise.

**Pin-resolution:** crystals have no pin-reference fields; `_PIN_FIELDS_BY_CATEGORY["crystal"]` is the empty tuple (already set in Task 2).

---

## mcu.schema.json v1.0 — 2026-04-27

Initial release. Phase 3b (extraction breadth). Catalog-tier-only extraction: identity-level facts (core, memory, peripheral counts, package, supply, debug interface, reset pin, temperature grades). Per-peripheral instance and pin-mux detail is explicitly deferred to Tier 2 (`mcu_peripherals.schema.json`, v1.5). Field union from ATmega328P-AU (Atmel/Microchip 8-bit AVR, TQFP-32, 32K flash) + STM32F103C8T6 (ST Cortex-M3 32-bit, LQFP-48, 64K flash).

Required: `core_family` (open string, not enum — accommodates future cores). All other fields nullable or defaultable.

**Plain-integer memory and frequency fields** (NOT SpecValue lists — these specs have no min/typ/max spread worth capturing at catalog tier): `core_speed_max` (Hz), `flash_size` (bytes), `ram_size` (bytes), `eeprom_size` (bytes), `pin_count`, `gpio_count`, `nvic_priorities`. SpecValue lists used only for supply voltages with real min/max ranges: `vdd_range`, `vddio_range`, `vdda_range`. This avoids spec_value unit enum sprawl (`bytes` and `Hz` prefix variants not added).

**peripheral_counts** is a closed object with required-int properties (`uart`, `spi`, `i2c`, `can`, `usb`, `ethernet`, `dac`, `timer_general`, `timer_advanced`, all `minimum: 0`). Convention: **0 for absent peripherals** (not null). When `peripheral_counts.dac = 0`, also set top-level `dac: null`. The prompt's hard rules document this exclusion explicitly. Per-instance peripheral configuration is Tier 2.

**adc/dac** are closed summary objects (bit_depth, channel_count, sample_rate_max_hz) capturing the part-level ADC/DAC characteristics. Null when the part has no ADC/DAC. Not SpecValue fields — these are structural counts, not spread specs.

**nvic_priorities** is null for non-Cortex-M cores (AVR, PIC, 8051, classic RISC-V without NVIC). For Cortex-M3: 16 (4-bit priority field). Documented in field description and prompt hard rule.

**eeprom_size convention:** use `0` for parts with no EEPROM (STM32F103C8T6 → 0); use actual byte count for parts with EEPROM (ATmega328P → 1024); null only when not determinable.

**debug_interface** is an enum string: `swd | jtag | swd_jtag | debugwire | pdi | spi_isp | none | null`. Covers the major debug/programming interfaces across AVR (debugwire), XMEGA (pdi), Cortex-M (swd, jtag, swd_jtag), and older ISP parts.

**boot_pins** is an array of `{pin_number, function}` objects or an empty array (AVR uses fuses, not boot pins) or null.

`reset_pin` matches `base.pinout[*].numbers` when populated. Pin-resolution registered as `_PIN_FIELDS_BY_CATEGORY["mcu"] = ("reset_pin",)` (from Task 2, already in verify_v14_extraction).

**Inherited conventions from diode/transistor/opamp:**
- `thermal_resistance`: nested object with `rtheta_ja`/`rtheta_jc`/`rtheta_jl` nullable SpecValue lists (K/W or °C/W).
- `package.body_mm`: nested `{length, width, height}` (no `_mm` suffix on inner fields; aligns with base.schema.json's pre-existing body_mm shape).

**No new spec_value.schema.json unit additions required.** Flash/RAM/EEPROM are plain integers; frequencies are plain integers; voltages use existing `"V"` unit. All 18 existing unit tokens remain unchanged.

**Field count: 22 properties** (well under the 35-property ceiling).

---

## opamp.schema.json v1.0 — 2026-04-27

Initial release. Phase 3b (extraction breadth). Fields cover general-purpose, precision, rail-to-rail I/O, rail-to-rail output, JFET-input, CMOS-input, chopper, instrumentation, and comparator op-amps. Field union from LM358 (Fairchild → ON Semi BJT general-purpose dual single-supply, SOIC-8/PDIP-8) + MCP6004 (Microchip CMOS rail-to-rail I/O quad, SOIC-14/PDIP-14/TSSOP-14).

Required: `opamp_topology` (enum) + `channels` (integer). All other fields nullable.

**Topology enum addition vs. design spec:** the design spec listed 8 topology values; v1.0 ships 9 — added `comparator` to cover open-collector comparator parts (LM393, LM339) which share op-amp IC families and packages. Treating comparators as an opamp-topology variant rather than a separate schema reduces Phase 3b/4 fragmentation; downstream consumers gate on the enum value.

`iq_per_amp` is per-channel quiescent current (NOT total Iq — divide by `channels` if the datasheet only gives total supply current ICC).

`shutdown_pin` matches `base.pinout[*].numbers` when populated. Both MVP MPNs lack a shutdown pin (`null` for both); the field exists for future shutdownable parts (e.g. MCP6N11, OPA376). Pin-resolution registered as `_PIN_FIELDS_BY_CATEGORY["opamp"] = ("shutdown_pin",)` (already from Task 2).

`vsupply_range` is the total spread (V+ to V−). LM358 spans 3–32V single = ±1.5V to ±16V split; the schema stores the single-supply equivalent with a condition note for the split-supply range.

`vout_swing_high` and `vout_swing_low` are stored as positive headroom-from-rail values (NOT absolute voltages). For rail-to-rail output parts, typical values are 25–50mV. For non-rail-to-rail parts (e.g. LM358), output swing high is 1.5–2V headroom from V+; output swing low is 5–20mV above V− at light load.

**v1.4 deferrals** (deferred to v1.5 to avoid spec_value unit enum sprawl):
- `noise_voltage_density` — would need `V/√Hz` unit
- `noise_current_density` — would need `A/√Hz` unit
- `phase_margin` — would need degrees unit
These are real op-amp parameters but their units don't fit the canonical SI enum pattern cleanly.

**spec_value.schema.json amendments (required by opamp field set):**
- Added `"V/s"` to `unit` enum — slew rate in V/s (NOT V/µs; store 0.6V/µs as `6e5`).
- Added `"dB"` to `unit` enum — CMRR, PSRR, open-loop gain.
Both additive non-breaking changes; existing cached extractions remain valid.

`thermal_resistance` follows the diode/transistor convention: `rtheta_ja`/`rtheta_jc`/`rtheta_jl` nullable SpecValue lists.

`package.body_mm` follows the diode/transistor convention: nested `{length, width, height}` (no `_mm` suffix on inner fields; aligns with base.schema.json's body_mm shape).

---

## transistor.schema.json v1.0 — 2026-04-27

Initial release. Phase 3b (extraction breadth). Fields cover BJT (NPN/PNP), MOSFET (N/P-channel), JFET, IGBT discrete transistors. Field union from 2N3904 (MCC NPN BJT, TO-92) + IRLML6344 (IR/Infineon N-MOSFET, SOT-23) datasheet review.

Required: `transistor_type` (enum). All other fields nullable. BJT-vs-FET encoded as null fields per inactive type (no `oneOf` discriminator) — schema accepts a part with all FET fields populated and all BJT fields null, or vice versa. The prompt's hard rules document this exclusion explicitly.

`pin_assignment` is a closed object with 6 nullable string fields (`base_pin`, `collector_pin`, `emitter_pin`, `gate_pin`, `drain_pin`, `source_pin`). For BJT/IGBT, populate base/collector/emitter; for FET/JFET, populate gate/drain/source. Pin-resolution against `base.pinout` is registered as the empty tuple in `_PIN_FIELDS_BY_CATEGORY["transistor"]` — the nested object's pin-string fields are not yet validated against pinout. v1.5 may add nested-object pin-resolution.

`hfe`, `id_max`, `power_dissipation`, `vce_sat`, `rds_on` accept multiple SpecValues per part disambiguated via condition string (different test currents, gate voltages, or temperatures).

`thermal_resistance` follows the diode-established convention: nested object with `rtheta_ja` / `rtheta_jc` / `rtheta_jl` nullable SpecValue lists (K/W or °C/W).

`package.body_mm` follows the diode-established convention: nested `{length, width, height}` (no `_mm` suffix on inner fields; aligns with base.schema.json's pre-existing shape).

**spec_value.schema.json amendments (required by transistor field set):**
- Added `null` to `unit` type (dimensionless quantities — `hfe` current gain has no SI unit).
- Added `"C"` (coulombs) to `unit` enum (gate charge fields `qg`, `qgd`).
Both are additive non-breaking changes; existing cached extractions remain valid.

---

## diode.schema.json v1.0 — 2026-04-27

Initial release. Phase 3b (extraction breadth). Fields cover signal, switching, Schottky, zener, TVS, rectifier, bridge, and varicap diodes. Field union from 1N4148 (Vishay signal switching, DO-35) + MBRS540T3G (ON Semi Schottky power, SMC) datasheet review.

Required: `diode_type` (enum). All other fields nullable to accommodate type-specific characteristics:
- `vz` only for zeners
- `trr` typically null for slow rectifiers/zeners
- `cd` most relevant for varicaps and signal/switching diodes
- `breakdown_voltage` separate from `vr_max` (1N4148 specs both at 100V; MBRS540T3G doesn't spec breakdown explicitly)

**Field-union additions vs. design-spec field list** (per Decision 10, schema covers union of both MVP MPNs' fields): `breakdown_voltage`, `tj_max`, and the third `thermal_resistance.rtheta_jl` sub-field (junction-to-lead) were added during datasheet read of 1N4148 + MBRS540T3G — they were not in the original spec field list but are real datasheet-published parameters worth capturing. Spec deviation is licensed by the field-union methodology.

`if_max` and `vr_max` accept multiple SpecValues per part disambiguated via condition string (continuous / average / repetitive peak; VRRM / VR / VRWM).

`thermal_resistance` is a nested object with three nullable sub-fields (`rtheta_ja`, `rtheta_jc`, `rtheta_jl` — all SpecValue lists, K/W). Through-hole parts typically have only `rtheta_ja`; SMD parts often have both `rtheta_jl` and `rtheta_ja`.

`package.body_mm` is a NESTED object `{length, width, height}` (Phase 3b option A convention — first new schema using this shape; inner field names align with `base.schema.json`'s pre-existing body_mm shape, no `_mm` suffix). Symmetric across categories (transistor/opamp/mcu/crystal will adopt same shape in subsequent tasks).

Pin-resolution: diodes have no pin-reference fields; `_PIN_FIELDS_BY_CATEGORY["diode"]` is the empty tuple (already set in Task 2).

---

## scout — 1.0 (2026-04-25, Phase 3a)

Fat-scout output: `{mpn, metadata, categories, extraction_pages, quality_verdict}`. Identifies datasheet characteristics, target category extensions, per-task page lists, and a quality verdict gating extraction dispatch.

## plan — 1.0 (2026-04-25, Phase 3a)

Orchestration plan written by `plan_extraction.py`, consumed by the dispatcher and `merge_results.py`. Shape: `{plan_version, mpn, pdf_path, pdf_sha256, cache_dir, scout_ref, tasks[], execution: {started_at, completed_at, outcomes[]}}`. Each task carries `task_id`, `subagent_role`, `tier`, `schema`, `prompt_template`, `pages`, `depends_on`, `status`, `result_ref`.

## base — 1.0 (2026-04-19, v1.4)

Initial version.

Shape: `{family, description, package, thermal, absolute_max, recommended_operating, esd, moisture_sensitivity, compliance, pinout, pin_relationships}`. `absolute_max`, `recommended_operating`, `esd`, and `thermal` are objects keyed by parameter name → `SpecValue[]` (see spec §4). `pinout` is a `$ref` to `pinout.schema.json`.

## pinout — 1.0 (2026-04-19, v1.4) — still-calibrating

Initial version. Pin shape: `{numbers[], name, type, subtype, description, power_domain, alt_functions[], is_5v_tolerant, absolute_max, recommended, drive_strength, notes, evidence}`. Type vocabulary mirrors KiCad ERC pin types.

Flagged `x-still-calibrating: true` — shape may shift before v1.5.

## spec_value — 1.0 (2026-04-19, v1.4)

Initial version. `{min, typ, max, unit, condition, notes, evidence: {page, section, confidence, method}}`. Canonical SI units only. Always serialized inside a list (one-element list for single-value specs).

## regulator — 0.3 (2026-04-19, v1.4)

Initial version. Category extension for voltage regulators. Flat topology enum per spec §7 (`ldo|buck|boost|buck_boost|sepic|flyback|charge_pump|isolated`). Optional SpecValue[] fields for vin_range, vout_range, iout_max, reference_voltage, cin_min, cout_min, inductor_range, switching_freq, dropout, psrr, line_regulation, load_regulation. `stability_conditions` + `sequencing` nested objects feed SV-001 and ST-001.

Version 0.3 (not 1.0) because the field set may still shift — the first real extractions against diverse parts (LDO vs buck vs boost) may prompt adjustments. Promoted to 1.0 once v1.4 corpus re-extraction validates the shape.

## extraction — 1.0 (2026-04-19, v1.4)

Initial version. Top-level per-MPN file envelope: `{schema_version, source, extraction, base, categories, <per-category>}`. `source.family_ref` and `source.sha256` enable Tier 1 dedup; `categories[]` lists the active extensions.

## manifest — 1.0 (2026-04-19, v1.4)

Initial version. `datasheets/manifest.json` shape covering both legacy `extractions` index (v1.3 compat) and new `pdfs` SHA-dedup section (Tier 1).
