#!/usr/bin/env python3
"""Translate BOM and Pick-and-Place (CPL) files into JLCPCB upload format.

Two subcommands:
    bom  — read Altium xlsx or KiCad CSV BOM, write JLCPCB BOM CSV
    pnp  — read CPL CSV, write JLCPCB Pick-and-Place CSV
           (with optional --bom filter to drop CPL rows whose designators
            don't appear in the BOM — avoids JLCPCB upload rejection)

Stdlib-only except optional ``openpyxl`` for Altium xlsx input.

Inspired by MattStarfield/kicad-happy fork commits fe440c8 + 8d8d06c.
Clean reimplementation under the kicad-happy MIT license.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Iterator


# --- Header field synonyms (loose-match dictionaries) -----------------------

BOM_DES_FIELDS = ("designator", "reference", "references", "refdes", "ref")
BOM_VAL_FIELDS = ("comment", "value", "val")
BOM_FOOT_FIELDS = ("footprint", "package", "pattern")
BOM_MPN_FIELDS = ("mpn", "manufacturer part number", "manufacturer pn", "mfg pn")
BOM_MFG_FIELDS = ("manufacturer", "mfg", "mfr", "vendor")
BOM_QTY_FIELDS = ("quantity", "qty")

PNP_REF_FIELDS = ("designator", "reference", "refdes", "ref")
PNP_X_FIELDS = ("mid x", "midx", "x", "center-x", "centerx", "ref x", "refx")
PNP_Y_FIELDS = ("mid y", "midy", "y", "center-y", "centery", "ref y", "refy")
PNP_LAYER_FIELDS = ("layer", "side")
PNP_ROT_FIELDS = ("rotation", "rot", "angle")

# --- Markers that indicate a row should be skipped --------------------------

DNP_MARKERS = ("no stuff", "dnp", "do not populate", "dni", "noload", "no load")
PCB_MARKERS = ("pcb,", "bare pcb", "pcb-")

# Header-row detection: scan first N rows, pick the one with the most matches.
HEADER_SCAN_LIMIT = 20


def _loose_match(cell: str, candidates: tuple[str, ...]) -> bool:
    """Case-insensitive substring match against any candidate.

    >>> _loose_match("Designator", ("designator", "reference"))
    True
    >>> _loose_match("Ref Des", ("refdes",))
    True
    >>> _loose_match("Quantity", ("designator",))
    False
    >>> _loose_match("", ("designator",))
    False
    """
    if not cell:
        return False
    cell_lc = cell.strip().lower()
    cell_no_space = cell_lc.replace(" ", "")
    return any(c in cell_lc or c in cell_no_space for c in candidates)


def _find_col(header: list[str], candidates: tuple[str, ...]) -> int | None:
    """Return index of first header cell matching any candidate, else None.

    Exact match first, then loose substring (via _loose_match for
    space-tolerance like "Ref Des" → "refdes").

    >>> _find_col(["Designator", "Comment"], ("comment",))
    1
    >>> _find_col(["Ref Des", "Value"], ("refdes",))
    0
    >>> _find_col(["A", "B"], ("c",)) is None
    True
    """
    lower = [(c or "").strip().lower() for c in header]
    for i, cell in enumerate(lower):
        if cell in candidates:
            return i
    for i, cell in enumerate(header):
        if _loose_match(cell, candidates):
            return i
    return None


def _is_dnp(value: str) -> bool:
    """Return True if value matches any DNP marker.

    >>> _is_dnp("No Stuff")
    True
    >>> _is_dnp("DNP")
    True
    >>> _is_dnp("100nF")
    False
    """
    if not value:
        return False
    v = value.strip().lower()
    return any(m in v for m in DNP_MARKERS)


def _is_pcb_marker(value: str) -> bool:
    """Return True if value matches any PCB-marker (bare-PCB sentinel row).

    >>> _is_pcb_marker("Bare PCB")
    True
    >>> _is_pcb_marker("PCB-001")
    True
    >>> _is_pcb_marker("PCB,REV2")
    True
    >>> _is_pcb_marker("100nF")
    False
    """
    if not value:
        return False
    v = value.strip().lower()
    return any(m in v for m in PCB_MARKERS)


def _detect_header_row(rows: list[list[str]]) -> int:
    """Return index of best-match header row in the first HEADER_SCAN_LIMIT rows.

    Score = count of (BOM_DES, BOM_VAL, BOM_FOOT, BOM_MPN) field matches.
    Requires at least 2 matches to count as a header. Returns 0 if no row qualifies.

    >>> _detect_header_row([["a", "b"], ["Designator", "Value", "Footprint"]])
    1
    >>> _detect_header_row([["Designator", "Value"]])
    0
    """
    best_idx, best_score = 0, 0
    for i, row in enumerate(rows[:HEADER_SCAN_LIMIT]):
        if not row:
            continue
        cells_lc = [(c or "").strip().lower() for c in row]
        score = sum(
            1
            for group in (BOM_DES_FIELDS, BOM_VAL_FIELDS, BOM_FOOT_FIELDS, BOM_MPN_FIELDS)
            if any(any(c in cell for c in group) for cell in cells_lc)
        )
        if score > best_score and score >= 2:
            best_idx, best_score = i, score
    return best_idx


UNIT_TO_MM = {
    "mm": 1.0,
    "mil": 0.0254,
    "inch": 25.4,
    "in": 25.4,
    "cm": 10.0,
}


def _parse_units_from_header(header_cell: str) -> str:
    """Extract a unit hint from a header cell like 'Mid X (mil)' → 'mil'.

    >>> _parse_units_from_header("Mid X (mil)")
    'mil'
    >>> _parse_units_from_header("Mid Y(mm)")
    'mm'
    >>> _parse_units_from_header("Center-X [inch]")
    'inch'
    >>> _parse_units_from_header("Reference")
    ''
    """
    if not header_cell:
        return ""
    s = header_cell.strip().lower()
    for unit in UNIT_TO_MM:
        for opener, closer in (("(", ")"), ("[", "]")):
            tok = f"{opener}{unit}{closer}"
            if tok in s:
                return unit
    return ""


def _coord_to_mm(cell: str, default_unit: str) -> float | None:
    """Parse a coordinate cell to mm. Honor in-cell unit suffix if present.

    >>> _coord_to_mm("12.5", "mm")
    12.5
    >>> _coord_to_mm("100mil", "mm")
    2.54
    >>> _coord_to_mm("1inch", "")
    25.4
    >>> _coord_to_mm("", "mm") is None
    True
    """
    if not cell:
        return None
    s = cell.strip().lower()
    # In-cell unit suffix override
    for unit, factor in UNIT_TO_MM.items():
        if s.endswith(unit):
            try:
                return float(s[: -len(unit)].strip()) * factor
            except ValueError:
                return None
    # Bare numeric — use default unit
    try:
        value = float(s)
    except ValueError:
        return None
    factor = UNIT_TO_MM.get(default_unit, 1.0) if default_unit else 1.0
    return value * factor


def _normalize_layer(cell: str) -> str:
    """Normalize layer label to 'T' or 'B'. Pass through unknowns unchanged.

    >>> _normalize_layer("TopLayer")
    'T'
    >>> _normalize_layer("F.Cu")
    'T'
    >>> _normalize_layer("Top")
    'T'
    >>> _normalize_layer("BottomLayer")
    'B'
    >>> _normalize_layer("B.Cu")
    'B'
    >>> _normalize_layer("Inner1")
    'Inner1'
    """
    if not cell:
        return cell
    s = cell.strip().lower()
    if s in ("top", "toplayer", "f.cu", "front", "t"):
        return "T"
    if s in ("bottom", "bottomlayer", "b.cu", "back", "b"):
        return "B"
    return cell.strip()


def _detect_pnp_header_row(rows: list[list[str]]) -> int:
    """Return index of best-match CPL header row (analogous to BOM detection).

    >>> _detect_pnp_header_row([["x", "y"], ["Designator", "Mid X", "Mid Y", "Layer"]])
    1
    """
    best_idx, best_score = 0, 0
    for i, row in enumerate(rows[:HEADER_SCAN_LIMIT]):
        if not row:
            continue
        cells_lc = [(c or "").strip().lower() for c in row]
        score = sum(
            1
            for group in (PNP_REF_FIELDS, PNP_X_FIELDS, PNP_Y_FIELDS, PNP_LAYER_FIELDS)
            if any(any(c in cell for c in group) for cell in cells_lc)
        )
        if score > best_score and score >= 2:
            best_idx, best_score = i, score
    return best_idx


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="translate_bom_pnp",
        description="Translate BOM/CPL into JLCPCB upload format.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_bom = sub.add_parser("bom", help="Translate a BOM file to JLCPCB format.")
    p_bom.add_argument("input", help="Input BOM file (.csv or .xlsx).")
    p_bom.add_argument("-o", "--output", required=True, help="Output CSV path.")

    p_pnp = sub.add_parser("pnp", help="Translate a CPL file to JLCPCB format.")
    p_pnp.add_argument("input", help="Input CPL file (.csv).")
    p_pnp.add_argument("-o", "--output", required=True, help="Output CSV path.")
    p_pnp.add_argument(
        "--bom",
        help="BOM CSV path. If supplied, CPL rows whose designators are not in "
             "the BOM are dropped (avoids JLCPCB upload rejection on orphans).",
    )

    sub.add_parser("self-test", help="Run embedded end-to-end tests and exit.")

    args = parser.parse_args(argv)

    if args.cmd == "self-test":
        return _self_test()
    if args.cmd == "bom":
        stats = translate_bom(args.input, args.output)
    elif args.cmd == "pnp":
        stats = translate_pnp(args.input, args.output, bom_filter_path=args.bom)
    else:
        parser.error(f"Unknown command: {args.cmd}")

    print(json.dumps(stats, indent=2))
    return 0


def _read_csv_rows(path: str) -> list[list[str]]:
    """Read a CSV file into a list of rows (each row a list of strings)."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [list(row) for row in csv.reader(f)]


def translate_bom(input_path: str, output_path: str) -> dict:
    """Translate a BOM file to JLCPCB upload format.

    Supports KiCad CSV and Altium-exported CSV. Altium xlsx input is
    deferred to a follow-up (requires optional ``openpyxl``); raise
    a clear error for now.
    """
    in_path = Path(input_path)
    if in_path.suffix.lower() in (".xlsx", ".xls"):
        raise NotImplementedError(
            f"xlsx input not yet supported (input: {input_path}). "
            "Convert to CSV in Altium/Excel and rerun."
        )

    rows = _read_csv_rows(input_path)
    if not rows:
        raise ValueError(f"BOM is empty: {input_path}")

    header_idx = _detect_header_row(rows)
    header = rows[header_idx]
    data_rows = rows[header_idx + 1 :]

    col_des = _find_col(header, BOM_DES_FIELDS)
    col_val = _find_col(header, BOM_VAL_FIELDS)
    col_foot = _find_col(header, BOM_FOOT_FIELDS)
    col_mpn = _find_col(header, BOM_MPN_FIELDS)
    col_mfg = _find_col(header, BOM_MFG_FIELDS)
    col_qty = _find_col(header, BOM_QTY_FIELDS)

    if col_des is None or col_val is None:
        raise ValueError(
            f"BOM missing required columns (Designator/Reference and Value/Comment). "
            f"Header at row {header_idx}: {header}"
        )

    stats = {
        "input": input_path,
        "output": output_path,
        "header_row": header_idx,
        "rows_in": 0,
        "rows_out": 0,
        "skipped_dnp": 0,
        "skipped_pcb_marker": 0,
        "continuation_rows_merged": 0,
    }

    output_rows: list[dict] = []
    current: dict | None = None

    def _cell(row: list[str], idx: int | None) -> str:
        if idx is None or idx >= len(row):
            return ""
        return (row[idx] or "").strip()

    for raw in data_rows:
        stats["rows_in"] += 1
        if not any((c or "").strip() for c in raw):
            continue

        des = _cell(raw, col_des)
        val = _cell(raw, col_val)
        mpn = _cell(raw, col_mpn)
        mfg = _cell(raw, col_mfg)

        # Continuation row: no designator, but MPN/Mfg present — alt-part for prior row.
        if not des and (mpn or mfg) and current is not None:
            if mpn:
                current["alt_mpns"].append(mpn)
            if mfg:
                current["alt_mfgs"].append(mfg)
            stats["continuation_rows_merged"] += 1
            continue

        if not des:
            continue

        if _is_pcb_marker(val) or _is_pcb_marker(des):
            stats["skipped_pcb_marker"] += 1
            current = None
            continue
        if _is_dnp(val):
            stats["skipped_dnp"] += 1
            current = None
            continue

        current = {
            "designator": des,
            "value": val,
            "footprint": _cell(raw, col_foot),
            "mpn": mpn,
            "manufacturer": mfg,
            "quantity": _cell(raw, col_qty),
            "alt_mpns": [],
            "alt_mfgs": [],
        }
        output_rows.append(current)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Comment",
                "Designator",
                "Footprint",
                "LCSC Part #",
                "MPN",
                "Manufacturer",
                "Quantity",
                "Notes",
            ]
        )
        for r in output_rows:
            notes = ""
            if r["alt_mpns"]:
                notes = "alt MPN: " + ", ".join(r["alt_mpns"])
            writer.writerow(
                [
                    r["value"],
                    r["designator"],
                    r["footprint"],
                    "",  # LCSC Part # — user populates separately
                    r["mpn"],
                    r["manufacturer"],
                    r["quantity"],
                    notes,
                ]
            )
            stats["rows_out"] += 1

    return stats


def _expand_designators(field: str) -> list[str]:
    """Split a comma/whitespace-separated designator list into individual refs.

    >>> _expand_designators("C1, C2, C5")
    ['C1', 'C2', 'C5']
    >>> _expand_designators("R1")
    ['R1']
    >>> _expand_designators("C1; C2")
    ['C1', 'C2']
    >>> _expand_designators("")
    []
    """
    if not field:
        return []
    for sep in (",", ";"):
        field = field.replace(sep, " ")
    return [tok.strip() for tok in field.split() if tok.strip()]


def _read_bom_designators(bom_path: str) -> set[str]:
    """Read BOM CSV and return the set of all designators present.

    Accepts either JLCPCB-format output (Designator column) or
    upstream BOM formats (Reference/Designator/RefDes synonyms).
    """
    rows = _read_csv_rows(bom_path)
    if not rows:
        return set()

    header_idx = _detect_header_row(rows)
    header = rows[header_idx]
    col_des = _find_col(header, BOM_DES_FIELDS)
    if col_des is None:
        raise ValueError(
            f"BOM at {bom_path} has no Designator column (header row {header_idx}: {header})"
        )

    refs: set[str] = set()
    for raw in rows[header_idx + 1 :]:
        if col_des >= len(raw):
            continue
        refs.update(_expand_designators(raw[col_des]))
    return refs


def translate_pnp(
    input_path: str, output_path: str, *, bom_filter_path: str | None = None
) -> dict:
    """Translate a CPL file to JLCPCB Pick-and-Place format.

    If ``bom_filter_path`` is supplied, CPL rows whose designators are
    not present in the BOM are dropped (avoids JLCPCB upload rejection
    on orphan designators).
    """
    rows = _read_csv_rows(input_path)
    if not rows:
        raise ValueError(f"CPL is empty: {input_path}")

    header_idx = _detect_pnp_header_row(rows)
    header = rows[header_idx]
    data_rows = rows[header_idx + 1 :]

    col_ref = _find_col(header, PNP_REF_FIELDS)
    col_x = _find_col(header, PNP_X_FIELDS)
    col_y = _find_col(header, PNP_Y_FIELDS)
    col_layer = _find_col(header, PNP_LAYER_FIELDS)
    col_rot = _find_col(header, PNP_ROT_FIELDS)

    if col_ref is None or col_x is None or col_y is None:
        raise ValueError(
            f"CPL missing required columns (Designator, Mid X, Mid Y). "
            f"Header at row {header_idx}: {header}"
        )

    default_x_unit = _parse_units_from_header(header[col_x])
    default_y_unit = _parse_units_from_header(header[col_y])
    default_unit = default_x_unit or default_y_unit  # whichever has a hint
    if default_unit:
        default_x_unit = default_x_unit or default_unit
        default_y_unit = default_y_unit or default_unit

    stats = {
        "input": input_path,
        "output": output_path,
        "header_row": header_idx,
        "default_unit": default_unit or "mm",
        "rows_in": 0,
        "rows_out": 0,
        "skipped_no_coords": 0,
        "filtered_orphans": 0,
        "filtered_orphan_samples": [],
        "bom_designators": 0,
    }

    bom_designators: set[str] | None = None
    if bom_filter_path:
        bom_designators = _read_bom_designators(bom_filter_path)
        stats["bom_designators"] = len(bom_designators)

    def _cell(row: list[str], idx: int | None) -> str:
        if idx is None or idx >= len(row):
            return ""
        return (row[idx] or "").strip()

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])

        for raw in data_rows:
            stats["rows_in"] += 1
            if not any((c or "").strip() for c in raw):
                continue

            ref = _cell(raw, col_ref)
            if not ref:
                continue

            if bom_designators is not None and ref not in bom_designators:
                stats["filtered_orphans"] += 1
                if len(stats["filtered_orphan_samples"]) < 15:
                    stats["filtered_orphan_samples"].append(ref)
                continue

            x_mm = _coord_to_mm(_cell(raw, col_x), default_x_unit)
            y_mm = _coord_to_mm(_cell(raw, col_y), default_y_unit)
            if x_mm is None or y_mm is None:
                stats["skipped_no_coords"] += 1
                continue

            layer = _normalize_layer(_cell(raw, col_layer))
            rotation = _cell(raw, col_rot) or "0"

            writer.writerow(
                [
                    ref,
                    f"{x_mm:.4f}mm",
                    f"{y_mm:.4f}mm",
                    layer,
                    rotation,
                ]
            )
            stats["rows_out"] += 1

    return stats


def _self_test() -> int:
    """End-to-end smoke test. Returns 0 on success, 1 on failure."""
    import tempfile

    failures: list[str] = []

    # --- BOM translation: KiCad-style CSV with DNP, PCB marker, continuation row ---
    bom_csv = (
        "Project: demo\n"
        "Generated: 2026-05-16\n"
        "Reference,Value,Footprint,Manufacturer,Manufacturer Part Number\n"
        "C1,100nF,Capacitor_SMD:C_0402_1005Metric,Yageo,CC0402KRX7R9BB104\n"
        ",,,Murata,GRM155R71C104KA88\n"  # continuation row — alt MPN
        "R1,10k,Resistor_SMD:R_0402_1005Metric,Yageo,RC0402FR-0710KL\n"
        "DNP1,DO NOT POPULATE,Capacitor_SMD:C_0402_1005Metric,,\n"
        "PCB1,Bare PCB,,,\n"
        "U1,STM32G030F6P6,Package_SO:TSSOP-20,STMicro,STM32G030F6P6\n"
    )

    with tempfile.TemporaryDirectory() as tmp:
        in_path = Path(tmp) / "bom_in.csv"
        out_path = Path(tmp) / "bom_out.csv"
        in_path.write_text(bom_csv)

        stats = translate_bom(str(in_path), str(out_path))

        if stats["rows_out"] != 3:
            failures.append(
                f"BOM rows_out: expected 3 (C1, R1, U1), got {stats['rows_out']}"
            )
        if stats["skipped_dnp"] != 1:
            failures.append(f"BOM skipped_dnp: expected 1, got {stats['skipped_dnp']}")
        if stats["skipped_pcb_marker"] != 1:
            failures.append(
                f"BOM skipped_pcb_marker: expected 1, got {stats['skipped_pcb_marker']}"
            )
        if stats["continuation_rows_merged"] != 1:
            failures.append(
                f"BOM continuation_rows_merged: expected 1, got "
                f"{stats['continuation_rows_merged']}"
            )

        out_text = out_path.read_text()
        if "alt MPN: GRM155R71C104KA88" not in out_text:
            failures.append("BOM output missing alt-MPN notes column")
        if "DO NOT POPULATE" in out_text:
            failures.append("BOM output unexpectedly contains DNP row")
        if "Bare PCB" in out_text:
            failures.append("BOM output unexpectedly contains PCB-marker row")

    # --- PNP translation: mil-unit CPL with TopLayer/BottomLayer + bare numeric ---
    pnp_csv = (
        "Designator,Mid X (mil),Mid Y (mil),Layer,Rotation\n"
        "R1,100,200,TopLayer,90\n"
        "C1,500.5,1000,BottomLayer,0\n"
        "U1,2000,3000,F.Cu,180\n"
        ",,,,\n"
        "BAD,not-a-number,500,TopLayer,0\n"
    )

    with tempfile.TemporaryDirectory() as tmp:
        in_path = Path(tmp) / "cpl_in.csv"
        out_path = Path(tmp) / "cpl_out.csv"
        in_path.write_text(pnp_csv)
        stats = translate_pnp(str(in_path), str(out_path))

        if stats["rows_out"] != 3:
            failures.append(f"PNP rows_out: expected 3 (R1,C1,U1), got {stats['rows_out']}")
        if stats["skipped_no_coords"] != 1:
            failures.append(
                f"PNP skipped_no_coords: expected 1 (BAD), got {stats['skipped_no_coords']}"
            )
        if stats["default_unit"] != "mil":
            failures.append(
                f"PNP default_unit: expected 'mil', got {stats['default_unit']!r}"
            )

        out_text = out_path.read_text()
        # 100 mil = 2.54 mm, 200 mil = 5.08 mm
        if "2.5400mm" not in out_text or "5.0800mm" not in out_text:
            failures.append(
                "PNP output missing expected mil→mm conversion (2.5400mm/5.0800mm)"
            )
        # Layer normalization
        if ",T," not in out_text:
            failures.append("PNP output missing normalized 'T' layer")
        if ",B," not in out_text:
            failures.append("PNP output missing normalized 'B' layer")

    # --- PNP with --bom filter: drops CPL rows whose designators aren't in BOM ---
    bom_for_filter = (
        "Comment,Designator,Footprint,LCSC Part #,MPN,Manufacturer,Quantity,Notes\n"
        "100nF,C1,Cap_0402,,,,,\n"
        "10k,R1,Res_0402,,,,,\n"
    )
    cpl_for_filter = (
        "Designator,Mid X (mm),Mid Y (mm),Layer,Rotation\n"
        "R1,10.0,10.0,T,0\n"
        "C1,20.0,20.0,T,90\n"
        "U1,30.0,30.0,T,0\n"
        "TP1,40.0,40.0,T,0\n"
    )

    with tempfile.TemporaryDirectory() as tmp:
        bom_path = Path(tmp) / "bom_for_filter.csv"
        cpl_path = Path(tmp) / "cpl_for_filter.csv"
        out_path = Path(tmp) / "cpl_out_filtered.csv"
        bom_path.write_text(bom_for_filter)
        cpl_path.write_text(cpl_for_filter)

        stats = translate_pnp(
            str(cpl_path), str(out_path), bom_filter_path=str(bom_path)
        )

        if stats["rows_out"] != 2:
            failures.append(
                f"PNP-filter rows_out: expected 2 (R1, C1 in BOM), got {stats['rows_out']}"
            )
        if stats["filtered_orphans"] != 2:
            failures.append(
                f"PNP-filter filtered_orphans: expected 2 (U1, TP1), got "
                f"{stats['filtered_orphans']}"
            )
        if set(stats["filtered_orphan_samples"]) != {"U1", "TP1"}:
            failures.append(
                f"PNP-filter orphan_samples: expected {{U1, TP1}}, got "
                f"{stats['filtered_orphan_samples']}"
            )
        if stats["bom_designators"] != 2:
            failures.append(
                f"PNP-filter bom_designators: expected 2, got {stats['bom_designators']}"
            )

        out_text = out_path.read_text()
        if "U1," in out_text or "TP1," in out_text:
            failures.append("PNP-filter output unexpectedly contains orphan designators")

    if failures:
        print("self-test: FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("self-test: PASS (BOM + PNP + --bom filter)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
