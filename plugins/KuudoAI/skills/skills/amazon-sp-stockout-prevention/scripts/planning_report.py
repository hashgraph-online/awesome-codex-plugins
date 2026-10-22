#!/usr/bin/env python3
"""Summarize Amazon's FBA inventory planning report for stockout triage.

Reads GET_FBA_INVENTORY_PLANNING_DATA (tab-separated) from the pre-signed URL
returned by getReportDocument, or from a local file, and prints compact JSON:
one row per SKU with Amazon's days of supply, recommended ship-in quantity and
date, health status, and a risk band. The download is streamed into memory and
never written to disk, because the report is the seller's data.

Usage (filter first; the default answer is the at-risk slice):
  planning_report.py URL_OR_PATH                       # at-risk bands, top 25
  planning_report.py URL_OR_PATH --skus A,B             # just these SKUs
  planning_report.py URL_OR_PATH --max-days 30          # days of supply < 30
  planning_report.py URL_OR_PATH --bands CRITICAL,WARNING --min-t30 10
  planning_report.py URL_OR_PATH --needs-ship-in        # Amazon recommends a ship-in
  planning_report.py URL_OR_PATH --in-transit           # SKUs with stock on the way
  planning_report.py URL_OR_PATH --all --limit 0        # everything: large, see below

Filters combine with AND. band_counts always covers the whole report, and the
output says how many rows matched, how many were printed, and roughly how
large the full match would be. --all with more than 60 matching rows adds a
context_warning. Only ask for everything when the user explicitly wants it.

Bands: OUT_OF_STOCK (0 available, sold in the last 30 days), CRITICAL
(<7 days), WARNING (<21), OUT_NO_RECENT_SALES (0 available and no recent sales,
but Amazon recommends a ship-in: confirm the listing is active), HEALTHY,
INACTIVE (0 available, no sales, no recommendation), UNKNOWN (no
days-of-supply value). By default only the at-risk bands are listed; --all
lists every SKU. Standard library only (Python 3.9+).
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import sys
import urllib.request

# Report columns this summary uses, keyed by output field. A tuple lists
# alternative header names: Amazon's documented names and the live report's
# headers don't always agree (docs: "Reserved FC Transfer", live: "fc-transfer").
COLUMNS = {
    "sku": "sku",
    "asin": "asin",
    "product_name": "product-name",
    "available": "available",
    "inbound_quantity": "inbound-quantity",
    "inbound_working": "inbound-working",
    "inbound_shipped": "inbound-shipped",
    "inbound_received": "inbound-received",
    "reserved_fc_transfer": ("fc-transfer", "Reserved FC Transfer"),
    "reserved_fc_processing": "Reserved FC Processing",
    "units_shipped_t7": "units-shipped-t7",
    "units_shipped_t30": "units-shipped-t30",
    "days_of_supply": "days-of-supply",
    "total_days_of_supply": "Total Days of Supply (including units from open shipments)",
    "recommended_ship_in_quantity": "Recommended ship-in quantity",
    "recommended_ship_in_date": "Recommended ship-in date",
    "health_status": "fba-inventory-level-health-status",
    "alert": "alert",
    "low_inventory_fee_this_week": "Low-Inventory-Level fee applied in current week?",
    "snapshot_date": "snapshot-date",
}
# Fields printed per row by default; --full prints every field above.
COMPACT = ("sku", "band", "available", "inbound_in_transit", "units_shipped_t7",
           "units_shipped_t30", "days_of_supply", "total_days_of_supply",
           "recommended_ship_in_quantity", "recommended_ship_in_date",
           "health_status", "low_inventory_fee_this_week")
NUMERIC = {
    "available", "inbound_quantity", "inbound_working", "inbound_shipped",
    "inbound_received", "reserved_fc_transfer", "reserved_fc_processing",
    "units_shipped_t7", "units_shipped_t30", "days_of_supply",
    "total_days_of_supply", "recommended_ship_in_quantity",
}


def read_text(source: str) -> str:
    """Return the report text from an HTTPS URL or a local path."""
    if source.startswith(("https://", "http://")):
        with urllib.request.urlopen(source, timeout=120) as response:
            raw = response.read()
    else:
        with open(source, "rb") as handle:
            raw = handle.read()
    if raw[:2] == b"\x1f\x8b":  # GZIP when compressionAlgorithm is set
        raw = gzip.decompress(raw)
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def number(value: str | None) -> float | None:
    if value is None or value.strip() in ("", "-", "N/A"):
        return None
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def pick(record: dict, column: str | tuple) -> str | None:
    for name in (column if isinstance(column, tuple) else (column,)):
        if name in record:
            return record[name]
    return None


def band(row: dict, critical: float, warning: float) -> str:
    """Risk band. Zero stock is split so dormant SKUs don't read as critical."""
    available = row["available"] or 0
    sold = row["units_shipped_t30"] or 0
    ship_in = row["recommended_ship_in_quantity"] or 0
    if available <= 0:
        if sold > 0:
            return "OUT_OF_STOCK"
        return "OUT_NO_RECENT_SALES" if ship_in > 0 else "INACTIVE"
    days = row["days_of_supply"]
    if days is None:
        return "UNKNOWN"
    if days < critical:
        return "CRITICAL"
    if days < warning:
        return "WARNING"
    return "HEALTHY"


def summarize(text: str, args: argparse.Namespace) -> dict:
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    header = reader.fieldnames or []
    names = lambda c: c if isinstance(c, tuple) else (c,)
    missing = [names(col)[0] for col in COLUMNS.values() if not any(n in header for n in names(col))]
    wanted = {s.strip() for s in args.skus.split(",")} if args.skus else None
    bands = {b.strip().upper() for b in args.bands.split(",")} if args.bands else None

    rows = []
    for record in reader:          # every row is parsed and counted; filters apply only to display
        row = {}
        for field, column in COLUMNS.items():
            value = pick(record, column)
            row[field] = number(value) if field in NUMERIC else (value or None)
        # Units actually on their way: shipped plus at the FC being received.
        # inbound_quantity also counts working units that haven't left the seller.
        row["inbound_in_transit"] = (row["inbound_shipped"] or 0) + (row["inbound_received"] or 0)
        row["band"] = band(row, args.critical, args.warning)
        rows.append(row)

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["band"]] = counts.get(row["band"], 0) + 1

    at_risk = ("OUT_OF_STOCK", "CRITICAL", "WARNING", "OUT_NO_RECENT_SALES")
    filtered = bool(wanted or bands or args.max_days is not None or args.min_t30 is not None
                    or args.needs_ship_in or args.in_transit)

    def keep(r: dict) -> bool:
        if wanted and r["sku"] not in wanted:
            return False
        if bands and r["band"] not in bands:
            return False
        if not (args.all or filtered) and r["band"] not in at_risk:
            return False
        if args.max_days is not None and (r["days_of_supply"] is None or r["days_of_supply"] >= args.max_days):
            return False
        if args.min_t30 is not None and (r["units_shipped_t30"] or 0) < args.min_t30:
            return False
        if args.needs_ship_in and not (r["recommended_ship_in_quantity"] or 0) > 0:
            return False
        if args.in_transit and not r["inbound_in_transit"] > 0:
            return False
        return True

    shown = [r for r in rows if keep(r)]
    order = {b: i for i, b in enumerate(at_risk + ("UNKNOWN", "HEALTHY", "INACTIVE"))}
    shown.sort(key=lambda r: (order[r["band"]], r["days_of_supply"] if r["days_of_supply"] is not None else 1e9))
    matched = len(shown)
    projected = [{k: r[k] for k in COMPACT} for r in shown] if not args.full else shown
    full_match_bytes = sum(len(json.dumps(r, separators=(",", ":"))) + 3 for r in projected)
    if args.limit:
        projected = projected[: args.limit]
    shown = projected

    return {
        "source": "GET_FBA_INVENTORY_PLANNING_DATA",
        "snapshot_date": rows[0]["snapshot_date"] if rows else None,
        "skus_in_report": len(rows),
        "band_counts": counts,
        "thresholds_days": {"critical_below": args.critical, "warning_below": args.warning},
        "missing_columns": missing,
        "rows_matched": matched,
        "rows_printed": len(shown),
        "rows_omitted": matched - len(shown),
        "full_match_size_kb": round(full_match_bytes / 1024, 1),
        **({"context_warning": (
            f"{matched} rows (about {round(full_match_bytes / 1024)} KB) match. "
            "That is a lot of context. Prefer a filter (--max-days, --bands, "
            "--min-t30, --needs-ship-in, --in-transit, --skus) unless the user "
            "explicitly asked for everything.")} if args.all and matched > 60 else {}),
        "rows": shown,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", help="Pre-signed report URL or local TSV path")
    parser.add_argument("--skus", help="Comma-separated seller SKUs to include")
    parser.add_argument("--all", action="store_true", help="Every band, including HEALTHY/INACTIVE (large!)")
    parser.add_argument("--bands", help="Comma-separated bands to include, e.g. CRITICAL,WARNING")
    parser.add_argument("--max-days", type=float, help="Only SKUs with days of supply below this")
    parser.add_argument("--min-t30", type=float, help="Only SKUs that shipped at least this many units in 30 days")
    parser.add_argument("--needs-ship-in", action="store_true", help="Only SKUs Amazon recommends shipping in")
    parser.add_argument("--in-transit", action="store_true", help="Only SKUs with shipped/receiving inbound units")
    parser.add_argument("--limit", type=int, default=25, help="Max rows to print (0 = no cap)")
    parser.add_argument("--full", action="store_true", help="Print every field per row")
    parser.add_argument("--critical", type=float, default=7.0)
    parser.add_argument("--warning", type=float, default=21.0)
    args = parser.parse_args()
    try:
        text = read_text(args.source)
    except Exception as exc:  # expired URL, network, or file errors
        error = {"error": f"{type(exc).__name__}: {exc}"}
        if args.source.startswith(("https://", "http://")):
            error["hint"] = ("Pre-signed URLs expire after about 5 minutes. "
                             "Call getReportDocument again for a fresh one.")
        print(json.dumps(error))
        return 1
    result = summarize(text, args)
    rows = result.pop("rows")
    # One compact line per row keeps 500-SKU output small and still readable.
    head = json.dumps(result, separators=(",", ":"))
    body = ",\n ".join(json.dumps(r, separators=(",", ":")) for r in rows)
    print(head[:-1] + ',"rows":[\n ' + body + "\n]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
