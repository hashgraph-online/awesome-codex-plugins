"""Tests that lock the allocation math. Run: python -m pytest tests/ -q

These guard the only thing in this skill that must be exact: the budgets.
"""
import json
import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import allocate as A  # noqa: E402

HERE = os.path.dirname(__file__)
SAMPLE = os.path.join(HERE, "..", "references", "sample_run_input.json")


def _bundle():
    with open(SAMPLE) as f:
        bundle = json.load(f)
    bundle.setdefault("account_context", {
        "advertiser_account_id": "amzn1.ads-account.g.example",
        "profile_id": "1234567890",
        "marketplace": "US",
        "currency_code": "USD",
        "timezone": "America/Los_Angeles",
    })
    bundle.setdefault("data_provenance", {
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
    })
    bundle.setdefault("amazon_budget_controls", {
        "average_daily_budget_overdelivery_pct": 0.0,
        "active_budget_rules": [],
    })
    bundle.setdefault("portfolio_product_lines", {"Product A": "Product A"})
    return bundle


# --- Phase 1 ---------------------------------------------------------------

def test_pool_is_dow_weighted_share():
    c = A.Controls()
    dow = _bundle()["dow_index"]
    p = A.compute_pacing(date(2026, 6, 15), 50000.0, 18000.0, dow, {}, c, None)
    assert p.remaining_budget == pytest.approx(32000.0)
    assert p.remaining_days == 16
    assert p.todays_pool == pytest.approx(1720.2, abs=1.0)


def test_last_day_takes_full_remaining():
    p = A.compute_pacing(date(2026, 6, 30), 50000.0, 49000.0, {}, {}, A.Controls(), None)
    assert p.remaining_days == 1 and p.todays_pool == pytest.approx(1000.0)


def test_hard_ceiling_pauses():
    p = A.compute_pacing(date(2026, 6, 20), 50000.0, 50500.0, {}, {}, A.Controls(), None)
    assert p.hard_ceiling_paused and p.todays_pool == 0.0


# --- Classification --------------------------------------------------------

def test_unclassified_excluded_via_plan():
    plan = A.plan_day(_bundle())
    excluded = [e["campaign_id"] for e in plan["excluded_campaigns"]]
    assert "999000111" in excluded  # "Summer Sale Push" has no strategy token
    assert any(a["id"] == "A-1" for a in plan["alerts"])


def test_longest_strategy_token_wins():
    c = A.Campaign("1", "X | PL | Brand Defense | SP", "PL", "SP", 10.0,
                   actual_roas=9.0, days_of_data=14)
    ok, _, _ = A.classify(c, {"PL": "PL"})
    assert ok and c.strategy == "Brand Defense"


# --- Phase 2/3 -------------------------------------------------------------

def test_allocation_sums_to_pool_unconstrained():
    b = _bundle()
    b["strategy_ceilings"] = {}
    b["controls"]["max_daily_change_pct"] = None
    b["campaigns"] = [c for c in b["campaigns"] if c["campaign_id"] != "999000111"]
    plan = A.plan_day(b)
    assert plan["total_proposed"] == pytest.approx(plan["todays_pool"], abs=0.5)


def test_audit_boost_increases_share():
    rules = [A.TargetRule("SP", "Non-Branded", "PL", 4.0)]
    base = A.Campaign("a", "x|PL|Non-Branded|SP", "PL", "SP", 50.0, 4.0, 14, 0)
    boost = A.Campaign("b", "y|PL|Non-Branded|SP", "PL", "SP", 50.0, 4.0, 14, 5)
    for c in (base, boost):
        A.classify(c, {"PL": "PL"})
    allocs, _ = A.allocate(2000.0, [base, boost], rules, A.Controls(), {}, {})
    amap = {a.campaign.campaign_id: a.final_budget for a in allocs}
    assert amap["b"] > amap["a"]


def test_insufficient_data_uses_neutral_ratio():
    rules = [A.TargetRule("SP", "Non-Branded", "PL", 4.0)]
    c = A.Campaign("a", "x|PL|Non-Branded|SP", "PL", "SP", 50.0, 99.0, 1, 0)
    A.classify(c, {"PL": "PL"})
    allocs, _ = A.allocate(1000.0, [c], rules, A.Controls(), {}, {})
    assert allocs[0].efficiency_ratio == 1.0


def test_change_cap_clamps_swings():
    b = _bundle()
    b["controls"]["max_daily_change_pct"] = 0.35
    plan = A.plan_day(b)
    for ch in plan["proposed_changes"]:
        if ch["delta_pct"] is not None:
            assert ch["delta_pct"] <= 0.3501  # never exceeds +35%


def test_floor_enforced():
    b = _bundle()
    b["strategy_ceilings"] = {}
    # Force a tiny pool: pretend almost the whole month is spent.
    b["monthly_plan"]["mtd_actual"] = 49800.0
    b.pop("daily_actuals")
    with pytest.raises(ValueError, match="floor.*pool"):
        A.plan_day(b)


# --- Daily series for the pacing report ------------------------------------

def test_daily_series_spans_month_and_reconciles():
    plan = A.plan_day(_bundle())
    s = plan["daily_series"]
    assert len(s) == 30  # June
    # Planned splits the month. Forward values replace today's raw target with the
    # executable constrained proposal, so they may conservatively undershoot.
    assert sum(d["planned_budget"] for d in s) == pytest.approx(50000.0, abs=0.5)
    fwd = [d for d in s if not d["is_past"]]
    assert sum(d["revised_forward_target"] for d in fwd) == pytest.approx(
        plan["remaining_budget"] - plan["today_spend_target"] + plan["total_proposed"],
        abs=0.5,
    )


def test_today_revised_target_equals_executable_proposal():
    """The report's today bar reflects campaign constraints, not the raw target."""
    plan = A.plan_day(_bundle())
    today = next(d for d in plan["daily_series"] if d["is_today"])
    assert today["revised_forward_target"] == pytest.approx(plan["total_proposed"], abs=0.01)


def test_daily_actuals_echoed_for_past_only():
    plan = A.plan_day(_bundle())
    past = [d for d in plan["daily_series"] if d["is_past"]]
    future = [d for d in plan["daily_series"] if not d["is_past"]]
    assert sum(d["actual_spend"] for d in past) == pytest.approx(18000.0, abs=0.5)
    assert all(d["actual_spend"] is None for d in future)
    assert all(d["revised_forward_target"] is None for d in past)


# --- The propose-only contract ---------------------------------------------

def test_plan_is_propose_only():
    """plan_day returns proposals; it has no write path and imports no client."""
    src = open(os.path.join(HERE, "..", "scripts", "allocate.py")).read()
    assert "requests" not in src and "boto3" not in src
    assert "cm_UpdateCampaign" not in src  # writes live in the skill, not here


# --- Fail-closed financial inputs -------------------------------------------

def test_missing_mtd_actual_is_rejected():
    b = _bundle()
    del b["monthly_plan"]["mtd_actual"]
    with pytest.raises(ValueError, match="mtd_actual"):
        A.plan_day(b)


def test_missing_target_rule_is_rejected():
    b = _bundle()
    b["target_rules"] = []
    with pytest.raises(ValueError, match="target rule"):
        A.plan_day(b)


def test_target_rule_does_not_fall_back_across_product_lines():
    b = _bundle()
    b["campaigns"] = [dict(
        b["campaigns"][1],
        portfolio="Product B",
        name="Example | Product B | Non-Branded | SP | Broad",
    )]
    b["portfolio_product_lines"]["Product B"] = "Product B"
    with pytest.raises(ValueError, match="target rule"):
        A.plan_day(b)


def test_ad_type_name_fallback_uses_delimited_tokens():
    c = A.Campaign("1", "Display | PL | Non-Branded", "PL", None, 10.0)
    ok, dim, _ = A.classify(c, {"PL": "PL"})
    assert not ok
    assert dim == "ad_type"
    assert c.ad_type is None


def test_portfolio_name_is_not_assumed_to_be_a_product_line():
    c = A.Campaign("1", "Example | Non-Branded | SP", "Unmapped Portfolio", "SP", 10.0)
    ok, dim, _ = A.classify(c, {"Known Portfolio": "Product A"})
    assert not ok
    assert dim == "product_line"


def test_account_context_and_provenance_are_required():
    for field in ("account_context", "data_provenance", "amazon_budget_controls"):
        b = _bundle()
        del b[field]
        with pytest.raises(ValueError, match=field):
            A.plan_day(b)


def test_live_run_controls_must_be_explicit():
    b = _bundle()
    del b["controls"]["min_daily_budget"]
    with pytest.raises(ValueError, match="controls.min_daily_budget"):
        A.plan_day(b)


def test_active_amazon_budget_rules_are_rejected_until_modeled():
    b = _bundle()
    b["amazon_budget_controls"]["active_budget_rules"] = [{"rule_id": "rule-1"}]
    with pytest.raises(ValueError, match="active budget rules"):
        A.plan_day(b)


def test_overdelivery_setting_reserves_daily_budget_headroom():
    b = _bundle()
    b["amazon_budget_controls"]["average_daily_budget_overdelivery_pct"] = 0.25
    plan = A.plan_day(b)
    assert plan["todays_pool"] == pytest.approx(
        plan["today_spend_target"] / 1.25, abs=0.01
    )


def test_roas_window_excludes_last_two_days_of_immature_sales():
    b = _bundle()
    b["data_provenance"]["performance_actuals"]["roas_data_through"] = "2026-06-14"
    with pytest.raises(ValueError, match="roas_data_through"):
        A.plan_day(b)


def test_proposal_id_is_deterministic_and_input_bound():
    base = _bundle()
    first = A.plan_day(base)["proposal_id"]
    assert first == A.plan_day(_bundle())["proposal_id"]
    changed = _bundle()
    changed["monthly_plan"]["budget"] += 1
    assert A.plan_day(changed)["proposal_id"] != first


# --- Constraint preservation ------------------------------------------------

def test_infeasible_floor_and_ceiling_are_rejected():
    cs = [
        A.Campaign(str(i), f"X{i} | PL | Non-Branded | SP", "PL", "SP", 10.0, 4.0, 14)
        for i in range(2)
    ]
    for c in cs:
        A.classify(c, {"PL": "PL"})
    rules = [A.TargetRule("SP", "Non-Branded", "PL", 4.0)]
    with pytest.raises(ValueError, match="floor.*ceiling"):
        A.allocate(100.0, cs, rules, A.Controls(min_daily_budget=40.0), {"PL": 0.5}, {})


def test_overlapping_ceilings_remain_satisfied_after_redistribution():
    rows = [
        ("a", "PL1", "Brand Defense", 10.0),
        ("b", "PL1", "Non-Branded", 8.0),
        ("c", "PL2", "Non-Branded", 2.0),
    ]
    cs, rules = [], []
    for cid, pl, strategy, roas in rows:
        c = A.Campaign(cid, f"X | {pl} | {strategy} | SP", pl, "SP", 10.0, roas, 14)
        A.classify(c, {"PL1": "PL1", "PL2": "PL2"})
        cs.append(c)
        rules.append(A.TargetRule("SP", strategy, pl, 1.0))
    allocs, _ = A.allocate(
        100.0, cs, rules, A.Controls(min_daily_budget=0.0),
        {"PL1": 0.60}, {"Non-Branded": 0.55},
    )
    by_id = {a.campaign.campaign_id: a.final_budget for a in allocs}
    assert by_id["a"] + by_id["b"] <= 60.0 + 1e-6
    assert by_id["b"] + by_id["c"] <= 55.0 + 1e-6
    assert sum(by_id.values()) <= 100.0 + 1e-6


def test_hard_ceiling_proposes_pause_actions_not_zero_budgets():
    b = _bundle()
    b["monthly_plan"]["mtd_actual"] = b["monthly_plan"]["budget"] + 1
    b.pop("daily_actuals")
    plan = A.plan_day(b)
    assert plan["proposed_changes"] == []
    assert plan["proposed_actions"]
    assert all(a["action"] == "pause_campaign" for a in plan["proposed_actions"])
    assert all("proposed_daily_budget" not in a for a in plan["proposed_actions"])


def test_today_report_forecast_uses_executable_proposal():
    plan = A.plan_day(_bundle())
    today = next(d for d in plan["daily_series"] if d["is_today"])
    assert today["revised_forward_target"] == pytest.approx(plan["total_proposed"], abs=0.01)
