#!/usr/bin/env python3
"""Course Dashboard generator.

Renders a Course Passport into a single self-contained HTML file the professor
can open locally — a complete overview of the course design and every generated
resource, with clickable links to artifact files on disk.

Usage:
  python3 scripts/build_dashboard.py path/to/course_passport.yaml [-o out.html]

Output defaults to course_dashboard.html next to the passport, so relative
artifact links resolve. Deterministic apart from the generation timestamp:
regenerate freely at every checkpoint — the passport is the source of truth,
the dashboard is a build product.

Sections: at-a-glance cards (grade composition, Bloom distribution, semester
strip) · gates with live re-check · alignment matrix · outcomes · assessment
plan · schedule with week resources · policies · artifacts ledger · learners,
workload & iteration history. No external dependencies; prints cleanly.

Exit codes: 0 = written · 2 = error
"""

import argparse
import datetime
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_passport import load_passport, crossref_findings  # noqa: E402
from check_alignment_gate import gate_findings, suppress_dismissed  # noqa: E402

e = html.escape

BLOOM_ORDER = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
BLOOM = {"remember": "#64748b", "understand": "#0891b2", "apply": "#2563eb",
         "analyze": "#7c3aed", "evaluate": "#c026d3", "create": "#dc2626"}
PALETTE = ["#2563eb", "#0891b2", "#7c3aed", "#d97706", "#16a34a",
           "#dc2626", "#c026d3", "#475569", "#ca8a04", "#0d9488"]
GATE = {"pass": ("#16a34a", "pass"), "fail": ("#dc2626", "fail"),
        "not_run": ("#94a3b8", "not run")}
SEV = {"BLOCK": "#dc2626", "WARN": "#d97706", "NOT_EVALUABLE": "#64748b"}

CSS = """
:root{--ink:#1e293b;--mut:#64748b;--line:#e2e8f0;--bg:#f8fafc;--acc:#2563eb}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,
"Segoe UI","PingFang SC","Noto Sans",sans-serif;color:var(--ink);background:var(--bg)}
header{background:#fff;border-bottom:1px solid var(--line);padding:26px 32px}
h1{margin:0 0 4px;font-size:22px}
.sub{color:var(--mut)}.chips{margin-top:10px}
.chip{display:inline-block;background:var(--bg);border:1px solid var(--line);
border-radius:999px;padding:2px 10px;margin:2px 4px 2px 0;font-size:12.5px}
nav{position:sticky;top:0;background:#fff;border-bottom:1px solid var(--line);
padding:8px 32px;z-index:9}nav a{color:var(--acc);text-decoration:none;margin-right:14px;
font-size:13.5px;white-space:nowrap}
main{max-width:1100px;margin:0 auto;padding:22px 32px 64px}
details.sec{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:4px 24px 6px;margin:16px 0}
details.sec[open]{padding-bottom:20px}
details.sec>summary{cursor:pointer;list-style:none;font-size:16px;font-weight:700;
padding:14px 0;user-select:none}
details.sec>summary::before{content:"▸ ";color:var(--mut)}
details.sec[open]>summary::before{content:"▾ "}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th{text-align:left;color:var(--mut);font-weight:600;border-bottom:2px solid var(--line);
padding:6px 8px}td{border-bottom:1px solid var(--line);padding:7px 8px;vertical-align:top}
.b{display:inline-block;color:#fff;border-radius:4px;padding:1px 7px;font-size:11.5px;
font-weight:600}
a.tag,span.tag{display:inline-block;background:#eef2ff;color:#3730a3;border-radius:4px;
padding:1px 6px;font-size:11.5px;margin:1px 2px;text-decoration:none}
a.tag:hover{background:#e0e7ff}
.bar{background:var(--line);border-radius:4px;height:8px;min-width:110px}
.bar i{display:block;height:8px;border-radius:4px;background:var(--acc)}
.ok{color:#16a34a}.miss{color:#dc2626;font-weight:600}.dim{color:var(--mut);font-size:12.5px}
a.f{color:var(--acc);text-decoration:none}a.f:hover{text-decoration:underline}
footer{color:var(--mut);font-size:12.5px;text-align:center;padding:18px}
.note{background:#fffbeb;border:1px solid #fde68a;border-radius:8px;
padding:10px 14px;font-size:13px;margin-top:10px}
mark.np{background:#fef3c7;border-radius:3px;padding:0 3px;font-size:12.5px}
.cards{display:flex;gap:16px;flex-wrap:wrap;margin-top:4px}
.card{flex:1 1 280px;border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card h3{margin:0 0 10px;font-size:13.5px;color:var(--mut);font-weight:600;
text-transform:uppercase;letter-spacing:.4px}
.dwrap{display:flex;align-items:center;gap:16px}
.donut{position:relative;width:132px;height:132px;border-radius:50%;flex:none}
.donut i{position:absolute;inset:32px;background:#fff;border-radius:50%;display:flex;
align-items:center;justify-content:center;font-weight:700;font-size:15px}
.legend{font-size:12px;line-height:1.7}.legend b{font-weight:600}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;
vertical-align:-1px}
.bb{display:flex;align-items:center;gap:8px;margin:5px 0;font-size:12.5px}
.bb .lbl{width:86px;flex:none;text-align:right;color:var(--mut)}
.bb .tr{flex:1;background:var(--bg);border-radius:4px;height:14px}
.bb .tr i{display:block;height:14px;border-radius:4px}
.strip{display:flex;gap:3px;flex-wrap:wrap;margin-top:4px}
.wk{width:30px;height:38px;border:1px solid var(--line);border-radius:5px;background:#fff;
font-size:9.5px;color:var(--mut);text-align:center;padding-top:2px;position:relative}
.wk.res{background:#dbeafe;border-color:#93c5fd}
.wk.log{background:repeating-linear-gradient(45deg,#f1f5f9,#f1f5f9 4px,#fff 4px,#fff 8px)}
.wk .dots{position:absolute;bottom:3px;left:0;right:0;text-align:center;letter-spacing:1px;
font-size:8px;color:#dc2626}
.mx td,.mx th{text-align:center;padding:4px 6px}
.mx td:first-child,.mx th:first-child{text-align:left}
.mx .hit{color:#fff;border-radius:4px;font-weight:700}
.mxw{display:inline-block;width:9px;height:9px;border-radius:2px;background:var(--line);
margin:0 1px}.mxw.on{background:#60a5fa}
@media print{nav,.donut i{display:none}details.sec{break-inside:avoid;border:none}
details.sec>summary::before{content:""}body{background:#fff}}
"""

SCRIPT = """
document.querySelectorAll('a[href^="#"]').forEach(a=>a.addEventListener('click',()=>{
  const t=document.querySelector(a.getAttribute('href'));
  if(t){const d=t.closest('details');if(d)d.open=true;}
}));
"""


def badge(text, color):
    return f'<span class="b" style="background:{color}">{e(str(text))}</span>'


def ref_chip(rid):
    return f'<a class="tag" href="#{e(rid)}">{e(rid)}</a>'


def chips(ids, empty=""):
    return "".join(ref_chip(x) for x in ids or []) or (
        f'<span class="miss">{empty}</span>' if empty else '<span class="dim">—</span>')


def file_cell(base, ref):
    if not ref:
        return '<span class="dim">—</span>'
    if (base / ref).exists():
        return f'<a class="f" href="{e(ref)}">{e(ref)}</a>'
    return f'<span class="miss" title="file not found next to the passport">{e(ref)} ⚠ missing</span>'


def np_mark(text):
    """Highlight [NEEDS PROFESSOR INPUT: ...] markers inside escaped text."""
    return re.sub(r"(\[NEEDS PROFESSOR INPUT[^\]]*\])", r"<mark class=np>\1</mark>", e(text))


def section(sid, title, body, open_=True):
    return (f"<details class='sec' id='{sid}' {'open' if open_ else ''}>"
            f"<summary>{e(title)}</summary>{body}</details>")


def week_num(wid):
    m = re.match(r"^W(\d+)$", wid or "")
    return int(m.group(1)) if m else 0


# --- at-a-glance cards --------------------------------------------------------

def card_weights(plan):
    stops, legend, cum = [], [], 0.0
    for i, a in enumerate(plan):
        w = a.get("weight") or 0
        if w <= 0:
            continue
        color = PALETTE[i % len(PALETTE)]
        stops.append(f"{color} {cum}% {cum + w}%")
        legend.append(f"<div><span class=sw style='background:{color}'></span>"
                      f"<b>{e(a['id'])}</b> {e(a.get('title','')[:30])} — {w}%</div>")
        cum += w
    if cum < 100:
        stops.append(f"#e2e8f0 {cum}% 100%")
        legend.append(f"<div><span class=sw style='background:#e2e8f0'></span>"
                      f"unallocated — {round(100 - cum, 1)}%</div>")
    total = round(cum, 1)
    total_txt = f"{int(total) if total == int(total) else total}%"
    return (f"<div class=card><h3>Grade composition</h3><div class=dwrap>"
            f"<div class=donut style='background:conic-gradient({','.join(stops)})'>"
            f"<i>{total_txt}</i></div><div class=legend>{''.join(legend)}</div></div></div>")


def card_bloom(los):
    counts = {b: 0 for b in BLOOM_ORDER}
    for o in los:
        if o.get("bloom_level") in counts:
            counts[o["bloom_level"]] += 1
    mx = max(counts.values()) or 1
    rows = "".join(
        f"<div class=bb><span class=lbl>{b}</span><span class=tr>"
        f"<i style='width:{counts[b]/mx*100:.0f}%;background:{BLOOM[b]}'></i></span>"
        f"<span class=dim>{counts[b]}</span></div>" for b in BLOOM_ORDER)
    return (f"<div class=card><h3>Outcomes by Bloom level</h3>{rows}"
            f"<div class=dim style='margin-top:8px'>{len(los)} outcomes total</div></div>")


def card_strip(weeks, a_by_id):
    cells = []
    for w in weeks:
        cls = "wk"
        if w.get("artifact_refs"):
            cls += " res"
        if w.get("tag") == "logistics":
            cls += " log"
        due = w.get("assessments_due") or []
        tip = f"{w['id']}: {w.get('topic','')}"
        if due:
            tip += " — due: " + ", ".join(due)
        dots = "●" * min(len(due), 4)
        cells.append(f"<div class='{cls}' title='{e(tip)}'>{e(w['id'])}"
                     f"<div class=dots>{dots}</div></div>")
    return (f"<div class=card><h3>Semester</h3><div class=strip>{''.join(cells)}</div>"
            f"<div class=dim style='margin-top:8px'>blue = materials built · striped = "
            f"logistics week · ● = assessment due</div></div>")


def sec_glance(p):
    plan = p.get("assessment_plan") or []
    los = p.get("learning_outcomes") or []
    weeks = p.get("schedule") or []
    a_by_id = {a.get("id"): a for a in plan}
    return section("glance", "Course at a glance",
                   f"<div class=cards>{card_weights(plan)}{card_bloom(los)}"
                   f"{card_strip(weeks, a_by_id)}</div>")


# --- alignment matrix ---------------------------------------------------------

def sec_matrix(p):
    los = p.get("learning_outcomes") or []
    plan = p.get("assessment_plan") or []
    weeks = [w.get("id") for w in p.get("schedule") or []]
    if not los or not plan:
        return ""
    head = "".join(f"<th>{ref_chip(a['id'])}</th>" for a in plan)
    rows = []
    for i, o in enumerate(los):
        assessed = set(o.get("assessed_by") or [])
        cells = "".join(
            f"<td>{'<span class=hit style=background:' + BLOOM.get(o.get('bloom_level'), '#64748b') + '>✓</span>' if a['id'] in assessed else '<span class=dim>·</span>'}</td>"
            for a in plan)
        taught = set(o.get("taught_in") or [])
        strip = "".join(f"<span class='mxw{' on' if w in taught else ''}' title='{e(w)}'></span>"
                        for w in weeks)
        rows.append(f"<tr><td>{ref_chip(o['id'])} "
                    f"{badge(o.get('bloom_level',''), BLOOM.get(o.get('bloom_level'), '#64748b'))}"
                    f"<div style='margin-top:3px'>{strip}</div></td>{cells}</tr>")
    body = (f"<table class=mx><tr><th>outcome · taught-in weeks</th>{head}</tr>"
            + "".join(rows) + "</table>"
            "<p class=dim>✓ = the assessment evidences the outcome (colored by Bloom "
            "level). The dot strip under each outcome marks the weeks it is taught — "
            "together these are the constructive-alignment triangle the Alignment Gate "
            "checks.</p>")
    return section("matrix", "Alignment matrix", body)


# --- main sections ------------------------------------------------------------

def sec_outcomes(p):
    rows = []
    for o in p.get("learning_outcomes") or []:
        bl = o.get("bloom_level", "")
        rows.append(
            f"<tr id='{e(o['id'])}'><td><b>{e(o['id'])}</b></td>"
            f"<td>{e(o.get('statement',''))}</td>"
            f"<td>{badge(bl, BLOOM.get(bl, '#64748b'))}</td>"
            f"<td>{chips(o.get('assessed_by'), 'unassessed')}</td>"
            f"<td>{chips(o.get('taught_in'), 'untaught')}</td></tr>")
    return section("outcomes", "Learning outcomes",
                   "<table><tr><th>id</th><th>statement</th><th>Bloom</th>"
                   "<th>assessed by</th><th>taught in</th></tr>" + "".join(rows) + "</table>")


def sec_assessments(p, base):
    rows = []
    weeks_due = {}
    for w in p.get("schedule") or []:
        for aid in w.get("assessments_due") or []:
            weeks_due.setdefault(aid, []).append(w["id"])
    for a in p.get("assessment_plan") or []:
        w = a.get("weight") or 0
        air = a.get("ai_resilience", "not_reviewed")
        air_color = {"reviewed": "#16a34a", "redesigned": "#2563eb"}.get(air, "#d97706")
        due = chips(weeks_due.get(a["id"]))
        rows.append(
            f"<tr id='{e(a['id'])}'><td><b>{e(a['id'])}</b></td><td>{e(a.get('title',''))}"
            f"<div class=dim>{e(a.get('type',''))} · {e(str(a.get('week') or ''))}</div></td>"
            f"<td><div class=bar><i style='width:{min(w,100)}%'></i></div>"
            f"<span class=dim>{w}%</span></td>"
            f"<td>{chips(a.get('outcomes_assessed'))}</td><td>{due}</td>"
            f"<td>{badge(air, air_color)}</td>"
            f"<td>{file_cell(base, a.get('artifact_ref'))}</td></tr>")
    return section("assessments", "Assessment plan",
                   "<table><tr><th>id</th><th>assessment</th><th>weight</th>"
                   "<th>outcomes</th><th>due</th><th>AI integrity</th><th>artifact</th></tr>"
                   + "".join(rows) + "</table>")


def sec_schedule(p, base):
    rows = []
    for w in p.get("schedule") or []:
        refs = "".join(f"<div>{file_cell(base, r)}</div>" for r in w.get("artifact_refs") or []) \
               or '<span class="dim">none yet</span>'
        tag = ' <span class="tag">logistics</span>' if w.get("tag") == "logistics" else ""
        rows.append(
            f"<tr id='{e(w['id'])}'><td><b>{e(w['id'])}</b></td>"
            f"<td>{e(w.get('topic',''))}{tag}</td>"
            f"<td>{chips(w.get('outcomes'))}</td>"
            f"<td>{chips(w.get('assessments_due'))}</td>"
            f"<td>{refs}</td></tr>")
    return section("schedule", "Schedule & week resources",
                   "<table><tr><th>week</th><th>topic</th><th>outcomes</th><th>due</th>"
                   "<th>resources</th></tr>" + "".join(rows) + "</table>")


def sec_policies(p):
    pol = p.get("policies") or {}
    labels = [("grading_scheme", "Grading scheme"), ("late_policy", "Late work"),
              ("ai_use_policy", "AI use"), ("integrity_policy", "Academic integrity"),
              ("attendance_policy", "Attendance")]
    rows = []
    for key, label in labels:
        val = (pol.get(key) or "").strip()
        cell = np_mark(val) if val else '<span class="dim">not set</span>'
        rows.append(f"<tr><td style='width:170px'><b>{e(label)}</b></td><td>{cell}</td></tr>")
    extra = {k: v for k, v in pol.items() if k not in dict(labels) and v}
    for k, v in extra.items():
        rows.append(f"<tr><td><b>{e(k)}</b></td><td>{np_mark(str(v))}</td></tr>")
    body = ("<table>" + "".join(rows) + "</table>"
            "<p class=dim>Highlighted markers are institution-specific facts the suite "
            "never invents — fill them from your faculty handbook.</p>")
    return section("policies", "Policies", body, open_=False)


def sec_artifacts(p, base):
    arts = p.get("artifacts") or []
    confirmed = sum(1 for a in arts if a.get("confirmed_by_professor"))
    missing = sum(1 for a in arts if a.get("path") and not (base / a["path"]).exists())
    rows = []
    for a in arts:
        ok = '<span class="ok">✓ confirmed</span>' if a.get("confirmed_by_professor") \
            else '<span class="dim">pending confirmation</span>'
        rows.append(
            f"<tr><td>{file_cell(base, a.get('path'))}</td><td>{e(a.get('type',''))}</td>"
            f"<td>{e(str(a.get('produced_by','')))}</td><td>{e(str(a.get('stage','')))}</td>"
            f"<td>{ok}</td></tr>")
    stats = (f"<p class=dim>{len(arts)} artifacts · {confirmed} confirmed · "
             f"{missing} missing on disk</p>")
    return section("artifacts", "Artifacts ledger",
                   stats + "<table><tr><th>file</th><th>type</th><th>produced by</th>"
                   "<th>stage</th><th>status</th></tr>" + "".join(rows) + "</table>")


def sec_gates(p):
    out = []
    for name, gate in (p.get("gates") or {}).items():
        color, label = GATE.get((gate or {}).get("status", "not_run"), GATE["not_run"])
        out.append(f"<p><b>{e(name.replace('_', ' '))}</b> {badge(label, color)} "
                   f"<span class=dim>last run: {e(str((gate or {}).get('last_run') or '—'))}</span></p>")
        fnds = (gate or {}).get("findings") or []
        if fnds:
            rows = []
            for f in fnds:
                st = (f'<span class=dim>dismissed: {e(f["dismissed"])}</span>'
                      if f.get("dismissed") else "open")
                rows.append(
                    f"<tr><td>{badge(f.get('severity',''), SEV.get(f.get('severity'), '#64748b'))}</td>"
                    f"<td><b>{e(f.get('check_id',''))}</b></td><td>{e(f.get('detail',''))}</td>"
                    f"<td>{st}</td></tr>")
            out.append("<table><tr><th></th><th>check</th><th>finding</th>"
                       "<th>status</th></tr>" + "".join(rows) + "</table>")
    # live re-check, so the dashboard never shows a stale green
    live, _ = gate_findings(p)
    live, _ = suppress_dismissed(live, p)
    live += [f for f in crossref_findings(p)]
    if live:
        items = "".join(f"<li>{badge(f['severity'], SEV.get(f['severity'], '#64748b'))} "
                        f"<b>{e(f['check_id'])}</b> {e(f['detail'])}</li>" for f in live)
        out.append(f"<div class=note><b>Live re-check found open issues "
                   f"(passport changed since the gate last ran?):</b><ul>{items}</ul></div>")
    else:
        out.append('<p class="dim">Live re-check: structure and alignment checks are clean right now.</p>')
    return section("gates", "Gates", "".join(out))


def sec_learners(p):
    lp = p.get("learner_profile") or {}
    parts = []
    pairs = [("prior_knowledge", "Prior knowledge"), ("motivation_context", "Motivation"),
             ("accessibility_needs", "Accessibility")]
    rows = "".join(f"<tr><td style='width:170px'><b>{e(lbl)}</b></td>"
                   f"<td>{np_mark(str(lp.get(k) or '')) or '<span class=dim>—</span>'}</td></tr>"
                   for k, lbl in pairs)
    parts.append(f"<table>{rows}</table>")
    kd = "".join(f"<li>{e(d)}</li>" for d in lp.get("known_difficulties") or [])
    if kd:
        parts.append(f"<p><b>Known difficulties</b></p><ul>{kd}</ul>")
    ce = lp.get("cohort_evidence")
    if ce:
        parts.append("<p><b>Cohort evidence</b> <span class=dim>(aggregates from "
                     "cohort-analyst — no individual data)</span></p>"
                     f"<pre class=dim style='white-space:pre-wrap'>{e(str(ce))}</pre>")
    return section("learners", "Learner profile", "".join(parts), open_=False)


def sec_misc(p):
    wa = p.get("workload_audit") or {}
    est, tgt = wa.get("estimated_hours_per_week"), wa.get("credit_hour_target")
    pct = min((est or 0) / tgt * 100, 140) if (est and tgt) else 0
    gauge = (f"<div class=bar style='max-width:300px'><i style='width:{pct:.0f}%;"
             f"background:{'#16a34a' if wa.get('status') == 'within_range' else '#d97706'}'></i></div>"
             if est and tgt else "")
    wl = (f"<p>estimated <b>{e(str(est))}</b> h/week out of class vs target "
          f"{e(str(tgt))} — {badge(wa.get('status', 'not_audited'), '#16a34a' if wa.get('status') == 'within_range' else '#d97706')}</p>{gauge}")
    if wa.get("constants_used"):
        wl += f"<p class=dim>{e(str(wa['constants_used']))}</p>"
    its = "".join(
        f"<li><b>{e(i.get('term',''))}</b>: "
        f"{'; '.join(e(c) for c in i.get('changes') or [])}"
        f"<div class=dim>{e(i.get('evidence',''))}</div></li>"
        for i in p.get("iteration_history") or []) or "<li class=dim>none yet</li>"
    return section("more", "Workload & iteration",
                   wl + f"<p><b>Iteration history:</b></p><ul>{its}</ul>")


def build(passport_path, out_path=None):
    passport_path = Path(passport_path)
    p = load_passport(passport_path)
    base = passport_path.parent
    out = Path(out_path) if out_path else base / "course_dashboard.html"

    c = p.get("course") or {}
    arts = p.get("artifacts") or []
    confirmed = sum(1 for a in arts if a.get("confirmed_by_professor"))
    chips_html = "".join(f'<span class="chip">{e(x)}</span>' for x in [
        f"{len(p.get('learning_outcomes') or [])} outcomes",
        f"{len(p.get('assessment_plan') or [])} assessments",
        f"{len(p.get('schedule') or [])} weeks",
        f"{confirmed}/{len(arts)} artifacts confirmed",
        str(c.get("modality") or ""),
        f"{c.get('class_size') or '?'} students",
        f"{c.get('contact_hours_per_week') or '?'} h/wk contact",
        ("prereq: " + ", ".join(c.get("prerequisites") or [])) if c.get("prerequisites") else "",
    ] if x)

    body = (sec_glance(p) + sec_gates(p) + sec_matrix(p) + sec_outcomes(p)
            + sec_assessments(p, base) + sec_schedule(p, base) + sec_policies(p)
            + sec_artifacts(p, base) + sec_learners(p) + sec_misc(p))
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    nav = "".join(f'<a href="#{sid}">{label}</a>' for sid, label in [
        ("glance", "Glance"), ("gates", "Gates"), ("matrix", "Matrix"),
        ("outcomes", "Outcomes"), ("assessments", "Assessments"),
        ("schedule", "Schedule"), ("policies", "Policies"),
        ("artifacts", "Artifacts"), ("learners", "Learners"), ("more", "More")])
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(c.get('code',''))} — Course Dashboard</title><style>{CSS}</style></head><body>
<header><h1>{e(c.get('code',''))}: {e(c.get('title',''))}</h1>
<div class="sub">{e(c.get('discipline',''))} · {e(c.get('level',''))} ·
{e(c.get('language_of_instruction',''))}</div>
<div class="chips">{chips_html}</div></header>
<nav>{nav}</nav>
<main>{body}</main>
<footer>Generated {e(stamp)} from {e(passport_path.name)} ·
regenerate anytime: <code>python3 scripts/build_dashboard.py {e(str(passport_path.name))}</code> ·
Teaching Skills</footer><script>{SCRIPT}</script></body></html>"""
    out.write_text(doc, encoding="utf-8")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("passport")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args(argv)
    try:
        out = build(args.passport, args.out)
    except Exception as ex:
        print(f"error: {type(ex).__name__}: {ex}", file=sys.stderr)
        return 2
    print(f"dashboard written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
