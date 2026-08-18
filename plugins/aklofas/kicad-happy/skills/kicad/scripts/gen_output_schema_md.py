"""Regenerate skills/kicad/references/output-schema.md from envelope dataclasses.

Run:
    python3 skills/kicad/scripts/gen_output_schema_md.py

Emits a human-readable reference table derived from the same dataclass
definitions that drive --schema. No manual duplication.
"""
from __future__ import annotations

import sys
import typing
from dataclasses import MISSING, fields, is_dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = REPO_ROOT / "skills" / "kicad" / "scripts"
EMC_SCRIPTS = REPO_ROOT / "skills" / "emc" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(EMC_SCRIPTS))

from envelopes.schematic import SchematicEnvelope  # noqa: E402
from envelopes.pcb import PCBEnvelope  # noqa: E402
from envelopes.gerber import GerberEnvelope  # noqa: E402
from envelopes.thermal import ThermalEnvelope  # noqa: E402
from envelopes.cross_analysis import CrossAnalysisEnvelope  # noqa: E402
from emc_envelope import EMCEnvelope  # noqa: E402


HEADER = """\
# Analyzer JSON Output Schema

**Generated from envelope dataclasses. Do not hand-edit.**
Regenerate: `python3 skills/kicad/scripts/gen_output_schema_md.py`

Source-of-truth modules:
- `skills/kicad/scripts/analyzer_envelope.py` — shared primitives (TrustSummary, Finding, BySeverity, ...)
- `skills/kicad/scripts/envelopes/*.py` — per-analyzer envelopes (schematic, pcb, gerber, thermal, cross_analysis)
- `skills/emc/scripts/emc_envelope.py` — EMC envelope

For the authoritative machine-readable JSON Schema Draft 2020-12, use `--schema` on any analyzer:

```bash
python3 skills/kicad/scripts/analyze_schematic.py --schema
python3 skills/kicad/scripts/analyze_pcb.py --schema
python3 skills/kicad/scripts/analyze_gerbers.py --schema
python3 skills/kicad/scripts/analyze_thermal.py --schema
python3 skills/emc/scripts/analyze_emc.py --schema
python3 skills/kicad/scripts/cross_analysis.py --schema
```

v1.4 schema-break notes:
- Output of `--schema` is real JSON Schema Draft 2020-12 (prior: descriptive-string dict).
- `schema_version` bumped 1.3.0 → 1.4.0 on every analyzer.
- `trust_summary.by_confidence` aggregate key renamed: `datasheet-backed` → `datasheet_backed`. Per-finding `confidence` VALUE stays `datasheet-backed`.

## Contract Tiers

Every analyzer envelope is organized into three tiers. Consumers can
rely on Tier 1 shapes; Tier 2 is analyzer-specific and best read via
the declared dataclass types; Tier 3 is compatibility residue slated
for removal and should not be written against in new code.

### Tier 1 — Standardized envelope (stable across v1.4)

Present on every analyzer output. Shape locked by the shared primitives
in `analyzer_envelope.py`. Breaking changes bump the analyzer's
`schema_version`.

- `analyzer_type` — `const` string discriminator naming the analyzer.
- `schema_version` — `const` string matching the semver.
- `summary` — per-analyzer roll-up (`total_findings`, `by_severity`,
  analyzer-specific counts). Inner shape is analyzer-specific but the
  top-level key is Tier 1.
- `trust_summary` — trust posture: `total_findings`, `trust_level`,
  `by_confidence`, `by_evidence_source`, `provenance_coverage_pct`,
  `bom_coverage` (schematic only).
- `findings` — `list[Finding]`. Actionable items with severity +
  recommendation.
- `assessments` — `list[Assessment]`. Informational measurements (no
  severity, no recommendation). Empty on analyzers with no assessment
  content today.
- `inputs` — `InputsBlock`. `source_files`, `source_hashes`, `run_id`,
  `config_hash`, `upstream_artifacts`.
- `compat` — `CompatBlock`. `minimum_consumer_version`,
  `deprecated_fields`, `experimental_fields`.

### Tier 2 — Analyzer-specific body

Everything emitted by a given analyzer that is not listed in Tier 1.
Shape is declared by the per-analyzer envelope in `envelopes/*.py` or
`emc_envelope.py`. Typical Tier 2 keys include `statistics`,
`components`, `nets`, `bom`, `ic_pin_analysis`, `design_analysis`,
`bus_topology`, `placement_analysis`, `power_net_routing`,
`connectivity_graph`, EMC `test_plan` / `regulatory_coverage`, thermal
`thermal_score`, gerber `layers` / `drills` / `completeness`, etc.

Several Tier 2 fields are currently typed as loose `dict` or
`list[dict]` with `TODO(v1.5)` markers. Consumers that need stable
shapes from these should wait for the v1.5 per-rule_id tightening pass.

### Tier 3 — Compatibility residue

Empty for v1.4. The v1.4 clean break removed prior residue:

- `schematic.file`, `pcb.file` — removed; use `inputs.source_files[0]`.
- `thermal.thermal_assessments` — renamed to `thermal.assessments`
  (sibling to `findings`, not inside it).
- Descriptive-string `--schema` output — replaced by real JSON Schema
  Draft 2020-12.
- `trust_summary.by_confidence.datasheet-backed` key — renamed to
  `datasheet_backed` (hyphen removed only for the aggregate-count key;
  the per-finding `confidence` VALUE still uses `datasheet-backed`).
- Deprecated `summary.critical` / `.high` / `.medium` / `.low` / `.info`
  keys on thermal — removed in v1.4.
"""


def _type_str(tp) -> str:
    import types as _types

    # PEP 604 union (X | Y)
    if isinstance(tp, getattr(_types, "UnionType", ())):
        args = typing.get_args(tp)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and len(args) == 2:
            return f"{_type_str(non_none[0])} | null"
        return " | ".join(_type_str(a) for a in args)

    origin = typing.get_origin(tp)
    args = typing.get_args(tp)

    if origin is typing.Union:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and len(args) == 2:
            return f"{_type_str(non_none[0])} | null"
        return " | ".join(_type_str(a) for a in args)

    if origin in (list,):
        return f"list[{_type_str(args[0])}]" if args else "list"
    if origin in (dict,):
        if args and len(args) == 2:
            return f"dict[str, {_type_str(args[1])}]"
        return "dict"
    if tp is int:
        return "int"
    if tp is float:
        return "float"
    if tp is str:
        return "string"
    if tp is bool:
        return "bool"
    if tp is type(None):
        return "null"
    if is_dataclass(tp):
        return tp.__name__
    # Bare list/dict without args
    if tp is list:
        return "list"
    if tp is dict:
        return "dict"
    return str(tp)


def _clean_desc(desc: str) -> str:
    """Make a description table-cell-safe: single line, escape pipes."""
    # Collapse whitespace (including newlines) to single spaces
    out = " ".join(desc.split())
    # Escape pipes so they don't split the table cell
    out = out.replace("|", "\\|")
    return out


def _emit_envelope(cls, *, intro: str) -> str:
    hints = typing.get_type_hints(cls)
    out = [
        f"## {cls.__name__}\n",
        intro,
        "",
        "| Key | Type | Required | Description |",
        "|-----|------|----------|-------------|",
    ]
    for f in fields(cls):
        meta = f.metadata or {}
        json_name = meta.get("json_name", f.name)
        is_req = f.default is MISSING and f.default_factory is MISSING
        desc = _clean_desc(meta.get("description", ""))
        # Escape pipes inside the rendered type (e.g. "string | null")
        # so they don't break the markdown table column count.
        type_cell = _type_str(hints[f.name]).replace("|", "\\|")
        out.append(
            f"| `{json_name}` | `{type_cell}` | "
            f"{'yes' if is_req else 'no'} | {desc} |"
        )
    return "\n".join(out) + "\n"


def main():
    parts = [HEADER]
    parts.append(_emit_envelope(
        SchematicEnvelope,
        intro="Output of `python3 skills/kicad/scripts/analyze_schematic.py <file>.kicad_sch`.",
    ))
    parts.append(_emit_envelope(
        PCBEnvelope,
        intro="Output of `python3 skills/kicad/scripts/analyze_pcb.py <file>.kicad_pcb`.",
    ))
    parts.append(_emit_envelope(
        GerberEnvelope,
        intro="Output of `python3 skills/kicad/scripts/analyze_gerbers.py <gerber_dir>/`.",
    ))
    parts.append(_emit_envelope(
        ThermalEnvelope,
        intro="Output of `python3 skills/kicad/scripts/analyze_thermal.py --schematic ... --pcb ...`.",
    ))
    parts.append(_emit_envelope(
        EMCEnvelope,
        intro="Output of `python3 skills/emc/scripts/analyze_emc.py --schematic ... --pcb ...`.",
    ))
    parts.append(_emit_envelope(
        CrossAnalysisEnvelope,
        intro="Output of `python3 skills/kicad/scripts/cross_analysis.py --schematic ... --pcb ...`.",
    ))
    out_path = REPO_ROOT / "skills" / "kicad" / "references" / "output-schema.md"
    out_path.write_text("\n".join(parts))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
