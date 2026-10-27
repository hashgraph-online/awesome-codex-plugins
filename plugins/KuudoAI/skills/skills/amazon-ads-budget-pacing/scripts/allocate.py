#!/usr/bin/env python3
"""Deterministic Amazon Ads budget allocation — the math the skill must never
do in its head.

Self-contained (stdlib only). Reads one run-bundle JSON (config + actuals +
campaigns assembled by the skill from the Ads / Agent Flow MCPs), writes a
proposed day-plan JSON. It PROPOSES only — it never calls Amazon. Writing
budgets is a separate Ads MCP call the skill makes after human approval.

Usage:
    python allocate.py run_input.json [plan_out.json]

Input schema: see references/run-input.schema.md. Phase formulas: see
references/phase-math.md.

Why this is code and not prose: it moves client money daily and must be
reproducible and auditable. Same inputs -> same budgets, every run, with a
trail of WHY each number came out the way it did.
"""
from __future__ import annotations

import calendar
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

NEUTRAL_RATIO = 1.0
MIN_DAYS_FOR_RATIO = 3

STRATEGIES = ["Brand Defense", "Non-Branded", "Conquesting", "Cross-Sell", "Invest to Grow"]
AD_TYPES = ["SP", "SBV", "SB", "SD"]  # SBV before SB so the longer token wins


# --------------------------------------------------------------------------
# Inputs (plain dataclasses; an adapter/skill fills these from MCP responses)
# --------------------------------------------------------------------------

@dataclass
class Controls:
    min_daily_budget: float = 25.0
    hard_spend_ceiling: bool = True
    honor_minimums_at_low_budget: bool = True
    apply_dow_seasonality: bool = True
    pacing_health_weight: float = 0.30
    exhaustion_penalty_factor: float = 0.30
    max_daily_change_pct: float | None = None  # e.g. 0.35 = clamp moves to +/-35%

    def validate(self) -> list[str]:
        errs = []
        if not math.isfinite(self.min_daily_budget) or self.min_daily_budget < 0:
            errs.append("min_daily_budget must be >= 0")
        if not math.isfinite(self.pacing_health_weight) or not 0 <= self.pacing_health_weight <= 1:
            errs.append("pacing_health_weight must be between 0 and 1")
        if not math.isfinite(self.exhaustion_penalty_factor) or self.exhaustion_penalty_factor < 0:
            errs.append("exhaustion_penalty_factor must be >= 0")
        if (self.max_daily_change_pct is not None and
                (not math.isfinite(self.max_daily_change_pct) or self.max_daily_change_pct <= 0)):
            errs.append("max_daily_change_pct must be > 0 or null")
        return errs


@dataclass
class Campaign:
    campaign_id: str
    name: str
    portfolio: str | None
    ad_type: str | None
    current_daily_budget: float
    actual_roas: float | None = None
    days_of_data: int = 0
    exhausted_before_6pm_days_l7: int = 0
    enabled: bool = True
    # filled by classification:
    strategy: str | None = None
    product_line: str | None = None

    @property
    def classified(self) -> bool:
        return all([self.ad_type, self.strategy, self.product_line])


@dataclass
class TargetRule:
    ad_type: str
    strategy: str
    product_line: str
    target_roas: float
    lookback_days: int = 14


# --------------------------------------------------------------------------
# Classification (Section 2)
# --------------------------------------------------------------------------

def _match_token(name: str, tokens: list[str]) -> str | None:
    for tok in sorted(tokens, key=len, reverse=True):  # longest wins
        pattern = rf"(?<![A-Za-z0-9]){re.escape(tok)}(?![A-Za-z0-9])"
        if re.search(pattern, name or "", flags=re.IGNORECASE):
            return tok
    return None


def classify(c: Campaign, portfolio_to_pl: dict[str, str]) -> tuple[bool, str | None, str | None]:
    """Returns (ok, failed_dimension, reason). Mutates c with resolved fields."""
    if not c.ad_type:
        m = _match_token(c.name, AD_TYPES)
        if not m:
            return False, "ad_type", "No ad type from metadata and no SP/SB/SBV/SD token in name."
        c.ad_type = m
    if not c.strategy:
        m = _match_token(c.name, STRATEGIES)
        if not m:
            return False, "strategy", ("Name has no recognized strategy token "
                                       "(Brand Defense/Non-Branded/Conquesting/Cross-Sell/Invest to Grow).")
        c.strategy = m
    if not c.product_line:
        pl = portfolio_to_pl.get(c.portfolio) if c.portfolio else None
        pl = pl or _match_token(c.name, list(portfolio_to_pl.values()))
        if not pl:
            return False, "product_line", "Portfolio missing/ambiguous and no product line token in name."
        c.product_line = pl
    return True, None, None


# --------------------------------------------------------------------------
# Phase 1 — pacing (Section 3)
# --------------------------------------------------------------------------

@dataclass
class Pacing:
    today: date
    monthly_budget: float
    actuals_to_date: float
    remaining_budget: float
    remaining_days: int
    today_share: float
    todays_pool: float
    pacing_pct: float | None
    hard_ceiling_paused: bool
    warnings: list[str] = field(default_factory=list)


def _raw_share(d: date, dow_index: dict[str, float], event_mult: dict[str, float],
               apply_dow: bool) -> float:
    """One day's unnormalized weight = DOW index x event multiplier."""
    idx = dow_index.get(d.strftime("%A"), 1.0) if apply_dow else 1.0
    return idx * event_mult.get(d.isoformat(), 1.0)


def compute_pacing(today: date, monthly_budget: float, mtd_actual: float,
                   dow_index: dict[str, float], event_mult: dict[str, float],
                   controls: Controls, mtd_planned_to_date: float | None) -> Pacing:
    remaining = monthly_budget - mtd_actual
    dim = calendar.monthrange(today.year, today.month)[1]
    last = date(today.year, today.month, dim)
    fwd = [today + timedelta(days=i) for i in range((last - today).days + 1)]

    def raw(d: date) -> float:
        return _raw_share(d, dow_index, event_mult, controls.apply_dow_seasonality)

    raws = {d: raw(d) for d in fwd}
    total = sum(raws.values())
    pacing_pct = (mtd_actual / mtd_planned_to_date) if mtd_planned_to_date else None
    warns: list[str] = []

    if remaining <= 0 and controls.hard_spend_ceiling:
        return Pacing(today, monthly_budget, mtd_actual, remaining, len(fwd), 0.0, 0.0,
                      pacing_pct, True,
                      ["Remaining budget <= 0 and hard ceiling on: propose pausing all campaigns."])
    if remaining <= 0:
        warns.append("Remaining budget <= 0 but hard ceiling off: continuing at floors.")

    if today == last or total == 0:
        share, pool = 1.0, max(remaining, 0.0)
    else:
        share = raws[today] / total
        pool = max(remaining, 0.0) * share
    return Pacing(today, monthly_budget, mtd_actual, remaining, len(fwd),
                  share, pool, pacing_pct, False, warns)


def build_daily_series(today: date, monthly_budget: float,
                       dow_index: dict[str, float], event_mult: dict[str, float],
                       controls: Controls, remaining_budget: float,
                       daily_actuals: dict[str, float]) -> list[dict]:
    """Per-day plan for the whole month, for the pacing report (report.py).

    For each calendar day in the current month, emit the *planned* daily budget
    (the month's budget split by DOW x event weight), the *revised forward
    target* for today and future days (remaining budget re-weighted over the
    days that are left — the operative reforecast), and the *actual* spend for
    past days when the caller supplies it. report.py turns this into the
    planned-vs-actual bars and the cumulative pacing curve; this function does
    not touch Amazon and adds no new inputs the allocator didn't already use.
    """
    dim = calendar.monthrange(today.year, today.month)[1]
    month_days = [date(today.year, today.month, d) for d in range(1, dim + 1)]
    fwd_days = [d for d in month_days if d >= today]
    apply = controls.apply_dow_seasonality
    raw_all = {d: _raw_share(d, dow_index, event_mult, apply) for d in month_days}
    total_month = sum(raw_all.values()) or 1.0
    total_fwd = sum(raw_all[d] for d in fwd_days) or 1.0
    rem = max(remaining_budget, 0.0)

    series: list[dict] = []
    for d in month_days:
        iso = d.isoformat()
        revised = (rem * raw_all[d] / total_fwd) if d >= today else None
        actual = daily_actuals.get(iso)
        series.append({
            "date": iso,
            "weekday": d.strftime("%A"),
            "dow_index": round(dow_index.get(d.strftime("%A"), 1.0) if apply else 1.0, 4),
            "event_multiplier": event_mult.get(iso, 1.0),
            "planned_budget": round(monthly_budget * raw_all[d] / total_month, 2),
            "revised_forward_target": round(revised, 2) if revised is not None else None,
            "actual_spend": round(actual, 2) if actual is not None else None,
            "is_today": d == today,
            "is_past": d < today,
        })
    return series


# --------------------------------------------------------------------------
# Phase 2 + 3 — allocation with audit boost, ceilings, floor (Sections 4-5)
# --------------------------------------------------------------------------

@dataclass
class Alloc:
    campaign: Campaign
    efficiency_ratio: float
    adjusted_score: float
    raw_allocation: float
    final_budget: float
    floored: bool = False
    ceiling_clipped: bool = False
    change_capped: bool = False
    notes: list[str] = field(default_factory=list)


def _rule_for(rules: list[TargetRule], c: Campaign) -> TargetRule | None:
    for r in rules:
        if (r.ad_type, r.strategy, r.product_line) == (c.ad_type, c.strategy, c.product_line):
            return r
    return None


def allocate(pool: float, campaigns: list[Campaign], rules: list[TargetRule],
             controls: Controls, pl_ceilings: dict[str, float],
             strat_ceilings: dict[str, float]) -> tuple[list[Alloc], list[str]]:
    warns: list[str] = []
    if not campaigns:
        return [], ["No eligible campaigns to allocate."]

    scored: list[Alloc] = []
    for c in campaigns:
        rule = _rule_for(rules, c)
        if rule is None:
            raise ValueError(
                f"No exact target rule for campaign {c.campaign_id} "
                f"({c.ad_type} / {c.strategy} / {c.product_line})."
            )
        target = rule.target_roas
        if c.days_of_data < MIN_DAYS_FOR_RATIO or c.actual_roas is None:
            ratio = NEUTRAL_RATIO
        else:
            ratio = c.actual_roas / target
        adj = ratio
        notes = []
        if c.days_of_data < MIN_DAYS_FOR_RATIO:
            notes.append(f"Only {c.days_of_data}d data (<{MIN_DAYS_FOR_RATIO}); neutral ratio.")
        if c.exhausted_before_6pm_days_l7 >= 3:
            adj = ratio * (1.0 + controls.pacing_health_weight * controls.exhaustion_penalty_factor)
            notes.append(f"Audit boost: exhausted <6PM on {c.exhausted_before_6pm_days_l7}/7 days.")
        scored.append(Alloc(c, ratio, adj, 0.0, 0.0, notes=notes))

    _allocate_with_constraints(scored, controls, pool, pl_ceilings, strat_ceilings, warns)
    _apply_change_cap(scored, controls, warns)
    _assert_ceilings(scored, pl_ceilings, strat_ceilings, pool)
    total = sum(a.final_budget for a in scored)
    if total < pool - 0.01:
        warns.append(
            f"{pool - total:,.2f} currency units remain unallocated because ceilings or change caps bind."
        )
    elif total > pool + 0.01:
        warns.append(
            f"Proposed budgets exceed today's pool by {total - pool:,.2f} currency units because change caps bind."
        )
    return scored, warns


def _constraints(scored, pl_ceilings, strat_ceilings, pool):
    constraints = []
    for ceilings, attr in ((pl_ceilings, "product_line"), (strat_ceilings, "strategy")):
        for key, pct in ceilings.items():
            if not isinstance(pct, (int, float)) or not math.isfinite(pct) or not 0 <= pct <= 1:
                raise ValueError(f"{attr} ceiling for {key} must be between 0 and 1.")
            members = [i for i, a in enumerate(scored) if getattr(a.campaign, attr) == key]
            if members:
                constraints.append((attr, key, pct * pool, members))
    return constraints


def _allocate_with_constraints(scored, controls, pool, pl_ceilings, strat_ceilings, warns):
    """Weighted water-fill that never violates configured group ceilings.

    Saturating one overlapping bucket can leave part of the pool unallocated.
    That conservative outcome is preferable to silently breaking a hard cap.
    """
    floor = controls.min_daily_budget
    floor_total = floor * len(scored)
    if floor_total > pool + 1e-9:
        if controls.honor_minimums_at_low_budget:
            raise ValueError(
                f"Per-campaign floor total {floor_total:,.2f} exceeds today's pool {pool:,.2f}."
            )
        total_score = sum(a.adjusted_score for a in scored) or 1.0
        for a in scored:
            a.final_budget = pool * a.adjusted_score / total_score
            a.raw_allocation = a.final_budget
            a.notes.append("Below-floor proportional scaling (explicit low-budget mode).")
        warns.append("Budget below configured floors; explicit low-budget scaling applied.")
        return

    constraints = _constraints(scored, pl_ceilings, strat_ceilings, pool)
    for attr, key, cap, members in constraints:
        required = floor * len(members)
        if required > cap + 1e-9:
            raise ValueError(
                f"Per-campaign floor total {required:,.2f} conflicts with {attr} "
                f"ceiling {cap:,.2f} for {key}."
            )

    for a in scored:
        a.final_budget = floor
        a.floored = floor > 0

    residual = pool - floor_total
    active = set(range(len(scored)))
    while residual > 1e-9 and active:
        total_score = sum(scored[i].adjusted_score for i in active) or float(len(active))
        shares = {
            i: residual * (scored[i].adjusted_score / total_score)
            for i in active
        }
        factor = 1.0
        for _attr, _key, cap, members in constraints:
            member_active = [i for i in members if i in active]
            proposed = sum(shares[i] for i in member_active)
            if proposed <= 0:
                continue
            remaining_cap = cap - sum(scored[i].final_budget for i in members)
            factor = min(factor, max(0.0, remaining_cap / proposed))

        allocated = 0.0
        for i, share in shares.items():
            increment = share * factor
            scored[i].final_budget += increment
            allocated += increment
        residual -= allocated
        if factor >= 1.0 - 1e-12:
            break

        saturated = []
        for attr, key, cap, members in constraints:
            if sum(scored[i].final_budget for i in members) >= cap - 1e-8:
                saturated.append((attr, key, members))
        removed = set()
        for attr, key, members in saturated:
            for i in members:
                if i in active:
                    scored[i].ceiling_clipped = True
                    scored[i].notes.append(f"Limited by {attr} ceiling for {key}.")
                    removed.add(i)
        if not removed:
            break
        active -= removed

    for a in scored:
        a.raw_allocation = a.final_budget
        if a.final_budget > floor + 1e-9:
            a.floored = False


def _assert_ceilings(scored, pl_ceilings, strat_ceilings, pool):
    for attr, key, cap, members in _constraints(scored, pl_ceilings, strat_ceilings, pool):
        actual = sum(scored[i].final_budget for i in members)
        if actual > cap + 0.01:
            raise ValueError(
                f"Daily change cap conflicts with {attr} ceiling for {key}: "
                f"{actual:,.2f} > {cap:,.2f}."
            )


def _apply_change_cap(scored, controls, warns):
    """OPEN-1 guardrail: clamp any one-day move to +/- max_daily_change_pct."""
    cap = controls.max_daily_change_pct
    if not cap:
        return
    for a in scored:
        cur = a.campaign.current_daily_budget
        if cur <= 0:
            continue
        hi, lo = cur * (1 + cap), cur * (1 - cap)
        if a.final_budget > hi:
            a.final_budget, a.change_capped = hi, True
            a.notes.append(f"Capped to +{cap*100:.0f}% daily change.")
        elif a.final_budget < lo:
            a.final_budget, a.change_capped = lo, True
            a.notes.append(f"Capped to -{cap*100:.0f}% daily change.")


# --------------------------------------------------------------------------
# Alerts (A-1..A-6)
# --------------------------------------------------------------------------

def evaluate_alerts(pacing: Pacing, allocs: list[Alloc],
                    failures: list[tuple[Campaign, str, str]]) -> list[dict]:
    alerts: list[dict] = []
    for c, dim, reason in failures:
        alerts.append({"id": "A-1", "severity": "CRITICAL", "subject": c.name,
                       "detail": f"Unclassified ({dim}): {reason} Excluded from automation."})
    if pacing.pacing_pct is not None:
        if pacing.pacing_pct > 1.20:
            alerts.append({"id": "A-2", "severity": "HIGH", "subject": "ACCOUNT",
                           "detail": f"MTD spend {pacing.pacing_pct*100:.0f}% of plan (>120%)."})
        elif pacing.pacing_pct < 0.80:
            alerts.append({"id": "A-3", "severity": "MEDIUM", "subject": "ACCOUNT",
                           "detail": f"MTD spend {pacing.pacing_pct*100:.0f}% of plan (<80%)."})
    if allocs:
        avg = sum(a.final_budget for a in allocs) / len(allocs)
        for a in allocs:
            if a.efficiency_ratio < 0.70 and a.final_budget > avg:
                alerts.append({"id": "A-4", "severity": "HIGH", "subject": a.campaign.name,
                               "detail": f"High spend / low ROAS: efficiency {a.efficiency_ratio:.2f}."})
            if a.efficiency_ratio > 1.30 and (a.floored or a.ceiling_clipped or a.final_budget < avg):
                alerts.append({"id": "A-5", "severity": "MEDIUM", "subject": a.campaign.name,
                               "detail": f"Low spend / high ROAS: efficiency {a.efficiency_ratio:.2f}. Possible upside."})
    for a in allocs:
        if a.campaign.exhausted_before_6pm_days_l7 >= 3:
            alerts.append({"id": "A-6", "severity": "MEDIUM", "subject": a.campaign.name,
                           "detail": f"Chronic exhaustion: out of budget <6PM {a.campaign.exhausted_before_6pm_days_l7}/7 days."})
    return alerts


# --------------------------------------------------------------------------
# Orchestration: bundle -> plan (PROPOSE ONLY)
# --------------------------------------------------------------------------

def _finite_nonnegative(value, label):
    if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{label} must be a finite non-negative number.")


def _validate_bundle(bundle: dict, as_of: date) -> None:
    for field in (
        "account_context", "data_provenance", "amazon_budget_controls",
        "portfolio_product_lines",
    ):
        if field not in bundle:
            raise ValueError(f"Missing required {field}.")

    controls = bundle.get("controls")
    required_controls = (
        "min_daily_budget", "hard_spend_ceiling", "honor_minimums_at_low_budget",
        "apply_dow_seasonality", "pacing_health_weight", "exhaustion_penalty_factor",
        "max_daily_change_pct",
    )
    if not isinstance(controls, dict):
        raise ValueError("controls is required.")
    for field in required_controls:
        if field not in controls:
            raise ValueError(f"controls.{field} is required for a pacing run.")

    context = bundle["account_context"]
    for field in ("advertiser_account_id", "profile_id", "marketplace", "currency_code", "timezone"):
        if not isinstance(context.get(field), str) or not context[field].strip():
            raise ValueError(f"account_context.{field} is required.")
    if not re.fullmatch(r"[A-Z]{3}", context["currency_code"]):
        raise ValueError("account_context.currency_code must be a three-letter uppercase code.")

    provenance = bundle["data_provenance"]
    for section, fields in {
        "current_budgets": ("source", "retrieved_at"),
        "performance_actuals": (
            "source", "retrieved_at", "data_through", "roas_data_through", "preliminary"
        ),
    }.items():
        record = provenance.get(section)
        if not isinstance(record, dict):
            raise ValueError(f"data_provenance.{section} is required.")
        for field in fields:
            if field not in record or record[field] in (None, ""):
                raise ValueError(f"data_provenance.{section}.{field} is required.")
    if not isinstance(provenance["performance_actuals"]["preliminary"], bool):
        raise ValueError("data_provenance.performance_actuals.preliminary must be boolean.")
    try:
        roas_through = datetime.strptime(
            provenance["performance_actuals"]["roas_data_through"], "%Y-%m-%d"
        ).date()
    except ValueError as exc:
        raise ValueError(
            "data_provenance.performance_actuals.roas_data_through must be YYYY-MM-DD."
        ) from exc
    if roas_through > as_of - timedelta(days=2):
        raise ValueError(
            "data_provenance.performance_actuals.roas_data_through must exclude "
            "the two most recent days because attributed sales may be immature."
        )

    budget_controls = bundle["amazon_budget_controls"]
    if "average_daily_budget_overdelivery_pct" not in budget_controls:
        raise ValueError("amazon_budget_controls.average_daily_budget_overdelivery_pct is required.")
    overdelivery = budget_controls["average_daily_budget_overdelivery_pct"]
    if (not isinstance(overdelivery, (int, float)) or not math.isfinite(overdelivery)
            or not 0 <= overdelivery <= 1):
        raise ValueError(
            "amazon_budget_controls.average_daily_budget_overdelivery_pct must be between 0 and 1."
        )
    rules = budget_controls.get("active_budget_rules")
    if not isinstance(rules, list):
        raise ValueError("amazon_budget_controls.active_budget_rules must be an array.")
    if rules:
        raise ValueError(
            "Unmodeled active budget rules can increase campaign budgets; disable or model them before pacing."
        )

    portfolio_map = bundle["portfolio_product_lines"]
    if not isinstance(portfolio_map, dict):
        raise ValueError("portfolio_product_lines must be an object.")
    if any(not isinstance(k, str) or not isinstance(v, str) or not k or not v
           for k, v in portfolio_map.items()):
        raise ValueError("portfolio_product_lines keys and values must be non-empty strings.")

    plan = bundle.get("monthly_plan")
    if not isinstance(plan, dict):
        raise ValueError("monthly_plan is required.")
    for field in ("month", "budget", "mtd_actual"):
        if field not in plan:
            raise ValueError(f"monthly_plan.{field} is required.")
    valid_months = {as_of.strftime("%B %Y"), as_of.strftime("%Y-%m")}
    if plan["month"] not in valid_months:
        raise ValueError(
            f"monthly_plan.month {plan['month']!r} does not match as_of month {as_of:%Y-%m}."
        )
    _finite_nonnegative(plan["budget"], "monthly_plan.budget")
    _finite_nonnegative(plan["mtd_actual"], "monthly_plan.mtd_actual")

    campaigns = bundle.get("campaigns")
    if not isinstance(campaigns, list) or not campaigns:
        raise ValueError("campaigns must contain at least one campaign.")
    ids = [str(c.get("campaign_id", "")) for c in campaigns]
    if any(not cid for cid in ids) or len(ids) != len(set(ids)):
        raise ValueError("campaigns must have unique, non-empty campaign_id values.")
    for c in campaigns:
        _finite_nonnegative(c.get("current_daily_budget"), f"campaign {c['campaign_id']} current_daily_budget")
        if c.get("actual_roas") is not None:
            _finite_nonnegative(c["actual_roas"], f"campaign {c['campaign_id']} actual_roas")

    target_rules = bundle.get("target_rules")
    if not isinstance(target_rules, list) or not target_rules:
        raise ValueError("At least one exact target rule is required.")
    keys = []
    for rule in target_rules:
        key = (rule.get("ad_type"), rule.get("strategy"), rule.get("product_line"))
        if None in key:
            raise ValueError("Each target rule requires ad_type, strategy, and product_line.")
        keys.append(key)
        if not isinstance(rule.get("target_roas"), (int, float)) or rule["target_roas"] <= 0:
            raise ValueError(f"target rule {key} target_roas must be positive.")
        if not isinstance(rule.get("lookback_days", 14), int) or rule.get("lookback_days", 14) < 3:
            raise ValueError(f"target rule {key} lookback_days must be at least 3.")
    if len(keys) != len(set(keys)):
        raise ValueError("Target rules must be unique by ad_type, strategy, and product_line.")

    daily_actuals = bundle.get("daily_actuals", {})
    if daily_actuals:
        for day, amount in daily_actuals.items():
            _finite_nonnegative(amount, f"daily_actuals.{day}")
            try:
                actual_day = datetime.strptime(day, "%Y-%m-%d").date()
            except ValueError as exc:
                raise ValueError(f"daily_actuals key {day!r} must be YYYY-MM-DD.") from exc
            if actual_day >= as_of:
                raise ValueError("daily_actuals must contain completed days before as_of only.")
        if abs(sum(daily_actuals.values()) - plan["mtd_actual"]) > 0.01:
            raise ValueError("daily_actuals must reconcile to monthly_plan.mtd_actual.")

    for name, mapping in (
        ("dow_index", bundle.get("dow_index", {})),
        ("event_multipliers", bundle.get("event_multipliers", {})),
        ("product_line_ceilings", bundle.get("product_line_ceilings", {})),
        ("strategy_ceilings", bundle.get("strategy_ceilings", {})),
    ):
        if not isinstance(mapping, dict):
            raise ValueError(f"{name} must be an object.")
        for key, value in mapping.items():
            _finite_nonnegative(value, f"{name}.{key}")
            if "ceilings" in name and value > 1:
                raise ValueError(f"{name}.{key} must be between 0 and 1.")

def plan_day(bundle: dict) -> dict:
    controls = Controls(**bundle.get("controls", {}))
    errs = controls.validate()
    if errs:
        raise ValueError("Invalid controls: " + "; ".join(errs))

    as_of = datetime.strptime(bundle["as_of"], "%Y-%m-%d").date()
    _validate_bundle(bundle, as_of)
    plan = bundle["monthly_plan"]
    rules = [TargetRule(**r) for r in bundle.get("target_rules", [])]
    portfolio_to_pl = bundle["portfolio_product_lines"]

    campaigns = [Campaign(**c) for c in bundle["campaigns"]]
    eligible, failures = [], []
    for c in campaigns:
        ok, dim, reason = classify(c, portfolio_to_pl)
        if ok and c.enabled:
            eligible.append(c)
        elif not ok:
            failures.append((c, dim, reason))

    dow_index = bundle.get("dow_index", {})
    pacing = compute_pacing(
        as_of, plan["budget"], plan["mtd_actual"],
        dow_index, bundle.get("event_multipliers", {}),
        controls, bundle.get("mtd_planned_to_date"))
    today_spend_target = pacing.todays_pool
    overdelivery = bundle["amazon_budget_controls"]["average_daily_budget_overdelivery_pct"]
    if not pacing.hard_ceiling_paused:
        pacing.todays_pool = today_spend_target / (1.0 + overdelivery)

    daily_series = build_daily_series(
        as_of, plan["budget"], dow_index, bundle.get("event_multipliers", {}),
        controls, pacing.remaining_budget, bundle.get("daily_actuals", {}))

    if pacing.hard_ceiling_paused:
        actions = [{
            "campaign_id": c.campaign_id,
            "name": c.name,
            "action": "pause_campaign",
            "current_state": "ENABLED",
            "proposed_state": "PAUSED",
            "reason": "Monthly hard ceiling reached.",
        } for c in eligible]
        alerts = evaluate_alerts(pacing, [], failures)
        return _plan_dict(as_of, plan, pacing, [], actions, alerts, failures,
                          pacing.warnings, 0.0, today_spend_target, daily_series,
                          dow_index, bundle)

    allocs, warns = allocate(pacing.todays_pool, eligible, rules, controls,
                             bundle.get("product_line_ceilings", {}),
                             bundle.get("strategy_ceilings", {}))
    changes = []
    for a in allocs:
        cur, new = a.campaign.current_daily_budget, round(a.final_budget, 2)
        changes.append(_change(a.campaign.campaign_id, a.campaign.name, cur, new,
                               round(a.efficiency_ratio, 3), a.floored,
                               a.ceiling_clipped, a.change_capped, a.notes))
    alerts = evaluate_alerts(pacing, allocs, failures)
    total = round(sum(a.final_budget for a in allocs), 2)
    for day in daily_series:
        if day["is_today"]:
            day["revised_forward_target"] = total
            break
    return _plan_dict(as_of, plan, pacing, changes, [], alerts, failures,
                      list(pacing.warnings) + list(warns), total,
                      today_spend_target, daily_series, dow_index, bundle)


def _change(cid, name, cur, new, eff, floored, ceil, capped, notes):
    return {"campaign_id": cid, "name": name, "current_daily_budget": cur,
            "proposed_daily_budget": new, "delta": round(new - cur, 2),
            "delta_pct": round((new - cur) / cur, 4) if cur else None,
            "efficiency_ratio": eff, "floored": floored,
            "ceiling_clipped": ceil, "change_capped": capped, "notes": notes}


def _plan_dict(as_of, plan, pacing, changes, actions, alerts, failures, warns, total,
               today_spend_target, daily_series=None, dow_index=None, bundle=None):
    proposal_id = hashlib.sha256(
        json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    return {
        "proposal_id": proposal_id,
        "as_of": as_of.isoformat(),
        "month": plan["month"],
        "monthly_budget": plan["budget"],
        "actuals_to_date": plan["mtd_actual"],
        "remaining_budget": round(pacing.remaining_budget, 2),
        "remaining_days": pacing.remaining_days,
        "today_spend_target": round(today_spend_target, 2),
        "todays_pool": round(pacing.todays_pool, 2),
        "pacing_pct": pacing.pacing_pct,
        "hard_ceiling_paused": pacing.hard_ceiling_paused,
        "total_proposed": total,
        "proposed_changes": changes,
        "proposed_actions": actions,
        "alerts": alerts,
        "excluded_campaigns": [{"campaign_id": c.campaign_id, "name": c.name,
                                "reason": f"{dim}: {reason}"} for c, dim, reason in failures],
        "warnings": warns,
        "daily_series": daily_series or [],
        "dow_index": dow_index or {},
        "account_context": bundle["account_context"],
        "data_provenance": bundle["data_provenance"],
        "amazon_budget_controls": bundle["amazon_budget_controls"],
    }


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print(__doc__)
        sys.exit(1)
    with open(argv[0]) as f:
        bundle = json.load(f)
    plan = plan_day(bundle)
    out = argv[1] if len(argv) > 1 else None
    if out:
        with open(out, "w") as f:
            json.dump(plan, f, indent=2)
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
