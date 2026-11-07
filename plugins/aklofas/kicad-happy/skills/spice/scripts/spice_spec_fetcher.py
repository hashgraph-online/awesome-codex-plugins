"""
Fetch component parametric specs from distributor APIs and datasheet PDFs.

Tier 2 (API) and Tier 3 (datasheet) model resolution. Queries LCSC (no auth),
DigiKey (OAuth), element14 (API key), and Mouser (API key) for opamp-relevant
parametric data. Falls back to datasheet PDF extraction when API specs are
insufficient.

All network calls are optional — if no API credentials are available or the
part isn't found, returns None and the cascade falls through to the lookup
table.
"""

import json
import math
import os
import re
import urllib.request
import urllib.error
import urllib.parse

import _core_path  # noqa: F401
from kicad_core import token_cache
from kicad_core.diagnostics import record
from kicad_core.executables import find_executable
from distributor_core.verify import same_part


# ---------------------------------------------------------------------------
# Parametric field mapping — each distributor uses different names
# Maps distributor-specific parameter names to our standard spec keys
# ---------------------------------------------------------------------------

# Common parameter name patterns across distributors (case-insensitive matching)
_OPAMP_PARAM_MAP = [
    # (regex pattern on param name, our spec key, unit conversion)
    (r"gain.?bandwidth|gbw|gbp", "gbw_hz", "_freq"),
    (r"slew.?rate", "slew_vus", "_slew"),
    (r"input.?offset.?volt", "vos_mv", "_voltage_mv"),
    (r"voltage.?supply.*single|supply.?voltage|operating.?voltage", "_supply_range", "_voltage_range"),
    (r"current.?output|output.?current", "iout_ma", "_current_ma"),
    (r"input.?impedance|input.?resistance", "rin_ohms", "_resistance"),
    (r"rail.?to.?rail|rrio|rro", "_rro_flag", "_bool"),
    (r"open.?loop.?gain|voltage.?gain|aol|avol", "aol_db", "_db"),
    (r"3.?db.?bandwidth|bandwidth.*3db|-3db|unity.?gain", "gbw_hz", "_freq"),
    (r"number.?of.?channels|channels", "_channels", "_int"),
]

_LDO_PARAM_MAP = [
    (r"output.?voltage|vout", "_vout", "_voltage"),
    (r"dropout|vdo", "dropout_mv", "_voltage_mv"),
    (r"quiescent.?current|iq|ground.?current", "iq_ua", "_current_ua"),
    (r"output.?current|iout|current.?output", "iout_max_ma", "_current_ma"),
]


def _parse_value_with_unit(text, conversion):
    """Parse a parametric value string into a float with unit conversion.

    Args:
        text: Value string like "1MHz", "0.3V/µs", "2mV", "3V ~ 32V"
        conversion: Conversion type string

    Returns:
        Float in our standard units, or None
    """
    if not text:
        return None
    text = text.strip()

    if conversion == "_freq":
        # Parse frequency: "1MHz", "3.5 MHz", "350kHz", "1GHz"
        m = re.search(r'([\d.]+)\s*(GHz|MHz|kHz|Hz)', text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            unit = m.group(2).lower()
            mult = {"ghz": 1e9, "mhz": 1e6, "khz": 1e3, "hz": 1}
            return val * mult.get(unit, 1)

    elif conversion == "_slew":
        # Parse slew rate: "0.3V/µs", "13 V/us", "1350V/µs"
        m = re.search(r'([\d.]+)\s*V/?[µu]?s', text, re.IGNORECASE)
        if m:
            return float(m.group(1))

    elif conversion == "_voltage_mv":
        # Parse voltage in mV: "2mV", "0.075mV", "150µV"
        m = re.search(r'([\d.]+)\s*(mV|µV|uV|V)', text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            unit = m.group(2).lower()
            if unit == "v":
                return val * 1000
            elif unit in ("µv", "uv"):
                return val / 1000
            return val  # already mV

    elif conversion == "_voltage":
        # Parse voltage: "3.3V", "5V", "1.8V"
        m = re.search(r'([\d.]+)\s*V', text, re.IGNORECASE)
        if m:
            return float(m.group(1))

    elif conversion == "_voltage_range":
        # Parse range: "3V ~ 32V", "2.7V to 5.5V"
        m = re.findall(r'([\d.]+)\s*V', text)
        if len(m) >= 2:
            return (float(m[0]), float(m[-1]))  # (min, max)
        elif len(m) == 1:
            return float(m[0])

    elif conversion == "_current_ma":
        # Parse current in mA: "150mA", "1A", "500µA"
        m = re.search(r'([\d.]+)\s*(A|mA|µA|uA)', text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            unit = m.group(2).lower()
            if unit == "a":
                return val * 1000
            elif unit in ("µa", "ua"):
                return val / 1000
            return val  # already mA

    elif conversion == "_current_ua":
        m = re.search(r'([\d.]+)\s*(A|mA|µA|uA)', text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            unit = m.group(2).lower()
            if unit == "a":
                return val * 1e6
            elif unit == "ma":
                return val * 1000
            return val  # already µA

    elif conversion == "_resistance":
        m = re.search(r'([\d.]+)\s*(TΩ|GΩ|MΩ|kΩ|Ω|Tohm|Gohm|Mohm|kohm|ohm)', text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            unit = m.group(2).lower().replace("ω", "ohm")
            mult = {"tohm": 1e12, "gohm": 1e9, "mohm": 1e6, "kohm": 1e3, "ohm": 1}
            return val * mult.get(unit, 1)

    elif conversion == "_db":
        m = re.search(r'([\d.]+)\s*d[Bb]', text)
        if m:
            return float(m.group(1))

    elif conversion == "_bool":
        return text.lower() in ("yes", "true", "1", "rail-to-rail")

    elif conversion == "_int":
        m = re.search(r'(\d+)', text)
        if m:
            return int(m.group(1))

    return None


def _extract_specs_from_params(params, param_map):
    """Extract specs from a list of (name, value) parameter pairs.

    Args:
        params: List of (param_name_str, param_value_str) tuples
        param_map: List of (regex, spec_key, conversion) tuples

    Returns:
        Dict of extracted specs
    """
    specs = {}
    for param_name, param_value in params:
        if not param_name or not param_value:
            continue
        pname_lower = param_name.lower()
        for pattern, spec_key, conversion in param_map:
            if re.search(pattern, pname_lower):
                val = _parse_value_with_unit(param_value, conversion)
                if val is not None:
                    if spec_key == "_supply_range" and isinstance(val, tuple):
                        specs["supply_min"] = val[0]
                        specs["supply_max"] = val[1]
                    elif spec_key == "_rro_flag":
                        specs["rro"] = bool(val)
                    elif spec_key == "_channels":
                        pass  # Not used for model generation
                    elif spec_key.startswith("_"):
                        pass  # Internal, skip
                    else:
                        specs[spec_key] = val
                break
    return specs


# ---------------------------------------------------------------------------
# LCSC / jlcsearch (no auth required)
# ---------------------------------------------------------------------------

def _is_requested(mpn, hit):
    """True when a distributor's part number is the requested one (an exact match)."""
    return isinstance(hit, str) and same_part(mpn, hit, ordering_suffixes=False)


def fetch_specs_lcsc(mpn):
    """Query LCSC (jlcsearch) for parametric specs. No auth needed.

    Returns:
        specs dict or None
    """
    try:
        url = f"https://jlcsearch.tscircuit.com/api/search?q={urllib.parse.quote(mpn)}&limit=5&full=true"
        req = urllib.request.Request(url, headers={"User-Agent": "kicad-happy-spice/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        for comp in data.get("components", []):
            extra = comp.get("extra", {})
            comp_mpn = extra.get("mpn", "")
            if not _is_requested(mpn, comp_mpn):
                continue

            attrs = extra.get("attributes", {})
            if not attrs:
                continue

            params = [(k, v) for k, v in attrs.items()]
            specs = _extract_specs_from_params(params, _OPAMP_PARAM_MAP)

            # Need at least GBW to be useful for an opamp model
            if specs.get("gbw_hz"):
                specs["_source"] = "api:lcsc"
                return specs

            # Try LDO params
            specs = _extract_specs_from_params(params, _LDO_PARAM_MAP)
            if specs.get("dropout_mv") or specs.get("iout_max_ma"):
                specs["_source"] = "api:lcsc"
                return specs

    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError):
        pass
    return None


# ---------------------------------------------------------------------------
# DigiKey (OAuth 2.0)
# ---------------------------------------------------------------------------

def _get_digikey_token():
    """Get DigiKey OAuth token using client credentials flow.

    Returns:
        access_token string or None
    """
    client_id = os.environ.get("DIGIKEY_CLIENT_ID")
    client_secret = os.environ.get("DIGIKEY_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None

    cached = token_cache.load_token("digikey_token", client_id)
    if cached:
        return cached

    try:
        data = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        }).encode()
        req = urllib.request.Request(
            "https://api.digikey.com/v1/oauth2/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            token_data = json.loads(resp.read())

        access_token = token_data["access_token"]
        # Cache with 9-minute TTL (token valid for 10 min)
        token_cache.store_token("digikey_token", client_id, access_token, 540)
        return access_token
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError):
        return None


def fetch_specs_digikey(mpn):
    """Query DigiKey API for parametric specs.

    Returns:
        specs dict or None
    """
    token = _get_digikey_token()
    if not token:
        return None

    client_id = os.environ.get("DIGIKEY_CLIENT_ID", "")

    try:
        body = json.dumps({"Keywords": mpn, "Limit": 5}).encode()
        req = urllib.request.Request(
            "https://api.digikey.com/products/v4/search/keyword",
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "X-DIGIKEY-Client-Id": client_id,
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        for product in data.get("Products", []):
            prod_mpn = product.get("ManufacturerProductNumber", "")
            if not _is_requested(mpn, prod_mpn):
                continue

            parameters = product.get("Parameters", [])
            if not parameters:
                continue

            params = [(p.get("ParameterText", ""), p.get("ValueText", ""))
                      for p in parameters]
            specs = _extract_specs_from_params(params, _OPAMP_PARAM_MAP)
            if specs.get("gbw_hz"):
                specs["_source"] = "api:digikey"
                return specs

            specs = _extract_specs_from_params(params, _LDO_PARAM_MAP)
            if specs.get("dropout_mv") or specs.get("iout_max_ma"):
                specs["_source"] = "api:digikey"
                return specs

    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError):
        pass
    return None


# ---------------------------------------------------------------------------
# element14 / Newark / Farnell (simple API key)
# ---------------------------------------------------------------------------

def fetch_specs_element14(mpn):
    """Query element14 API for parametric specs.

    Returns:
        specs dict or None
    """
    api_key = os.environ.get("ELEMENT14_API_KEY")
    if not api_key:
        return None

    try:
        params = urllib.parse.urlencode({
            "callInfo.apiKey": api_key,
            "term": f"manuPartNum:{mpn}",
            "storeInfo.id": "us.newark.com",
            "resultsSettings.offset": 0,
            "resultsSettings.numberOfResults": 5,
            "resultsSettings.responseGroup": "medium",
        })
        url = f"https://api.element14.com/catalog/products?{params}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        products = data.get("manufacturerPartNumberSearchReturn", {}).get("products", [])
        for product in products:
            if not _is_requested(mpn, product.get("translatedManufacturerPartNumber")):
                continue
            attrs = product.get("attributes", [])
            if not attrs:
                continue
            params_list = [(a.get("attributeLabel", ""), a.get("attributeValue", ""))
                           for a in attrs]
            specs = _extract_specs_from_params(params_list, _OPAMP_PARAM_MAP)
            if specs.get("gbw_hz"):
                specs["_source"] = "api:element14"
                return specs

    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError):
        pass
    return None


# ---------------------------------------------------------------------------
# Mouser (simple API key)
# ---------------------------------------------------------------------------

def fetch_specs_mouser(mpn):
    """Query Mouser API for parametric specs.

    Returns:
        specs dict or None
    """
    api_key = os.environ.get("MOUSER_SEARCH_API_KEY") or os.environ.get("MOUSER_PART_API_KEY")
    if not api_key:
        return None

    try:
        body = json.dumps({
            "SearchByPartRequest": {
                "mouserPartNumber": mpn,
                "partSearchOptions": ""
            }
        }).encode()
        url = f"https://api.mouser.com/api/v1/search/partnumber?apiKey={api_key}"
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        for part in data.get("SearchResults", {}).get("Parts", []):
            if not _is_requested(mpn, part.get("ManufacturerPartNumber")):
                continue
            attrs = part.get("ProductAttributes", [])
            if not attrs:
                continue
            params = [(a.get("AttributeName", ""), a.get("AttributeValue", ""))
                      for a in attrs]
            specs = _extract_specs_from_params(params, _OPAMP_PARAM_MAP)
            if specs.get("gbw_hz"):
                specs["_source"] = "api:mouser"
                return specs

    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError):
        pass
    return None


# ---------------------------------------------------------------------------
# Datasheet PDF spec extraction (Tier 3)
# ---------------------------------------------------------------------------

def fetch_specs_from_datasheet(mpn, project_dir):
    """Extract specs from a downloaded datasheet PDF.

    Looks for the datasheet in <project_dir>/datasheets/ using the
    manifest.json file (legacy index.json still supported). If found, reads
    the PDF and extracts electrical specs from the first few pages.

    This is a text-based heuristic extraction — not AI-powered. It looks for
    common datasheet table patterns like "Gain Bandwidth Product ... 1 ... MHz"
    and extracts the numeric values.

    Args:
        mpn: Part number to look up
        project_dir: Path to the KiCad project directory

    Returns:
        specs dict or None
    """
    if not project_dir:
        return None

    from pathlib import Path
    from datasheet_types.cache_reader import read_json_object
    from distributor_core.manifest import manifest_file_path
    ds_dir = Path(project_dir) / "datasheets"
    if ds_dir.is_symlink():
        return None
    index_path = ds_dir / "manifest.json"
    if not index_path.exists():
        index_path = ds_dir / "index.json"
    index = read_json_object(index_path)
    if index is None:
        return None

    # Look up MPN in index
    parts = index.get("parts")
    if not isinstance(parts, dict):
        return None
    entry = parts.get(mpn)
    if not entry:
        # Try case-insensitive match
        for key, val in parts.items():
            if key.upper() == mpn.upper():
                entry = val
                break
    if not isinstance(entry, dict) or entry.get("status") != "ok":
        return None

    pdf_path = manifest_file_path(ds_dir, entry.get("file"))
    if pdf_path is None or not pdf_path.is_file():
        return None

    # Try to extract text from PDF using pdftotext (optional dependency)
    tool = find_executable("pdftotext")
    if not tool:
        return None  # Can't extract without pdftotext

    import subprocess
    try:
        # Extract first 5 pages (electrical specs are usually in pages 2-5)
        result = subprocess.run(
            [tool, "-l", "5", str(pdf_path), "-"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
        )
        if result.returncode != 0:
            return None
        text = result.stdout
    except (subprocess.TimeoutExpired, OSError):
        return None

    if not text or len(text) < 100:
        return None

    # Heuristic extraction: look for common spec patterns
    specs = {}
    text_lower = text.lower()

    # GBW: "Gain Bandwidth Product ... 1 ... MHz" or "GBW ... 10 ... MHz"
    for pattern in [
        r'gain[- ]?bandwidth[- ]?product[^0-9]*?([\d.]+)\s*(MHz|kHz|GHz)',
        r'GBW[^0-9]*?([\d.]+)\s*(MHz|kHz|GHz)',
        r'unity[- ]?gain[- ]?bandwidth[^0-9]*?([\d.]+)\s*(MHz|kHz|GHz)',
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            unit = m.group(2).lower()
            mult = {"ghz": 1e9, "mhz": 1e6, "khz": 1e3}
            specs["gbw_hz"] = val * mult.get(unit, 1e6)
            break

    # Slew rate: "Slew Rate ... 0.3 ... V/µs"
    m = re.search(r'slew\s+rate[^0-9]*?([\d.]+)\s*V/[µu]?s', text, re.IGNORECASE)
    if m:
        specs["slew_vus"] = float(m.group(1))

    # Input offset: "Input Offset Voltage ... 2 ... mV"
    m = re.search(r'input\s+offset\s+voltage[^0-9]*?([\d.]+)\s*(mV|µV|uV)', text, re.IGNORECASE)
    if m:
        val = float(m.group(1))
        unit = m.group(2).lower()
        specs["vos_mv"] = val if "mv" in unit else val / 1000

    # Open-loop gain: "Open Loop Gain ... 100 ... dB"
    m = re.search(r'open[- ]?loop\s+(?:voltage\s+)?gain[^0-9]*?([\d.]+)\s*dB', text, re.IGNORECASE)
    if m:
        specs["aol_db"] = float(m.group(1))

    if specs.get("gbw_hz"):
        specs["_source"] = "datasheet:" + mpn
        return specs

    return None


# ---------------------------------------------------------------------------
# Unified fetch interface
# ---------------------------------------------------------------------------

_NUMERIC_SPECS = frozenset((
    "gbw_hz", "slew_vus", "vos_mv", "aol_db", "rin_ohms", "supply_min", "supply_max",
    "swing_v", "dropout_mv", "iq_ua", "iout_max_ma", "vref", "zout_ohms", "prop_delay_ns",
))
_BOOLEAN_SPECS = frozenset(("rro", "rri", "fixed"))
_OUTPUT_TYPES = frozenset(("push_pull", "open_collector", "open_drain"))


def _read_spice_specs(raw):
    """Keep only the spec values the model generators can use safely.

    Numbers must be finite JSON numbers, flags real JSON booleans, and the
    comparator output type one of its known names; anything else is dropped.
    """
    specs = {}
    for key, val in (raw.items() if isinstance(raw, dict) else ()):
        if key in _NUMERIC_SPECS:
            if isinstance(val, (int, float)) and not isinstance(val, bool) \
                    and math.isfinite(val):
                specs[key] = val
        elif key in _BOOLEAN_SPECS:
            if isinstance(val, bool):
                specs[key] = val
        elif key == "output_type" and val in _OUTPUT_TYPES:
            specs[key] = val
    return specs


def fetch_specs_from_extraction(mpn, project_dir):
    """Extract SPICE-relevant specs from a cached datasheet extraction."""
    if not project_dir:
        return None
    from pathlib import Path
    from datasheet_types.cache_reader import read_json_object, safe_extract_dir
    from distributor_core.manifest import manifest_file_path
    extract_dir = safe_extract_dir(Path(project_dir) / "datasheets" / "extracted")
    if extract_dir is None:
        return None
    index_path = extract_dir / "manifest.json"
    if not index_path.exists():
        index_path = extract_dir / "index.json"
    if not index_path.exists():
        return None
    index = read_json_object(index_path)
    if index is None:
        return None
    import re as _re
    key = _re.sub(r'[^A-Za-z0-9_]', '_', mpn.strip())
    exts = index.get("extractions")
    if not isinstance(exts, dict):
        return None
    entry = exts.get(key)
    if not entry:
        for k, v in exts.items():
            if k.upper() == key.upper():
                entry = v
                break
    if not entry:
        return None
    json_file = manifest_file_path(extract_dir, entry.get("file") if isinstance(entry, dict) else None)
    if json_file is None or not json_file.exists():
        return None
    extraction = read_json_object(json_file)
    if extraction is None:
        return None
    # Trust gate: skip low-quality extractions
    meta = extraction.get("meta", {})
    score = meta.get("extraction_score", 0) if isinstance(meta, dict) else None
    if not isinstance(score, (int, float)) or isinstance(score, bool) or score < 6.0:
        return None
    specs = _read_spice_specs(extraction.get("spice_specs"))
    if not specs:
        return None
    if specs.get("gbw_hz") or specs.get("vref") or specs.get("dropout_mv"):
        specs["_source"] = f"extraction:{mpn}"
        return specs
    return None


def fetch_specs(mpn, component_type=None, project_dir=None, *, diagnostics=None):
    """Try all available sources for component specs.

    Order: LCSC (no auth) → DigiKey → element14 → Mouser →
           extraction cache → datasheet PDF regex

    Args:
        mpn: Manufacturer part number
        component_type: Optional hint ("opamp", "ldo", etc.)
        project_dir: Optional project directory for datasheet lookup

    Returns:
        (specs_dict, source_string) or (None, None)
    """
    if not mpn or len(mpn) < 3:
        return None, None

    # Try each API source (LCSC first — no auth required)
    for fetch_fn, name in [
        (fetch_specs_lcsc, "lcsc"),
        (fetch_specs_digikey, "digikey"),
        (fetch_specs_element14, "element14"),
        (fetch_specs_mouser, "mouser"),
    ]:
        try:
            specs = fetch_fn(mpn)
            if specs:
                source = specs.pop("_source", f"api:{name}")
                return specs, source
        except Exception as exc:
            record(diagnostics, "spice_spec_fetcher.fetch_specs", exc,
                   f"{name} spec lookup skipped for {mpn}")
            continue

    # Try structured datasheet extraction cache
    if project_dir:
        try:
            specs = fetch_specs_from_extraction(mpn, project_dir)
            if specs:
                source = specs.pop("_source", f"extraction:{mpn}")
                return specs, source
        except Exception as exc:
            record(diagnostics, "spice_spec_fetcher.fetch_specs", exc,
                   f"extraction-cache spec lookup skipped for {mpn}")

    # Try heuristic datasheet PDF regex extraction (last resort)
    if project_dir:
        try:
            specs = fetch_specs_from_datasheet(mpn, project_dir)
            if specs:
                source = specs.pop("_source", f"datasheet:{mpn}")
                return specs, source
        except Exception as exc:
            record(diagnostics, "spice_spec_fetcher.fetch_specs", exc,
                   f"datasheet-PDF spec lookup skipped for {mpn}")

    return None, None
