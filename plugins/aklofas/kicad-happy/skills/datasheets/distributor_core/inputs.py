"""Distributor sync inputs: BOM projection, MPN-list reading, analyzer output.
Reads the analyzer BOM or an MPN list; id_keys sets the per-provider identifier keys
(their order is the dict-key order of each part)."""

import json
import re
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# MPN filtering — distinguish real manufacturer part numbers from generic values
# ---------------------------------------------------------------------------

# Matches generic passive values that someone typed into the MPN field
_GENERIC_VALUE_RE = re.compile(
    r"^[\d.]+\s*[pnuμmkMGR]?[FHΩRfhω]?$"    # 100nF, 10K, 4.7uF, 100R
    r"|^[\d.]+\s*[kKmM]?[Ωω]?$"               # 10K, 4.7k
    r"|^[\d.]+\s*[pnuμm]?[Ff]$"               # 100pF, 10uF
    r"|^[\d.]+\s*[pnuμm]?[Hh]$"               # 10uH
    r"|^[\d.]+%$"                               # 1%
    r"|^DNP$|^NC$|^N/?A$",
    re.IGNORECASE,
)


# Component types that never have useful datasheets
_SKIP_TYPES = {
    "test_point", "mounting_hole", "fiducial", "graphic",
    "jumper", "net_tie", "mechanical",
}


def is_real_mpn(mpn: str) -> bool:
    """Return True if the string looks like a real manufacturer part number."""
    mpn = mpn.strip()
    if not mpn or len(mpn) < 3:
        return False
    if _GENERIC_VALUE_RE.match(mpn):
        return False
    has_letter = any(c.isalpha() for c in mpn)
    has_digit = any(c.isdigit() for c in mpn)
    return has_letter and has_digit


# ---------------------------------------------------------------------------
# Schematic analysis — run analyzer or load pre-computed JSON
# ---------------------------------------------------------------------------

def get_analyzer_output(input_path: Path) -> dict | None:
    """Get analyzer output, either by running the analyzer or loading JSON."""
    if input_path.suffix == ".json":
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            print(f"Error: cannot read {input_path}: {e}", file=sys.stderr)
            return None
        if not isinstance(data, dict):
            print(f"Error: {input_path} is not analyzer output (a JSON object)", file=sys.stderr)
            return None
        bom = data.get("bom", [])
        if not isinstance(bom, list) or not all(isinstance(e, dict) for e in bom):
            print(f"Error: {input_path}: 'bom' is not a list of objects", file=sys.stderr)
            return None
        return data

    if input_path.suffix in (".kicad_sch", ".sch"):
        # Try importing the analyzer directly
        # The path insert resolves skills/kicad/scripts relative to this file.
        kicad_scripts = Path(__file__).resolve().parent.parent.parent / "kicad" / "scripts"
        if kicad_scripts.exists():
            sys.path.insert(0, str(kicad_scripts))
            try:
                from schematic.pipeline import analyze_schematic
                return analyze_schematic(str(input_path))
            except Exception as e:
                print(f"  Analyzer import failed ({e}), trying subprocess...",
                      file=sys.stderr)

        # Fall back to subprocess
        analyzer = kicad_scripts / "analyze_schematic.py"
        if not analyzer.exists():
            print(f"Error: Cannot find analyze_schematic.py at {analyzer}",
                  file=sys.stderr)
            return None
        try:
            result = subprocess.run(
                [sys.executable, str(analyzer), str(input_path), "--compact"],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                print(f"Error: Analyzer failed: {result.stderr[:500]}",
                      file=sys.stderr)
                return None
            return json.loads(result.stdout)
        except Exception as e:
            print(f"Error: Failed to run analyzer: {e}", file=sys.stderr)
            return None

    print(f"Error: Unsupported input file type: {input_path.suffix}",
          file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# MPN extraction from BOM
# ---------------------------------------------------------------------------

def _str(v) -> str:
    return v if isinstance(v, str) else ""


def _text(v) -> str:
    return v.strip() if isinstance(v, str) else ""


def extract_parts(analyzer_output: dict, id_keys=("digikey", "mouser", "lcsc"), search_key=None) -> list[dict]:
    """Extract unique parts with real MPNs or distributor PNs from analyzer BOM output.

    A part is included if it has at least one of: a real MPN, a DigiKey PN,
    a Mouser PN, or an LCSC PN. Users set up their KiCad projects differently —
    some only have MPNs, some only have distributor PNs, some have both.

    ``search_key`` names the distributor doing the searching: the Value fallback applies when
    the part has no real MPN and no number for that distributor (any ``id_keys`` number when
    None), since another distributor's number is no query for it.
    """
    bom = analyzer_output.get("bom", [])
    parts = []

    for entry in bom:
        if entry.get("dnp"):
            continue
        if _str(entry.get("type")) in _SKIP_TYPES:
            continue

        mpn = _text(entry.get("mpn"))
        ids = {k: _text(entry.get(k)) for k in id_keys}

        # Need at least one identifier to search for a datasheet
        has_mpn = is_real_mpn(mpn)
        has_distributor_pn = any(ids.values())
        # Fall back to Value field when MPN is empty but the Value
        # looks MPN-shaped (and the symbol isn't a generic Device:R/C/L
        # passive). Common pattern — many KiCad library symbols put the
        # MPN string in the Value field and leave the MPN property empty.
        from_value = False
        searchable_pn = bool(ids.get(search_key)) if search_key else has_distributor_pn
        if not has_mpn and not searchable_pn:
            value = _text(entry.get("value"))
            lib_id = _str(entry.get("lib_id"))
            if is_real_mpn(value) and not lib_id.startswith("Device:"):
                from_value = True
                mpn = value
                has_mpn = True
        if not has_mpn and not has_distributor_pn:
            continue

        refs = entry.get("references")
        refs = refs if isinstance(refs, list) else []
        parts.append({
            "mpn": mpn if has_mpn else "",
            "manufacturer": _str(entry.get("manufacturer")),
            "value": _str(entry.get("value")),
            "description": _str(entry.get("description")),
            "datasheet": _str(entry.get("datasheet")),
            "references": [r for r in refs if isinstance(r, str)],
            "type": _str(entry.get("type")),
            "mpn_source": "value" if from_value else "",
            **{k: ids[k] for k in id_keys},
        })

    return parts


def mpn_from_value(part: dict) -> bool:
    """True when the part's MPN was read from the symbol's Value field (a name that may cover a
    whole family, such as ``LM358``) rather than from an MPN property or an MPN list."""
    return part.get("mpn_source") == "value"


def load_mpn_list(path: Path, id_keys=("digikey", "mouser", "lcsc")) -> list[dict]:
    """Read MPNs from a text file, one per line.

    Skips blank lines, full-line comments (``# ...``), and inline
    ``# ...`` comments. Filters non-MPN strings via ``is_real_mpn()``
    and de-duplicates. Returns minimal part dicts compatible with
    ``extract_parts()`` output — distributor PN fields are empty since
    MPN-list mode drives searches via MPN lookup only.

    Intended for batch workflows (harness, bulk datasheet seeding)
    that don't have a KiCad project to point at.

    Note: MPNs containing a literal ``#`` character are not supported
    (they would be silently truncated by the inline-comment stripper).
    Use the positional schematic/JSON input for such parts instead.
    """
    parts: list[dict] = []
    seen: set[str] = set()
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            # Strip inline comments
            if "#" in line:
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue
            if not is_real_mpn(line):
                print(f"  Skipping '{line}': doesn't look like a real MPN",
                      file=sys.stderr)
                continue
            if line in seen:
                continue
            seen.add(line)
            parts.append({
                "mpn": line,
                "manufacturer": "",
                "value": "",
                "description": "",
                "datasheet": "",
                "references": [],
                "type": "",
                **{k: "" for k in id_keys},
            })
    return parts
