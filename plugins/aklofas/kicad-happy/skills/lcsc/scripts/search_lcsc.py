#!/usr/bin/env python3
"""Search LCSC Electronics / JLCPCB parts catalog.

Uses the free, unauthenticated jlcsearch community API to search components
by MPN, LCSC code, or parametric keywords. For exact Cxxxxx codes (and for
every hit in --details mode) the result is enriched from LCSC's direct
wmsc.lcsc.com product-detail endpoint, which supplies the manufacturer,
datasheet URL and price breaks that jlcsearch no longer returns.

Usage:
    python3 search_lcsc.py <query> [options]
    python3 search_lcsc.py "tactile switch" --basic
    python3 search_lcsc.py "0805 100R" --basic --in-stock
    python3 search_lcsc.py "C318884" --details
    python3 search_lcsc.py "ME2108" --json

Exit codes:
    0 = results found
    1 = no results found
    2 = API / network error
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

# Import from sibling script (same skill)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_datasheet_lcsc import (
    _get_datasheet_url,
    _get_description,
    _get_lcsc_code,
    _get_manufacturer,
    _get_mpn,
    _parse_extra,
    search_lcsc_direct,
)

_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
_JLCSEARCH_BASE = "https://jlcsearch.tscircuit.com"
_LCSC_CODE_RE = re.compile(r"^C\d+$", re.IGNORECASE)
_ENRICH_DELAY_S = 0.5  # be respectful to LCSC when enriching several hits


def search_jlcsearch(query: str, limit: int = 20, package: str = "", category: str = "") -> list[dict]:
    """Query the jlcsearch community API.

    General search returns ``{"components": [...]}``. Category endpoints
    return ``{"<category>": [...]}`` (keyed by the category name), so read
    the first list-valued key rather than assuming ``components``.
    """
    if category:
        endpoint = f"/{category.strip('/')}/list.json?search={urllib.parse.quote(query)}"
        url = f"{_JLCSEARCH_BASE}{endpoint}"
    else:
        params = [f"q={urllib.parse.quote(query)}", f"limit={max(limit, 20)}", "full=true"]
        if package:
            params.append(f"package={urllib.parse.quote(package)}")
        url = f"{_JLCSEARCH_BASE}/api/search?{'&'.join(params)}"

    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        comps = data.get("components")
        if comps is None:
            comps = next((v for v in data.values() if isinstance(v, list)), [])
        for c in comps:
            _parse_extra(c)
        return comps


def _parse_attributes(c: dict) -> dict:
    """Return parametric attributes as a dict.

    Category endpoints ship ``attributes`` as a JSON string; the wmsc
    fallback (via ``extra``) may ship a dict. Both normalize to a dict.
    """
    attrs = c.get("attributes")
    if attrs is None:
        attrs = _parse_extra(c).get("attributes")
    if isinstance(attrs, str):
        try:
            attrs = json.loads(attrs)
        except (json.JSONDecodeError, TypeError):
            return {}
    return attrs if isinstance(attrs, dict) else {}


def _price_breaks(price) -> list[dict]:
    """Normalize a price-break list to ``[{"min_qty": int, "price": float}]``.

    Accepts the wmsc ladder rows (``ladder`` / ``usdPrice``) that
    ``search_lcsc_direct`` passes through as ``price``, plus the legacy
    jlcsearch shapes (``qFrom`` / ``price`` and ``min_qty`` / ``price``).
    """
    breaks = []
    if not isinstance(price, list):
        return breaks
    for p in price:
        if not isinstance(p, dict):
            continue
        qty = p.get("ladder", p.get("min_qty", p.get("qFrom", 1)))
        val = p.get("usdPrice", p.get("price", p.get("productPrice", 0)))
        try:
            breaks.append({"min_qty": int(qty), "price": float(val)})
        except (TypeError, ValueError):
            continue
    return breaks


def normalize_component(c: dict) -> dict:
    """Normalize fields across the jlcsearch search, category and wmsc shapes."""
    attrs = _parse_attributes(c)
    lcsc_id = c.get("lcsc")

    pkg = _parse_extra(c).get("package") or c.get("package") or "-"
    desc = _get_description(c)
    if not desc and attrs:
        # Category rows ship an empty description; the parametric values are
        # the next best one-line summary.
        desc = " ".join(str(v) for v in attrs.values() if v not in (None, "", "-"))

    stock = c.get("stock")
    if stock is None:
        stock = 0

    # Basic part check (category rows may lack it; older shapes used 'basic')
    is_basic = c.get("is_basic")
    if is_basic is None:
        is_basic = bool(c.get("basic", 0))

    # Price: general search gives a scalar 'price'; category rows give
    # 'price1'; wmsc gives a ladder list in 'price'.
    prices = _price_breaks(c.get("price"))
    price = c.get("price")
    if price is None or isinstance(price, list):
        price = c.get("price1")
        if price is None:
            price = prices[0]["price"] if prices else 0.0

    return {
        "lcsc_code": _get_lcsc_code(c),
        "lcsc_id": int(lcsc_id) if str(lcsc_id or "").isdigit() else lcsc_id,
        "mpn": _get_mpn(c),
        "manufacturer": _get_manufacturer(c),
        "package": pkg,
        "description": desc.strip(),
        "is_basic": bool(is_basic),
        "stock": int(stock) if stock is not None else 0,
        "price_usd": float(price) if price else 0.0,
        "datasheet_url": _get_datasheet_url(c),
        "attributes": attrs,
        "prices": prices,
    }


def enrich_from_wmsc(item: dict) -> dict:
    """Fill blanks in a normalized item from LCSC's direct product-detail API.

    jlcsearch no longer returns manufacturer, datasheet URL or price breaks,
    so those come from wmsc.lcsc.com via ``search_lcsc_direct``. Stock and
    unit price stay as jlcsearch reported them (the JLCPCB assembly figures)
    unless jlcsearch had none.
    """
    code = item.get("lcsc_code", "")
    if not _LCSC_CODE_RE.match(code):
        return item
    direct = search_lcsc_direct(code)
    if not direct:
        return item
    detail = normalize_component(direct)
    for key in ("mpn", "manufacturer", "description", "datasheet_url"):
        if not item.get(key):
            item[key] = detail[key]
    if item.get("package") in ("", "-") and detail["package"] != "-":
        item["package"] = detail["package"]
    if not item.get("attributes"):
        item["attributes"] = detail["attributes"]
    if not item.get("prices"):
        item["prices"] = detail["prices"]
    if not item.get("stock"):
        item["stock"] = detail["stock"]
    if not item.get("price_usd"):
        item["price_usd"] = detail["price_usd"]
    return item


def format_table(results: list[dict]) -> str:
    """Format component results as a readable ASCII/Unicode table."""
    if not results:
        return "No components found."

    lines = []
    header = f"{'LCSC #':<9} {'MPN':<24} {'Package':<14} {'Type':<7} {'Stock':>9} {'Price($)':>9} {'Description'}"
    separator = "-" * 110
    lines.append(header)
    lines.append(separator)

    for item in results:
        part_type = "Basic" if item["is_basic"] else "Ext"
        mpn = item["mpn"][:23]
        pkg = item["package"][:13]
        stock_str = f"{item['stock']:,}"
        price_str = f"${item['price_usd']:.4f}" if item["price_usd"] > 0 else "-"
        desc = item["description"].replace("\n", " ")
        if len(desc) > 36:
            desc = desc[:33] + "..."
        lines.append(
            f"{item['lcsc_code']:<9} {mpn:<24} {pkg:<14} {part_type:<7} {stock_str:>9} {price_str:>9} {desc}"
        )

    return "\n".join(lines)


def format_details(item: dict) -> str:
    """Format single component with in-depth parametric details."""
    part_type = "Basic (No feeder fee on JLCPCB)" if item["is_basic"] else "Extended ($3 feeder fee on JLCPCB)"
    lines = [
        f"LCSC Code:      {item['lcsc_code']}",
        f"MPN:            {item['mpn']}",
        f"Manufacturer:   {item['manufacturer'] or '-'}",
        f"Package:        {item['package']}",
        f"JLCPCB Type:    {part_type}",
        f"Stock:          {item['stock']:,}",
        f"Unit Price:     ${item['price_usd']:.4f} USD",
        f"Datasheet:      {item['datasheet_url'] or '-'}",
        f"Description:    {item['description']}",
    ]

    attrs = item.get("attributes", {})
    if attrs:
        lines.append("Attributes:")
        for k, v in attrs.items():
            lines.append(f"  • {k}: {v}")

    prices = item.get("prices", [])
    if prices:
        lines.append("LCSC Price Breaks:")
        for p in prices:
            lines.append(f"  • {p['min_qty']}+: ${p['price']:.4f} USD")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Search LCSC Electronics and JLCPCB parts catalog.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 search_lcsc.py "tactile switch"
  python3 search_lcsc.py "0805 resistor 100R" --basic
  python3 search_lcsc.py "C318884" --details
  python3 search_lcsc.py "ME2108" --limit 5 --json
"""
    )
    parser.add_argument("query", help="Search query: MPN, LCSC code (Cxxxxx), or keywords")
    parser.add_argument("-n", "--limit", type=int, default=10, help="Max results to display (default: 10)")
    parser.add_argument("-p", "--package", default="", help="Filter by footprint / package (e.g. 0805, SOT-23)")
    parser.add_argument("--basic", action="store_true", help="Only show JLCPCB Basic parts")
    parser.add_argument("--in-stock", action="store_true", help="Only show parts with stock > 0")
    parser.add_argument("--min-stock", type=int, default=0, help="Minimum stock count required")
    parser.add_argument("--category", default="", help="Category search (resistors, capacitors, microcontrollers, voltage_regulators)")
    parser.add_argument("--sort", choices=["relevance", "price", "stock"], default="relevance", help="Sort results")
    parser.add_argument("-v", "--details", action="store_true", help="Show detailed view of results (enriched from LCSC, one extra request per result)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON format")

    args = parser.parse_args()

    query = args.query.strip()
    is_lcsc_code = bool(_LCSC_CODE_RE.match(query))
    try:
        raw_components = search_jlcsearch(
            query=query,
            limit=args.limit,
            package=args.package,
            category=args.category
        )
    except Exception as e:
        # An exact LCSC code can still be served by the direct lookup below
        if is_lcsc_code:
            raw_components = []
        else:
            print(f"Error connecting to jlcsearch API: {e}", file=sys.stderr)
            sys.exit(2)

    # Fallback to wmsc direct if jlcsearch returned nothing for Cxxxxx code
    if not raw_components and is_lcsc_code:
        direct = search_lcsc_direct(query)
        if direct:
            raw_components = [direct]

    # Normalize components
    normalized = [normalize_component(c) for c in raw_components]

    # Apply filters
    filtered = []
    for item in normalized:
        if args.basic and not item["is_basic"]:
            continue
        if args.in_stock and item["stock"] <= 0:
            continue
        if args.min_stock > 0 and item["stock"] < args.min_stock:
            continue
        if args.package and args.package.lower() not in item["package"].lower():
            continue
        filtered.append(item)

    # Sort
    if args.sort == "price":
        filtered.sort(key=lambda x: x["price_usd"])
    elif args.sort == "stock":
        filtered.sort(key=lambda x: x["stock"], reverse=True)

    # Limit
    results = filtered[:args.limit]

    # Enrich from LCSC direct: always for an exact Cxxxxx query, and for
    # every displayed hit in --details mode (manufacturer, datasheet, price
    # breaks are not in jlcsearch responses any more).
    if is_lcsc_code or args.details:
        for idx, item in enumerate(results):
            if idx:
                time.sleep(_ENRICH_DELAY_S)
            enrich_from_wmsc(item)

    if args.json:
        print(json.dumps({
            "query": query,
            "count": len(results),
            "total_matches": len(filtered),
            "components": results
        }, indent=2))
        sys.exit(0 if results else 1)

    if not results:
        print(f"No parts found matching '{query}'" + (" with specified filters." if (args.basic or args.in_stock or args.package) else "."))
        sys.exit(1)

    print(f"\nLCSC Search Results for '{query}' ({len(results)} shown of {len(filtered)} matches):\n")

    if args.details:
        for idx, item in enumerate(results, 1):
            print(f"--- Result [{idx}/{len(results)}] ---")
            print(format_details(item))
            print()
    else:
        print(format_table(results))
        basic_count = sum(1 for r in results if r["is_basic"])
        print(f"\nTip: Found {basic_count} Basic parts (no feeder setup fee on JLCPCB). Use --details for full specs.\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
