#!/usr/bin/env python3
"""
KiCad Gerber & Drill File Analyzer — comprehensive single-pass extraction.

Parses Gerber RS-274X files and Excellon drill files to extract:
- Layer identification (X2 attributes, KiCad 5 comment format, filename patterns)
- Component list, net list, and pin-to-net connectivity (from X2 TO attributes)
- Aperture definitions, function classification, and trace width distribution
- Board dimensions (from Edge.Cuts extents or .gbrjob)
- Drill hole sizes, counts, and classification (via / component / mounting)
- Layer completeness verification (against .gbrjob expected list or defaults)
- Layer alignment (coordinate range consistency)
- Inner copper layer detection (4+ layer boards)
- .gbrjob metadata (stackup, design rules, board specs)
- SMD vs THT pad analysis, minimum feature size

Usage:
    python analyze_gerbers.py <gerber_directory> [--output file.json] [--compact] [--full]
"""

import json
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from envelopes.gerber import GerberEnvelope  # noqa: E402
from schema_codec import emit_schema  # noqa: E402
from inputs_builder import build_inputs, build_compat  # noqa: E402
from capability_mode import get_capability_mode_ref  # noqa: E402

ANALYZER_SOURCE = "gerber"

_POWER_KEYWORDS_GERBER = {"vcc", "vdd", "gnd", "agnd", "dgnd", "gndref",
                          "vss", "avdd", "dvdd", "vbat", "vbus", "vin"}

# ---------------------------------------------------------------------------
# Gerber parser
# ---------------------------------------------------------------------------

def parse_gerber(path: str) -> dict:
    """Parse a single Gerber RS-274X file with full X2 object attribute extraction.

    Single stateful pass extracts:
    - Format, units, coordinate range, operation counts (flash/draw/region)
    - Aperture definitions with per-aperture TA function tags
    - X2 file attributes (TF) — modern %TF...% and KiCad 5 G04 comment format
    - X2 object attributes (TO) — component refs, net names, pin mappings
    - Trace width distribution from conductor apertures
    """
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
        lines = content.splitlines()

    result = {
        "file": str(path),
        "filename": Path(path).name,
        "format": None,
        "units": None,
        "apertures": {},
        "x2_attributes": {},
        "flash_count": 0,
        "draw_count": 0,
        "region_count": 0,
        "coordinate_range": {"x_min": float("inf"), "x_max": float("-inf"),
                             "y_min": float("inf"), "y_max": float("-inf")},
        "polarity_changes": 0,
        "line_count": len(lines),
    }

    # --- Phase 1: regex extraction for format and units (need these for coords) ---

    fs_match = re.search(r"%FS([LT])([AI])X(\d)(\d)Y(\d)(\d)\*%", content)
    if fs_match:
        result["format"] = {
            "zero_omit": "leading" if fs_match.group(1) == "L" else "trailing",
            "notation": "absolute" if fs_match.group(2) == "A" else "incremental",
            "x_integer": int(fs_match.group(3)),
            "x_decimal": int(fs_match.group(4)),
            "y_integer": int(fs_match.group(5)),
            "y_decimal": int(fs_match.group(6)),
        }

    if "%MOIN*%" in content:
        result["units"] = "inch"
    elif "%MOMM*%" in content:
        result["units"] = "mm"

    # X2 file attributes — modern format: %TF.Key,Value*%
    for match in re.finditer(r"%TF\.(\w+),([^*]*)\*%", content):
        result["x2_attributes"][match.group(1)] = match.group(2)

    # X2 file attributes — KiCad 5 comment format: G04 #@! TF.Key,Value*
    for match in re.finditer(r"G04 #@! TF\.(\w+),([^*]*)\*", content):
        key = match.group(1)
        if key not in result["x2_attributes"]:
            result["x2_attributes"][key] = match.group(2)

    # --- Phase 2: stateful line-by-line pass ---

    x_div = 10 ** result["format"]["x_decimal"] if result["format"] else 1e6
    y_div = 10 ** result["format"]["y_decimal"] if result["format"] else 1e6

    # Aperture function tracking (TA precedes AD, TD clears)
    pending_aper_function = None
    aperture_functions = {}     # D-code -> function string
    current_aperture = None             # currently selected D-code
    aperture_flash_counts = {}          # D-code -> flash instance count

    # X2 object attribute state
    current_component = None
    current_net = None
    component_pads = {}         # ref -> pad flash count
    component_nets = {}         # ref -> set of net names
    net_names = set()
    net_draw_counts = {}        # net_name -> draw count (D01 operations)
    net_flash_counts = {}       # net_name -> flash count (D03 operations)
    pin_mappings = []           # [{ref, pin, pin_name, net}]

    # Aperture dimension tracking for trace width / min feature analysis
    aperture_dims = {}          # D-code -> parsed dimension info

    for line in lines:
        s = line.strip()

        # -- Aperture attribute (TA) --
        m = re.match(r"%TA\.AperFunction,([^*]*)\*%", s)
        if m:
            pending_aper_function = m.group(1)
            continue

        # -- Aperture definition (AD) --
        m = re.match(r"%AD(D\d+)(\w+),?([^*]*)\*%", s)
        if m:
            ap_id = m.group(1)
            ap_type = m.group(2)
            ap_params = m.group(3) or ""
            result["apertures"][ap_id] = {
                "type": ap_type,
                "params": ap_params if ap_params else None,
            }
            if pending_aper_function:
                aperture_functions[ap_id] = pending_aper_function
                result["apertures"][ap_id]["function"] = pending_aper_function
            # Parse dimension for trace width / feature size analysis
            dim = _parse_aperture_dimension(ap_type, ap_params, result["units"])
            if dim is not None:
                aperture_dims[ap_id] = {
                    "width_mm": dim,
                    "function": pending_aper_function or "",
                }
            continue

        # -- Clear attributes (TD) — per X2 spec, clears ALL object attributes --
        if s == "%TD*%":
            pending_aper_function = None
            current_component = None
            current_net = None
            continue

        # -- Object attributes (TO) — component, net, pin --
        m = re.match(r"%TO\.C,([^*]*)\*%", s)
        if m:
            current_component = m.group(1)
            if current_component not in component_pads:
                component_pads[current_component] = 0
                component_nets[current_component] = set()
            continue

        m = re.match(r"%TO\.N,([^*]*)\*%", s)
        if m:
            current_net = m.group(1)
            net_names.add(current_net)
            if current_component and current_component in component_nets:
                component_nets[current_component].add(current_net)
            continue

        m = re.match(r"%TO\.P,([^,]*),([^,*]*)(?:,([^*]*))?\*%", s)
        if m:
            pin_mappings.append({
                "ref": m.group(1),
                "pin": m.group(2),
                "pin_name": m.group(3) or "",
                "net": current_net or "",
            })
            continue

        # -- Polarity --
        if s.startswith("%LP"):
            result["polarity_changes"] += 1
            continue

        # -- Region start --
        if s == "G36*":
            result["region_count"] += 1

        # -- Aperture selection (Dnn* where nn >= 10) --
        ap_sel = re.match(r"^(D[1-9]\d+)\*$", s)
        if ap_sel:
            current_aperture = ap_sel.group(1)

        # -- Operations: flash (D03), draw (D01) --
        if "D03" in s:
            result["flash_count"] += 1
            if current_aperture:
                aperture_flash_counts[current_aperture] = aperture_flash_counts.get(current_aperture, 0) + 1
            if current_component and current_component in component_pads:
                component_pads[current_component] += 1
            if current_net:
                net_flash_counts[current_net] = net_flash_counts.get(current_net, 0) + 1
        elif "D01" in s:
            result["draw_count"] += 1
            if current_net:
                net_draw_counts[current_net] = net_draw_counts.get(current_net, 0) + 1

        # -- Coordinate extraction --
        cm = re.match(r"X(-?\d+)Y(-?\d+)", s)
        if cm:
            x = int(cm.group(1)) / x_div
            y = int(cm.group(2)) / y_div
            cr = result["coordinate_range"]
            if x < cr["x_min"]: cr["x_min"] = x
            if x > cr["x_max"]: cr["x_max"] = x
            if y < cr["y_min"]: cr["y_min"] = y
            if y > cr["y_max"]: cr["y_max"] = y

    # Fix infinite values if no coordinates found
    for key in result["coordinate_range"]:
        if result["coordinate_range"][key] in (float("inf"), float("-inf")):
            result["coordinate_range"][key] = 0

    # Identify layer type
    result["layer_type"] = identify_layer_type(Path(path).name, result["x2_attributes"])

    # --- Build X2 object summary ---
    has_x2_objects = bool(component_pads or net_names or pin_mappings)
    if has_x2_objects:
        # Per-net copper usage (draws = traces, flashes = pads)
        net_copper_usage = {}
        for net in net_names:
            draws = net_draw_counts.get(net, 0)
            flashes = net_flash_counts.get(net, 0)
            if draws > 0 or flashes > 0:
                net_copper_usage[net] = {
                    "draw_operations": draws,
                    "flash_operations": flashes,
                    "total_operations": draws + flashes,
                }

        result["x2_objects"] = {
            "component_refs": sorted(component_pads.keys()),
            "component_pads": {r: c for r, c in sorted(component_pads.items()) if c > 0},
            "component_nets": {r: sorted(ns) for r, ns in sorted(component_nets.items()) if ns},
            "net_names": sorted(net_names),
            "pin_mappings": pin_mappings,
            "net_copper_usage": net_copper_usage,
        }

    # --- Aperture analysis ---
    func_counts = {}
    conductor_widths = set()
    all_dims = []
    for ap_id, info in aperture_dims.items():
        func = info.get("function", "")
        if func:
            base_func = func.split(",")[0]  # "SMDPad,CuDef" → "SMDPad"
            func_counts[base_func] = func_counts.get(base_func, 0) + 1
        if "Conductor" in func and info["width_mm"] > 0:
            conductor_widths.add(round(info["width_mm"], 4))
        if info["width_mm"] > 0:
            all_dims.append(info["width_mm"])

    # Count flash instances per aperture function (KH-173: instance counts, not unique defs)
    func_flash_counts = {}
    for ap_id, info in aperture_dims.items():
        func = info.get("function", "")
        if func:
            base_func = func.split(",")[0]
            flashes = aperture_flash_counts.get(ap_id, 0)
            func_flash_counts[base_func] = func_flash_counts.get(base_func, 0) + flashes

    if func_counts or conductor_widths or all_dims:
        result["aperture_analysis"] = {}
        if func_counts:
            result["aperture_analysis"]["by_function"] = func_counts
        if func_flash_counts:
            result["aperture_analysis"]["by_function_flashes"] = func_flash_counts
        if conductor_widths:
            result["aperture_analysis"]["conductor_widths_mm"] = sorted(conductor_widths)
        if all_dims:
            result["aperture_analysis"]["min_feature_mm"] = round(min(all_dims), 4)

    return result


def _parse_aperture_dimension(ap_type: str, ap_params: str, units: str | None) -> float | None:
    """Extract the primary dimension (mm) from an aperture definition.

    Returns the smallest relevant dimension (e.g., diameter for circle,
    smaller side for rectangle). Returns None if unparseable.
    """
    if not ap_params:
        return None

    try:
        if ap_type == "C":
            # Circle: C,diameter
            dim = float(ap_params.split("X")[0])
        elif ap_type == "R":
            # Rectangle: R,widthXheight
            parts = ap_params.split("X")
            dim = min(float(parts[0]), float(parts[1]))
        elif ap_type == "O":
            # Obround/Oval: O,widthXheight
            parts = ap_params.split("X")
            dim = min(float(parts[0]), float(parts[1]))
        elif ap_type == "RoundRect":
            # RoundRect macro: first param is corner radius, then 8 corner coords
            # The overall pad size requires geometry — use 2× corner radius as
            # a conservative minimum feature estimate
            parts = ap_params.split("X")
            radius = float(parts[0])
            dim = radius * 2
        else:
            return None
    except (ValueError, IndexError):
        return None

    if dim <= 0:
        return None

    # Convert to mm if needed
    if units == "inch":
        dim *= 25.4

    return dim


# ---------------------------------------------------------------------------
# Drill parser
# ---------------------------------------------------------------------------

def parse_drill(path: str) -> dict:
    """Parse an Excellon drill file."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    result = {
        "file": str(path),
        "filename": Path(path).name,
        "units": None,
        "tools": {},
        "hole_count": 0,
        "coordinate_range": {"x_min": float("inf"), "x_max": float("-inf"),
                             "y_min": float("inf"), "y_max": float("-inf")},
        "x2_attributes": {},
    }

    current_tool = None
    pending_aper_function = None
    fmt_decimals = None       # from ; FORMAT={3:3/...} comment
    coord_divisor = None      # set on first coordinate line

    for line in lines:
        line = line.strip()

        # Units
        if "METRIC" in line or "MOMM" in line.upper():
            result["units"] = "mm"
        elif "INCH" in line:
            result["units"] = "inch"

        # KiCad FORMAT comment: ; FORMAT={3:3/ absolute / metric / ...}
        fmt_match = re.match(r";\s*FORMAT=\{(\d+):(\d+)/", line)
        if fmt_match:
            fmt_decimals = int(fmt_match.group(2))

        # X2 attributes from comments: ; #@! TF.Key,Value
        tf_match = re.match(r";\s*#@!\s*TF\.(\w+),(.*)", line)
        if tf_match:
            result["x2_attributes"][tf_match.group(1)] = tf_match.group(2).strip()

        # Per-tool aperture function: ; #@! TA.AperFunction,Plated,PTH,ViaDrill
        ta_match = re.match(r";\s*#@!\s*TA\.AperFunction,(.*)", line)
        if ta_match:
            pending_aper_function = ta_match.group(1).strip()

        # Tool definition in header
        tool_match = re.match(r"T(\d+)C(\d+\.?\d*)", line)
        if tool_match:
            tool_num = f"T{tool_match.group(1)}"
            diameter = float(tool_match.group(2))
            if result["units"] == "inch":
                diameter *= 25.4
            result["tools"][tool_num] = {
                "diameter_mm": round(diameter, 4),
                "hole_count": 0,
            }
            if pending_aper_function:
                result["tools"][tool_num]["aper_function"] = pending_aper_function
                pending_aper_function = None

        # End of header
        if line == "%":
            continue

        # Tool selection
        tool_sel = re.match(r"^(T\d+)$", line)
        if tool_sel:
            current_tool = tool_sel.group(1)
            continue

        # Drill hit
        coord_match = re.match(r"X(-?\d+\.?\d*)Y(-?\d+\.?\d*)", line)
        if coord_match and current_tool:
            x_str = coord_match.group(1)
            y_str = coord_match.group(2)
            x = float(x_str)
            y = float(y_str)

            # Detect integer vs decimal format on first coordinate
            if coord_divisor is None:
                if "." in x_str or "." in y_str:
                    coord_divisor = 1  # explicit decimal — no conversion
                elif fmt_decimals is not None:
                    coord_divisor = 10 ** fmt_decimals
                elif result["units"] == "inch":
                    coord_divisor = 10000  # standard 2:4 format
                else:
                    coord_divisor = 1000   # standard metric 3:3 format

            if coord_divisor > 1:
                x /= coord_divisor
                y /= coord_divisor

            if result["units"] == "inch":
                x *= 25.4
                y *= 25.4

            result["hole_count"] += 1
            if current_tool in result["tools"]:
                result["tools"][current_tool]["hole_count"] += 1

            cr = result["coordinate_range"]
            if x < cr["x_min"]: cr["x_min"] = x
            if x > cr["x_max"]: cr["x_max"] = x
            if y < cr["y_min"]: cr["y_min"] = y
            if y > cr["y_max"]: cr["y_max"] = y

    # Fix infinite values
    for key in result["coordinate_range"]:
        if result["coordinate_range"][key] in (float("inf"), float("-inf")):
            result["coordinate_range"][key] = 0

    # Determine PTH vs NPTH from filename or X2 FileFunction
    file_func = result["x2_attributes"].get("FileFunction", "")
    name_lower = Path(path).name.lower()
    if "NonPlated" in file_func or "npth" in name_lower:
        result["type"] = "NPTH"
    elif "MixedPlating" in file_func:
        result["type"] = "mixed"
    elif "Plated" in file_func or "pth" in name_lower:
        result["type"] = "PTH"
    else:
        result["type"] = "unknown"

    # Extract layer span from FileFunction (e.g., "Plated,1,4,PTH" → layers 1-4)
    ff_match = re.match(r"(?:(?:Non)?Plated|MixedPlating),(\d+),(\d+)", file_func)
    if ff_match:
        result["layer_span"] = [int(ff_match.group(1)), int(ff_match.group(2))]

    return result


# ---------------------------------------------------------------------------
# Layer identification
# ---------------------------------------------------------------------------

def identify_layer_type(filename: str, x2_attrs: dict) -> str:
    """Identify layer type from X2 attributes or filename patterns."""
    file_function = x2_attrs.get("FileFunction", "").lower()
    if file_function:
        if "copper" in file_function:
            # Cross-check: .gko extension always means board outline, even if
            # X2 FileFunction incorrectly says copper (KiCad 8 export bug)
            if Path(filename).suffix.lower() == ".gko":
                return "Edge.Cuts"
            if "top" in file_function:
                return "F.Cu"
            if "bot" in file_function:
                return "B.Cu"
            # Inner copper layers: "copper,l2,inr" or "copper,l3,inr"
            # X2 uses absolute layer position (L2 = second copper layer), but KiCad
            # names inner layers starting at In1.Cu. For a 4-layer board, L2→In1, L3→In2.
            inr_match = re.search(r"copper,l(\d+),inr", file_function)
            if inr_match:
                abs_pos = int(inr_match.group(1))
                inner_idx = abs_pos - 1  # L2→In1, L3→In2, etc.
                return f"In{inner_idx}.Cu"
        if "soldermask" in file_function:
            return "F.Mask" if "top" in file_function else "B.Mask"
        if "paste" in file_function or "solderpaste" in file_function:
            return "F.Paste" if "top" in file_function else "B.Paste"
        if "legend" in file_function or "silkscreen" in file_function:
            return "F.SilkS" if "top" in file_function else "B.SilkS"
        if "profile" in file_function:
            return "Edge.Cuts"

    # Fall back to filename patterns
    name = filename.lower()

    # Inner copper layers (check before outer to avoid false matches)
    inner_match = re.search(r"in(\d+)[_.]cu", name)
    if inner_match:
        return f"In{inner_match.group(1)}.Cu"
    # Protel-style inner layers: .g1, .g2, .g3, .g4, .g2l, .g3l, .g4l
    protel_inner = re.search(r"\.g(\d+)l?$", name)
    if protel_inner:
        layer_num = int(protel_inner.group(1))
        if layer_num >= 1:
            return f"In{layer_num}.Cu"

    patterns = {
        "f_cu": "F.Cu", "f.cu": "F.Cu", "front_cu": "F.Cu",
        "b_cu": "B.Cu", "b.cu": "B.Cu", "back_cu": "B.Cu",
        "f_mask": "F.Mask", "f.mask": "F.Mask",
        "b_mask": "B.Mask", "b.mask": "B.Mask",
        "f_paste": "F.Paste", "f.paste": "F.Paste",
        "b_paste": "B.Paste", "b.paste": "B.Paste",
        "f_silkscreen": "F.SilkS", "f_silks": "F.SilkS", "f.silks": "F.SilkS",
        "b_silkscreen": "B.SilkS", "b_silks": "B.SilkS", "b.silks": "B.SilkS",
        "edge_cuts": "Edge.Cuts", "edge.cuts": "Edge.Cuts",
    }
    for pattern, layer in patterns.items():
        if pattern in name:
            return layer

    # Protel-style outer extensions
    ext = Path(filename).suffix.lower()
    ext_map = {
        ".gtl": "F.Cu", ".gbl": "B.Cu",
        ".gts": "F.Mask", ".gbs": "B.Mask",
        ".gtp": "F.Paste", ".gbp": "B.Paste",
        ".gto": "F.SilkS", ".gbo": "B.SilkS",
        ".gm1": "Edge.Cuts", ".gko": "Edge.Cuts",
    }
    if ext in ext_map:
        return ext_map[ext]

    return "unknown"


# ---------------------------------------------------------------------------
# Job file parser
# ---------------------------------------------------------------------------

def parse_job_file(path: str) -> dict | None:
    """Parse a .gbrjob file and extract structured metadata."""
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    result = {}

    header = data.get("Header", {})
    gen_sw = header.get("GenerationSoftware", {})
    if gen_sw:
        result["generator"] = f"{gen_sw.get('Application', '')} {gen_sw.get('Version', '')}".strip()
        result["vendor"] = gen_sw.get("Vendor", "")
    result["creation_date"] = header.get("CreationDate", "")

    specs = data.get("GeneralSpecs", {})
    if specs:
        size = specs.get("Size", {})
        result["board_width_mm"] = size.get("X", 0)
        result["board_height_mm"] = size.get("Y", 0)
        result["layer_count"] = specs.get("LayerNumber", 0)
        result["board_thickness_mm"] = specs.get("BoardThickness", 0)
        result["finish"] = specs.get("Finish", "")
        project = specs.get("ProjectId", {})
        if project:
            result["project_name"] = project.get("Name", "")

    rules = data.get("DesignRules", [])
    if rules:
        result["design_rules"] = []
        for rule in rules:
            entry = {"layers": rule.get("Layers", "")}
            for key in ("PadToPad", "PadToTrack", "TrackToTrack",
                        "MinLineWidth", "TrackToRegion", "RegionToRegion"):
                if key in rule:
                    entry[key] = rule[key]
            result["design_rules"].append(entry)

    files = data.get("FilesAttributes", [])
    if files:
        result["expected_files"] = []
        for f in files:
            result["expected_files"].append({
                "path": f.get("Path", ""),
                "function": f.get("FileFunction", ""),
                "polarity": f.get("FilePolarity", ""),
            })

    stackup = data.get("MaterialStackup", [])
    if stackup:
        result["stackup"] = []
        for layer in stackup:
            entry = {"type": layer.get("Type", ""), "name": layer.get("Name", "")}
            if "Thickness" in layer:
                entry["thickness_mm"] = layer["Thickness"]
            if "Material" in layer:
                entry["material"] = layer["Material"]
            result["stackup"].append(entry)

    return result


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def classify_drill_tools(drills: list[dict]) -> dict:
    """Classify drill holes by function: vias, component pins, mounting holes."""
    via_count = 0
    component_count = 0
    mounting_count = 0

    via_tools = []
    component_tools = []
    mounting_tools = []

    for d in drills:
        for tool_name, tool_info in d.get("tools", {}).items():
            count = tool_info["hole_count"]
            dia = tool_info["diameter_mm"]
            aper = tool_info.get("aper_function", "")

            if d.get("type") == "NPTH":
                # Check per-tool X2 aper_function first
                if "ViaDrill" in aper:
                    via_count += count
                    if count > 0:
                        via_tools.append({"diameter_mm": dia, "count": count})
                elif "ComponentDrill" in aper:
                    # KH-186: KiCad labels all NPTH as ComponentDrill;
                    # large NPTH holes (>= 2.5mm) are mounting/standoff holes
                    if dia >= 2.5:
                        mounting_count += count
                        if count > 0:
                            mounting_tools.append({"diameter_mm": dia, "count": count, "type": "NPTH"})
                    else:
                        component_count += count
                        if count > 0:
                            component_tools.append({"diameter_mm": dia, "count": count, "type": "NPTH"})
                else:
                    # NPTH heuristic: small holes are component alignment pins
                    if dia <= 2.0:
                        component_count += count
                        if count > 0:
                            component_tools.append({"diameter_mm": dia, "count": count, "type": "NPTH"})
                    else:
                        mounting_count += count
                        if count > 0:
                            mounting_tools.append({"diameter_mm": dia, "count": count, "type": "NPTH"})
                continue

            if "ViaDrill" in aper:
                via_count += count
                if count > 0:
                    via_tools.append({"diameter_mm": dia, "count": count})
            elif "ComponentDrill" in aper:
                # KH-186: large non-plated holes are mounting regardless of X2
                if "NonPlated" in aper and dia >= 2.5:
                    mounting_count += count
                    if count > 0:
                        mounting_tools.append({"diameter_mm": dia, "count": count, "type": "NPTH"})
                else:
                    component_count += count
                    if count > 0:
                        component_tools.append({"diameter_mm": dia, "count": count})
            else:
                # Heuristic fallback
                if dia <= 0.45:
                    via_count += count
                    if count > 0:
                        via_tools.append({"diameter_mm": dia, "count": count})
                elif dia <= 1.3:
                    component_count += count
                    if count > 0:
                        component_tools.append({"diameter_mm": dia, "count": count})
                else:
                    mounting_count += count
                    if count > 0:
                        mounting_tools.append({"diameter_mm": dia, "count": count, "type": "PTH"})

    return {
        "vias": {"count": via_count, "tools": sorted(via_tools, key=lambda t: t["diameter_mm"])},
        "component_holes": {"count": component_count, "tools": sorted(component_tools, key=lambda t: t["diameter_mm"])},
        "mounting_holes": {"count": mounting_count, "tools": sorted(mounting_tools, key=lambda t: t["diameter_mm"])},
        "classification_method": "x2_attributes" if any(
            "aper_function" in ti
            for d in drills for ti in d.get("tools", {}).values()
        ) else "diameter_heuristic",
    }


def check_completeness(gerbers: list[dict], drills: list[dict],
                        job_info: dict | None = None) -> dict:
    """Check if all expected layers are present."""
    found_layers = set()
    for g in gerbers:
        lt = g.get("layer_type")
        if lt and lt != "unknown":
            found_layers.add(lt)

    expected_from_job = set()
    if job_info and "expected_files" in job_info:
        for ef in job_info["expected_files"]:
            lt = identify_layer_type(ef["path"], {"FileFunction": ef["function"]})
            if lt != "unknown":
                expected_from_job.add(lt)

    if expected_from_job:
        missing = expected_from_job - found_layers
        extra = found_layers - expected_from_job
        return {
            "found_layers": sorted(found_layers),
            "expected_layers": sorted(expected_from_job),
            "missing": sorted(missing),
            "extra": sorted(extra),
            "has_pth_drill": any(d.get("type") in ("PTH", "mixed") for d in drills),
            "has_npth_drill": any(d.get("type") in ("NPTH", "mixed") for d in drills),
            "complete": len(missing) == 0,
            "source": "gbrjob",
        }

    inner_layers = {lt for lt in found_layers if lt.startswith("In") and lt.endswith(".Cu")}
    required = {"F.Cu", "B.Cu", "F.Mask", "B.Mask", "Edge.Cuts"} | inner_layers
    recommended = {"F.SilkS", "F.Paste"}

    return {
        "found_layers": sorted(found_layers),
        # expected_layers is schema-required; on the defaults path there's
        # no .gbrjob to declare expectations, so emit [] honestly (TH-043).
        "expected_layers": [],
        "missing_required": sorted(required - found_layers),
        "missing_recommended": sorted(recommended - found_layers),
        "has_pth_drill": any(d.get("type") in ("PTH", "mixed") for d in drills),
        "has_npth_drill": any(d.get("type") in ("NPTH", "mixed") for d in drills),
        "complete": len(required - found_layers) == 0 and any(
            d.get("type") in ("PTH", "mixed", "unknown") for d in drills),
        "source": "defaults",
    }


def check_alignment(gerbers: list[dict], drills: list[dict]) -> dict:
    """Check that all layers have consistent coordinate ranges."""
    ranges = {}
    for g in gerbers:
        lt = g.get("layer_type", "unknown")
        if lt != "unknown":
            cr = g["coordinate_range"]
            ranges[lt] = {
                "width": round(cr["x_max"] - cr["x_min"], 3),
                "height": round(cr["y_max"] - cr["y_min"], 3),
            }
    for d in drills:
        cr = d["coordinate_range"]
        ranges[f"drill_{d.get('type', 'unknown')}"] = {
            "width": round(cr["x_max"] - cr["x_min"], 3),
            "height": round(cr["y_max"] - cr["y_min"], 3),
        }

    alignment_layers = {k: v for k, v in ranges.items()
                        if k in ("F.Cu", "B.Cu", "Edge.Cuts") or
                        (k.startswith("In") and k.endswith(".Cu"))}
    widths = [r["width"] for r in alignment_layers.values() if r["width"] > 0]
    heights = [r["height"] for r in alignment_layers.values() if r["height"] > 0]

    # Use relative threshold: 5% of Edge.Cuts dimension, minimum 2.0mm
    edge = alignment_layers.get("Edge.Cuts")
    threshold_w = max(2.0, edge["width"] * 0.05) if edge and edge["width"] > 0 else 2.0
    threshold_h = max(2.0, edge["height"] * 0.05) if edge and edge["height"] > 0 else 2.0

    aligned = True
    issues = []
    if widths and max(widths) - min(widths) > threshold_w:
        aligned = False
        issues.append(f"Width varies by {max(widths) - min(widths):.1f}mm across copper/edge layers")
    if heights and max(heights) - min(heights) > threshold_h:
        aligned = False
        issues.append(f"Height varies by {max(heights) - min(heights):.1f}mm across copper/edge layers")

    return {"aligned": aligned, "issues": issues, "layer_extents": ranges}


def compute_board_dimensions(gerbers: list[dict], job_info: dict | None) -> dict:
    """Compute board dimensions from .gbrjob or Edge.Cuts extents."""
    if job_info:
        w = job_info.get("board_width_mm", 0)
        h = job_info.get("board_height_mm", 0)
        if w > 0 and h > 0:
            return {"width_mm": round(w, 2), "height_mm": round(h, 2),
                    "area_mm2": round(w * h, 1), "source": "gbrjob"}

    for g in gerbers:
        if g.get("layer_type") == "Edge.Cuts":
            cr = g["coordinate_range"]
            w = cr["x_max"] - cr["x_min"]
            h = cr["y_max"] - cr["y_min"]
            # Convert inches to mm if gerber uses MOIN units
            if g.get("units") == "inch":
                w *= 25.4
                h *= 25.4
            if w > 0 and h > 0:
                return {"width_mm": round(w, 2), "height_mm": round(h, 2),
                        "area_mm2": round(w * h, 1), "source": "edge_cuts_extents"}
    return {}


def build_component_analysis(gerbers: list[dict], drills: list[dict]) -> dict | None:
    """Merge component/net/pin data across all gerber layers.

    Only produces output when X2 TO attributes are present (KiCad 6+).
    """
    all_refs = set()
    front_refs = set()
    back_refs = set()
    all_nets = set()
    all_pins = []
    component_pads = {}
    component_nets = {}
    seen_pins = set()  # dedup (ref, pin) across layers

    for g in gerbers:
        x2o = g.get("x2_objects")
        if not x2o:
            continue

        layer_type = g.get("layer_type", "")
        refs = set(x2o.get("component_refs", []))
        all_refs |= refs

        # Determine component side from mask/silk/paste/copper layers
        if layer_type in ("F.Cu", "F.Mask", "F.SilkS", "F.Paste"):
            front_refs |= refs
        elif layer_type in ("B.Cu", "B.Mask", "B.SilkS", "B.Paste"):
            back_refs |= refs

        all_nets |= set(x2o.get("net_names", []))

        # Merge pads (take max per ref since same pad appears on mask/paste too)
        for ref, count in x2o.get("component_pads", {}).items():
            component_pads[ref] = max(component_pads.get(ref, 0), count)

        # Merge nets per component
        for ref, nets in x2o.get("component_nets", {}).items():
            if ref not in component_nets:
                component_nets[ref] = set()
            component_nets[ref].update(nets)

        # Merge pin mappings (dedup by ref+pin)
        for pm in x2o.get("pin_mappings", []):
            key = (pm["ref"], pm["pin"])
            if key not in seen_pins:
                seen_pins.add(key)
                all_pins.append(pm)

    if not all_refs:
        return None

    # Classify nets
    power_prefixes = ("+", "-")
    power_nets = set()
    signal_nets = set()
    unnamed_nets = 0
    for n in all_nets:
        nl = n.lower()
        if nl in _POWER_KEYWORDS_GERBER or n.startswith(power_prefixes) or nl.startswith("vcc") or nl.startswith("vdd"):
            power_nets.add(n)
        elif n.startswith("Net-(") or n.startswith("unconnected-("):
            unnamed_nets += 1
        else:
            signal_nets.add(n)

    # Components that are only on back
    back_only = back_refs - front_refs

    result = {
        "total_unique": len(all_refs),
        "front_side": len(front_refs),
        "back_side": len(back_only),
        "component_refs": sorted(all_refs),
        "has_x2_data": True,
    }

    if component_pads:
        result["pads_per_component"] = {r: c for r, c in sorted(component_pads.items())}
        result["total_pads"] = sum(component_pads.values())

    return result


def build_net_analysis(gerbers: list[dict]) -> dict | None:
    """Merge net data across copper layers."""
    all_nets = set()
    all_pins = []
    seen_pins = set()

    for g in gerbers:
        x2o = g.get("x2_objects")
        if not x2o:
            continue
        lt = g.get("layer_type", "")
        if not lt.endswith(".Cu"):
            continue  # nets only meaningful from copper layers
        all_nets |= set(x2o.get("net_names", []))
        for pm in x2o.get("pin_mappings", []):
            key = (pm["ref"], pm["pin"])
            if key not in seen_pins:
                seen_pins.add(key)
                all_pins.append(pm)

    if not all_nets:
        return None

    # Classify
    power_nets = []
    signal_nets = []
    unnamed_count = 0
    for n in sorted(all_nets):
        nl = n.lower()
        if (nl in _POWER_KEYWORDS_GERBER or n.startswith(("+", "-"))
                or nl.startswith(("vcc", "vdd", "vss"))):
            power_nets.append(n)
        elif n.startswith("Net-(") or n.startswith("unconnected-("):
            unnamed_count += 1
        else:
            signal_nets.append(n)

    return {
        "total_unique": len(all_nets),
        "named_nets": len(all_nets) - unnamed_count,
        "unnamed_nets": unnamed_count,
        "power_nets": power_nets,
        "signal_nets": signal_nets,
        "total_pins": len(all_pins),
    }


def build_trace_analysis(gerbers: list[dict]) -> dict | None:
    """Extract trace width distribution and minimum feature size across copper layers."""
    conductor_widths = set()
    min_feature = float("inf")

    for g in gerbers:
        aa = g.get("aperture_analysis")
        if not aa:
            continue
        lt = g.get("layer_type", "")
        if not lt.endswith(".Cu"):
            continue
        for w in aa.get("conductor_widths_mm", []):
            conductor_widths.add(w)
        mf = aa.get("min_feature_mm")
        if mf is not None and mf < min_feature:
            min_feature = mf

    if not conductor_widths:
        return None

    widths = sorted(conductor_widths)
    return {
        "unique_widths_mm": widths,
        "min_trace_mm": widths[0],
        "max_trace_mm": widths[-1],
        "width_count": len(widths),
        "min_feature_mm": round(min_feature, 4) if min_feature < float("inf") else None,
    }


def build_pad_summary(gerbers: list[dict], drill_class: dict) -> dict:
    """Summarize pad types across layers: SMD, via, heatsink, THT."""
    smd = 0
    via = 0
    heatsink = 0

    for g in gerbers:
        aa = g.get("aperture_analysis", {})
        # KH-173: prefer by_function_flashes (instance counts) over by_function (unique defs)
        bf = aa.get("by_function_flashes") or aa.get("by_function", {})
        lt = g.get("layer_type", "")
        if not lt.endswith(".Cu"):
            continue
        smd += bf.get("SMDPad", 0)
        via += bf.get("ViaPad", 0)
        heatsink += bf.get("HeatsinkPad", 0)

    # Fallback: when no X2 aperture functions, estimate SMD pad count from
    # paste layer flashes (paste layers only contain SMD pad openings)
    smd_source = "x2_aperture_function"
    if smd == 0:
        paste_flashes = 0
        for g in gerbers:
            lt = g.get("layer_type", "")
            if lt in ("F.Paste", "B.Paste"):
                paste_flashes += g.get("flash_count", 0)
        if paste_flashes > 0:
            smd = paste_flashes
            smd_source = "paste_layer_flashes"

    tht = drill_class.get("component_holes", {}).get("count", 0)

    result = {
        "smd_apertures": smd,
        "via_apertures": via,
        "heatsink_apertures": heatsink,
        "tht_holes": tht,
        "smd_source": smd_source,
        # smd_ratio is a schema-required key; emit 0.0 when nothing to
        # ratio (no SMD pads and no plated holes) so the schema-vs-emit
        # drift can't surface (TH-043).
        "smd_ratio": (round(smd / (smd + tht), 2)
                      if smd + tht > 0 else 0.0),
    }

    return result


# ---------------------------------------------------------------------------
# Zip archive scanning
# ---------------------------------------------------------------------------

_GERBER_EXTENSIONS = frozenset({
    ".gbr", ".gtl", ".gbl", ".gts", ".gbs", ".gtp", ".gbp",
    ".gto", ".gbo", ".gko", ".gm1",
    ".g1", ".g2", ".g3", ".g4",
    ".drl", ".gbrjob",
})


def scan_zip_archives(gerber_dir: Path, loose_gerber_files: list[Path],
                      loose_drill_files: list[Path]) -> list[dict] | None:
    """Scan zip files for gerber/drill contents and compare against loose files.

    Reports each zip's contents, modification time, and how its timestamp
    compares to the loose (unzipped) gerber files. This helps catch stale
    archives that don't reflect the current design, or stale loose files
    left over from an old unzip.
    """
    zip_files = sorted(gerber_dir.glob("*.zip")) + sorted(gerber_dir.glob("*.ZIP"))
    zip_files = sorted(set(zip_files))
    if not zip_files:
        return None

    # Latest mtime among loose gerber/drill files
    loose_files = list(loose_gerber_files) + list(loose_drill_files)
    loose_mtimes = []
    for f in loose_files:
        try:
            loose_mtimes.append(f.stat().st_mtime)
        except OSError:
            pass
    latest_loose_mtime = max(loose_mtimes) if loose_mtimes else None

    results = []
    for zf_path in zip_files:
        entry: dict = {
            "filename": zf_path.name,
            "size_bytes": zf_path.stat().st_size,
        }

        try:
            zf_mtime = zf_path.stat().st_mtime
            entry["modified"] = datetime.fromtimestamp(
                zf_mtime, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
        except OSError:
            zf_mtime = None

        try:
            with zipfile.ZipFile(zf_path, "r") as zf:
                members = zf.namelist()
                gerber_members = []
                drill_members = []
                other_members = []
                for name in members:
                    ext = Path(name).suffix.lower()
                    if ext == ".drl":
                        drill_members.append(name)
                    elif ext in _GERBER_EXTENSIONS:
                        gerber_members.append(name)
                    else:
                        other_members.append(name)

                entry["total_files"] = len(members)
                entry["gerber_files"] = len(gerber_members)
                entry["drill_files"] = len(drill_members)
                entry["other_files"] = len(other_members)

                # Latest file date inside the zip (from zip directory entries)
                latest_inside = None
                for info in zf.infolist():
                    try:
                        dt = datetime(*info.date_time, tzinfo=timezone.utc)
                        ts = dt.timestamp()
                        if latest_inside is None or ts > latest_inside:
                            latest_inside = ts
                    except (ValueError, OSError):
                        pass

                if latest_inside is not None:
                    entry["newest_member_date"] = datetime.fromtimestamp(
                        latest_inside, tz=timezone.utc
                    ).strftime("%Y-%m-%dT%H:%M:%SZ")

                # Compare zip contents date vs loose files
                compare_ts = latest_inside if latest_inside is not None else zf_mtime
                if compare_ts is not None and latest_loose_mtime is not None:
                    delta_seconds = latest_loose_mtime - compare_ts
                    if delta_seconds > 60:
                        entry["vs_loose_files"] = "loose_files_newer"
                        entry["age_delta_hours"] = round(delta_seconds / 3600, 1)
                    elif delta_seconds < -60:
                        entry["vs_loose_files"] = "archive_newer"
                        entry["age_delta_hours"] = round(-delta_seconds / 3600, 1)
                    else:
                        entry["vs_loose_files"] = "same_age"

        except zipfile.BadZipFile:
            entry["error"] = "not a valid zip file"
        except (OSError, ValueError, KeyError, TypeError) as e:
            entry["error"] = str(e)

        results.append(entry)

    return results


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def _is_excellon_file(path: Path) -> bool:
    """Check if a file is likely an Excellon drill file by header inspection."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            head = f.read(1024)
        return "M48" in head or re.search(r"T\d+C\d", head) is not None
    except (OSError, UnicodeDecodeError):
        return False


def analyze_gerbers(directory: str, full: bool = False) -> dict:
    """Main analysis function for a gerber directory."""
    gerber_dir = Path(directory)

    # Find all gerber and drill files
    gerber_files = sorted(gerber_dir.glob("*.gbr")) + sorted(gerber_dir.glob("*.g*"))
    drill_files = sorted(gerber_dir.glob("*.drl"))
    job_files = sorted(gerber_dir.glob("*.gbrjob"))

    # Also pick up uppercase extensions
    for ext in ("*.GBR", "*.GTL", "*.GBL", "*.GTS", "*.GBS", "*.GTO", "*.GBO",
                "*.GKO", "*.GM1", "*.G1", "*.G2", "*.G3", "*.G4",
                "*.G2L", "*.G3L", "*.G4L", "*.G5L", "*.G6L",
                "*.GTP", "*.GBP", "*.DRL"):
        if ext == "*.DRL":
            drill_files.extend(sorted(gerber_dir.glob(ext)))
        else:
            gerber_files.extend(sorted(gerber_dir.glob(ext)))

    # Eagle outputs drill files with .TXT extension — validate header before including
    drill_set = set(drill_files)
    for txt_ext in ("*.TXT", "*.txt"):
        for txt_path in gerber_dir.glob(txt_ext):
            if txt_path not in drill_set and _is_excellon_file(txt_path):
                drill_files.append(txt_path)

    gerber_files = sorted(set(gerber_files))
    gerber_files = [f for f in gerber_files
                    if f.suffix.lower() not in (".drl", ".gbrjob", ".zip", ".pos", ".txt")]
    drill_files = sorted(set(drill_files))

    # Scan zip archives before parsing (uses file lists for timestamp comparison)
    zip_scan = scan_zip_archives(gerber_dir, gerber_files, drill_files)

    # Parse
    gerbers = []
    for gf in gerber_files:
        try:
            gerbers.append(parse_gerber(str(gf)))
        except (OSError, ValueError, UnicodeDecodeError) as e:
            gerbers.append({"file": str(gf), "filename": gf.name, "error": str(e),
                            "layer_type": "unknown"})

    drills = []
    for df in drill_files:
        try:
            drills.append(parse_drill(str(df)))
        except (OSError, ValueError, UnicodeDecodeError) as e:
            drills.append({"file": str(df), "filename": df.name, "error": str(e)})

    job_info = None
    if job_files:
        job_info = parse_job_file(str(job_files[0]))

    # Layer count
    copper_layers = [g for g in gerbers
                     if g.get("layer_type", "").endswith(".Cu") and "error" not in g]
    layer_count = len(copper_layers)
    if job_info and job_info.get("layer_count"):
        layer_count = max(layer_count, job_info["layer_count"])
    for d in drills:
        span = d.get("layer_span")
        if span:
            layer_count = max(layer_count, span[1])
    # Infer layer count from X2 FileFunction Ln designation (e.g., "Copper,L4,Bot")
    for g in gerbers:
        ff = g.get("x2_attributes", {}).get("FileFunction", "")
        ln_match = re.search(r"Copper,L(\d+)", ff, re.IGNORECASE)
        if ln_match:
            layer_count = max(layer_count, int(ln_match.group(1)))

    # Classify drills first — needed by completeness check (KH-184)
    drill_classification = classify_drill_tools(drills)

    # KH-184: Infer PTH from drill classification when type is unknown
    if drill_classification.get("vias", {}).get("count", 0) > 0:
        for d in drills:
            if d.get("type") == "unknown":
                d["type"] = "PTH"

    # Run checks
    completeness = check_completeness(gerbers, drills, job_info)
    alignment = check_alignment(gerbers, drills)
    board_dims = compute_board_dimensions(gerbers, job_info)

    # Higher-level analyses
    component_analysis = build_component_analysis(gerbers, drills)
    net_analysis = build_net_analysis(gerbers)
    trace_analysis = build_trace_analysis(gerbers)
    pad_summary = build_pad_summary(gerbers, drill_classification)

    # Statistics
    total_holes = sum(d.get("hole_count", 0) for d in drills)
    total_flashes = sum(g.get("flash_count", 0) for g in gerbers)
    total_draws = sum(g.get("draw_count", 0) for g in gerbers)

    # Drill tools summary
    all_tools = {}
    for d in drills:
        for tool_name, tool_info in d.get("tools", {}).items():
            key = f"{tool_info['diameter_mm']}mm"
            if key not in all_tools:
                all_tools[key] = {"diameter_mm": tool_info["diameter_mm"],
                                  "count": 0, "type": d.get("type", "")}
            all_tools[key]["count"] += tool_info["hole_count"]

    # Gerber summary (compact — strip raw data)
    gerber_summary = []
    for g in gerbers:
        entry = {
            "filename": g.get("filename", ""),
            "layer_type": g.get("layer_type", "unknown"),
            "units": g.get("units", ""),
            "aperture_count": len(g.get("apertures", {})),
            "flash_count": g.get("flash_count", 0),
            "draw_count": g.get("draw_count", 0),
            "region_count": g.get("region_count", 0),
        }
        x2 = g.get("x2_attributes", {})
        if x2:
            entry["x2_attributes"] = x2
        aa = g.get("aperture_analysis")
        if aa:
            entry["aperture_analysis"] = aa
        # Component/net counts per layer (compact summary)
        x2o = g.get("x2_objects")
        if x2o:
            entry["x2_component_count"] = len(x2o.get("component_refs", []))
            entry["x2_net_count"] = len(x2o.get("net_names", []))
            entry["x2_pin_count"] = len(x2o.get("pin_mappings", []))
        if "error" in g:
            entry["error"] = g["error"]
        gerber_summary.append(entry)

    # Drill summary
    drill_summary = []
    for d in drills:
        entry = {
            "filename": d.get("filename", ""),
            "type": d.get("type", "unknown"),
            "units": d.get("units", ""),
            "hole_count": d.get("hole_count", 0),
            "tools": d.get("tools", {}),
        }
        if d.get("layer_span"):
            entry["layer_span"] = d["layer_span"]
        x2 = d.get("x2_attributes", {})
        if x2:
            entry["x2_attributes"] = x2
        if "error" in d:
            entry["error"] = d["error"]
        drill_summary.append(entry)

    # Generator
    generator = None
    if job_info and job_info.get("generator"):
        generator = job_info["generator"]
    else:
        for g in gerbers:
            gen = g.get("x2_attributes", {}).get("GenerationSoftware", "")
            if gen:
                generator = gen
                break

    result = {
        "analyzer_type": "gerber",
        "schema_version": "1.4.0",
        "directory": str(directory),
        "generator": generator,
        "layer_count": layer_count,
        "board_dimensions": board_dims,
        "statistics": {
            "gerber_files": len(gerbers),
            "drill_files": len(drills),
            "total_holes": total_holes,
            "total_flashes": total_flashes,
            "total_draws": total_draws,
        },
        "completeness": completeness,
        "alignment": alignment,
        "drill_classification": drill_classification,
        "pad_summary": pad_summary,
    }

    if trace_analysis:
        result["trace_widths"] = trace_analysis
    if component_analysis:
        result["component_analysis"] = component_analysis
    if net_analysis:
        result["net_analysis"] = net_analysis

    result["gerbers"] = gerber_summary
    result["drills"] = drill_summary
    result["drill_tools"] = all_tools

    if job_info:
        result["job_file"] = job_info

    if zip_scan:
        result["zip_archives"] = zip_scan

    findings = _build_gerber_findings(
        completeness, alignment, drill_classification,
        gerber_summary, drill_summary, result["statistics"])
    result["findings"] = findings
    result["assessments"] = []

    sev_counts = {}
    for f in findings:
        sev = f.get("severity", "info")
        sev_counts[sev] = sev_counts.get(sev, 0) + 1
    result["summary"] = {
        "total_findings": len(findings),
        "by_severity": {
            "error": sev_counts.get("error", 0),
            "warning": sev_counts.get("warning", 0),
            "info": sev_counts.get("info", 0),
        },
    }
    from finding_schema import compute_trust_summary
    result["trust_summary"] = compute_trust_summary(findings)

    # Full mode: include raw pin-to-net connectivity
    if full and any(g.get("x2_objects") for g in gerbers):
        all_pins = []
        seen = set()
        for g in gerbers:
            x2o = g.get("x2_objects")
            if not x2o:
                continue
            for pm in x2o.get("pin_mappings", []):
                key = (pm["ref"], pm["pin"])
                if key not in seen:
                    seen.add(key)
                    all_pins.append(pm)
        if all_pins:
            result["connectivity"] = sorted(all_pins, key=lambda p: (p["ref"], p["pin"]))

    return result


def _build_gerber_findings(completeness, alignment, drill_classification,
                           gerber_summary, drills, statistics) -> list:
    """Build rich findings from gerber analysis data."""
    findings = []

    # GR-001: Missing layers
    required_layers = {'F.Cu', 'B.Cu', 'Edge.Cuts'}
    if completeness.get('source') == 'gbrjob':
        missing = completeness.get('missing', [])
    else:
        missing = completeness.get('missing_required', []) + completeness.get('missing_recommended', [])
        required_layers.update(completeness.get('missing_required', []))

    for layer in missing:
        is_required = layer in required_layers
        findings.append({
            'detector': 'analyze_gerbers',
            'rule_id': 'GR-001',
            'category': 'gerber_completeness',
            'severity': 'warning' if is_required else 'info',
            'confidence': 'deterministic',
            'evidence_source': 'topology',
            'summary': f'Missing layer: {layer}',
            'description': f'Expected {"required" if is_required else "recommended"} layer {layer} not found in gerber set.',
            'components': [],
            'nets': [],
            'pins': [],
            'recommendation': f'Add {layer} to gerber export.',
            'report_context': {'section': 'Gerber Completeness', 'impact': 'Fab may reject' if is_required else 'Assembly quality', 'standard_ref': ''},
        })

    # GR-003: Missing or empty drill file
    has_drill = statistics.get('drill_files', 0) > 0
    if not has_drill:
        findings.append({
            'detector': 'analyze_gerbers',
            'rule_id': 'GR-003',
            'category': 'gerber_completeness',
            'severity': 'warning',
            'confidence': 'deterministic',
            'evidence_source': 'topology',
            'summary': 'No drill file in gerber set',
            'description': 'No Excellon drill file found. PCB fabrication requires drill data.',
            'components': [],
            'nets': [],
            'pins': [],
            'recommendation': 'Include drill file(s) in gerber export.',
            'report_context': {'section': 'Gerber Completeness', 'impact': 'Fab will reject', 'standard_ref': ''},
        })
    elif statistics.get('total_holes', 0) == 0:
        findings.append({
            'detector': 'analyze_gerbers',
            'rule_id': 'GR-003',
            'category': 'gerber_completeness',
            'severity': 'info',
            'confidence': 'deterministic',
            'evidence_source': 'topology',
            'summary': 'Drill file has 0 holes',
            'description': 'Drill file present but contains no hole definitions.',
            'components': [],
            'nets': [],
            'pins': [],
            'recommendation': 'Verify drill file was exported correctly.',
            'report_context': {'section': 'Gerber Completeness', 'impact': '', 'standard_ref': ''},
        })

    # GR-002: Alignment issues
    for issue in alignment.get('issues', []):
        findings.append({
            'detector': 'analyze_gerbers',
            'rule_id': 'GR-002',
            'category': 'gerber_alignment',
            'severity': 'warning',
            'confidence': 'deterministic',
            'evidence_source': 'topology',
            'summary': f'Alignment: {issue}',
            'description': f'Layer alignment issue: {issue}',
            'components': [],
            'nets': [],
            'pins': [],
            'recommendation': 'Re-export gerbers to ensure consistent layer alignment.',
            'report_context': {'section': 'Gerber Alignment', 'impact': 'Layer misregistration', 'standard_ref': ''},
        })

    # GR-004: Solder paste aperture mismatch
    # Compare flash counts between paste and copper layers
    paste_flashes = {}
    copper_flashes = {}
    for g in gerber_summary:
        lt = g.get('layer_type', '')
        flashes = g.get('flash_count', 0)
        if 'Paste' in lt and flashes > 0:
            side = 'F' if lt.startswith('F') else 'B'
            paste_flashes[side] = paste_flashes.get(side, 0) + flashes
        elif '.Cu' in lt and (lt.startswith('F.') or lt.startswith('B.')):
            side = 'F' if lt.startswith('F') else 'B'
            copper_flashes[side] = copper_flashes.get(side, 0) + flashes

    for side in paste_flashes:
        p_count = paste_flashes[side]
        c_count = copper_flashes.get(side, 0)
        if c_count > 0 and p_count < c_count * 0.5:
            ratio = p_count / c_count * 100
            findings.append({
                'detector': 'analyze_gerbers',
                'rule_id': 'GR-004',
                'category': 'gerber_completeness',
                'severity': 'warning',
                'confidence': 'heuristic',
                'evidence_source': 'topology',
                'summary': f'{side} paste layer: {p_count} flashes vs {c_count} copper ({ratio:.0f}%)',
                'description': f'{side}-side paste layer has significantly fewer flashes ({p_count}) than copper layer ({c_count}). This may indicate missing solder paste apertures.',
                'components': [],
                'nets': [],
                'pins': [],
                'recommendation': 'Check solder paste aperture generation — missing apertures cause assembly defects.',
                'report_context': {'section': 'Gerber Completeness', 'impact': 'Assembly solder joint quality', 'standard_ref': ''},
            })

    # GR-005: Board outline not closed (heuristic)
    # Check if Edge.Cuts layer exists and has reasonable draw count
    edge_layer = None
    for g in gerber_summary:
        if g.get('layer_type', '') == 'Edge.Cuts':
            edge_layer = g
            break
    if edge_layer:
        draws = edge_layer.get('draw_count', 0)
        if draws > 0 and draws < 4:
            findings.append({
                'detector': 'analyze_gerbers',
                'rule_id': 'GR-005',
                'category': 'gerber_completeness',
                'severity': 'error',
                'confidence': 'heuristic',
                'evidence_source': 'topology',
                'summary': f'Board outline may not be closed — only {draws} draw(s)',
                'description': f'Edge.Cuts layer has only {draws} draw command(s). A closed rectangular outline needs at least 4. The outline may be incomplete.',
                'components': [],
                'nets': [],
                'pins': [],
                'recommendation': 'Verify board outline forms a closed shape before submitting to fab.',
                'report_context': {'section': 'Gerber Completeness', 'impact': 'Fab will reject open outlines', 'standard_ref': ''},
            })
    elif completeness.get('complete', True) is False:
        # Edge.Cuts missing entirely — already covered by GR-001
        pass

    return findings


def main():
    import argparse
    parser = argparse.ArgumentParser(description="KiCad Gerber & Drill File Analyzer")
    parser.add_argument("directory", nargs="?", help="Path to gerber/drill file directory")
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")
    parser.add_argument("--analysis-dir",
                        help="Write gerbers.json to this directory (analysis folder convention)")
    parser.add_argument("--compact", action="store_true", help="Compact JSON output")
    parser.add_argument("--full", action="store_true",
                        help="Include full pin-to-net connectivity data")
    parser.add_argument("--text", action="store_true",
                        help="Print human-readable text summary")
    parser.add_argument("--schema", action="store_true",
                        help="Print JSON output schema and exit")
    parser.add_argument('--stage', default=None,
                        choices=['schematic', 'layout', 'pre_fab', 'bring_up'],
                        help='Filter findings by review stage')
    parser.add_argument('--audience', default=None,
                        choices=['designer', 'reviewer', 'manager'],
                        help='Audience level for summaries and --text output')
    parser.add_argument('--only-deterministic', action='store_true',
                        help='Accepted for consistency; analyzers never write llm_* fields. '
                             'Honored by downstream consumers (Phase 4 spec §3.4).')
    args = parser.parse_args()

    if args.schema:
        emit_schema(GerberEnvelope)

    if not args.directory:
        parser.error("the following arguments are required: directory")

    # Build inputs provenance block (Track 1.3). Walk the gerber directory
    # and hash every gerber/drill/job file present.
    _gerber_dir = Path(args.directory)
    _gerber_exts = {".gbr", ".gbl", ".gtl", ".gbs", ".gts",
                    ".gbo", ".gto", ".gm1", ".gko", ".drl",
                    ".xln", ".nc",
                    ".g1", ".g2", ".g3", ".g4",
                    ".g2l", ".g3l", ".g4l", ".g5l", ".g6l",
                    ".gtp", ".gbp"}
    _gerber_files = []
    if _gerber_dir.is_dir():
        for p in sorted(_gerber_dir.iterdir()):
            if not p.is_file():
                continue
            if p.suffix.lower() in _gerber_exts or p.name.lower().endswith(".gbrjob"):
                _gerber_files.append(p)
            elif p.suffix.lower() == ".txt" and _is_excellon_file(p):
                _gerber_files.append(p)
    # Resolve canonical analysis_dir ONCE (audit Highest-Risk #4).
    if args.analysis_dir:
        _analysis_dir = Path(args.analysis_dir)
    elif args.output:
        _analysis_dir = Path(args.output).parent
    else:
        _analysis_dir = Path("analysis")

    # Resolve capability_mode_ref BEFORE build_inputs (audit Highest-Risk #5).
    _capability_mode_ref = get_capability_mode_ref(_analysis_dir)

    inputs = build_inputs(
        source_files=_gerber_files,
        run_id=_capability_mode_ref["run_id"],
    )
    compat = build_compat()

    result = analyze_gerbers(args.directory, full=args.full)
    # Inject provenance.
    result["inputs"] = inputs
    result["compat"] = compat

    from output_filters import apply_output_filters
    apply_output_filters(result, args.stage, args.audience)

    # Guarantee every finding carries a stable finding_id (Layer 2 merge keys
    # on it). Runs after filtering; before any output branch.
    from finding_schema import assign_finding_ids
    assign_finding_ids(result.get("findings", []), "gerber")

    # Wire capability_mode_ref (Phase 4 spec §3.3). Resolved early so
    # inputs.run_id and capability_mode_ref.run_id match.
    result["capability_mode_ref"] = _capability_mode_ref

    # Determine output path
    output_path = args.output
    indent = None if args.compact else 2
    output_json = json.dumps(result, indent=indent, default=str)

    if not output_path and args.analysis_dir:
        # Route into the current run folder via the manifest. Use the
        # canonical filename (gerber.json) so the manifest tracks it.
        import tempfile
        from analysis_cache import overwrite_current, CANONICAL_OUTPUTS, get_current_run
        analysis_dir = args.analysis_dir
        if not os.path.isabs(analysis_dir):
            analysis_dir = os.path.abspath(analysis_dir)
        filename = CANONICAL_OUTPUTS.get('gerber', 'gerber.json')
        with tempfile.TemporaryDirectory() as tmp_dir:
            Path(os.path.join(tmp_dir, filename)).write_text(output_json)
            overwrite_current(analysis_dir, tmp_dir, source_hashes=None)
        current = get_current_run(analysis_dir)
        if current:
            out_path = os.path.join(current[0], filename)
        else:
            out_path = os.path.join(analysis_dir, filename)
        print(f"Written to {out_path}", file=sys.stderr)
    elif output_path:
        Path(output_path).write_text(output_json)
        print(f"Written to {output_path}", file=sys.stderr)
    elif args.text:
        from output_filters import format_text
        print(format_text(result.get('findings', []), args.audience or 'designer', args.stage))
    else:
        print(output_json)


if __name__ == "__main__":
    main()
