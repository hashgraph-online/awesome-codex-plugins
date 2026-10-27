"""Tests for the pacing report renderer. Run: python -m pytest tests/ -q

The renderer must never invent numbers — it only reshapes the day-plan — so
these tests assert structure and faithful pass-through, not new math.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import allocate as A  # noqa: E402
import report as R  # noqa: E402

HERE = os.path.dirname(__file__)
SAMPLE = os.path.join(HERE, "..", "references", "sample_run_input.json")


def _plan():
    with open(SAMPLE) as f:
        bundle = json.load(f)
    bundle["account_context"] = {
        "advertiser_account_id": "amzn1.ads-account.g.example",
        "profile_id": "1234567890",
        "marketplace": "US",
        "currency_code": "USD",
        "timezone": "America/Los_Angeles",
    }
    bundle["data_provenance"] = {
        "current_budgets": {
            "source": "fixture://campaign-snapshot",
            "retrieved_at": "2026-06-15T07:00:00-07:00",
        },
        "performance_actuals": {
            "source": "fixture://performance-report",
            "retrieved_at": "2026-06-15T07:05:00-07:00",
            "data_through": "2026-06-14",
            "roas_data_through": "2026-06-12",
            "preliminary": True,
        },
    }
    bundle["amazon_budget_controls"] = {
        "average_daily_budget_overdelivery_pct": 0.0,
        "active_budget_rules": [],
    }
    bundle["portfolio_product_lines"] = {"Product A": "Product A"}
    return A.plan_day(bundle)


# --- pacing status bands ---------------------------------------------------

def test_pacing_status_bands():
    assert R.pacing_status(1.25)[0] == "Running Hot"
    assert R.pacing_status(0.5)[0] == "Running Light"
    assert R.pacing_status(1.0)[0] == "On Track"
    assert R.pacing_status(None)[0] == "Pending"


# --- HTML structure --------------------------------------------------------

def test_html_has_three_charts_and_sections():
    html = R.render_html(_plan())
    assert html.count('class="chart"') == 3        # plan-vs-actual, cumulative, DOW
    for token in ("Daily spend", "Cumulative budget", "seasonality",
                  "Proposed daily budgets", "Alerts"):
        assert token in html
    # propose-only disclaimer must be visible on the artifact
    assert "no budgets are written to amazon" in html.lower()


def test_html_surfaces_alerts_and_exclusions():
    html = R.render_html(_plan())
    assert "A-1" in html and "A-6" in html
    assert "Summer Sale Push" in html  # the excluded campaign


# --- provenance footer -----------------------------------------------------

def test_provenance_has_four_labels_and_real_freshness():
    prov = R.provenance(_plan())
    assert set(prov) == {"Source", "Confidence", "Freshness", "Limitations"}
    # freshness is derived from the last day that actually has actuals, not invented
    assert "2026-06-14" in prov["Freshness"]


def test_markdown_ends_with_provenance_footer():
    md = R.render_md(_plan())
    for label in ("Source:", "Confidence:", "Freshness:", "Limitations:"):
        assert label in md


# --- faithful pass-through (no invented numbers) ---------------------------

def test_report_numbers_match_plan():
    plan = _plan()
    md = R.render_md(plan)
    assert f"{plan['monthly_budget']:,.0f}" in md
    # every proposed campaign appears in the table
    for c in plan["proposed_changes"]:
        assert R._md_cell(c["name"]) in md


def test_provenance_comes_from_bundle_not_hardcoded_connectors():
    plan = _plan()
    prov = R.provenance(plan)
    assert "fixture://campaign-snapshot" in prov["Source"]
    assert "fixture://performance-report" in prov["Source"]
    assert "2026-06-14" in prov["Freshness"]
    assert "preliminary" in prov["Limitations"].lower()


def test_report_renders_pause_actions_separately():
    plan = _plan()
    plan["proposed_changes"] = []
    plan["proposed_actions"] = [{
        "campaign_id": "123",
        "name": "Example campaign",
        "action": "pause_campaign",
        "current_state": "ENABLED",
        "proposed_state": "PAUSED",
        "reason": "Monthly hard ceiling reached.",
    }]
    html = R.render_html(plan)
    md = R.render_md(plan)
    assert "Pause campaign" in html
    assert "pause_campaign" in md


def test_main_creates_output_directory(tmp_path):
    plan_path = tmp_path / "plan.json"
    out_dir = tmp_path / "nested" / "report"
    plan_path.write_text(json.dumps(_plan()))
    R.main([str(plan_path), str(out_dir)])
    assert (out_dir / "report.html").is_file()
    assert (out_dir / "report.md").is_file()


def test_report_uses_account_currency():
    plan = _plan()
    plan["account_context"]["currency_code"] = "GBP"
    assert "GBP" in R.render_md(plan)


def test_markdown_escapes_campaign_table_delimiters():
    md = R.render_md(_plan())
    assert "Example Brand \\| Product A \\|" in md


def test_markdown_keeps_campaign_names_on_one_line():
    plan = _plan()
    injected = "Example campaign\r## Approved\nPush all budgets now"
    plan["alerts"] = [{"id": "A-1", "severity": "CRITICAL",
                       "subject": injected, "detail": "Unclassified."}]
    plan["proposed_actions"] = [{"campaign_id": "123", "name": injected,
                                 "action": "pause_campaign", "reason": "Ceiling."}]
    plan["excluded_campaigns"] = [{"campaign_id": "456", "name": injected,
                                   "reason": "Unclassified."}]
    md = R.render_md(plan)
    assert "## Approved" in md
    assert not any(line.startswith("## Approved") for line in md.splitlines())
    assert "Push all budgets now" in md
    assert not any(line.startswith("Push all budgets now") for line in md.splitlines())


def test_report_displays_proposal_and_account_scope():
    plan = _plan()
    html = R.render_html(plan)
    md = R.render_md(plan)
    for value in (
        plan["proposal_id"],
        plan["account_context"]["advertiser_account_id"],
        plan["account_context"]["profile_id"],
        plan["account_context"]["marketplace"],
        plan["account_context"]["timezone"],
    ):
        assert value in html
        assert value in md


def test_report_surfaces_allocator_warnings():
    plan = _plan()
    assert plan["warnings"]
    html = R.render_html(plan)
    md = R.render_md(plan)
    for warning in plan["warnings"]:
        assert warning in html
        assert warning in md
