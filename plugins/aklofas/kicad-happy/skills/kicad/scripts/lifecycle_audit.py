#!/usr/bin/env python3
"""Component lifecycle and temperature audit.

Reads analyzer JSON output (BOM section) and queries distributor APIs for
lifecycle status and operating temperature data. Flags obsolete, NRND, and
EOL components, and checks temperature range coverage against a design target.

This is a standalone script (not part of the analyzer) because it requires
network access for distributor API queries. The analyzer must remain
zero-dependency and offline.

Usage:
    python3 lifecycle_audit.py analysis.json
    python3 lifecycle_audit.py analysis.json --temp-range "industrial"
    python3 lifecycle_audit.py analysis.json --temp-range="-40,85"  # use = for negative min
    python3 lifecycle_audit.py analysis.json --output lifecycle.json
    python3 lifecycle_audit.py analysis.json --only digikey

Environment:
    DIGIKEY_CLIENT_ID, DIGIKEY_CLIENT_SECRET — DigiKey OAuth 2.0
    MOUSER_SEARCH_API_KEY — Mouser API key
    ELEMENT14_API_KEY — element14/Newark API key
    (LCSC requires no credentials)
"""

import argparse
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


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


def _normalize_status(raw: str | None) -> str:
    """Normalize a lifecycle status string to a standard value."""
    if not raw:
        return "unknown"
    return _STATUS_NORMALIZE.get(raw.lower().strip(), "unknown")


# ---------------------------------------------------------------------------
# Temperature parsing
# ---------------------------------------------------------------------------

def _parse_temp_range(text: str) -> tuple[float, float] | None:
    """Parse temperature range from distributor attribute string.

    Examples: "-40°C ~ 85°C", "-40C to +125C", "-40°C~+85°C", "0 ~ 70"
    """
    if not text:
        return None
    m = re.search(r'(-?\d+)\s*°?\s*C?\s*[~\-–—to]+\s*\+?(-?\d+)\s*°?\s*C?', text)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None


# ---------------------------------------------------------------------------
# MPN filtering (same pattern as sync_datasheets_digikey.py)
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

    # Token cache
    cache_path = os.path.join(tempfile.gettempdir(), "digikey_token_cache.json")
    try:
        with open(cache_path) as f:
            cache = json.load(f)
        if cache.get("expires_at", 0) > time.time():
            return cache["access_token"], client_id
    except (OSError, json.JSONDecodeError, KeyError):
        pass

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
        with open(cache_path, "w") as f:
            json.dump({"access_token": token, "expires_at": time.time() + 540}, f)
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

    for product in data.get("Products", []):
        prod_mpn = product.get("ManufacturerProductNumber", "")
        if not prod_mpn.upper().startswith(mpn.upper()[:6]):
            continue

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
                "partSearchOptions": "",
            }
        }).encode()
        url = f"https://api.mouser.com/api/v1/search/partnumber?apiKey={api_key}"
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return None

    for part in data.get("SearchResults", {}).get("Parts", []):
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

    for comp in data.get("components", []):
        extra = comp.get("extra", {})
        comp_mpn = extra.get("mpn", "")
        if not comp_mpn or not comp_mpn.upper().startswith(mpn.upper()[:6]):
            continue

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
    for product in products:
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

def read_extraction_temperature(mpn: str, project_dir: str) -> dict | None:
    """Read temperature data from datasheet extraction cache."""
    if not project_dir:
        return None

    sanitized = re.sub(r'[^A-Za-z0-9_]', '_', mpn.strip())
    extract_path = Path(project_dir) / "datasheets" / "extracted" / f"{sanitized}.json"

    if not extract_path.exists():
        # Try index lookup
        extracted_dir = Path(project_dir) / "datasheets" / "extracted"
        idx_path = extracted_dir / "manifest.json"
        if not idx_path.exists():
            idx_path = extracted_dir / "index.json"
        if idx_path.exists():
            try:
                with open(idx_path) as f:
                    idx = json.load(f)
                for k, v in idx.get("extractions", {}).items():
                    if k.upper() == sanitized.upper():
                        extract_path = Path(project_dir) / "datasheets" / "extracted" / v.get("file", "")
                        break
            except (json.JSONDecodeError, OSError):
                pass
        if not extract_path.exists():
            return None

    try:
        with open(extract_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    ops = data.get("recommended_operating_conditions", {})
    temp_min = ops.get("temp_min_c")
    temp_max = ops.get("temp_max_c")
    if temp_min is not None and temp_max is not None:
        return {
            "temp_min_c": temp_min,
            "temp_max_c": temp_max,
            "source": "extraction_cache",
        }
    return None


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

    for source_name, fn in api_fns.items():
        if sources and source_name not in sources:
            continue
        try:
            time.sleep(delay)
            data = fn(mpn)
            if data:
                result["sources"][source_name] = data
                # Update best status
                raw_status = data.get("status")
                if raw_status:
                    normalized = _normalize_status(raw_status)
                    per_source_status[source_name] = normalized
                    if normalized != "unknown":
                        best_status = normalized
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
    _non_active = {"obsolete", "discontinued", "last_time_buy", "nrnd"}
    has_active = any(s == "active" for s in per_source_status.values())
    has_non_active = any(s in _non_active for s in per_source_status.values())
    result["consensus_split"] = has_active and has_non_active
    result["per_source_status"] = per_source_status
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

    # KH-348: LCSC/jlcsearch exposes no lifecycle/obsolescence data — an
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
        if status in ("nrnd", "last_time_buy", "obsolete", "discontinued"):
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
                eol_srcs = sorted(s for s, st in per_source.items() if st != 'active')
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
            finding['summary'] = f"{mpn}: active ({len(refs)} ref(s))"
            finding['components'] = sorted(refs)
            finding['nets'] = []
            finding['pins'] = []
            finding['report_context'] = {'section': 'Lifecycle', 'impact': '', 'standard_ref': ''}

        lifecycle_findings.append(finding)

        # LC-005: Single-source detection
        if status == 'active':
            active_sources = [src_name for src_name, src_data in finding.get('sources', {}).items()
                              if src_data.get('status') in ('active', 'Active', None)
                              and src_data.get('found', True)]
            total_queried = len(finding.get('sources', {}))
            if total_queried >= 2 and len(active_sources) == 1:
                lifecycle_findings.append({
                    'mpn': mpn,
                    'references': sorted(refs),
                    'status': 'active',
                    'single_source': True,
                    'source_name': active_sources[0],
                    'detector': 'audit_bom',
                    'rule_id': 'LC-005',
                    'category': 'lifecycle',
                    'severity': 'info',
                    'confidence': 'deterministic',
                    'evidence_source': 'datasheet',
                    'summary': f'{mpn}: single source ({active_sources[0]})',
                    'description': f'Component {mpn} ({len(refs)} ref(s)) is only available from {active_sources[0]} out of {total_queried} sources checked.',
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
                weeks = 0
                if isinstance(lt, (int, float)):
                    weeks = int(lt)
                elif isinstance(lt, str):
                    m = re.search(r'(\d+)', lt)
                    if m:
                        weeks = int(m.group(1))
                        if 'day' in lt.lower():
                            weeks = weeks // 7
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
                'evidence_source': 'datasheet',
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
                        "min_shortfall_c": design_min - comp_min if below_min else 0,
                        "max_shortfall_c": design_max - comp_max if above_max else 0,
                    },
                    "detector": "audit_bom",
                    "rule_id": "LT-001",
                    "category": "temperature",
                    "confidence": "deterministic",
                    "evidence_source": "api_lookup" if temp.get("source") else "heuristic_rule",
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
        "sources_available": list({src for f in lifecycle_findings for src in f.get("sources", {})}),
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Component lifecycle and temperature audit",
    )
    parser.add_argument(
        "input",
        help="Path to analyzer JSON output",
    )
    parser.add_argument(
        "--temp-range",
        help="Design temperature range: preset name (commercial, industrial, "
             "extended, automotive, military) or 'min,max' in °C. When the min "
             "is negative, use the = form so argparse doesn't read it as a flag: "
             "--temp-range=\"-40,85\"",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--analysis-dir",
        help="Write lifecycle.json to this directory (analysis folder convention). "
             "Routes the output through the current run via the manifest, matching "
             "every other analyzer. Ignored if --output is also passed.",
    )
    parser.add_argument(
        "--only",
        help="Query only specific sources (comma-separated: digikey,mouser,lcsc,element14)",
    )
    parser.add_argument(
        "--delay", type=float, default=1.0,
        help="Seconds between API calls (default: 1.0)",
    )
    parser.add_argument(
        "--suggest-alternatives", action="store_true",
        help="Search for replacement parts when EOL/NRND/obsolete (extra API calls)",
    )
    parser.add_argument(
        "--only-deterministic", action="store_true",
        help="Read raw analysis/<run>/<analyzer>.json instead of "
             "analysis/merged/<run>/<analyzer>.json. "
             "Strips Layer 2 overlays for CI/offline use (Phase 4 spec §3.4).",
    )
    args = parser.parse_args()

    # Load analyzer JSON (honor --only-deterministic: skip merged/ overlay)
    input_path = Path(args.input)
    if not args.only_deterministic:
        candidate = input_path.parent.parent / "merged" / input_path.parent.name / input_path.name
        if candidate.exists():
            input_path = candidate
    with open(input_path) as f:
        analysis = json.load(f)

    # Resolve project directory from analyzer JSON
    source_file = analysis.get("file", "")
    project_dir = str(Path(source_file).parent) if source_file else str(input_path.parent)

    # Parse temperature range
    temp_range = None
    if args.temp_range:
        if args.temp_range in _TEMP_PRESETS:
            temp_range = _TEMP_PRESETS[args.temp_range]
        else:
            parts = args.temp_range.split(",")
            if len(parts) == 2:
                try:
                    temp_range = (float(parts[0]), float(parts[1]))
                except ValueError:
                    print(f"Error: Invalid temp range '{args.temp_range}'. "
                          f"Use preset name or 'min,max'.", file=sys.stderr)
                    sys.exit(1)
            else:
                print(f"Error: Invalid temp range '{args.temp_range}'. "
                      f"Presets: {', '.join(_TEMP_PRESETS.keys())}", file=sys.stderr)
                sys.exit(1)

    # Parse sources
    sources = args.only.split(",") if args.only else []

    # Run audit
    result = audit_bom(analysis, project_dir=project_dir, temp_range=temp_range,
                       sources=sources, delay=args.delay,
                       suggest_alternatives=args.suggest_alternatives)

    # Output
    output_json = json.dumps(result, indent=2)
    output_path = args.output
    analysis_dir_mode = (not output_path
                         and hasattr(args, "analysis_dir")
                         and args.analysis_dir)

    if analysis_dir_mode:
        import tempfile
        from analysis_cache import overwrite_current, CANONICAL_OUTPUTS, get_current_run
        analysis_dir = args.analysis_dir
        if not os.path.isabs(analysis_dir):
            analysis_dir = os.path.abspath(analysis_dir)
        filename = CANONICAL_OUTPUTS.get("lifecycle", "lifecycle.json")
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_out = os.path.join(tmp_dir, filename)
            with open(tmp_out, "w") as f:
                f.write(output_json)
            overwrite_current(analysis_dir, tmp_dir, source_hashes=None)
        current = get_current_run(analysis_dir)
        if current:
            out_path = os.path.join(current[0], filename)
        else:
            out_path = os.path.join(analysis_dir, filename)
        print(f"Audit written to {out_path}", file=sys.stderr)
    elif output_path:
        with open(output_path, "w") as f:
            f.write(output_json)
        print(f"Audit written to {output_path}", file=sys.stderr)
    else:
        print(output_json)

    # Summary to stderr
    summary = result.get("lifecycle_summary", {})
    total = result.get("components_checked", 0)
    print(f"\nLifecycle audit: {total} components checked", file=sys.stderr)
    for status_key in ("active", "nrnd", "last_time_buy", "obsolete", "discontinued", "unknown"):
        count = summary.get(status_key, 0)
        if count:
            print(f"  {status_key}: {count}", file=sys.stderr)

    if result.get("temperature_summary"):
        ts = result["temperature_summary"]
        print(f"Temperature audit: {ts['components_checked']} checked, "
              f"{ts['components_failing_spec']} failing "
              f"({ts['design_target']['grade']} range)", file=sys.stderr)

    for obs in result.get("observations", []):
        print(f"  ! {obs}", file=sys.stderr)


if __name__ == "__main__":
    main()
