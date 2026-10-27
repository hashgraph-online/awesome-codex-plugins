from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "compute_metrics.py"
SPEC = importlib.util.spec_from_file_location("compute_metrics", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def amount(value: float, currency: str | None = "USD") -> dict[str, object]:
    result: dict[str, object] = {"amount": value}
    if currency is not None:
        result["currencyCode"] = currency
    return result


def report(
    *,
    granularity: str = "DAY",
    daily_rows: list[dict[str, object]] | None = None,
    asin_rows: list[dict[str, object]] | None = None,
    marketplace_ids: list[str] | None = None,
) -> dict[str, object]:
    return {
        "reportSpecification": {
            "reportType": "GET_SALES_AND_TRAFFIC_REPORT",
            "reportOptions": {"dateGranularity": granularity, "asinGranularity": "CHILD"},
            "dataStartTime": "2026-01-01",
            "dataEndTime": "2026-01-31",
            "marketplaceIds": marketplace_ids or ["ATVPDKIKX0DER"],
        },
        "salesAndTrafficByDate": daily_rows or [],
        "salesAndTrafficByAsin": asin_rows or [],
    }


def daily_row(
    date: str,
    revenue: float,
    *,
    currency: str | None = "USD",
    units: int = 1,
    sessions: int = 10,
    page_views: int = 20,
    buy_box: float = 50,
    include_b2b: bool = False,
    b2b_revenue: float = 0,
    b2b_units: int = 0,
) -> dict[str, object]:
    sales: dict[str, object] = {
        "orderedProductSales": amount(revenue, currency),
        "unitsOrdered": units,
        "totalOrderItems": units,
    }
    if include_b2b:
        sales.update(
            {
                "orderedProductSalesB2B": amount(b2b_revenue, currency),
                "unitsOrderedB2B": b2b_units,
                "totalOrderItemsB2B": b2b_units,
            }
        )
    return {
        "date": date,
        "salesByDate": sales,
        "trafficByDate": {
            "sessions": sessions,
            "pageViews": page_views,
            "buyBoxPercentage": buy_box,
            "unitSessionPercentage": units / sessions * 100 if sessions else 0,
        },
    }


def asin_row(
    asin: str,
    revenue: float,
    *,
    units: int = 1,
    sessions: int = 10,
    include_b2b: bool = False,
    b2b_revenue: float = 0,
    b2b_units: int = 0,
) -> dict[str, object]:
    sales: dict[str, object] = {
        "orderedProductSales": amount(revenue),
        "unitsOrdered": units,
        "totalOrderItems": units,
    }
    if include_b2b:
        sales.update(
            {
                "orderedProductSalesB2B": amount(b2b_revenue),
                "unitsOrderedB2B": b2b_units,
                "totalOrderItemsB2B": b2b_units,
            }
        )
    return {
        "parentAsin": asin,
        "childAsin": asin,
        "salesByAsin": sales,
        "trafficByAsin": {
            "sessions": sessions,
            "pageViews": sessions * 2,
            "unitSessionPercentage": units / sessions * 100 if sessions else 0,
        },
    }


class ComputeMetricsTests(unittest.TestCase):
    def test_non_daily_report_does_not_emit_daily_calculations(self) -> None:
        payload = report(
            granularity="WEEK",
            daily_rows=[daily_row("2026-01-04", 100), daily_row("2026-01-11", 120)],
        )

        metrics = MODULE.compute_metrics(payload)

        self.assertFalse(metrics["daily_trends"]["available"])
        self.assertEqual(metrics["daily_trends"]["granularity"], "WEEK")
        self.assertEqual(metrics["daily_trends"]["rows"], [])
        self.assertIn("DAY", metrics["daily_trends"]["reason"])

    def test_missing_b2b_fields_do_not_create_non_b2b_residuals(self) -> None:
        metrics = MODULE.compute_metrics(
            report(daily_rows=[daily_row("2026-01-01", 100, units=10)])
        )

        self.assertFalse(metrics["validation"]["b2b_fields_present"])
        self.assertFalse(metrics["validation"]["b2b_available"])
        self.assertIsNone(metrics["portfolio"]["non_b2b_revenue"])
        self.assertIsNone(metrics["portfolio"]["non_b2b_units"])

    def test_present_zero_b2b_fields_are_available_and_allow_residuals(self) -> None:
        metrics = MODULE.compute_metrics(
            report(
                daily_rows=[
                    daily_row(
                        "2026-01-01",
                        100,
                        units=10,
                        include_b2b=True,
                        b2b_revenue=0,
                        b2b_units=0,
                    )
                ]
            )
        )

        self.assertTrue(metrics["validation"]["b2b_fields_present"])
        self.assertTrue(metrics["validation"]["b2b_available"])
        self.assertEqual(metrics["portfolio"]["non_b2b_revenue"], 100)
        self.assertEqual(metrics["portfolio"]["non_b2b_units"], 10)

    def test_inconsistent_b2b_values_suppress_residuals(self) -> None:
        metrics = MODULE.compute_metrics(
            report(
                daily_rows=[
                    daily_row(
                        "2026-01-01",
                        100,
                        units=10,
                        include_b2b=True,
                        b2b_revenue=110,
                        b2b_units=11,
                    )
                ]
            )
        )

        self.assertFalse(metrics["validation"]["b2b_subset_valid"])
        self.assertIsNone(metrics["portfolio"]["non_b2b_revenue"])
        self.assertIsNone(metrics["portfolio"]["non_b2b_units"])

    def test_missing_or_mixed_currency_is_not_labeled_usd(self) -> None:
        missing = MODULE.compute_metrics(
            report(daily_rows=[daily_row("2026-01-01", 100, currency=None)])
        )
        mixed = MODULE.compute_metrics(
            report(
                daily_rows=[
                    daily_row("2026-01-01", 100, currency="USD"),
                    daily_row("2026-01-02", 100, currency="CAD"),
                ]
            )
        )

        self.assertIsNone(missing["source"]["currency"])
        self.assertFalse(missing["validation"]["currency_valid"])
        self.assertIsNone(mixed["source"]["currency"])
        self.assertFalse(mixed["validation"]["currency_valid"])
        self.assertEqual(mixed["validation"]["observed_currencies"], ["CAD", "USD"])
        self.assertIsNone(mixed["portfolio"]["ordered_product_sales"])
        self.assertFalse(mixed["daily_trends"]["available"])

    def test_buy_box_average_is_weighted_by_page_views(self) -> None:
        metrics = MODULE.compute_metrics(
            report(
                daily_rows=[
                    daily_row("2026-01-01", 100, page_views=100, buy_box=50),
                    daily_row("2026-01-02", 100, page_views=300, buy_box=100),
                ]
            )
        )

        self.assertEqual(metrics["portfolio"]["buy_box_pct"], 87.5)
        self.assertEqual(metrics["portfolio"]["buy_box_weight"], "page_views")

    def test_daily_summary_discloses_threshold_and_weekday_weekend_gap(self) -> None:
        rows = [
            daily_row("2026-01-05", 100),  # Monday
            daily_row("2026-01-06", 100),
            daily_row("2026-01-07", 100),
            daily_row("2026-01-10", 200),  # Saturday
            daily_row("2026-01-11", 200),  # Sunday
        ]

        metrics = MODULE.compute_metrics(report(daily_rows=rows))
        summary = metrics["daily_trends"]["summary"]

        self.assertEqual(summary["anomaly_threshold_pct"], 20)
        self.assertEqual(summary["anomaly_count"], 2)
        self.assertEqual(summary["weekday_average_revenue"], 100)
        self.assertEqual(summary["weekend_average_revenue"], 200)
        self.assertEqual(summary["weekend_vs_weekday_gap_pct"], 100)
        self.assertEqual(
            list(summary["day_of_week_average_revenue"]),
            ["Monday", "Tuesday", "Wednesday", "Saturday", "Sunday"],
        )

    def test_report_shape_validation_checks_type_marketplace_and_arrays(self) -> None:
        payload = report(marketplace_ids=["one", "two"])
        payload["reportSpecification"]["reportType"] = "OTHER_REPORT"
        payload["salesAndTrafficByDate"] = {}

        metrics = MODULE.compute_metrics(payload)

        self.assertFalse(metrics["validation"]["report_type_valid"])
        self.assertFalse(metrics["validation"]["marketplace_valid"])
        self.assertFalse(metrics["validation"]["has_expected_sp_api_shape"])

    def test_thresholds_are_configurable_and_disclosed(self) -> None:
        payload = report(
            daily_rows=[
                daily_row(
                    "2026-01-01",
                    100,
                    include_b2b=True,
                    b2b_revenue=40,
                    b2b_units=0,
                )
            ],
            asin_rows=[
                asin_row(
                    "B000000001",
                    100,
                    units=1,
                    sessions=20,
                    include_b2b=True,
                    b2b_revenue=40,
                )
            ],
        )

        metrics = MODULE.compute_metrics(
            payload,
            anomaly_threshold_pct=30,
            low_conversion_min_sessions=10,
            low_conversion_max_pct=6,
            b2b_heavy_min_share_pct=30,
        )

        self.assertEqual(
            metrics["source"]["analysis_parameters"],
            {
                "top_n": 10,
                "anomaly_threshold_pct": 30,
                "low_conversion_min_sessions": 10,
                "low_conversion_max_pct": 6,
                "b2b_heavy_min_share_pct": 30,
            },
        )
        self.assertEqual(
            metrics["asin_rankings"]["high_traffic_low_conversion"][0]["child_asin"],
            "B000000001",
        )
        self.assertEqual(
            metrics["b2b"]["b2b_heavy_asins"][0]["child_asin"],
            "B000000001",
        )

    def test_missing_b2b_fields_do_not_publish_zero_b2b_share(self) -> None:
        metrics = MODULE.compute_metrics(
            report(asin_rows=[asin_row("B000000001", 100)])
        )

        self.assertIsNone(
            metrics["asin_rankings"]["top_by_revenue"][0]["b2b_revenue_share_pct"]
        )


if __name__ == "__main__":
    unittest.main()
