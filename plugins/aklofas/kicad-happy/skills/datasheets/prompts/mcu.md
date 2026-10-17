# Datasheet MCU Extractor Subagent

You are extracting the **MCU category extension** (core, memory, peripheral counts, supply, package, debug interface, reset pin, temperature grades) from an electronics component datasheet PDF.

## Task

Read `{{PDF_PATH}}` (focus pages: `{{PAGES}}`). Target MPN: **`{{MPN}}`**.

Produce a single JSON object matching this schema: `{{SCHEMA_PATH}}`.

## Scope — catalog tier only

This is a **catalog-tier** extraction. Capture identity-level facts about the MCU: what is it, how much memory, how many peripherals of each type, what are the supply ranges. Do NOT attempt per-peripheral instance configuration, pin-mux tables, or alternate function maps — those are Tier 2 fields deferred to v1.5 (`mcu_peripherals.schema.json`).

## Field guide

- `core_family`: string. Open-form identifier for the CPU core — do not guess a value not found in the datasheet. Examples: `"cortex_m0"`, `"cortex_m0plus"`, `"cortex_m3"`, `"cortex_m4"`, `"cortex_m4f"`, `"cortex_m7"`, `"cortex_m33"`, `"avr_8bit"`, `"avr_8bit_atmega"`, `"avr_8bit_attiny"`, `"pic16"`, `"pic32"`, `"riscv_rv32"`, `"8051"`. Use lowercase with underscores. This is the only required field.

- `core_speed_max`: integer or null. Maximum CPU clock frequency **in Hz** (NOT MHz). Found on cover page, Features list, or Electrical Characteristics. Store 72MHz as `72000000`. Null when not found.

- `flash_size`: integer or null. Internal flash size **in bytes** (NOT KB). Store 32K as `32768`, 64K as `65536`. Null when the part has no internal flash.

- `ram_size`: integer or null. Internal SRAM size **in bytes**. Store 20K as `20480`. Null when not determinable.

- `eeprom_size`: integer or null. Internal EEPROM size **in bytes**. Use `0` for parts with no EEPROM (e.g. STM32F103C8T6 has no EEPROM → `0`). Use the actual byte count for AVR parts with EEPROM (e.g. ATmega328P 1K EEPROM → `1024`). Null when not determinable.

- `pin_count`: integer or null. Total package pin count. Found on cover page or package description.

- `gpio_count`: integer or null. Number of GPIO pins. Often listed in the Features section. Null when not found.

- `nvic_priorities`: integer or null. Number of NVIC interrupt priority levels (Cortex-M parts only). For Cortex-M3: `16`. Null for non-Cortex-M cores (AVR, PIC, 8051, RISC-V without NVIC). Found in the NVIC section of the programming manual or CPU description.

- `vdd_range`: SpecValue list (unit: `"V"`). Main supply voltage range. Condition carries frequency-dependent restrictions when relevant (e.g. AVR 20MHz requires 4.5–5.5V).

- `vddio_range`: SpecValue list or null (unit: `"V"`). Separate I/O supply range. Null when I/O supply is shared with VDD (most single-supply MCUs).

- `vdda_range`: SpecValue list or null (unit: `"V"`). Analog supply range (AVCC, VDDA). Null when analog supply is shared with VDD and no separate spec is given.

- `peripheral_counts`: object or null. Counts of each peripheral type. **Use 0 for peripherals the part lacks — not null.** The object's inner properties are required to be non-negative integers.
  - `uart`: count of UART/USART interfaces (each independent channel). STM32F103C8T6 → 3.
  - `spi`: count of SPI interfaces. ATmega328P → 1.
  - `i2c`: count of I2C interfaces.
  - `can`: count of CAN interfaces. 0 for most low-end MCUs.
  - `usb`: count of USB peripheral instances (NOT endpoint count).
  - `ethernet`: count of Ethernet MAC interfaces. 0 for most MCUs.
  - `dac`: count of DAC peripheral instances. 0 when no DAC present. Also set top-level `dac: null` when `peripheral_counts.dac = 0`.
  - `timer_general`: count of general-purpose timers (basic + general; exclude advanced-control timers). STM32F103C8T6 → 4 (TIM2/3/4 general + TIM6/7 basic where present, or just TIM2/3/4 for C8).
  - `timer_advanced`: count of advanced-control timer instances (TIM1 type with complementary outputs, dead-time). STM32F103C8T6 → 1 (TIM1).

- `adc`: object or null. ADC summary. Null when no ADC. Catalog tier — single summary for the whole part:
  - `bit_depth`: integer or null. ADC resolution (e.g. 10, 12).
  - `channel_count`: integer or null. Total muxed channel count across all ADC peripherals (e.g. ATmega328P → 8 channels, STM32F103C8T6 → 10 external channels).
  - `sample_rate_max_hz`: number or null. Maximum sample rate in Hz. ATmega328P → `76900` (76.9 ksps). STM32F103C8T6 → `1000000` (1 MSPS).

- `dac`: object or null. DAC summary. Null when no DAC (the common case for most budget MCUs). Same shape as `adc`. When `peripheral_counts.dac = 0`, set `dac: null`.

- `boot_pins`: array or null. Boot configuration pins that control startup mode. Empty array `[]` when the part has no boot pins (e.g. AVR uses fuse-controlled boot section — no pin). Array of `{pin_number, function}` objects otherwise. For STM32F103C8T6: `[{"pin_number": "44", "function": "BOOT0"}]`. Null when not determinable.

- `debug_interface`: enum or null. Primary debug/programming interface:
  - `"swd"` — SWD only (some small Cortex-M parts)
  - `"jtag"` — JTAG only
  - `"swd_jtag"` — both SWD and JTAG (STM32F103C8T6, most Cortex-M)
  - `"debugwire"` — Atmel debugWIRE (ATmega328P, ATtiny)
  - `"pdi"` — Atmel PDI (XMEGA)
  - `"spi_isp"` — SPI-based ISP (older AVR, PIC)
  - `"none"` — no on-chip debug interface
  - `null` when not determinable

- `reset_pin`: string or null. RESET/NRST pin number (matches `base.pinout[*].numbers`). For ATmega328P-AU TQFP-32: `"29"`. For STM32F103C8T6 LQFP-48: `"7"`. Null when not determinable.

- `temperature_grades`: array of strings or null. Operating temperature grade strings from the datasheet Features or Ordering Information section. Example: `["industrial: -40 to +85"]`. Null when not stated.

- `thermal_resistance`: nested object or null with three nullable SpecValue-list sub-fields (unit `"°C/W"` or `"K/W"`):
  - `rtheta_ja` — junction-to-ambient. Present for most packages.
  - `rtheta_jc` — junction-to-case. Null when not specified.
  - `rtheta_jl` — junction-to-lead. Null for most MCU packages.
  Found in Thermal Characteristics section.

- `package`: object with `code` (string), `pin_count` (integer), `pitch_mm` (number or null), `body_mm` (nested object with `length`, `width`, `height` — all numbers in millimeters), `thermal_pad` (boolean or null), `evidence`. Found in Package Dimensions / Mechanical Data.

## Hard rules

1. **Canonical SI units. No exceptions.** Memory sizes in **bytes** (NOT KB/MB — store 32K as `32768`). Frequencies in **Hz** (NOT MHz — store 72MHz as `72000000`). Voltages in **V**. Sample rates in **Hz**.
2. **Every SpecValue requires `evidence`** with `page` (1-based integer), `section` (string or null), `confidence` (`"high"`, `"medium"`, or `"low"`), `method` (one of `table`, `prose`, `curve`, `calculated`, `derived`).
3. **Catalog tier only.** Capture peripheral *counts* in `peripheral_counts`, not per-peripheral detail. The peripheral_counts object exists to answer "how many UARTs", not "which pins does UART1 use". Per-instance configuration is v1.5 work.
4. **peripheral_counts uses 0 for absent peripherals, not null.** If a part has no DAC, set `peripheral_counts.dac = 0` AND set top-level `dac: null`.
5. **reset_pin matches base.pinout[*].numbers exactly** when populated. If you cannot find the pin number in the pinout, set null.
6. **nvic_priorities is null for non-Cortex-M cores.** AVR, PIC, 8051, classic RISC-V without NVIC → null.
7. **eeprom_size convention:** use `0` for parts with no EEPROM (e.g. STM32F103C8T6); use the actual byte count for parts that have EEPROM (e.g. ATmega328P → `1024`). Null only when not determinable.
8. **OMIT fields you cannot find** (leave as null). No guessing. A missing `core_speed_max` is better than a hallucinated one.

## Output format

Return only the JSON object. No prose, no fences. Output must validate against `{{SCHEMA_PATH}}`.

Example (STM32F103C8T6 — ST Cortex-M3 32-bit, LQFP-48; values from datasheet):

```json
{
  "core_family": "cortex_m3",
  "core_speed_max": 72000000,
  "flash_size": 65536,
  "ram_size": 20480,
  "eeprom_size": 0,
  "pin_count": 48,
  "gpio_count": 37,
  "nvic_priorities": 16,
  "vdd_range": [
    {"min": 2.0, "typ": null, "max": 3.6, "unit": "V",
     "condition": "VDD operating range",
     "notes": null,
     "evidence": {"page": 3, "section": "Electrical Characteristics", "confidence": "high", "method": "table"}}
  ],
  "vddio_range": null,
  "vdda_range": [
    {"min": 2.0, "typ": null, "max": 3.6, "unit": "V",
     "condition": "VDDA analog supply",
     "notes": null,
     "evidence": {"page": 3, "section": "Electrical Characteristics", "confidence": "high", "method": "table"}}
  ],
  "peripheral_counts": {
    "uart": 3,
    "spi": 2,
    "i2c": 2,
    "can": 1,
    "usb": 1,
    "ethernet": 0,
    "dac": 0,
    "timer_general": 4,
    "timer_advanced": 1
  },
  "adc": {
    "bit_depth": 12,
    "channel_count": 10,
    "sample_rate_max_hz": 1000000.0
  },
  "dac": null,
  "boot_pins": [
    {"pin_number": "44", "function": "BOOT0"}
  ],
  "debug_interface": "swd_jtag",
  "reset_pin": "7",
  "temperature_grades": ["industrial: -40 to +85"],
  "thermal_resistance": {
    "rtheta_ja": [
      {"min": null, "typ": 60, "max": null, "unit": "°C/W",
       "condition": "LQFP-48, free air",
       "notes": null,
       "evidence": {"page": 2, "section": "Thermal Characteristics", "confidence": "medium", "method": "prose"}}
    ],
    "rtheta_jc": null,
    "rtheta_jl": null
  },
  "package": {
    "code": "LQFP-48",
    "pin_count": 48,
    "pitch_mm": 0.5,
    "body_mm": {"length": 7.0, "width": 7.0, "height": 1.4},
    "thermal_pad": false,
    "evidence": {"page": 80, "section": "Package Mechanical Data", "confidence": "high", "method": "table"}
  }
}
```
