#!/usr/bin/env python3
"""Render an Amazon Ads pacing report from an allocate.py day-plan.

Turns the day-plan JSON (the output of `allocate.py`) into a client-ready
pacing report — "the pacing desk": a dark instrument-panel control surface that
mirrors the customer's Spend Pacing workbook visuals:

  1. A hero burn-gauge — spend vs the monthly ceiling, with the on-plan marker
  2. Planned vs Actual/Forecast daily spend (grouped bars, today marked)
  3. Cumulative budget pacing — actual burn-up plus the current forward planning
     target, with today's executable campaign constraints reflected
  4. Day-of-week seasonality (diverging from the 1.0 average line)
  5. Pacing status + alert console + proposed-change table with delta bars

It is a *renderer*, not a calculator — every number comes straight from the
day-plan, so the report can never disagree with the budgets allocate.py
proposed. Like allocate.py it is stdlib-only (charts are hand-built inline SVG,
motion is CSS-only, fonts are system-available), so the artifact is fully
self-contained: it runs unchanged locally, offline, or inside a code-factory
sandbox with no install and no network.

Usage:
    python report.py plan.json [out_dir]      # writes report.html + report.md

`plan.json` is the file allocate.py writes (its second CLI arg). `out_dir`
defaults to the current directory.
"""
from __future__ import annotations

import html
import json
import os
import sys

# ---- signal palette (the report's single visual source of truth) ------------
# Anthropic house style: warm earth tones on bone/ivory. Clay = overspend /
# attention. Sage = the corrective forward path. Slate = the disciplined plan
# baseline. The whole report speaks this three-word language, calmly.
C_PLAN = "#8fa3ad"      # plan baseline (muted dusty slate)
C_ACTUAL = "#cc785c"    # actual spend / the hot burn (Anthropic clay)
C_FCST = "#7c9a6e"      # forecast / corrective forward (sage)
C_GOLD = "#c2913f"      # today / focus marker (kraft gold)
C_HOT = "#b0512f"       # critical / running-hot status (deep terracotta)
C_GOOD = "#5f8463"      # on-track status (sage green)
C_WARN = "#c2913f"      # running-light / medium severity (ochre)
C_GRID = "#e4e0d4"      # chart gridlines (warm hairline)
C_AXIS = "#9a9488"      # axis labels (warm muted)
C_TEXT = "#1f1e1b"      # primary text (warm ink)


# ---- pacing status ----------------------------------------------------------

def pacing_status(pacing_pct):
    """(label, color) from MTD actual / MTD plan, matching the brief's bands."""
    if pacing_pct is None:
        return "Pending", "#8a8576"
    if pacing_pct > 1.20:
        return "Running Hot", C_HOT
    if pacing_pct < 0.80:
        return "Running Light", C_WARN
    return "On Track", C_GOOD


# ---- tiny SVG chart kit (no dependencies) -----------------------------------

_CW, _CH = 900, 300
_ML, _MR, _MT, _MB = 56, 18, 18, 38
_PW, _PH = _CW - _ML - _MR, _CH - _MT - _MB


def _esc(s):
    return html.escape(str(s), quote=True)


def _md_cell(value):
    return " ".join(str(value).splitlines()).replace("|", "\\|")


def _money(v, currency):
    return f"{currency} {v:,.0f}"


def _kmoney(v):
    """Compact numeric amount for tight chart labels; currency is in the report."""
    if abs(v) >= 1000:
        return f"{v/1000:,.1f}k".replace(".0k", "k")
    return f"{v:,.0f}"


def _defs(uid, base_color):
    """Per-chart area-fill gradient, namespaced by uid to avoid collisions.

    Clean line work (no glow halo) suits the warm editorial surface — the
    gradient gives the actual-burn area a soft clay wash and nothing more.
    """
    return (
        f'<defs>'
        f'<linearGradient id="area{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{base_color}" stop-opacity="0.20"/>'
        f'<stop offset="1" stop-color="{base_color}" stop-opacity="0"/></linearGradient>'
        f'</defs>'
    )


def _frame(uid, ymax, yfmt, defs_color=C_ACTUAL):
    """Chart background: defs + horizontal gridlines + right-edge y labels."""
    out = [f'<svg viewBox="0 0 {_CW} {_CH}" class="chart" role="img" preserveAspectRatio="xMidYMid meet">',
           _defs(uid, defs_color)]
    for i in range(5):
        y = _MT + _PH - (i / 4) * _PH
        val = (i / 4) * ymax
        dash = ' stroke-dasharray="1,4"' if i else ''   # solid baseline, dotted above
        out.append(f'<line x1="{_ML}" y1="{y:.1f}" x2="{_ML+_PW}" y2="{y:.1f}" stroke="{C_GRID}" '
                   f'stroke-width="1"{dash}/>')
        out.append(f'<text x="{_ML-10}" y="{y+3.5:.1f}" class="yl">{_esc(yfmt(val))}</text>')
    return out


def chart_planned_vs_actual(series):
    """Grouped bars: Plan vs (Actual for past days / Forecast for future)."""
    plan = [d["planned_budget"] or 0 for d in series]
    other, ocolor = [], []
    for d in series:
        if d["is_past"]:
            other.append(d["actual_spend"] or 0); ocolor.append(C_ACTUAL)
        else:
            other.append(d["revised_forward_target"] or 0); ocolor.append(C_FCST)
    ymax = max(plan + other + [1]) * 1.16
    n = len(series)
    slot = _PW / n
    bw = max(2.0, slot * 0.34)
    out = _frame("D", ymax, _kmoney, C_ACTUAL)
    today_x = None
    for i, d in enumerate(series):
        x0 = _ML + i * slot
        hp = (plan[i] / ymax) * _PH
        ho = (other[i] / ymax) * _PH
        cx = x0 + slot / 2
        # plan bar (left, slate), actual/forecast bar (right, clay or sage)
        out.append(f'<rect x="{cx-bw-0.6:.1f}" y="{_MT+_PH-hp:.1f}" width="{bw:.1f}" '
                   f'height="{max(hp,0):.1f}" rx="1.6" fill="{C_PLAN}" opacity="0.55"/>')
        fop = "0.78" if not d["is_past"] else "1"   # future forecast bars a touch lighter
        out.append(f'<rect x="{cx+0.6:.1f}" y="{_MT+_PH-ho:.1f}" width="{bw:.1f}" '
                   f'height="{max(ho,0):.1f}" rx="1.6" fill="{ocolor[i]}" opacity="{fop}"/>')
        if d["is_today"]:
            today_x = cx
        day = int(d["date"][-2:])
        if day == 1 or day % 5 == 0:
            out.append(f'<text x="{cx:.1f}" y="{_MT+_PH+16}" class="xl">{day}</text>')
    if today_x is not None:
        out.append(f'<line x1="{today_x:.1f}" y1="{_MT-2}" x2="{today_x:.1f}" y2="{_MT+_PH}" '
                   f'stroke="{C_GOLD}" stroke-width="1.2" stroke-dasharray="2,3" opacity="0.85"/>')
        out.append(f'<rect x="{today_x-22:.1f}" y="{_MT-15}" width="44" height="14" rx="7" '
                   f'fill="{C_GOLD}"/>')
        out.append(f'<text x="{today_x:.1f}" y="{_MT-5}" class="todaychip">TODAY</text>')
    out.append("</svg>")
    return "".join(out)


def chart_cumulative(series, monthly_budget):
    """Cumulative planned vs actual, plus a forward planning scenario.

    The hot coral line is what actually burned. From the last actual it hands
    off to a sage dotted line built from the day-plan's revised-forward targets.
    Today's point reflects executable campaign constraints; future points remain
    targets that are recalculated on each run.
    """
    cum_plan, cum_act, running_p, running_a = [], [], 0.0, 0.0
    last_actual_i = -1
    for i, d in enumerate(series):
        running_p += d["planned_budget"] or 0
        cum_plan.append(running_p)
        if d["actual_spend"] is not None:
            running_a += d["actual_spend"]; cum_act.append(running_a); last_actual_i = i
        else:
            cum_act.append(None)
    # corrected forward path: actual-so-far + the revised-forward targets ahead
    proj, run = [], running_a
    for i, d in enumerate(series):
        if i < last_actual_i:
            proj.append(None)
        elif i == last_actual_i:
            proj.append(run)
        else:
            run += d["revised_forward_target"] or 0
            proj.append(run)
    ymax = max([monthly_budget] + cum_plan + [running_a, run]) * 1.10
    n = len(series)

    def pt(i, v):
        x = _ML + (i / max(n - 1, 1)) * _PW
        y = _MT + _PH - (v / ymax) * _PH
        return f"{x:.1f},{y:.1f}"

    def xy(i, v):
        return [float(p) for p in pt(i, v).split(",")]

    out = _frame("C", ymax, _kmoney, C_ACTUAL)
    # ceiling
    yb = _MT + _PH - (monthly_budget / ymax) * _PH
    out.append(f'<line x1="{_ML}" y1="{yb:.1f}" x2="{_ML+_PW}" y2="{yb:.1f}" '
               f'stroke="{C_HOT}" stroke-width="1.2" stroke-dasharray="6,4" opacity="0.8"/>')
    out.append(f'<text x="{_ML+_PW}" y="{yb-6:.1f}" class="ceil">CEILING {_kmoney(monthly_budget)}</text>')
    # plan line (steel)
    out.append(f'<polyline fill="none" stroke="{C_PLAN}" stroke-width="2" stroke-opacity="0.85" '
               f'points="{" ".join(pt(i, v) for i, v in enumerate(cum_plan))}"/>')
    # corrected forward trajectory (sage dotted) + faint fill to ceiling
    proj_idx = [i for i, v in enumerate(proj) if v is not None]
    if len(proj_idx) > 1:
        pp = " ".join(pt(i, proj[i]) for i in proj_idx)
        out.append(f'<polyline fill="none" stroke="{C_FCST}" stroke-width="2" '
                   f'stroke-dasharray="2,4" stroke-linecap="round" points="{pp}"/>')
        ex, ey = xy(proj_idx[-1], proj[proj_idx[-1]])
        out.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="3.5" fill="{C_FCST}" '
                   f'stroke="#faf9f5" stroke-width="1.5"/>')
    # actual burn (hot coral) with area fill + glow + draw-on animation
    if last_actual_i >= 0:
        line_pts = [pt(i, cum_act[i]) for i in range(last_actual_i + 1)]
        x0, _ = xy(0, cum_act[0]); xL, yL = xy(last_actual_i, cum_act[last_actual_i])
        base = _MT + _PH
        out.append(f'<polygon fill="url(#areaC)" points="{x0:.1f},{base:.1f} '
                   f'{" ".join(line_pts)} {xL:.1f},{base:.1f}"/>')
        out.append(f'<polyline class="draw" fill="none" stroke="{C_ACTUAL}" stroke-width="2.4" '
                   f'stroke-linecap="round" stroke-linejoin="round" points="{" ".join(line_pts)}"/>')
        out.append(f'<circle cx="{xL:.1f}" cy="{yL:.1f}" r="4" fill="{C_ACTUAL}" '
                   f'stroke="#faf9f5" stroke-width="1.5"/>')
    for i, d in enumerate(series):
        day = int(d["date"][-2:])
        if day == 1 or day % 5 == 0:
            x = _ML + (i / max(n - 1, 1)) * _PW
            out.append(f'<text x="{x:.1f}" y="{_MT+_PH+16}" class="xl">{day}</text>')
    out.append("</svg>")
    return "".join(out)


_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def chart_dow(dow_index):
    """Diverging bars around the 1.0 average line: above = sage, below = gold."""
    if not dow_index:
        return ""
    vals = [dow_index.get(w, 1.0) for w in _WEEK]
    dev = max([abs(v - 1.0) for v in vals] + [0.05]) * 1.25
    n = len(_WEEK)
    slot = _PW / n
    bw = slot * 0.46
    out = [f'<svg viewBox="0 0 {_CW} {_CH}" class="chart" role="img" preserveAspectRatio="xMidYMid meet">',
           _defs("W", C_FCST)]
    y0 = _MT + _PH / 2  # the 1.0 average baseline, centered
    half = _PH / 2 - 6
    out.append(f'<line x1="{_ML}" y1="{y0:.1f}" x2="{_ML+_PW}" y2="{y0:.1f}" '
               f'stroke="{C_AXIS}" stroke-width="1" stroke-dasharray="2,3" opacity="0.7"/>')
    out.append(f'<text x="{_ML-10}" y="{y0+3.5:.1f}" class="yl">1.00</text>')
    for i, w in enumerate(_WEEK):
        cx = _ML + i * slot + slot / 2
        d = vals[i] - 1.0
        h = (abs(d) / dev) * half
        up = d >= 0
        y = y0 - h if up else y0
        color = C_FCST if up else C_WARN
        out.append(f'<rect x="{cx-bw/2:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{max(h,0.5):.1f}" '
                   f'rx="1.6" fill="{color}" opacity="0.92"/>')
        ly = (y - 6) if up else (y + h + 13)
        out.append(f'<text x="{cx:.1f}" y="{ly:.1f}" class="bv" fill="{color}">{vals[i]:.2f}</text>')
        out.append(f'<text x="{cx:.1f}" y="{_MT+_PH+16}" class="xl">{w[:3].upper()}</text>')
    out.append("</svg>")
    return "".join(out)


# ---- provenance footer (analytics pattern) ----------------------------------

def provenance(plan):
    records = plan.get("data_provenance", {})
    budgets = records.get("current_budgets", {})
    actuals = records.get("performance_actuals", {})
    limitations = ["future values are planning targets recalculated on each run"]
    if actuals.get("preliminary"):
        limitations.append("performance actuals are preliminary")
    overdelivery = plan.get("amazon_budget_controls", {}).get(
        "average_daily_budget_overdelivery_pct", 0
    )
    if overdelivery:
        limitations.append(f"daily budget reserves {overdelivery:.0%} overdelivery headroom")
    if abs(plan.get("today_spend_target", 0) - plan.get("total_proposed", 0)) > 0.01:
        limitations.append("today's executable proposal differs from its unconstrained spend target")
    return {
        "Source": (
            f"current budgets: {budgets.get('source', 'not verified')} "
            f"(retrieved {budgets.get('retrieved_at', 'unknown')}); "
            f"performance actuals: {actuals.get('source', 'not verified')} "
            f"(retrieved {actuals.get('retrieved_at', 'unknown')})"
        ),
        "Confidence": (
            "medium-low — deterministic proposal using preliminary performance data"
            if actuals.get("preliminary") else
            "medium — deterministic proposal; depends on supplied source accuracy"
        ),
        "Freshness": f"performance data through {actuals.get('data_through', 'not verified')}",
        "Limitations": "; ".join(limitations),
    }


# ---- styles (palette lives in CSS custom properties; plain string, no f) -----

STYLE = """
:root{
  --paper:#f0eee6; --card:#faf9f5; --card2:#ffffff; --wash:#eae6da;
  --line:#e5e1d4; --line2:#dcd7c7;
  --ink:#1f1e1b; --ink2:#403d36; --mut:#6e6a60; --dim:#9b9583;
  --plan:#8fa3ad; --act:#cc785c; --act-d:#b0512f; --fcst:#7c9a6e;
  --gold:#c2913f; --good:#5f8463;
  --serif:ui-serif,Georgia,"Iowan Old Style","Apple Garamond","Times New Roman",serif;
  --sans:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
  font-size:13.5px;line-height:1.5;-webkit-font-smoothing:antialiased;
  background-image:radial-gradient(1200px 560px at 92% -10%, rgba(204,120,92,0.07), transparent 62%);
  background-attachment:fixed;}
body::after{content:"";position:fixed;inset:0;pointer-events:none;z-index:99;opacity:0.5;
  mix-blend-mode:multiply;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='matrix' values='0 0 0 0 0.06 0 0 0 0 0.05 0 0 0 0 0.04 0 0 0 0.025 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");}
.wrap{max-width:1000px;margin:0 auto;padding:48px 30px 84px}
.card-sh{box-shadow:0 1px 2px rgba(60,50,38,.04),0 10px 26px rgba(60,50,38,.045)}

/* reveal-on-load */
.reveal{animation:rise .6s cubic-bezier(.16,.7,.2,1) both;animation-delay:var(--d,0s)}
@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}

/* masthead */
.eyebrow{font-size:11px;letter-spacing:.26em;text-transform:uppercase;color:var(--act-d);
  font-weight:600;margin:0 0 16px;display:flex;align-items:center;gap:10px}
.eyebrow::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--act);
  box-shadow:0 0 0 4px rgba(204,120,92,0.14)}
h1{font-family:var(--serif);font-size:38px;line-height:1.04;letter-spacing:-.015em;
  margin:0 0 8px;font-weight:580;color:var(--ink)}
.client{color:var(--ink)} .h1sub{color:var(--dim);font-weight:400;font-style:italic}
.period{color:var(--mut);font-size:12.5px;margin:0}

/* hero strip: pacing readout + burn gauge */
.hero{display:grid;grid-template-columns:auto 1fr;gap:40px;align-items:center;
  margin:30px 0 8px;padding:30px 34px;background:var(--card);
  border:1px solid var(--line);border-radius:18px;
  box-shadow:0 1px 2px rgba(60,50,38,.04),0 12px 30px rgba(60,50,38,.05)}
.hero-fig{display:flex;flex-direction:column;gap:10px;min-width:150px}
.hero-num{font-family:var(--serif);font-size:74px;line-height:.86;font-weight:560;
  letter-spacing:-.03em;font-variant-numeric:tabular-nums;display:flex;align-items:baseline;gap:6px}
.hero-unit{font-size:26px;font-weight:500;color:var(--dim)}
.hero-cap{font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--mut);font-weight:500}
.status{align-self:flex-start;display:inline-flex;align-items:center;gap:7px;padding:5px 14px 5px 12px;
  border-radius:999px;font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
  color:#faf9f5}
.status::before{content:"";width:6px;height:6px;border-radius:50%;background:#faf9f5;opacity:.85}

/* burn gauge */
.gauge{display:flex;flex-direction:column;gap:12px}
.gauge-top{display:flex;justify-content:space-between;align-items:flex-end;font-size:11.5px;color:var(--mut)}
.gauge-top b{color:var(--ink);font-size:13.5px;font-weight:650}
.gauge-track{position:relative;height:15px;border-radius:8px;background:var(--wash);
  border:1px solid var(--line2);overflow:hidden}
.gauge-fill{position:absolute;top:0;left:0;bottom:0;border-radius:8px;
  background:linear-gradient(90deg,#d99873,var(--act));transform-origin:left;
  animation:grow 1.1s cubic-bezier(.16,.7,.2,1) both;animation-delay:.4s}
.gauge-fill.cool{background:linear-gradient(90deg,#9bb08c,var(--fcst))}
.gauge-fill.good{background:linear-gradient(90deg,#7da37e,var(--good))}
@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
.gauge-mark{position:absolute;top:-4px;bottom:-4px;width:2px;background:var(--ink);opacity:.78;
  box-shadow:0 0 0 3px var(--card)}
.gauge-mark::after{content:"";position:absolute;left:50%;top:-5px;width:5px;height:5px;
  border-radius:50%;background:var(--ink);transform:translateX(-50%)}
.gauge-mark span{position:absolute;top:-18px;left:50%;transform:translateX(-50%);white-space:nowrap;
  font-size:9.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--mut);font-weight:600}
.gauge-bot{display:flex;justify-content:space-between;font-size:11px;color:var(--dim)}
.gauge-bot b{color:var(--act-d);font-weight:650}

/* readouts row */
.readouts{display:grid;grid-template-columns:repeat(6,1fr);gap:1px;margin:24px 0 0;
  background:var(--line);border:1px solid var(--line);border-radius:14px;overflow:hidden;
  box-shadow:0 1px 2px rgba(60,50,38,.035),0 8px 22px rgba(60,50,38,.04)}
.ro{background:var(--card);padding:15px 17px;display:flex;flex-direction:column;gap:6px}
.ro-l{font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--mut);font-weight:600}
.ro-v{font-size:19px;font-weight:600;letter-spacing:-.01em;font-variant-numeric:tabular-nums;color:var(--ink)}
.ro-s{font-size:10.5px;color:var(--dim)}

/* sections + panels */
.section-t{font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--mut);
  font-weight:600;margin:46px 0 14px;display:flex;align-items:center;gap:14px}
.section-t::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,var(--line2),transparent)}
.panel{background:var(--card);border:1px solid var(--line);border-radius:16px;
  padding:20px 24px 16px;margin:14px 0;
  box-shadow:0 1px 2px rgba(60,50,38,.035),0 8px 22px rgba(60,50,38,.04)}
.panel-h{display:flex;justify-content:space-between;align-items:baseline;margin:0 0 8px;gap:14px;flex-wrap:wrap}
.panel-t{font-family:var(--serif);font-size:18px;font-weight:560;letter-spacing:-.01em;color:var(--ink)}
.panel-sub{font-size:11.5px;color:var(--dim);font-style:italic}
.legend{display:flex;gap:18px;flex-wrap:wrap}
.lg{display:inline-flex;align-items:center;gap:7px;font-size:11px;color:var(--mut)}
.lg i{width:12px;height:4px;border-radius:2px;display:inline-block}
.lg.dot i{width:12px;height:0;border-top:2px dotted currentColor;border-radius:0}
.chart{width:100%;height:auto;display:block;margin:4px 0 0}
.yl{font-size:10px;fill:var(--axis,#9a9488);text-anchor:end;font-family:var(--sans)}
.xl{font-size:10px;fill:#9a9488;text-anchor:middle;font-family:var(--sans)}
.bv{font-size:10.5px;text-anchor:middle;font-weight:650;font-family:var(--sans)}
.ceil{font-size:10px;fill:var(--act-d);text-anchor:end;letter-spacing:.08em;font-weight:600;font-family:var(--sans)}
.todaychip{font-size:8.5px;fill:#fffdf8;text-anchor:middle;font-weight:700;letter-spacing:.08em;font-family:var(--sans)}
.draw{stroke-dasharray:3200;stroke-dashoffset:3200;animation:draw 1.6s ease .5s forwards}
@keyframes draw{to{stroke-dashoffset:0}}

/* alert console */
.alerts{display:flex;flex-direction:column;gap:9px}
.alert{display:grid;grid-template-columns:auto auto 1fr;gap:15px;align-items:center;
  background:var(--card);border:1px solid var(--line);border-left-width:3px;border-radius:12px;
  padding:13px 18px}
.a-id{font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.03em;color:var(--mut)}
.sev{font-size:9.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  padding:3px 9px;border-radius:6px;color:#faf9f5;white-space:nowrap}
.a-body{display:flex;flex-direction:column;gap:2px;min-width:0}
.a-sub{font-size:12.5px;font-weight:600;color:var(--ink);overflow:hidden;text-overflow:ellipsis}
.a-det{font-size:11.5px;color:var(--mut)}
.no-alert{color:var(--dim);padding:15px 18px;background:var(--card);border:1px solid var(--line);border-radius:12px}

/* proposed table */
.tbl{width:100%;border-collapse:collapse;background:var(--card2);border:1px solid var(--line);
  border-radius:16px;overflow:hidden;
  box-shadow:0 1px 2px rgba(60,50,38,.035),0 8px 22px rgba(60,50,38,.04)}
.tbl th{font-size:9.5px;text-transform:uppercase;letter-spacing:.12em;color:var(--mut);
  text-align:left;padding:14px 18px;border-bottom:1px solid var(--line2);font-weight:600}
.tbl td{padding:14px 18px;border-bottom:1px solid var(--line);font-size:13px;vertical-align:middle;color:var(--ink2)}
.tbl tr:last-child td{border-bottom:none}
.tbl tbody tr:hover td{background:var(--card)}
.tbl .num{text-align:right;font-variant-numeric:tabular-nums}
.nm{font-size:12.5px;max-width:300px}
.nm b{font-weight:620;color:var(--ink)}.nm .tag{color:var(--dim);font-size:11px}
.delta{display:inline-flex;align-items:center;gap:8px;justify-content:flex-end;font-variant-numeric:tabular-nums;font-weight:650}
.dbar{position:relative;width:64px;height:6px;border-radius:3px;background:var(--wash);overflow:hidden;flex:none}
.dbar i{position:absolute;top:0;bottom:0;border-radius:3px}
.eff{font-weight:650;font-variant-numeric:tabular-nums}
.flags{display:flex;gap:5px;flex-wrap:wrap}
.flag{font-size:9px;letter-spacing:.04em;text-transform:uppercase;color:var(--mut);
  border:1px solid var(--line2);border-radius:5px;padding:2px 7px}
.up{color:var(--good)}.down{color:var(--act-d)}.flat{color:var(--mut)}

/* approval gate banner */
.gate{display:flex;align-items:center;gap:14px;margin:20px 0 0;padding:16px 20px;
  background:rgba(95,132,99,.08);border:1px solid rgba(95,132,99,.3);border-radius:14px;
  font-size:13px;color:var(--ink2)}
.gate .lock{font-size:17px;flex:none}
.gate b{color:var(--good)}

/* excluded */
.excl{list-style:none;padding:0;margin:10px 0 0;display:flex;flex-direction:column;gap:8px}
.excl li{font-size:12.5px;color:var(--mut);padding:13px 17px;background:var(--card);
  border:1px solid var(--line);border-left:3px solid var(--act-d);border-radius:12px}
.excl b{color:var(--ink)}

/* telemetry footer */
.telemetry{margin:46px 0 0;border-top:1px solid var(--line2);padding-top:20px;
  display:grid;grid-template-columns:repeat(2,1fr);gap:11px 36px}
.tm{display:flex;gap:12px;font-size:11.5px;line-height:1.55}
.tm-k{color:var(--mut);text-transform:uppercase;letter-spacing:.09em;font-size:9.5px;font-weight:600;
  padding-top:1px;flex:none;width:80px}
.tm-v{color:var(--dim)}
.sig{margin-top:26px;font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--dim);
  text-align:center}

@media (max-width:760px){
  .hero{grid-template-columns:1fr;gap:26px}
  .readouts{grid-template-columns:repeat(3,1fr)}
  .telemetry{grid-template-columns:1fr}
  h1{font-size:30px}.hero-num{font-size:60px}
}
@media (prefers-reduced-motion:reduce){
  *{animation:none!important}
  .gauge-fill{transform:none!important}.draw{stroke-dashoffset:0!important}
}
"""


# ---- HTML -------------------------------------------------------------------

_SEV = {"CRITICAL": "#b0512f", "HIGH": "#cc785c", "MEDIUM": "#c2913f", "LOW": "#8fa3ad"}


def _client_name(plan):
    """Best-effort client label from the first campaign name ("Client | ...")."""
    for c in plan.get("proposed_changes", []) + plan.get("excluded_campaigns", []):
        nm = c.get("name", "")
        if "|" in nm:
            return nm.split("|")[0].strip()
    return "Account"


def _short_name(name):
    """Drop the leading client token for tighter table rows."""
    parts = [p.strip() for p in name.split("|")]
    return " · ".join(parts[1:]) if len(parts) > 1 else name


def render_html(plan):
    status, scolor = pacing_status(plan.get("pacing_pct"))
    pct = plan.get("pacing_pct")
    pct_s = f"{pct*100:.0f}" if pct is not None else "—"
    budget = plan["monthly_budget"] or 1
    spent = plan["actuals_to_date"]
    fill = min(max(spent / budget, 0), 1.0) * 100
    mtd_plan = (spent / pct) if pct else None
    plan_mark = (min(mtd_plan / budget, 1.0) * 100) if (mtd_plan and budget) else None
    # gauge fill echoes status: hot=clay (default), light=sage, on-track=green
    if pct is None:
        gauge_class = "cool"
    elif pct > 1.20:
        gauge_class = ""
    elif pct < 0.80:
        gauge_class = "cool"
    else:
        gauge_class = "good"
    client = _client_name(plan)
    account = plan.get("account_context", {})
    currency = account.get("currency_code", "XXX")
    money = lambda value: _money(value, currency)
    scope = (
        f"advertiser {account.get('advertiser_account_id', 'unknown')} · "
        f"profile {account.get('profile_id', 'unknown')} · "
        f"{account.get('marketplace', 'unknown')} · {currency} · "
        f"{account.get('timezone', 'unknown')}"
    )

    # readouts
    kpis = [
        ("Monthly budget", money(budget), plan["month"]),
        ("Spent to date", money(spent), f"{fill:.0f}% of ceiling"),
        ("Remaining", money(plan["remaining_budget"]), f"over {plan['remaining_days']} days"),
        ("On-plan to date", money(mtd_plan) if mtd_plan else "—", "where pacing should sit"),
        ("Today's pool", money(plan["todays_pool"]), "after delivery reserve"),
        ("Total proposed", money(plan["total_proposed"]), "after campaign constraints"),
    ]
    ros = "".join(f'<div class="ro"><span class="ro-l">{_esc(l)}</span>'
                  f'<span class="ro-v">{_esc(v)}</span><span class="ro-s">{_esc(s)}</span></div>'
                  for l, v, s in kpis)

    mark_html = ""
    if plan_mark is not None:
        mark_html = (f'<div class="gauge-mark" style="left:{plan_mark:.1f}%">'
                     f'<span>on-plan {_kmoney(mtd_plan)}</span></div>')
    over = spent - mtd_plan if mtd_plan else None
    over_html = (f'<b>{money(over)} ahead of plan</b>' if over and over > 0
                 else (f'<b>{money(-over)} behind plan</b>' if over and over < 0 else 'on plan'))

    # alerts console
    alerts = ""
    for a in plan.get("alerts", []):
        sev = a.get("severity", "LOW"); col = _SEV.get(sev, C_PLAN)
        alerts += (f'<div class="alert" style="border-left-color:{col}">'
                   f'<span class="a-id">{_esc(a["id"])}</span>'
                   f'<span class="sev" style="background:{col}">{_esc(sev)}</span>'
                   f'<div class="a-body"><span class="a-sub">{_esc(a.get("subject",""))}</span>'
                   f'<span class="a-det">{_esc(a.get("detail",""))}</span></div></div>')
    alerts = f'<div class="alerts">{alerts}</div>' if alerts else \
        '<div class="no-alert">No alerts — pacing and efficiency within bands.</div>'
    warning_items = "".join(
        f'<div class="no-alert">{_esc(warning)}</div>'
        for warning in plan.get("warnings", [])
    )
    warnings_block = (
        f'<div class="section-t">Allocator warnings</div><div class="alerts">{warning_items}</div>'
        if warning_items else ""
    )

    # proposed table with delta bars
    changes = plan.get("proposed_changes", [])
    max_abs = max([abs(c["delta_pct"]) for c in changes if c["delta_pct"] is not None] + [0.01])
    rows = ""
    for c in changes:
        dp = c["delta_pct"]
        dps = f'{dp*100:+.0f}%' if dp is not None else "—"
        cls = "down" if c["delta"] < 0 else ("up" if c["delta"] > 0 else "flat")
        arrow = "▼" if c["delta"] < 0 else ("▲" if c["delta"] > 0 else "—")
        w = (abs(dp) / max_abs * 50) if dp is not None else 0   # half-width = 50%
        if c["delta"] < 0:
            bar = f'<i style="right:50%;width:{w:.0f}%;background:{C_ACTUAL}"></i>'
        elif c["delta"] > 0:
            bar = f'<i style="left:50%;width:{w:.0f}%;background:{C_FCST}"></i>'
        else:
            bar = ""
        eff = c["efficiency_ratio"]
        ecol = C_ACTUAL if eff < 0.70 else (C_FCST if eff > 1.30 else "var(--mut)")
        flags = "".join(f'<span class="flag">{f}</span>' for f, on in
                        (("floored", c["floored"]), ("ceiling", c["ceiling_clipped"]),
                         ("capped", c["change_capped"])) if on)
        rows += (f'<tr><td class="nm"><b>{_esc(_short_name(c["name"]))}</b></td>'
                 f'<td class="num">{money(c["current_daily_budget"])}</td>'
                 f'<td class="num">{money(c["proposed_daily_budget"])}</td>'
                 f'<td class="num"><span class="delta {cls}">'
                 f'<span class="dbar">{bar}</span>{arrow} {dps}</span></td>'
                 f'<td class="num eff" style="color:{ecol}">{eff:.2f}</td>'
                 f'<td><div class="flags">{flags}</div></td></tr>')

    excl = "".join(f'<li><b>{_esc(e["name"])}</b> — {_esc(e["reason"])}</li>'
                   for e in plan.get("excluded_campaigns", []))
    excl_block = (f'<div class="section-t">Excluded from automation</div>'
                  f'<ul class="excl">{excl}</ul>') if excl else ""

    action_rows = "".join(
        f'<tr><td class="nm"><b>{_esc(a["name"])}</b></td>'
        f'<td>{_esc(a["action"].replace("_", " ").capitalize())}</td>'
        f'<td>{_esc(a.get("current_state", ""))} → {_esc(a.get("proposed_state", ""))}</td>'
        f'<td>{_esc(a.get("reason", ""))}</td></tr>'
        for a in plan.get("proposed_actions", [])
    )
    action_block = (
        '<div class="section-t">Proposed account actions</div>'
        '<table class="tbl"><thead><tr><th>Campaign</th><th>Action</th>'
        f'<th>State</th><th>Reason</th></tr></thead><tbody>{action_rows}</tbody></table>'
        if action_rows else ""
    )

    prov = provenance(plan)
    prov_html = "".join(f'<div class="tm"><span class="tm-k">{_esc(k)}</span>'
                        f'<span class="tm-v">{_esc(v)}</span></div>' for k, v in prov.items())

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Budget Pacing — {_esc(client)} · {_esc(plan['month'])}</title>
<style>{STYLE}</style></head><body><div class="wrap">

<header class="reveal" style="--d:0s">
  <p class="eyebrow">Amazon Ads · Monthly Budget Pacing</p>
  <h1><span class="client">{_esc(client)}</span> <span class="h1sub">— {_esc(plan['month'])}</span></h1>
  <p class="period">Run as of {_esc(plan['as_of'])} · proposal {_esc(plan.get('proposal_id', 'unknown'))} · {_esc(scope)} · proposal only</p>
</header>

<section class="hero reveal" style="--d:.06s">
  <div class="hero-fig">
    <span class="hero-cap">Pacing vs plan</span>
    <span class="hero-num" style="color:{scolor}">{pct_s}<span class="hero-unit">%</span></span>
    <span class="status" style="background:{scolor}">{_esc(status)}</span>
  </div>
  <div class="gauge">
    <div class="gauge-top"><span>Spend against monthly ceiling</span>
      <span><b>{money(spent)}</b> / {money(budget)}</span></div>
    <div class="gauge-track">
      <div class="gauge-fill {gauge_class}" style="width:{fill:.1f}%"></div>
      {mark_html}
    </div>
    <div class="gauge-bot"><span>{over_html}</span>
      <span>{money(plan['remaining_budget'])} left · {plan['remaining_days']} days</span></div>
  </div>
</section>

<div class="readouts reveal" style="--d:.12s">{ros}</div>

<div class="section-t reveal" style="--d:.16s">Spend vs plan</div>
<div class="panel reveal" style="--d:.18s">
  <div class="panel-h"><span class="panel-t">Daily spend — plan vs actual / forecast</span>
    <div class="legend"><span class="lg" style="color:var(--plan)"><i style="background:var(--plan)"></i>Plan</span>
      <span class="lg" style="color:var(--act)"><i style="background:var(--act)"></i>Actual</span>
      <span class="lg" style="color:var(--fcst)"><i style="background:var(--fcst)"></i>Forecast</span></div></div>
  {chart_planned_vs_actual(plan['daily_series'])}
</div>
<div class="panel reveal" style="--d:.24s">
  <div class="panel-h"><span class="panel-t">Cumulative budget pacing</span>
    <span class="panel-sub">green = forward planning target; future runs recalculate it</span></div>
  <div class="legend" style="margin:2px 0 0">
    <span class="lg" style="color:var(--plan)"><i style="background:var(--plan)"></i>Cumulative plan</span>
    <span class="lg" style="color:var(--act)"><i style="background:var(--act)"></i>Actual burn</span>
    <span class="lg dot" style="color:var(--fcst)"><i></i>Corrected forecast</span></div>
  {chart_cumulative(plan['daily_series'], plan['monthly_budget'])}
</div>

<div class="section-t reveal" style="--d:.28s">Seasonality</div>
<div class="panel reveal" style="--d:.30s">
  <div class="panel-h"><span class="panel-t">Day-of-week seasonality index</span>
    <span class="panel-sub">deviation from the 1.0 average · above the line in green, below in gold</span></div>
  {chart_dow(plan.get('dow_index', {}))}
</div>

<div class="section-t reveal" style="--d:.34s">Alerts</div>
<div class="reveal" style="--d:.36s">{alerts}</div>

{warnings_block}

<div class="section-t reveal" style="--d:.40s">Proposed daily budgets</div>
<div class="reveal" style="--d:.42s">
<table class="tbl"><thead><tr><th>Campaign</th><th class="num">Current</th>
<th class="num">Proposed</th><th class="num">Change</th><th class="num">Eff.</th><th>Flags</th></tr></thead>
<tbody>{rows}</tbody></table>
<div class="gate"><span class="lock">🔒</span><span><b>Proposed only</b> — no budgets are written to Amazon until a human approves this change-set.</span></div>
</div>

{action_block}

{excl_block}

<div class="telemetry reveal" style="--d:.5s">{prov_html}</div>
<div class="sig">Amazon Ads · Budget Pacing · {_esc(client)}</div>

</div></body></html>"""


def render_md(plan):
    status, _ = pacing_status(plan.get("pacing_pct"))
    pct = plan.get("pacing_pct")
    pct_s = f"{pct*100:.0f}%" if pct is not None else "—"
    budget = plan["monthly_budget"] or 1
    fill = min(max(plan["actuals_to_date"] / budget, 0), 1.0) * 100
    mtd_plan = (plan["actuals_to_date"] / pct) if pct else None
    account = plan.get("account_context", {})
    currency = account.get("currency_code", "XXX")
    money = lambda value: _money(value, currency)
    onplan = f" · on-plan to date {money(mtd_plan)}" if mtd_plan else ""
    L = [f"# Amazon Ads Pacing Report — {plan['month']}",
         f"*as of {plan['as_of']}* — **{status} ({pct_s} of plan)**", "",
         f"- Proposal ID: `{plan.get('proposal_id', 'unknown')}`",
         f"- Account scope: advertiser `{account.get('advertiser_account_id', 'unknown')}` · "
         f"profile `{account.get('profile_id', 'unknown')}` · "
         f"{account.get('marketplace', 'unknown')} · {currency} · "
         f"{account.get('timezone', 'unknown')}",
         f"- Monthly budget: {money(plan['monthly_budget'])}",
         f"- Spent to date: {money(plan['actuals_to_date'])} ({fill:.0f}% of ceiling){onplan}",
         f"- Remaining: {money(plan['remaining_budget'])} over {plan['remaining_days']} days",
         f"- Today's pool: {money(plan['todays_pool'])} · total proposed: {money(plan['total_proposed'])}",
         "", "Charts (planned-vs-actual, cumulative pacing, day-of-week seasonality) are in `report.html`.",
         "", "## Alerts"]
    if plan.get("alerts"):
        for a in plan["alerts"]:
            L.append(f"- **{a['id']} [{a.get('severity','')}]** {_md_cell(a.get('subject',''))}: {a.get('detail','')}")
    else:
        L.append("- None.")
    if plan.get("warnings"):
        L += ["", "## Allocator warnings"]
        L.extend(f"- {warning}" for warning in plan["warnings"])
    L += ["", "## Proposed daily budgets", "",
          "| Campaign | Current | Proposed | Δ% | Eff. |", "|---|---:|---:|---:|---:|"]
    for c in plan.get("proposed_changes", []):
        dp = c["delta_pct"]
        L.append(f"| {_md_cell(c['name'])} | {money(c['current_daily_budget'])} | "
                 f"{money(c['proposed_daily_budget'])} | "
                 f"{(f'{dp*100:+.0f}%' if dp is not None else '—')} | {c['efficiency_ratio']:.2f} |")
    if plan.get("proposed_actions"):
        L += ["", "## Proposed account actions"]
        for action in plan["proposed_actions"]:
            L.append(
                f"- `{action['action']}` — {_md_cell(action['name'])}: "
                f"{action.get('current_state', '')} → {action.get('proposed_state', '')}. "
                f"{action.get('reason', '')}"
            )
    if plan.get("excluded_campaigns"):
        L += ["", "## Excluded from automation"]
        for e in plan["excluded_campaigns"]:
            L.append(f"- {_md_cell(e['name'])} — {e['reason']}")
    L += ["", "_Proposed only — no budgets are written to Amazon until a human approves._", ""]
    for k, v in provenance(plan).items():
        L.append(f"{k}: {v}")
    return "\n".join(L)


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print(__doc__)
        sys.exit(1)
    with open(argv[0]) as f:
        plan = json.load(f)
    out_dir = argv[1].rstrip("/") if len(argv) > 1 else "."
    os.makedirs(out_dir, exist_ok=True)
    html_path, md_path = f"{out_dir}/report.html", f"{out_dir}/report.md"
    with open(html_path, "w") as f:
        f.write(render_html(plan))
    with open(md_path, "w") as f:
        f.write(render_md(plan))
    print(f"Wrote {html_path} and {md_path}")
    print(render_md(plan))


if __name__ == "__main__":
    main()
