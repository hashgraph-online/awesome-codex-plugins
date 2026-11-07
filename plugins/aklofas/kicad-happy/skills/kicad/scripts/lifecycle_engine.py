"""Lifecycle and temperature audit engine.

Distributor lifecycle queries, extraction temperature reads, the per-component
audit and the BOM audit that both lifecycle_audit.py and the schematic analyzer
run.
"""

import json
import math
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from kicad_core import token_cache


# ---------------------------------------------------------------------------
# Temperature presets
# ---------------------------------------------------------------------------

_TEMP_PRESETS = {
    "commercial": (0, 70),
    "industrial": (-40, 85),
    "extended": (-40, 105),
    "automotive": (-40, 125),
    "military": (-55, 125),
}

_LIFECYCLE_STATUS_RULES = {
    'obsolete': ('LC-001', 'error'),
    'discontinued': ('LC-001', 'error'),
    'last_time_buy': ('LC-002', 'warning'),
    'nrnd': ('LC-003', 'warning'),
    'unknown': ('LC-004', 'info'),
}


def _classify_temp_grade(temp_min: float, temp_max: float) -> str:
    """Classify a temperature range into an industry grade."""
    if temp_min <= -55 and temp_max >= 125:
        return "military"
    if temp_min <= -40 and temp_max >= 125:
        return "automotive"
    if temp_min <= -40 and temp_max >= 105:
        return "extended"
    if temp_min <= -40 and temp_max >= 85:
        return "industrial"
    if temp_min <= 0 and temp_max >= 70:
        return "commercial"
    return "non-standard"


# ---------------------------------------------------------------------------
# Status normalization
# ---------------------------------------------------------------------------

_STATUS_NORMALIZE = {
    # DigiKey ProductStatus.Status values
    "active": "active",
    "active, not stocked": "active",
    "discontinued": "discontinued",
    "last time buy": "last_time_buy",
    "not for new designs": "nrnd",
    "not recommended for new designs": "nrnd",
    "discontinued at digikey": "discontinued",
    "discontinued at digi-key": "discontinued",
    "obsolete": "obsolete",
    # Mouser
    "new product": "active",
    "end of life": "obsolete",
    "factory special order": "active",
    # Generic
    "nrnd": "nrnd",
    "eol": "obsolete",
    "ltb": "last_time_buy",
}

# Normalized statuses that mean "not active" (end of life or heading there).
_EOL_STATUSES = frozenset({"obsolete", "discontinued", "last_time_buy", "nrnd"})


def _normalize_status(raw: str | None) -> str:
    """Normalize a lifecycle status string to a standard value."""
    if not raw:
        return "unknown"
    return _STATUS_NORMALIZE.get(raw.lower().strip(), "unknown")


# Worst first; "unknown" states nothing and never wins.
_STATUS_RANK = ("obsolete", "discontinued", "last_time_buy", "nrnd", "active", "unknown")


def _worse_status(a: str, b: str) -> str:
    return a if _STATUS_RANK.index(a) <= _STATUS_RANK.index(b) else b


def _stated(label) -> bool:
    """A status label counts only when it has text; blank padding is no label."""
    return bool(label.strip()) if isinstance(label, str) else bool(label)


def _source_status(data: dict) -> str | None:
    """One distributor's status: the worse of its label and its discontinuation
    flag, or None when it states neither."""
    status = None
    if _stated(data.get("status")):
        status = _normalize_status(data["status"])
    if data.get("discontinued") is True:
        status = _worse_status(status or "unknown", "discontinued")
    return status


# ---------------------------------------------------------------------------
# Temperature parsing
# ---------------------------------------------------------------------------

def _temp_evidence_source(source: str | None) -> str:
    """Map a temperature-range source tag to a finding evidence_source.

    "extraction_cache" is a per-MPN datasheet extraction and is genuinely
    datasheet-backed; "api:<distributor>" is a catalogue lookup. Anything else
    (or nothing) is not evidence of either.
    """
    if not source:
        return 'heuristic_rule'
    if source == 'extraction_cache':
        return 'datasheet'
    if source.startswith('api:'):
        return 'api_lookup'
    return 'heuristic_rule'


def _parse_temp_range(text: str) -> tuple[float, float] | None:
    """Parse temperature range from distributor attribute string.

    Examples: "-40°C ~ 85°C", "-40C to +125C", "-40°C~+85°C", "0 ~ 70"
    """
    if not text:
        return None
    num = r'([+\-\u2212\u2013]?\d+(?:\.\d+)?)'
    m = re.search(r'(?<![\w.])' + num + r'\s*°?\s*C?\s*(?:~|to|[\-\u2013\u2014])\s*' + num
                  + r'(?!\d|\.\d|\s*°?\s*F)',
                  unicodedata.normalize('NFKC', text))
    if m:
        return tuple(sorted(float(g.replace('\u2212', '-').replace('\u2013', '-'))
                            for g in m.groups()))
    return None


def _lead_weeks(lead_time) -> int | None:
    """Whole weeks for a distributor lead time ("14 Weeks", "1,000 Days", 12.5),
    rounded up; None when it is not a usable non-negative number."""
    if isinstance(lead_time, bool):
        return None
    if isinstance(lead_time, str):
        m = re.search(r'(-?\d[\d,]*(?:\.\d+)?)', lead_time)
        if not m:
            return None
        n = float(m.group(1).replace(',', ''))
        if 'day' in lead_time.lower():
            n /= 7
    elif isinstance(lead_time, (int, float)):
        n = lead_time
    else:
        return None
    return math.ceil(n) if math.isfinite(n) and n >= 0 else None


# ---------------------------------------------------------------------------
# MPN filtering (same pattern as sync_datasheets_digikey.py)
# Twin of distributor_core.inputs (_GENERIC_VALUE_RE / _SKIP_TYPES).
# ---------------------------------------------------------------------------

_GENERIC_VALUE_RE = re.compile(
    r"^[\d.]+\s*[pnuμmkMGR]?[FHΩRfhω]?$"
    r"|^[\d.]+\s*[kKmM]?[Ωω]?$"
    r"|^[\d.]+\s*[pnuμm]?[Ff]$"
    r"|^[\d.]+\s*[pnuμm]?[Hh]$"
    r"|^[\d.]+%$"
    r"|^DNP$|^NC$|^N/?A$",
    re.IGNORECASE,
)

_SKIP_TYPES = {
    "test_point", "mounting_hole", "fiducial", "graphic",
    "jumper", "net_tie", "mechanical",
}


def _requested_results(mpn: str, items, mpn_of) -> list:
    """The provider results whose MPN is the requested part number, literal matches
    (case and whitespace aside) first. A family member, sibling or ordering variant is
    not the part: its lifecycle status says nothing about this one."""
    ds_pkg = str(Path(__file__).resolve().parents[2] / "datasheets")
    if ds_pkg not in sys.path:
        sys.path.insert(0, ds_pkg)
    from distributor_core.verify import same_part
    literal, normalised = [], []
    want = "".join(mpn.split()).upper()
    for item in items:
        hit = mpn_of(item)
        if not isinstance(hit, str):
            continue
        if "".join(hit.split()).upper() == want and want:
            literal.append(item)
        elif same_part(mpn, hit, allow_family=False, ordering_suffixes=False):
            normalised.append(item)
    return literal + normalised


def _lcsc_mpn(comp: dict):
    # jlcsearch rows now carry the MPN as top-level `mfr` and no `extra` block.
    extra = comp.get("extra") if isinstance(comp.get("extra"), dict) else {}
    return comp.get("mfr") or extra.get("mpn")


def _is_real_mpn(mpn: str) -> bool:
    if not mpn or len(mpn) < 3:
        return False
    if _GENERIC_VALUE_RE.match(mpn.strip()):
        return False
    has_letter = any(c.isalpha() for c in mpn)
    has_digit = any(c.isdigit() for c in mpn)
    return has_letter and has_digit


# ---------------------------------------------------------------------------
# DigiKey API (OAuth 2.0)
# ---------------------------------------------------------------------------

def _get_digikey_token() -> tuple[str, str] | None:
    client_id = os.environ.get("DIGIKEY_CLIENT_ID", "")
    client_secret = os.environ.get("DIGIKEY_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return None

    cached = token_cache.load_token("digikey_token", client_id)
    if cached:
        return cached, client_id

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
        token = token_data["access_token"]
        token_cache.store_token("digikey_token", client_id, token, 540)
        return token, client_id
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError):
        return None


def query_lifecycle_digikey(mpn: str) -> dict | None:
    """Query DigiKey for lifecycle and temperature data."""
    auth = _get_digikey_token()
    if not auth:
        return None
    token, client_id = auth

    try:
        body = json.dumps({"Keywords": mpn, "Limit": 3}).encode()
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
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return None

    for product in _requested_results(mpn, data.get("Products", []),
                                      lambda p: p.get("ManufacturerProductNumber")):

        result = {}

        # Lifecycle status
        status = product.get("ProductStatus", {})
        if isinstance(status, dict):
            result["status"] = status.get("Status")
        elif isinstance(status, str):
            result["status"] = status
        result["discontinued"] = product.get("Discontinued", False)

        # Operating temperature from parameters
        for param in product.get("Parameters", []):
            ptext = param.get("ParameterText", "").lower()
            pval = param.get("ValueText", "")
            if "operating temperature" in ptext and pval:
                temp = _parse_temp_range(pval)
                if temp:
                    result["temp_min_c"] = temp[0]
                    result["temp_max_c"] = temp[1]
                    result["temp_raw"] = pval
                break

        return result
    return None


# ---------------------------------------------------------------------------
# Mouser API
# ---------------------------------------------------------------------------

def query_lifecycle_mouser(mpn: str) -> dict | None:
    """Query Mouser for lifecycle and temperature data."""
    api_key = os.environ.get("MOUSER_SEARCH_API_KEY") or os.environ.get("MOUSER_PART_API_KEY")
    if not api_key:
        return None

    try:
        body = json.dumps({
            "SearchByPartRequest": {
                "mouserPartNumber": mpn,
                "partSearchOptions": "Exact",
            }
        }).encode()
        url = f"https://api.mouser.com/api/v1/search/partnumber?apiKey={api_key}"
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return None

    for part in _requested_results(mpn, data.get("SearchResults", {}).get("Parts", []),
                                   lambda p: p.get("ManufacturerPartNumber")):
        result = {}
        result["status"] = part.get("LifecycleStatus")
        result["discontinued"] = str(part.get("IsDiscontinued", "")).lower() == "true"
        result["lead_time"] = part.get("LeadTime")
        result["suggested_replacement"] = part.get("SuggestedReplacement")

        for attr in part.get("ProductAttributes", []):
            aname = attr.get("AttributeName", "").lower()
            aval = attr.get("AttributeValue", "")
            if "operating temperature" in aname and aval:
                temp = _parse_temp_range(aval)
                if temp:
                    result["temp_min_c"] = temp[0]
                    result["temp_max_c"] = temp[1]
                    result["temp_raw"] = aval
                break

        return result
    return None


# ---------------------------------------------------------------------------
# LCSC (no auth)
# ---------------------------------------------------------------------------

def query_lifecycle_lcsc(mpn: str) -> dict | None:
    """Query LCSC for availability and temperature data."""
    try:
        url = f"https://jlcsearch.tscircuit.com/api/search?q={urllib.parse.quote(mpn)}&limit=3&full=true"
        req = urllib.request.Request(url, headers={"User-Agent": "kicad-happy-lifecycle/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return None

    for comp in _requested_results(mpn, data.get("components", []), _lcsc_mpn):
        extra = comp.get("extra") if isinstance(comp.get("extra"), dict) else {}

        result = {}
        stock = comp.get("stock", 0)
        result["in_stock"] = stock > 0
        result["stock_qty"] = stock

        attrs = extra.get("attributes", {})
        for k, v in attrs.items():
            if "operating temperature" in k.lower() and v:
                temp = _parse_temp_range(v)
                if temp:
                    result["temp_min_c"] = temp[0]
                    result["temp_max_c"] = temp[1]
                    result["temp_raw"] = v
                break

        return result
    return None


# ---------------------------------------------------------------------------
# element14 API
# ---------------------------------------------------------------------------

def query_lifecycle_element14(mpn: str) -> dict | None:
    """Query element14 for lifecycle and temperature data."""
    api_key = os.environ.get("ELEMENT14_API_KEY")
    if not api_key:
        return None

    try:
        params = urllib.parse.urlencode({
            "callInfo.apiKey": api_key,
            "term": f"manuPartNum:{mpn}",
            "storeInfo.id": "us.newark.com",
            "resultsSettings.offset": 0,
            "resultsSettings.numberOfResults": 3,
            "resultsSettings.responseGroup": "medium",
        })
        url = f"https://api.element14.com/catalog/products?{params}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return None

    products = data.get("manufacturerPartNumberSearchReturn", {}).get("products", [])
    for product in _requested_results(mpn, products,
                                      lambda p: p.get("translatedManufacturerPartNumber")):
        result = {}
        for attr in product.get("attributes", []):
            label = attr.get("attributeLabel", "").lower()
            value = attr.get("attributeValue", "")
            if "lifecycle" in label or "status" in label:
                result["status"] = value
            elif "operating temperature" in label and value:
                temp = _parse_temp_range(value)
                if temp:
                    result["temp_min_c"] = temp[0]
                    result["temp_max_c"] = temp[1]
                    result["temp_raw"] = value
        if result:
            return result
    return None


# ---------------------------------------------------------------------------
# Datasheet extraction cache (local, no network)
# ---------------------------------------------------------------------------

# Ambient operating-range keys, most specific first. Absolute-maximum tables
# hold stress ratings ("ambient under bias"), so only the operating-named keys
# are read there.
_TA_KEYS = ("TA", "T_A", "T_AMB", "T_OPERATING", "TOPR", "T_OPR")
_ABS_MAX_KEYS = ("T_OPERATING", "TOPR", "T_OPR")
_NOT_AMBIENT_RE = re.compile(r"\b(?:junction|storage)\b|\bcase\s+temp")
_UNUSABLE = object()


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _celsius_range(values, need_condition):
    """The first acceptable °C SpecValue with both bounds as a sorted (min, max);
    _UNUSABLE when the acceptable entries all lack a bound; None when none qualifies."""
    one_bound = False
    for v in values if isinstance(values, list) else []:
        if not isinstance(v, dict):
            continue
        unit = unicodedata.normalize("NFKC", str(v.get("unit") or "")).replace(" ", "")
        if unit not in ("°C", "C", "degC"):
            continue
        cond = str(v.get("condition") or "").lower()
        if _NOT_AMBIENT_RE.search(cond):
            continue
        if need_condition and not ("ambient" in cond or "operating" in cond):
            continue
        lo, hi = v.get("min"), v.get("max")
        if _is_number(lo) and _is_number(hi):
            return tuple(sorted((float(lo), float(hi))))
        one_bound = True
    return _UNUSABLE if one_bound else None


def _v2_operating_temperature(ext: dict) -> tuple[float, float] | None:
    """Ambient operating range in degrees C from a v2 extraction's SpecValues.

    TA-style keys in base.recommended_operating, then any other
    recommended_operating entry whose condition names an ambient or operating
    temperature, then the operating-named keys in base.absolute_max. Junction,
    storage and case-temperature ranges never count. A row with a single bound
    is skipped; when recommended_operating has only such rows the result is
    None, never a wider absolute-maximum range.
    """
    base = ext.get("base")
    if not isinstance(base, dict):
        return None
    rec, absmax = (base.get(k) for k in ("recommended_operating", "absolute_max"))
    rec = rec if isinstance(rec, dict) else {}
    absmax = absmax if isinstance(absmax, dict) else {}

    def keyed(sec, keys):
        by_key = {str(k).upper(): k for k in sorted(sec, key=str)}
        for key in keys:
            if key in by_key:
                got = _celsius_range(sec[by_key[key]], False)
                if got is not None:
                    yield got

    def by_condition():
        for key in sorted(rec, key=str):
            if str(key).upper() not in _TA_KEYS and not str(key).upper().startswith("TJ"):
                got = _celsius_range(rec[key], True)
                if got is not None:
                    yield got

    one_bound = False
    for got in (*keyed(rec, _TA_KEYS), *by_condition()):
        if got is _UNUSABLE:
            one_bound = True
        else:
            return got
    if one_bound:
        return None
    for got in keyed(absmax, _ABS_MAX_KEYS):
        if got is not _UNUSABLE:
            return got
    return None


def _v1_operating_temperature(ext: dict, path) -> tuple | None:
    ops = ext.get("recommended_operating_conditions")
    if ops is None:
        return None
    if not isinstance(ops, dict):
        print(f"Warning: {path}: recommended_operating_conditions is not an object; "
              f"extraction temperature ignored", file=sys.stderr)
        return None
    lo, hi = ops.get("temp_min_c"), ops.get("temp_max_c")
    if _is_number(lo) and _is_number(hi):
        return tuple(sorted((lo, hi)))
    return None


def read_extraction_temperature(mpn: str, project_dir: str) -> dict | None:
    """Operating temperature range from the project's datasheet extraction cache.

    Looks the MPN up in <project_dir>/datasheets/extracted the way the
    datasheet consumers do (manifest, then <mpn>.json), then under the older
    underscore-only file name. A file that is not a readable JSON object is
    skipped with one warning.
    """
    if not project_dir:
        return None
    ds_scripts = str(Path(__file__).resolve().parents[2] / "datasheets" / "scripts")
    if ds_scripts not in sys.path:
        sys.path.insert(0, ds_scripts)
    from datasheet_extract_cache import get_cached_extraction
    from datasheet_types.cache_reader import read_json_object, safe_extract_dir, sanitize_mpn
    from distributor_core.manifest import manifest_file_path

    extract_dir = safe_extract_dir(Path(project_dir) / "datasheets" / "extracted")
    if extract_dir is None:
        return None
    ext, path = get_cached_extraction(extract_dir, mpn), extract_dir
    if ext is None:
        legacy = re.sub(r'[^A-Za-z0-9_]', '_', mpn.strip())
        candidates = [f"{sanitize_mpn(mpn)}.json", f"{legacy}.json"]
        for idx_name in ("manifest.json", "index.json"):
            idx = read_json_object(extract_dir / idx_name)
            if idx is not None:
                entries = idx.get("extractions")
                if entries is not None and not isinstance(entries, dict):
                    print(f"Warning: {extract_dir / idx_name}: 'extractions' is not an object; "
                          f"manifest ignored", file=sys.stderr)
                for k, v in (entries.items() if isinstance(entries, dict) else ()):
                    if str(k).upper() == legacy.upper() and isinstance(v, dict) \
                            and isinstance(v.get("file"), str):
                        candidates.append(v["file"])
                        break
                break
        for name in dict.fromkeys(candidates):
            p = manifest_file_path(extract_dir, name)
            if p is None or not p.is_file():
                continue
            ext, path = read_json_object(p), p
            if ext is None:
                print(f"Warning: {p}: not a readable JSON object; extraction ignored",
                      file=sys.stderr)
                return None
            break
    if ext is None:
        return None

    rng = _v2_operating_temperature(ext) or _v1_operating_temperature(ext, path)
    if rng is None:
        return None
    return {"temp_min_c": rng[0], "temp_max_c": rng[1], "source": "extraction_cache"}


# ---------------------------------------------------------------------------
# Per-component audit
# ---------------------------------------------------------------------------

def audit_component(mpn: str, sources: list[str], project_dir: str | None = None,
                    delay: float = 1.0) -> dict:
    """Query all available sources for one component's lifecycle + temperature."""
    result = {"mpn": mpn, "sources": {}}
    # Worst-case status across sources (drives the default finding severity).
    best_status = "unknown"
    # Track every source's normalized status so callers can detect disagreement
    # (e.g., DigiKey=active, Mouser=obsolete — severity should be WARNING, not
    # ERROR, because the part is still orderable from one distributor).
    per_source_status: dict[str, str] = {}
    temp_data = None

    # Try extraction cache first (no network, no delay)
    if project_dir:
        ext_temp = read_extraction_temperature(mpn, project_dir)
        if ext_temp:
            temp_data = ext_temp

    # Query distributor APIs
    api_fns = {
        "lcsc": query_lifecycle_lcsc,
        "digikey": query_lifecycle_digikey,
        "element14": query_lifecycle_element14,
        "mouser": query_lifecycle_mouser,
    }

    attempted = []
    for source_name, fn in api_fns.items():
        if sources and source_name not in sources:
            continue
        attempted.append(source_name)
        try:
            time.sleep(delay)
            data = fn(mpn)
            if data:
                result["sources"][source_name] = data
                normalized = _source_status(data)
                if normalized:
                    per_source_status[source_name] = normalized
                    best_status = _worse_status(best_status, normalized)
                # Update temperature if not already from extraction
                if not temp_data and data.get("temp_min_c") is not None:
                    temp_data = {
                        "temp_min_c": data["temp_min_c"],
                        "temp_max_c": data["temp_max_c"],
                        "source": f"api:{source_name}",
                    }
        except (urllib.error.URLError, OSError, json.JSONDecodeError,
                KeyError, ValueError, TypeError):
            continue

    result["status"] = best_status
    # Consensus: True when distributors disagree and at least one says active.
    # A part reported obsolete by one distributor but active by another is
    # still orderable, so the finding should be warning rather than error.
    has_active = any(s == "active" for s in per_source_status.values())
    has_non_active = any(s in _EOL_STATUSES for s in per_source_status.values())
    result["consensus_split"] = has_active and has_non_active
    result["per_source_status"] = per_source_status
    result["attempted"] = sorted(attempted)
    if temp_data:
        result["temperature"] = temp_data
    return result


def find_alternatives(mpn: str,
                      sources: list[str] | None = None,
                      delay: float = 1.0) -> list[dict]:
    """Search for active alternative parts when a component is EOL/NRND/obsolete.

    Checks Mouser's SuggestedReplacement field first, then searches DigiKey
    and LCSC for parts with similar descriptions.

    Returns list of alternatives with mpn, manufacturer, source, status.
    """
    alternatives = []
    seen_mpns = {mpn.upper()}  # Don't suggest the original part

    # 1. Mouser SuggestedReplacement (already in query data — check sources)
    if not sources or "mouser" in sources:
        api_key = os.environ.get("MOUSER_SEARCH_API_KEY") or os.environ.get("MOUSER_PART_API_KEY")
        if api_key:
            try:
                time.sleep(delay)
                body = json.dumps({
                    "SearchByPartRequest": {
                        "mouserPartNumber": mpn,
                        "partSearchOptions": "",
                    }
                }).encode()
                url = f"https://api.mouser.com/api/v1/search/partnumber?apiKey={api_key}"
                req = urllib.request.Request(url, data=body,
                                            headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read())
                for part in data.get("SearchResults", {}).get("Parts", []):
                    repl = part.get("SuggestedReplacement")
                    if repl and repl.upper() not in seen_mpns:
                        seen_mpns.add(repl.upper())
                        alternatives.append({
                            "mpn": repl,
                            "manufacturer": part.get("Manufacturer", ""),
                            "source": "mouser_suggestion",
                            "status": "suggested_replacement",
                        })
            except (urllib.error.URLError, OSError, json.JSONDecodeError):
                pass

    # 2. DigiKey keyword search for similar active parts
    if not sources or "digikey" in sources:
        auth = _get_digikey_token()
        if auth:
            token, client_id = auth
            # Search by the base part number (strip package suffix)
            base_mpn = re.sub(r'[A-Z]{0,3}$', '', mpn)  # Strip trailing package codes
            if len(base_mpn) >= 4:
                try:
                    time.sleep(delay)
                    body = json.dumps({"Keywords": base_mpn, "Limit": 5}).encode()
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
                        if not prod_mpn or prod_mpn.upper() in seen_mpns:
                            continue
                        # Only suggest active parts
                        prod_status = product.get("ProductStatus", {})
                        status_str = prod_status.get("Status", "") if isinstance(prod_status, dict) else str(prod_status)
                        if _normalize_status(status_str) == "active":
                            seen_mpns.add(prod_mpn.upper())
                            alternatives.append({
                                "mpn": prod_mpn,
                                "manufacturer": product.get("Manufacturer", {}).get("Name", ""),
                                "source": "digikey",
                                "status": "active",
                            })
                            if len(alternatives) >= 5:
                                break
                except (urllib.error.URLError, OSError, json.JSONDecodeError):
                    pass

    # 3. LCSC search for in-stock alternatives
    if not sources or "lcsc" in sources:
        base_mpn = re.sub(r'[A-Z]{0,3}$', '', mpn)
        if len(base_mpn) >= 4:
            try:
                time.sleep(delay)
                url = f"https://jlcsearch.tscircuit.com/api/search?q={urllib.parse.quote(base_mpn)}&limit=5&full=true"
                req = urllib.request.Request(url, headers={"User-Agent": "kicad-happy-lifecycle/1.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read())
                for comp in data.get("components", []):
                    extra = comp.get("extra", {})
                    comp_mpn = extra.get("mpn", "")
                    if not comp_mpn or comp_mpn.upper() in seen_mpns:
                        continue
                    stock = comp.get("stock", 0)
                    if stock > 0:
                        seen_mpns.add(comp_mpn.upper())
                        alternatives.append({
                            "mpn": comp_mpn,
                            "manufacturer": extra.get("manufacturer", ""),
                            "source": "lcsc",
                            "status": "in_stock",
                            "lcsc_stock": stock,
                        })
                        if len(alternatives) >= 5:
                            break
            except (urllib.error.URLError, OSError, json.JSONDecodeError):
                pass

    return alternatives[:5]  # Cap at 5 suggestions


# ---------------------------------------------------------------------------
# Main audit
# ---------------------------------------------------------------------------

def audit_bom(analysis_json: dict, project_dir: str | None = None,
              temp_range: tuple[float, float] | None = None,
              sources: list[str] | None = None,
              delay: float = 1.0,
              suggest_alternatives: bool = False) -> dict:
    """Audit all components in the BOM for lifecycle and temperature."""
    bom = analysis_json.get("bom", [])

    # Extract unique MPNs
    mpn_map = {}  # mpn -> list of references
    skipped = 0
    for entry in bom:
        if entry.get("dnp"):
            continue
        if entry.get("type", "") in _SKIP_TYPES:
            continue
        mpn = entry.get("mpn", "").strip()
        if not _is_real_mpn(mpn):
            skipped += 1
            continue
        mpn_map.setdefault(mpn, []).extend(entry.get("references", []))

    # LCSC/jlcsearch exposes no lifecycle/obsolescence data — an
    # LCSC-only audit can only ever return 'unknown'. Flag the capability
    # gap up front and skip the per-part LC-004 noise (rows are kept for
    # any temperature data).
    lcsc_only = bool(sources) and set(sources) == {"lcsc"}

    lifecycle_findings = []
    temperature_findings = []
    status_counts = {"active": 0, "nrnd": 0, "last_time_buy": 0,
                     "obsolete": 0, "discontinued": 0, "unknown": 0}
    grade_counts = {}
    temp_ok = 0
    temp_fail = 0

    total = len(mpn_map)
    for i, (mpn, refs) in enumerate(sorted(mpn_map.items())):
        print(f"[{i+1}/{total}] {mpn}", file=sys.stderr)
        data = audit_component(mpn, sources or [], project_dir, delay)

        # Lifecycle
        status = data.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

        finding = {
            "mpn": mpn,
            "references": sorted(refs),
            "status": status,
            "sources": data.get("sources", {}),
        }

        # Flag non-active statuses
        if status in _EOL_STATUSES:
            alert_map = {
                "nrnd": "NRND — not recommended for new designs, consider replacement",
                "last_time_buy": "Last Time Buy — order soon or find alternative",
                "obsolete": "Obsolete — find replacement part",
                "discontinued": "Discontinued — find replacement part",
            }
            finding["alert"] = alert_map.get(status, "")
            # Check for suggested replacement from API data
            for src_data in data.get("sources", {}).values():
                repl = src_data.get("suggested_replacement")
                if repl:
                    finding["suggested_replacement"] = repl
                    break
            # Search for alternatives if requested
            if suggest_alternatives:
                print(f"  Searching for alternatives...", file=sys.stderr)
                alts = find_alternatives(mpn, sources, delay)
                if alts:
                    finding["alternatives"] = alts

        rule_info = _LIFECYCLE_STATUS_RULES.get(status)
        if rule_info and not (lcsc_only and status == "unknown"):
            rule_id, severity = rule_info
            consensus_split = data.get('consensus_split', False)
            per_source = data.get('per_source_status', {})
            # Demote ERROR → WARNING when distributors disagree. The part is
            # still orderable from at least one active source, so "obsolete"
            # overstates the supply risk.
            split_note = ''
            if consensus_split and severity == 'error':
                severity = 'warning'
                active_srcs = sorted(s for s, st in per_source.items() if st == 'active')
                eol_srcs = sorted(s for s, st in per_source.items() if st in _EOL_STATUSES)
                split_note = (f" Distributor disagreement: {', '.join(active_srcs)} "
                              f"list it as active while {', '.join(eol_srcs)} "
                              f"flag EOL. Part is orderable today.")
            finding['detector'] = 'audit_bom'
            finding['rule_id'] = rule_id
            finding['category'] = 'lifecycle'
            finding['severity'] = severity
            finding['confidence'] = 'deterministic'
            finding['evidence_source'] = 'api_lookup'
            finding['summary'] = f"{mpn}: {status} ({len(refs)} ref(s))"
            if per_source:
                finding['per_source_status'] = per_source
            if consensus_split:
                finding['consensus_split'] = True
            finding['description'] = (finding.get('alert', f'Component {mpn} is {status}.')
                                      + split_note)
            finding['components'] = sorted(refs)
            finding['nets'] = []
            finding['pins'] = []
            finding['recommendation'] = (
                f"Replace {mpn} — part is {status}." if not consensus_split
                else f"Verify current availability before committing to {mpn}; "
                     f"consider locking to the active distributor or finding an "
                     f"alternate.")
            finding['report_context'] = {'section': 'Lifecycle', 'impact': 'Supply chain risk', 'standard_ref': ''}
        else:
            finding['detector'] = 'audit_bom'
            finding['rule_id'] = 'LC-ACT'
            finding['category'] = 'lifecycle'
            finding['severity'] = 'info'
            finding['confidence'] = 'deterministic'
            finding['evidence_source'] = 'api_lookup'
            if lcsc_only and status == 'unknown':
                # LCSC (jlcsearch) carries no lifecycle status field at all —
                # say so plainly instead of reusing the "active" wording.
                finding['summary'] = (f"{mpn}: unknown ({len(refs)} ref(s)) — "
                                      f"LCSC returns no lifecycle status")
                finding['description'] = (
                    f"Lifecycle status for {mpn} could not be determined: "
                    f"LCSC returns no lifecycle status. Use DigiKey, Mouser, "
                    f"or element14 credentials for a real lifecycle audit.")
            else:
                finding['summary'] = f"{mpn}: active ({len(refs)} ref(s))"
            finding['components'] = sorted(refs)
            finding['nets'] = []
            finding['pins'] = []
            finding['report_context'] = {'section': 'Lifecycle', 'impact': '', 'standard_ref': ''}

        lifecycle_findings.append(finding)

        # LC-005: Single-source detection. Denominator is sources
        # actually ATTEMPTED, not just the ones that responded — an errored
        # or timed-out source didn't confirm anything, it isn't absent from
        # the count. A response with status=None doesn't count as an active
        # confirmation either: a source counts as responding only when it
        # states something: a non-empty label, mapped or not, or a true flag.
        # An unmapped label (e.g. "Restricted Availability") is an answer that
        # did not confirm active, which is the case LC-005 exists for.
        # LCSC carries no lifecycle status field at
        # all, so it's excluded from the lifecycle source counts entirely
        # (it's a stock/price source, not a lifecycle source) — its
        # presence is still called out in the description when relevant.
        if status == 'active':
            attempted = [s for s in data.get('attempted', []) if s != 'lcsc']
            all_responded = finding.get('sources', {})
            per_source = data.get('per_source_status', {})
            responded = [s for s, d in all_responded.items()
                         if s != 'lcsc'
                         and (_stated(d.get('status')) or d.get('discontinued') is True)]
            active_confirmed = sorted(s for s in responded if per_source.get(s) == 'active')

            total_attempted = len(attempted)
            n_responded = len(responded)
            if len(active_confirmed) == 1 and n_responded >= 2:
                stock_note = ''
                if 'lcsc' in all_responded:
                    stock_note = (' LCSC also responded but is excluded as a '
                                  'stock-only source with no lifecycle status.')
                lifecycle_findings.append({
                    'mpn': mpn,
                    'references': sorted(refs),
                    'status': 'active',
                    'single_source': True,
                    'source_name': active_confirmed[0],
                    'total_attempted': total_attempted,
                    'responded': n_responded,
                    'active_confirmed': len(active_confirmed),
                    'detector': 'audit_bom',
                    'rule_id': 'LC-005',
                    'category': 'lifecycle',
                    'severity': 'info',
                    'confidence': 'deterministic',
                    'evidence_source': 'api_lookup',
                    'summary': f'{mpn}: single source ({active_confirmed[0]})',
                    'description': (
                        f'Component {mpn} ({len(refs)} ref(s)) is confirmed active by only '
                        f'{active_confirmed[0]} ({total_attempted} attempted, '
                        f'{n_responded} responded lifecycle source(s)).{stock_note}'),
                    'components': sorted(refs),
                    'nets': [],
                    'pins': [],
                    'recommendation': 'Consider qualifying an alternative source for supply chain resilience.',
                    'report_context': {'section': 'Lifecycle', 'impact': 'Supply chain fragility', 'standard_ref': ''},
                })

        # LC-006: Long lead time
        max_lead_weeks = 0
        lead_source = ''
        for src_name, src_data in finding.get('sources', {}).items():
            lt = src_data.get('lead_time')
            if lt:
                weeks = _lead_weeks(lt) or 0
                if weeks > max_lead_weeks:
                    max_lead_weeks = weeks
                    lead_source = src_name

        if max_lead_weeks > 12:
            severity = 'warning' if max_lead_weeks > 26 else 'info'
            lifecycle_findings.append({
                'mpn': mpn,
                'references': sorted(refs),
                'lead_weeks': max_lead_weeks,
                'lead_source': lead_source,
                'detector': 'audit_bom',
                'rule_id': 'LC-006',
                'category': 'lifecycle',
                'severity': severity,
                'confidence': 'deterministic',
                'evidence_source': 'api_lookup',
                'summary': f'{mpn}: {max_lead_weeks} week lead time',
                'description': f'Component {mpn} has {max_lead_weeks} week lead time (from {lead_source}).',
                'components': sorted(refs),
                'nets': [],
                'pins': [],
                'recommendation': f'Pre-order or stock {mpn} — long lead time risk.',
                'report_context': {'section': 'Lifecycle', 'impact': 'Procurement delay risk', 'standard_ref': ''},
            })

        # Temperature
        temp = data.get("temperature")
        if temp and temp_range:
            design_min, design_max = temp_range
            comp_min = temp["temp_min_c"]
            comp_max = temp["temp_max_c"]
            comp_grade = _classify_temp_grade(comp_min, comp_max)
            grade_counts[comp_grade] = grade_counts.get(comp_grade, 0) + 1

            below_min = comp_min > design_min
            above_max = comp_max < design_max

            if below_min or above_max:
                temp_fail += 1
                temperature_findings.append({
                    "mpn": mpn,
                    "references": sorted(refs),
                    "component_range": {"min_c": comp_min, "max_c": comp_max},
                    "component_grade": comp_grade,
                    "design_range": {"min_c": design_min, "max_c": design_max},
                    "data_source": temp.get("source", "unknown"),
                    "severity": "warning",
                    "alert": (f"{comp_grade.capitalize()} ({comp_min} to {comp_max}°C) component "
                              f"in {_classify_temp_grade(design_min, design_max)} "
                              f"({design_min} to {design_max}°C) design"),
                    "violations": {
                        "below_min": below_min,
                        "above_max": above_max,
                        "min_shortfall_c": comp_min - design_min if below_min else 0,
                        "max_shortfall_c": design_max - comp_max if above_max else 0,
                    },
                    "detector": "audit_bom",
                    "rule_id": "LT-001",
                    "category": "temperature",
                    "confidence": "deterministic",
                    # "extraction_cache" is a real per-MPN datasheet extraction and must
                    # not be downgraded to api_lookup; "api:<distributor>" is a lookup.
                    "evidence_source": _temp_evidence_source(temp.get("source")),
                    "summary": f"{mpn}: rated {comp_grade} ({comp_min}C to {comp_max}C), design needs {design_min}C to {design_max}C",
                    "components": sorted(refs),
                    "nets": [],
                    "pins": [],
                    "recommendation": f"Select component rated for full {design_min}C to {design_max}C range.",
                    "report_context": {"section": "Temperature", "impact": "Operating range violation", "standard_ref": ""},
                })
            else:
                temp_ok += 1
        elif temp:
            comp_grade = _classify_temp_grade(temp["temp_min_c"], temp["temp_max_c"])
            grade_counts[comp_grade] = grade_counts.get(comp_grade, 0) + 1

    # Build output
    result = {
        "analyzer_type": "lifecycle",
        "schema_version": "1.4.0",
        "audit_date": datetime.now().astimezone().isoformat(timespec='seconds'),
        "components_checked": total,
        "components_with_mpn": total,
        "components_without_mpn": skipped,
        "sources_available": sorted({src for f in lifecycle_findings for src in f.get("sources", {})}),
        "findings": lifecycle_findings,
        "lifecycle_summary": status_counts,
    }
    if lcsc_only:
        result["capability_note"] = (
            "LCSC (jlcsearch) exposes no lifecycle/obsolescence status — "
            "every part reads 'unknown' by construction. Use DigiKey, "
            "Mouser, or element14 credentials for a real lifecycle audit.")

    observations = []
    if lcsc_only:
        observations.append(
            "LCSC-only audit: lifecycle status unavailable from this source "
            "(all statuses 'unknown' by construction)")
    for status_key in ("nrnd", "last_time_buy", "obsolete", "discontinued"):
        count = status_counts.get(status_key, 0)
        if count:
            labels = {
                "nrnd": "Not Recommended for New Designs",
                "last_time_buy": "Last Time Buy",
                "obsolete": "Obsolete",
                "discontinued": "Discontinued",
            }
            observations.append(f"{count} component(s) {labels[status_key]}")

    if temp_range:
        design_min, design_max = temp_range
        result["findings"] = result["findings"] + temperature_findings
        result["temperature_summary"] = {
            "design_target": {
                "min_c": design_min,
                "max_c": design_max,
                "grade": _classify_temp_grade(design_min, design_max),
            },
            "components_checked": temp_ok + temp_fail,
            "components_meeting_spec": temp_ok,
            "components_failing_spec": temp_fail,
            "grade_distribution": grade_counts,
        }
        if temp_fail:
            observations.append(
                f"{temp_fail} component(s) don't meet {_classify_temp_grade(design_min, design_max)} "
                f"temperature range ({design_min} to {design_max}°C)"
            )

    if observations:
        result["observations"] = observations

    all_findings = result.get("findings", [])
    sev_counts = {"error": 0, "warning": 0, "info": 0}
    for f in all_findings:
        s = (f.get("severity") or "info").lower()
        if s in ("critical", "high", "error"):
            sev_counts["error"] += 1
        elif s in ("medium", "low", "warning"):
            sev_counts["warning"] += 1
        else:
            sev_counts["info"] += 1
    result["summary"] = {
        "total_findings": len(all_findings),
        "by_severity": sev_counts,
        "components_checked": total,
        "lifecycle_issues": len(lifecycle_findings),
        "temperature_issues": len(temperature_findings),
    }
    from finding_schema import compute_trust_summary
    result["trust_summary"] = compute_trust_summary(all_findings)

    return result
