#!/usr/bin/env python3
"""Compute deterministic metrics for Amazon SP-API Sales & Traffic reports.

This script intentionally produces metrics only. It does not generate the final
business narrative report; the LLM should use this compact JSON plus the skill's
report-template references to write the report.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

MetricRow = dict[str, Any]


def _amount(container: dict[str, Any], key: str) -> float:
    value = (container or {}).get(key) or {}
    if isinstance(value, dict):
        return float(value.get("amount") or 0)
    return float(value or 0)


def _currency_status(report: dict[str, Any]) -> tuple[str | None, list[str], int]:
    currencies: set[str] = set()
    missing = 0
    sources = (
        (report.get("salesAndTrafficByDate"), "salesByDate"),
        (report.get("salesAndTrafficByAsin"), "salesByAsin"),
    )
    for rows, sales_key in sources:
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            sales = row.get(sales_key) or {}
            if not isinstance(sales, dict):
                continue
            for amount_key in ("orderedProductSales", "orderedProductSalesB2B"):
                if amount_key not in sales:
                    continue
                value = sales.get(amount_key)
                code = value.get("currencyCode") if isinstance(value, dict) else None
                if code:
                    currencies.add(str(code))
                else:
                    missing += 1
    observed = sorted(currencies)
    valid = len(observed) == 1 and missing == 0
    return (observed[0] if valid else None, observed, missing)


def _date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d")
    except ValueError:
        return None


def _pct(numerator: float, denominator: float) -> float | None:
    if not denominator:
        return None
    return numerator / denominator * 100


def _round(value: float | None, places: int = 2) -> float | None:
    if value is None:
        return None
    return round(value, places)


def _flatten_daily(row: dict[str, Any]) -> MetricRow:
    sales = row.get("salesByDate") or {}
    traffic = row.get("trafficByDate") or {}
    return {
        "date": row.get("date"),
        "ordered_product_sales": _amount(sales, "orderedProductSales"),
        "ordered_product_sales_b2b": _amount(sales, "orderedProductSalesB2B"),
        "b2b_revenue_present": "orderedProductSalesB2B" in sales,
        "units_ordered": int(sales.get("unitsOrdered", 0) or 0),
        "units_ordered_b2b": int(sales.get("unitsOrderedB2B", 0) or 0),
        "b2b_units_present": "unitsOrderedB2B" in sales,
        "total_order_items": int(sales.get("totalOrderItems", 0) or 0),
        "total_order_items_b2b": int(sales.get("totalOrderItemsB2B", 0) or 0),
        "sessions": int(traffic.get("sessions", 0) or 0),
        "sessions_b2b": int(traffic.get("sessionsB2B", 0) or 0),
        "page_views": int(traffic.get("pageViews", 0) or 0),
        "page_views_b2b": int(traffic.get("pageViewsB2B", 0) or 0),
        "buy_box_percentage": _round(float(traffic["buyBoxPercentage"]))
        if traffic.get("buyBoxPercentage") is not None
        else None,
        "unit_session_percentage": _round(float(traffic["unitSessionPercentage"]))
        if traffic.get("unitSessionPercentage") is not None
        else None,
    }


def _flatten_asin(row: dict[str, Any]) -> MetricRow:
    sales = row.get("salesByAsin") or {}
    traffic = row.get("trafficByAsin") or {}
    units = int(sales.get("unitsOrdered", 0) or 0)
    sessions = int(traffic.get("sessions", 0) or 0)
    revenue = _amount(sales, "orderedProductSales")
    b2b_revenue = _amount(sales, "orderedProductSalesB2B")
    explicit_conversion = traffic.get("unitSessionPercentage")
    conversion = float(explicit_conversion) if explicit_conversion is not None else _pct(units, sessions)
    return {
        "parent_asin": row.get("parentAsin"),
        "child_asin": row.get("childAsin"),
        "ordered_product_sales": revenue,
        "ordered_product_sales_b2b": b2b_revenue,
        "b2b_revenue_present": "orderedProductSalesB2B" in sales,
        "units_ordered": units,
        "units_ordered_b2b": int(sales.get("unitsOrderedB2B", 0) or 0),
        "b2b_units_present": "unitsOrderedB2B" in sales,
        "total_order_items": int(sales.get("totalOrderItems", 0) or 0),
        "total_order_items_b2b": int(sales.get("totalOrderItemsB2B", 0) or 0),
        "sessions": sessions,
        "sessions_b2b": int(traffic.get("sessionsB2B", 0) or 0),
        "page_views": int(traffic.get("pageViews", 0) or 0),
        "page_views_b2b": int(traffic.get("pageViewsB2B", 0) or 0),
        "buy_box_percentage": _round(float(traffic["buyBoxPercentage"]))
        if traffic.get("buyBoxPercentage") is not None
        else None,
        "unit_session_percentage": _round(conversion),
        "average_selling_price": _round(revenue / units) if units else None,
        "b2b_revenue_share_pct": _round(_pct(b2b_revenue, revenue))
        if "orderedProductSalesB2B" in sales
        else None,
    }


def _moving_average(values: list[float], window: int = 7, min_periods: int = 3) -> list[float | None]:
    output: list[float | None] = []
    for index in range(len(values)):
        sample = values[max(0, index - window + 1) : index + 1]
        output.append(sum(sample) / len(sample) if len(sample) >= min_periods else None)
    return output


def _pct_change(values: list[float]) -> list[float | None]:
    changes: list[float | None] = [None]
    for previous, current in zip(values, values[1:]):
        changes.append(_pct(current - previous, previous) if previous else None)
    return changes


def _daily_metrics(
    rows: list[MetricRow], *, anomaly_threshold_pct: float = 20
) -> tuple[list[MetricRow], dict[str, Any]]:
    rows = sorted(rows, key=lambda row: row.get("date") or "")
    revenue = [float(row["ordered_product_sales"]) for row in rows]
    dod = _pct_change(revenue)
    ma7 = _moving_average(revenue)
    daily_table: list[MetricRow] = []
    for index, row in enumerate(rows):
        ma_value = ma7[index]
        deviation = _pct(row["ordered_product_sales"] - ma_value, ma_value) if ma_value else None
        daily_table.append(
            {
                "date": row["date"],
                "revenue": _round(row["ordered_product_sales"]),
                "b2b_revenue": _round(row["ordered_product_sales_b2b"]),
                "sessions": row["sessions"],
                "page_views": row["page_views"],
                "units": row["units_ordered"],
                "unit_session_pct": _round(row["unit_session_percentage"]),
                "dod_revenue_pct": _round(dod[index]),
                "ma7_revenue": _round(ma_value),
                "ma7_deviation_pct": _round(deviation),
                "anomaly": "spike"
                if deviation is not None and deviation >= anomaly_threshold_pct
                else "drop"
                if deviation is not None and deviation <= -anomaly_threshold_pct
                else "",
            }
        )

    dow: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        parsed = _date(row.get("date"))
        if parsed:
            dow[parsed.strftime("%A")].append(float(row["ordered_product_sales"]))
    calendar_order = (
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    )
    dow_averages = {
        day: _round(sum(dow[day]) / len(dow[day])) for day in calendar_order if day in dow
    }
    weekday_values = [
        value for day in calendar_order[:5] for value in dow.get(day, [])
    ]
    weekend_values = [
        value for day in calendar_order[5:] for value in dow.get(day, [])
    ]
    weekday_average = (
        sum(weekday_values) / len(weekday_values) if weekday_values else None
    )
    weekend_average = (
        sum(weekend_values) / len(weekend_values) if weekend_values else None
    )
    summary = {
        "period_revenue": _round(sum(revenue)),
        "daily_average_revenue": _round(sum(revenue) / len(revenue)) if revenue else 0,
        "best_day": max(daily_table, key=lambda row: row["revenue"]) if daily_table else None,
        "worst_day": min(daily_table, key=lambda row: row["revenue"]) if daily_table else None,
        "anomaly_threshold_pct": anomaly_threshold_pct,
        "anomaly_count": sum(1 for row in daily_table if row["anomaly"]),
        "weekday_average_revenue": _round(weekday_average),
        "weekend_average_revenue": _round(weekend_average),
        "weekend_vs_weekday_gap_pct": _round(
            _pct((weekend_average or 0) - weekday_average, weekday_average)
            if weekday_average is not None and weekend_average is not None
            else None
        ),
        "day_of_week_average_revenue": dow_averages,
    }
    if len(revenue) >= 14:
        previous = sum(revenue[-14:-7])
        recent = sum(revenue[-7:])
        summary["wow_revenue_pct"] = _round(_pct(recent - previous, previous))
    else:
        summary["wow_revenue_pct"] = None
    return daily_table, summary


def _compact_asin(row: MetricRow, *, include_money: bool = True) -> MetricRow:
    return {
        "parent_asin": row.get("parent_asin"),
        "child_asin": row.get("child_asin"),
        "revenue": _round(row["ordered_product_sales"]) if include_money else None,
        "sessions": row["sessions"],
        "page_views": row["page_views"],
        "units": row["units_ordered"],
        "unit_session_pct": _round(row.get("unit_session_percentage")),
        "average_selling_price": _round(row.get("average_selling_price"))
        if include_money
        else None,
        "b2b_revenue": _round(row["ordered_product_sales_b2b"])
        if include_money
        else None,
        "b2b_revenue_share_pct": _round(row.get("b2b_revenue_share_pct"))
        if include_money
        else None,
    }


def _top(
    rows: list[MetricRow], key: str, limit: int, *, include_money: bool = True
) -> list[MetricRow]:
    return [
        _compact_asin(row, include_money=include_money)
        for row in sorted(rows, key=lambda row: row.get(key) or 0, reverse=True)[:limit]
    ]


def compute_metrics(
    report: dict[str, Any],
    *,
    top_n: int = 10,
    anomaly_threshold_pct: float = 20,
    low_conversion_min_sessions: int = 100,
    low_conversion_max_pct: float = 10,
    b2b_heavy_min_share_pct: float = 50,
) -> dict[str, Any]:
    spec_value = report.get("reportSpecification")
    spec = spec_value if isinstance(spec_value, dict) else {}
    daily_source = report.get("salesAndTrafficByDate")
    asin_source = report.get("salesAndTrafficByAsin")
    daily_source_valid = isinstance(daily_source, list) and all(
        isinstance(row, dict) for row in daily_source
    )
    asin_source_valid = isinstance(asin_source, list) and all(
        isinstance(row, dict) for row in asin_source
    )
    daily = [_flatten_daily(row) for row in daily_source] if daily_source_valid else []
    asins = [_flatten_asin(row) for row in asin_source] if asin_source_valid else []
    top_n = max(1, min(top_n, 50))

    report_options = spec.get("reportOptions")
    report_options = report_options if isinstance(report_options, dict) else {}
    date_granularity = str(report_options.get("dateGranularity") or "DAY").upper()
    marketplace_ids = spec.get("marketplaceIds")
    marketplace_valid = (
        isinstance(marketplace_ids, list)
        and len(marketplace_ids) == 1
        and isinstance(marketplace_ids[0], str)
        and bool(marketplace_ids[0])
    )
    shape_valid = bool(spec) and daily_source_valid and asin_source_valid
    report_type_valid = spec.get("reportType") == "GET_SALES_AND_TRAFFIC_REPORT"
    currency, observed_currencies, missing_currency_values = _currency_status(report)

    total_revenue = sum(row["ordered_product_sales"] for row in daily) if daily else sum(row["ordered_product_sales"] for row in asins)
    b2b_revenue = sum(row["ordered_product_sales_b2b"] for row in daily) if daily else sum(row["ordered_product_sales_b2b"] for row in asins)
    total_units = sum(row["units_ordered"] for row in daily) if daily else sum(row["units_ordered"] for row in asins)
    b2b_units = sum(row["units_ordered_b2b"] for row in daily) if daily else sum(row["units_ordered_b2b"] for row in asins)
    total_sessions = sum(row["sessions"] for row in daily) if daily else sum(row["sessions"] for row in asins)
    total_page_views = sum(row["page_views"] for row in daily) if daily else sum(row["page_views"] for row in asins)
    total_order_items = sum(row["total_order_items"] for row in daily) if daily else sum(row["total_order_items"] for row in asins)
    buy_box_rows = [
        row
        for row in daily
        if row.get("buy_box_percentage") is not None and row["page_views"] > 0
    ]

    totals_source = daily if daily else asins
    b2b_revenue_fields_present = bool(totals_source) and all(
        row["b2b_revenue_present"] for row in totals_source
    )
    b2b_units_fields_present = bool(totals_source) and all(
        row["b2b_units_present"] for row in totals_source
    )
    b2b_fields_present = b2b_revenue_fields_present and b2b_units_fields_present
    b2b_subset_valid = bool(
        b2b_fields_present
        and 0 <= b2b_revenue <= total_revenue
        and 0 <= b2b_units <= total_units
    )

    currency_valid = currency is not None
    daily_available = date_granularity == "DAY" and bool(daily) and currency_valid
    daily_table, trend_summary = (
        _daily_metrics(daily, anomaly_threshold_pct=anomaly_threshold_pct)
        if daily_available
        else ([], {})
    )
    low_conversion = [
        row
        for row in asins
        if row["sessions"] >= low_conversion_min_sessions
        and row.get("unit_session_percentage") is not None
        and row["unit_session_percentage"] < low_conversion_max_pct
    ]
    b2b_rows = [row for row in asins if row["ordered_product_sales_b2b"] > 0]
    b2b_heavy = [
        row
        for row in b2b_rows
        if row["ordered_product_sales"]
        and row["ordered_product_sales_b2b"] / row["ordered_product_sales"] * 100
        >= b2b_heavy_min_share_pct
    ]

    return {
        "layout_version": 1,
        "source": {
            "report_type": spec.get("reportType"),
            "data_start_time": spec.get("dataStartTime"),
            "data_end_time": spec.get("dataEndTime"),
            "marketplace_ids": marketplace_ids if isinstance(marketplace_ids, list) else [],
            "report_options": report_options,
            "currency": currency,
            "analysis_parameters": {
                "top_n": top_n,
                "anomaly_threshold_pct": anomaly_threshold_pct,
                "low_conversion_min_sessions": low_conversion_min_sessions,
                "low_conversion_max_pct": low_conversion_max_pct,
                "b2b_heavy_min_share_pct": b2b_heavy_min_share_pct,
            },
            "observed_start_date": daily_table[0]["date"] if daily_table else None,
            "observed_end_date": daily_table[-1]["date"] if daily_table else None,
            "field_sources": {
                "daily_revenue": "salesAndTrafficByDate[].salesByDate.orderedProductSales.amount",
                "daily_b2b_revenue": "salesAndTrafficByDate[].salesByDate.orderedProductSalesB2B.amount",
                "daily_units": "salesAndTrafficByDate[].salesByDate.unitsOrdered",
                "daily_sessions": "salesAndTrafficByDate[].trafficByDate.sessions",
                "daily_page_views": "salesAndTrafficByDate[].trafficByDate.pageViews",
                "daily_conversion": "salesAndTrafficByDate[].trafficByDate.unitSessionPercentage",
                "asin_revenue": "salesAndTrafficByAsin[].salesByAsin.orderedProductSales.amount",
                "asin_units": "salesAndTrafficByAsin[].salesByAsin.unitsOrdered",
                "asin_sessions": "salesAndTrafficByAsin[].trafficByAsin.sessions",
                "asin_page_views": "salesAndTrafficByAsin[].trafficByAsin.pageViews",
                "asin_conversion": "salesAndTrafficByAsin[].trafficByAsin.unitSessionPercentage",
            },
        },
        "row_counts": {
            "daily_rows": len(daily),
            "asin_rows": len(asins),
            "active_asin_rows": sum(1 for row in asins if row["sessions"] or row["ordered_product_sales"]),
            "asins_with_sales": sum(1 for row in asins if row["ordered_product_sales"]),
            "asins_with_traffic": sum(1 for row in asins if row["sessions"]),
        },
        "portfolio": {
            "ordered_product_sales": _round(total_revenue) if currency_valid else None,
            "ordered_product_sales_b2b": _round(b2b_revenue)
            if currency_valid and b2b_fields_present
            else None,
            "non_b2b_revenue": _round(total_revenue - b2b_revenue)
            if b2b_subset_valid and currency_valid
            else None,
            "units_ordered": total_units,
            "units_ordered_b2b": b2b_units,
            "non_b2b_units": total_units - b2b_units if b2b_subset_valid else None,
            "total_order_items": total_order_items,
            "sessions": total_sessions,
            "page_views": total_page_views,
            "unit_session_pct": _round(_pct(total_units, total_sessions)),
            "b2b_revenue_share_pct": _round(_pct(b2b_revenue, total_revenue))
            if currency_valid and b2b_fields_present
            else None,
            "b2b_units_share_pct": _round(_pct(b2b_units, total_units)),
            "average_selling_price": _round(total_revenue / total_units)
            if currency_valid and total_units
            else None,
            "buy_box_pct": _round(
                sum(row["buy_box_percentage"] * row["page_views"] for row in buy_box_rows)
                / sum(row["page_views"] for row in buy_box_rows)
            )
            if buy_box_rows
            else None,
            "buy_box_weight": "page_views" if buy_box_rows else None,
        },
        "daily_trends": {
            "available": daily_available,
            "granularity": date_granularity,
            "reason": None
            if daily_available
            else "Daily trend metrics require DAY dateGranularity, at least one date row, and one validated currency.",
            "summary": trend_summary,
            "rows": daily_table,
        },
        "asin_rankings": {
            "top_by_revenue": _top(asins, "ordered_product_sales", top_n)
            if currency_valid
            else [],
            "top_by_sessions": _top(
                asins, "sessions", top_n, include_money=currency_valid
            ),
            "top_by_units": _top(
                asins, "units_ordered", top_n, include_money=currency_valid
            ),
            "high_traffic_low_conversion": [
                _compact_asin(row, include_money=currency_valid)
                for row in sorted(
                    low_conversion, key=lambda row: row["sessions"], reverse=True
                )[:top_n]
            ],
        },
        "b2b": {
            "top_by_revenue": _top(
                b2b_rows, "ordered_product_sales_b2b", top_n
            )
            if currency_valid
            else [],
            "b2b_heavy_asins": [
                _compact_asin(row)
                for row in sorted(
                    b2b_heavy,
                    key=lambda row: row["ordered_product_sales_b2b"],
                    reverse=True,
                )[:top_n]
            ]
            if currency_valid
            else [],
        },
        "validation": {
            "data_complete": shape_valid and bool(daily or asins),
            "data_available": bool(daily or asins),
            "daily_totals_source": "salesAndTrafficByDate" if daily else "salesAndTrafficByAsin",
            "b2b_fields_present": b2b_fields_present,
            "b2b_available": b2b_fields_present,
            "b2b_subset_valid": b2b_subset_valid,
            "currency_valid": currency_valid,
            "observed_currencies": observed_currencies,
            "missing_currency_values": missing_currency_values,
            "report_type_valid": report_type_valid,
            "marketplace_valid": marketplace_valid,
            "has_expected_sp_api_shape": shape_valid,
        },
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compute compact Sales & Traffic metrics JSON.")
    parser.add_argument("--input", required=True, help="Path to GET_SALES_AND_TRAFFIC_REPORT JSON")
    parser.add_argument("--metrics-out", help="Optional path for metrics JSON")
    parser.add_argument("--top-n", type=int, default=10, help="Maximum rows in top-N tables")
    parser.add_argument(
        "--anomaly-threshold-pct",
        type=float,
        default=20,
        help="Absolute MA7 deviation percentage used for spike/drop flags",
    )
    parser.add_argument(
        "--low-conversion-min-sessions",
        type=int,
        default=100,
        help="Minimum sessions for the low-conversion ASIN list",
    )
    parser.add_argument(
        "--low-conversion-max-pct",
        type=float,
        default=10,
        help="Exclusive unit-session percentage ceiling for low conversion",
    )
    parser.add_argument(
        "--b2b-heavy-min-share-pct",
        type=float,
        default=50,
        help="Inclusive B2B revenue-share percentage for B2B-heavy ASINs",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    report = json.loads(Path(args.input).read_text(encoding="utf-8"))
    metrics = compute_metrics(
        report,
        top_n=args.top_n,
        anomaly_threshold_pct=args.anomaly_threshold_pct,
        low_conversion_min_sessions=args.low_conversion_min_sessions,
        low_conversion_max_pct=args.low_conversion_max_pct,
        b2b_heavy_min_share_pct=args.b2b_heavy_min_share_pct,
    )
    payload = json.dumps(metrics, indent=2 if args.pretty else None, sort_keys=False)
    if args.metrics_out:
        Path(args.metrics_out).write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
