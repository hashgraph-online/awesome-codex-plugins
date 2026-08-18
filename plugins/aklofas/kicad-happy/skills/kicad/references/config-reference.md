# .kicad-happy.json Config Reference

Configuration file for kicad-happy. Placed in the project directory (or any parent directory). All analyzers, the EMC skill, and the BOM skill read this file automatically.

## File Format

JSONC — JSON with `//` and `/* */` comments, and trailing commas allowed. The parser is purely stdlib; no external dependencies.

```jsonc
// Comments are allowed anywhere
{
  "version": 1, // trailing commas are OK
  "project": {
    "name": "My Board",
  },
}
```

## Discovery and Merge Order

The loader walks upward from the project directory, collecting every `.kicad-happy.json` it finds, then includes `~/.kicad-happy.json` as the base layer (lowest precedence). Files are merged closest-wins:

```
~/.kicad-happy.json          ← base layer (user-wide defaults)
/home/user/hw/.kicad-happy.json   ← workspace layer
/home/user/hw/myboard/.kicad-happy.json  ← project layer (wins)
```

**Merge rules:**
- Dict values: deep-merged recursively; closer keys win on conflict.
- `suppressions`: **concatenated** across all layers (additive — all suppressions apply).
- All other lists: closer layer wins entirely (replaces the farther layer's list).

**Error handling:** Parse errors print a warning to stderr and skip that layer. The loader never crashes. Invalid field values are warned and skipped individually.

## Schema

### `version` (integer)

Always `1`. Reserved for future schema evolution.

---

### `project` (object)

Document metadata. Consumed by analyzers for report context.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Product or project name |
| `number` | string | Model or part number |
| `revision` | string | Document revision (e.g., "A", "1.2") |
| `company` | string | Manufacturer or organization name |
| `author` | string | Document author |
| `market` | string | Compliance market: `"us"`, `"eu"`, `"automotive"`, `"medical"`, `"military"` |
| `ambient_temperature_c` | number | Ambient temperature for thermal analysis (default: `25`) |
| `emc_standard` | string | EMC standard: `"fcc-class-b"`, `"fcc-class-a"`, `"cispr-class-a"`, `"cispr-class-b"` |
| `compliance_market` | string | Same as `market`; used by the EMC analyzer |

---

### `suppressions` (array of objects)

Suppress specific analyzer findings. **Additive across config layers** — suppressions from all discovered config files are combined. Findings are marked suppressed, never removed; suppressed findings still appear in reports with a note.

Each entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rule_id` | string | **Yes** | Exact rule ID to suppress (e.g., `"DC-001"`, `"SW-002"`) |
| `components` | array of strings | No | fnmatch glob patterns for component refs. At least one finding component must match at least one pattern. |
| `nets` | array of strings | No | fnmatch glob patterns for net names. At least one finding net must match at least one pattern. |
| `reason` | string | No | Human-readable explanation; shown in reports |

**Matching:** `rule_id` must match exactly. If `components` is present, the finding must reference at least one matching component. If `nets` is present, the finding must reference at least one matching net. All present filters must match (AND logic). Patterns use Python `fnmatch` syntax (`*`, `?`, `[seq]`).

**Entries missing `rule_id` are silently skipped** with a stderr warning.

```jsonc
"suppressions": [
  // Suppress for all instances of this rule
  {
    "rule_id": "DC-001",
    "reason": "Intentional — test pad left floating"
  },
  // Suppress only for specific components
  {
    "rule_id": "SW-002",
    "components": ["Q1", "Q2"],
    "reason": "Bootstrap topology confirmed with vendor"
  },
  // Suppress only for specific nets
  {
    "rule_id": "EMC-005",
    "nets": ["VBUS_RAW", "USB_*"],
    "reason": "USB VBUS handled by upstream filter board"
  },
]
```

---

### `preferred_suppliers` (array of strings) — v1.2

Ordered list of preferred suppliers for BOM sourcing. The BOM manager uses this to select the primary distributor instead of auto-detecting. First entry is primary.

Valid values: `"digikey"`, `"mouser"`, `"lcsc"`, `"element14"`.

Unknown values are warned and dropped. Default: `[]` (BOM manager auto-selects).

```jsonc
"preferred_suppliers": ["lcsc", "digikey"]
```

---

### `bom` (object) — v1.2

BOM conventions for this project.

| Field | Type | Description |
|-------|------|-------------|
| `field_priority` | array of strings | Ordered list of schematic field names to search for part numbers (e.g., `["MPN", "Digi-Key_PN"]`). Informational — guides the AI agent; no code enforcement. |
| `group_by` | string | How to group BOM lines: `"value"`, `"mpn"`, or `"value+footprint"` (default: `"value+footprint"`) |

Invalid `group_by` values are warned and the field is ignored (default behavior applies).

```jsonc
"bom": {
  "field_priority": ["MPN", "LCSC", "Digi-Key_PN"],
  "group_by": "mpn"
}
```

---

### `analysis` (object)

Controls analysis script behavior and output.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `output_dir` | string | `"analysis"` | Directory for analysis JSON output |
| `retention` | integer | `5` | Number of past analysis runs to keep |
| `auto_diff` | boolean | `true` | Automatically diff against the previous run |
| `track_in_git` | boolean | `false` | Include analysis output in git tracking |
| `diff_threshold` | string | `"major"` | Minimum change level to report: `"major"`, `"minor"`, or `"all"` |
| `power_rails` | object | `{}` | Power rail filtering and annotation (see below) |

#### `analysis.power_rails` (object) — v1.2

Filter and annotate power rails in analysis output. All patterns use fnmatch glob syntax.

| Field | Type | Description |
|-------|------|-------------|
| `ignore` | array of strings | Net name patterns to exclude from analysis. Ignored rails are removed from `rail_voltages`, `power_rails`, sleep current audit, and power tree figures. |
| `flag` | array of strings | Net name patterns to highlight for extra scrutiny. Flagged rails appear in top-level `flagged_rails`. |
| `voltage_overrides` | object | Manual voltage assignments: `{net_name: voltage_float}`. Overrides auto-detected voltages from regulator outputs and power symbol name inference. |

`ignore` and `flag` must be arrays; `voltage_overrides` values must be numeric. Invalid entries are warned and skipped.

```jsonc
"analysis": {
  "output_dir": "analysis",
  "retention": 5,
  "auto_diff": true,
  "track_in_git": false,
  "diff_threshold": "major",
  "power_rails": {
    "ignore": ["VBUS_RAW", "USB_*", "BOOT_*"],
    "flag": ["+12V_UNREGULATED", "BATT_*"],
    "voltage_overrides": {
      "+3V3_MCU": 3.3,
      "VDDIO": 1.8
    }
  }
}
```

---

### `design_intent` (object)

Explicit design intent overrides. When absent, each field is **auto-detected** from PCB fab notes, schematic title blocks, component MPNs, and board characteristics. See `design-intent.md` for the full auto-detection logic and per-market review priorities.

| Field | Type | Auto-detected when absent | Description |
|-------|------|--------------------------|-------------|
| `product_class` | string | Yes | `"prototype"` or `"production"` |
| `ipc_class` | integer | Yes (from fab notes / title block) | `1`, `2`, or `3` (default: `2`) |
| `target_market` | string | Yes (from component MPNs) | `"hobby"`, `"consumer"`, `"industrial"`, `"medical"`, `"automotive"`, `"aerospace"` |
| `expected_lifetime_years` | integer | Yes (market-adjusted) | Product expected lifetime in years |
| `operating_temp_range` | array of 2 numbers | Yes (market-adjusted) | `[min_C, max_C]` |
| `operating_temp_min` | number | — | Alternative to `operating_temp_range`; can be combined with `operating_temp_max` |
| `operating_temp_max` | number | — | Alternative to `operating_temp_range`; can be combined with `operating_temp_min` |
| `preferred_passive_size` | string | Yes (default `"0603"`) | `"0201"`, `"0402"`, `"0603"`, `"0805"`, `"1206"` |
| `test_coverage_target` | number | Yes (market-adjusted) | `0.0` to `1.0` |
| `approved_manufacturers` | array of strings | No | Restrict to approved manufacturers; empty means no restriction |

**Market-adjusted defaults for auto-detected fields:**

| Market | `operating_temp_range` | `test_coverage_target` | `expected_lifetime_years` |
|--------|----------------------|----------------------|--------------------------|
| hobby / consumer | [-10, 70] | 0.85 | 5 |
| industrial / medical | [-40, 85] | 0.90 | 10 |
| automotive | [-40, 125] | 0.95 | 15 |
| aerospace | [-55, 125] | 0.98 | 20 |

**IPC class auto-detection priority:**
1. Explicit config (`"ipc_class"` key)
2. PCB fab/user/comments layer text (looks for "IPC-6012 Class N", "IPC Class N", "IPC-6012EM/ES")
3. PCB title block fields
4. Schematic title block fields
5. Inferred from `target_market` (medical/aerospace → Class 3)
6. Default: Class 2

```jsonc
"design_intent": {
  "product_class": "production",
  "ipc_class": 2,
  "target_market": "consumer",
  "expected_lifetime_years": 7,
  "operating_temp_range": [-10, 60],
  "preferred_passive_size": "0402",
  "test_coverage_target": 0.90,
  "approved_manufacturers": ["Murata", "TDK", "Yageo", "ROHM"]
}
```

---

## Complete Example

Production consumer electronics board targeting the EU market. LCSC primary supplier, IPC Class 2, with suppressions, power rail filtering, BOM config, and branding.

```jsonc
{
  "version": 1,

  // ── Project metadata ────────────────────────────────────────────────
  "project": {
    "name": "Smart Thermostat Controller",
    "number": "STC-200",
    "revision": "B",
    "company": "Acme Devices Ltd.",
    "author": "A. Engineer",
    "market": "eu",                    // CE marking target
    "emc_standard": "cispr-class-b",
    "compliance_market": "eu",
    "ambient_temperature_c": 30        // indoor install, above ambient
  },

  // ── Preferred suppliers (LCSC primary for JLCPCB assembly) ───────────
  "preferred_suppliers": ["lcsc", "digikey"], // v1.2

  // ── BOM conventions ─────────────────────────────────────────────────
  "bom": {                                     // v1.2
    "field_priority": ["LCSC", "MPN", "Digi-Key_PN"],
    "group_by": "mpn"
  },

  // ── Suppressions (additive across config layers) ─────────────────────
  "suppressions": [
    {
      "rule_id": "DC-003",
      "components": ["TP*"],
      "reason": "Test points intentionally unpopulated in production build"
    },
    {
      "rule_id": "EMC-011",
      "nets": ["VBUS_RAW"],
      "reason": "VBUS filtered upstream on power input board; this board sees clean rail"
    },
    {
      "rule_id": "THM-002",
      "components": ["U4"],
      "reason": "U4 (WiFi module) has internal thermal management; Rth_JA from module datasheet used directly"
    }
  ],

  // ── Analysis behavior ────────────────────────────────────────────────
  "analysis": {
    "output_dir": "analysis",
    "retention": 10,
    "auto_diff": true,
    "track_in_git": false,
    "diff_threshold": "minor",         // catch minor changes in CI

    // Power rail tuning (v1.2)
    "power_rails": {
      // Exclude raw/intermediate rails from power tree figures and audit
      "ignore": ["VBUS_RAW", "VBUS_FILT", "BOOT_*"],

      // Highlight unregulated rail for extra scrutiny
      "flag": ["+12V_UNREG"],

      // Correct auto-detected voltages where inference is wrong
      "voltage_overrides": {
        "+3V3_MCU": 3.3,
        "+3V3_RADIO": 3.3,
        "VDDIO_SENS": 1.8
      }
    }
  },

  // ── Design intent ────────────────────────────────────────────────────
  "design_intent": {
    "product_class": "production",
    "ipc_class": 2,
    "target_market": "consumer",
    "expected_lifetime_years": 7,
    "operating_temp_range": [0, 55],   // indoor thermostat, not industrial
    "preferred_passive_size": "0402",
    "test_coverage_target": 0.90,
    "approved_manufacturers": ["Murata", "TDK", "Samsung", "ROHM", "Yageo", "onsemi", "STMicroelectronics"]
  }
}
```

## Quick Field Index

| Field path | Type | v1.2 | Default | Auto-detected |
|------------|------|-------|---------|---------------|
| `version` | int | — | 1 | — |
| `project.name` | string | — | — | — |
| `project.number` | string | — | — | — |
| `project.revision` | string | — | — | — |
| `project.company` | string | — | — | — |
| `project.author` | string | — | — | — |
| `project.market` | string | — | — | — |
| `project.ambient_temperature_c` | number | — | 25 | — |
| `project.emc_standard` | string | — | — | — |
| `project.compliance_market` | string | — | — | — |
| `suppressions` | array | — | [] | — |
| `preferred_suppliers` | array | Yes | [] | — |
| `bom.field_priority` | array | Yes | — | — |
| `bom.group_by` | string | Yes | `"value+footprint"` | — |
| `analysis.output_dir` | string | — | `"analysis"` | — |
| `analysis.retention` | int | — | 5 | — |
| `analysis.auto_diff` | bool | — | true | — |
| `analysis.track_in_git` | bool | — | false | — |
| `analysis.diff_threshold` | string | — | `"major"` | — |
| `analysis.power_rails.ignore` | array | Yes | [] | — |
| `analysis.power_rails.flag` | array | Yes | [] | — |
| `analysis.power_rails.voltage_overrides` | object | Yes | {} | — |
| `design_intent.product_class` | string | — | `"prototype"` | Yes |
| `design_intent.ipc_class` | int | — | 2 | Yes |
| `design_intent.target_market` | string | — | `"hobby"` | Yes |
| `design_intent.expected_lifetime_years` | int | — | market-adj. | Yes |
| `design_intent.operating_temp_range` | array[2] | — | market-adj. | Yes |
| `design_intent.operating_temp_min` | number | — | — | — |
| `design_intent.operating_temp_max` | number | — | — | — |
| `design_intent.preferred_passive_size` | string | — | `"0603"` | Yes |
| `design_intent.test_coverage_target` | number | — | market-adj. | Yes |
| `design_intent.approved_manufacturers` | array | — | [] | — |
