#!/usr/bin/env python3
"""Evidence gate for Deep Review findings (v2.0 spec §3.D).

One command, zero ceremony:

    python3 skills/kicad/review/scripts/deep_review_gate.py \
        analysis/deep_review.json --analysis-dir analysis/

1. Validates each finding against deep_review.schema.json
   (_mini_jsonschema; per-finding — invalid findings are quarantined,
   not fatal) plus the cross-field rule the mini validator can't
   express: >=1 design anchor AND >=1 evidence source.
2. Checks citations: components/nets/pins exist in the analyzer JSON
   (pins check the component ref only — a floating-pin finding
   legitimately cites a pin on no net); the cited datasheet page
   contains the quote (pdftotext when available; missing tool or PDF
   -> evidence_checked=partial, never quarantine); computation script
   paths resolve against --project-dir.
3. Stamps finding_ids (assign_deep_review_ids), mirrors evidence
   anchors to top-level components/nets/pins, canonical-sorts, writes
   back. Re-evaluates quarantined[] so corrected findings promote.
4. Failures land in quarantined[] with quarantine_reason — visible,
   never silently dropped.

Exit codes: 0 all verified; 1 >=1 quarantined; 2 I/O or top-level
shape error. Stdlib-only; pdftotext (poppler) optional.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(REPO_ROOT / "skills" / "kicad" / "scripts"))

from _mini_jsonschema import iter_errors            # noqa: E402
from finding_schema import assign_deep_review_ids   # noqa: E402

SCHEMA_PATH = (Path(__file__).resolve().parents[1] / "schemas"
               / "deep_review.schema.json")

ANCHOR_KEYS = ("components", "nets", "pins")


def load_anchor_sets(analysis_dir, run_id=None):
    """Component refs + net identities from the analyzer JSON.

    Resolves the run dir via analysis/manifest.json ('current' unless
    --run given); falls back to a flat analysis dir (schematic.json /
    pcb.json directly inside it) for ad-hoc layouts.
    A physical net carries up to three identities (KH-347): schematic
    internal name, annotated display_name, PCB net name. All three are
    accepted as citations.
    Returns (components: set[str], nets: set[str]).
    """
    analysis_dir = Path(analysis_dir)
    run_dir = analysis_dir
    manifest = analysis_dir / "manifest.json"
    if manifest.is_file():
        m = json.loads(manifest.read_text())
        rid = run_id or m.get("current")
        if rid and (analysis_dir / rid).is_dir():
            run_dir = analysis_dir / rid
    comps, nets = set(), set()
    sch = run_dir / "schematic.json"
    if sch.is_file():
        data = json.loads(sch.read_text())
        for c in data.get("components") or []:
            if isinstance(c, dict) and c.get("reference"):
                comps.add(str(c["reference"]).upper())
        for name, info in (data.get("nets") or {}).items():
            nets.add(str(name).upper())
            if isinstance(info, dict) and info.get("display_name"):
                nets.add(str(info["display_name"]).upper())
    pcb = run_dir / "pcb.json"
    if pcb.is_file():
        data = json.loads(pcb.read_text())
        for fp in data.get("footprints") or []:
            if isinstance(fp, dict) and fp.get("reference"):
                comps.add(str(fp["reference"]).upper())
        net_map = data.get("nets")
        if isinstance(net_map, dict):
            nets.update(str(v).upper() for v in net_map.values() if v)
        name_map = data.get("net_name_to_id")
        if isinstance(name_map, dict):
            nets.update(str(k).upper() for k in name_map if k)
    return comps, nets


def check_anchors(ev, comps, nets):
    fails = []
    for ref in ev.get("components") or []:
        if str(ref).upper() not in comps:
            fails.append(f"component {ref} not found in analyzer JSON")
    for net in ev.get("nets") or []:
        if str(net).upper() not in nets:
            fails.append(f"net {net} not found in analyzer JSON")
    for pin in ev.get("pins") or []:
        ref = str(pin).rsplit(".", 1)[0]
        if ref.upper() not in comps:
            fails.append(f"pin {pin}: component {ref} not found in analyzer JSON")
    return fails


def find_pdf(datasheets_dir, mpn):
    d = Path(datasheets_dir)
    if not d.is_dir():
        return None
    sanitized = re.sub(r"[^A-Za-z0-9_.-]", "_", mpn.strip())
    direct = d / f"{sanitized}.pdf"
    if direct.is_file():
        return direct
    lowered = sanitized.lower()
    for p in sorted(d.glob("*.pdf")):
        if p.stem.lower() == lowered:
            return p
    return None


def _norm_text(s):
    # NFKC folds ligatures/fullwidth forms; symbols and punctuation
    # (degree signs, dashes, curly quotes) collapse to word breaks.
    s = unicodedata.normalize("NFKC", s).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def _squash(s):
    return _norm_text(s).replace(" ", "")


def _quote_in_text(quote, text):
    """Containment tolerant of case, whitespace, punctuation, Unicode
    variants, and PDF line-wrap hyphenation (KH-347). The squashed
    fallback absorbs boundary shifts ("5.5V" vs "5.5 V", "over-\\nvoltage"
    vs "overvoltage")."""
    q = _norm_text(quote)
    if not q:
        return True
    return q in _norm_text(text) or _squash(quote) in _squash(text)


def check_datasheet(cites, datasheets_dir):
    """Returns (failures, partial). Missing tool/PDF -> partial, not failure."""
    fails, partial = [], False
    if shutil.which("pdftotext") is None:
        return fails, bool(cites)
    for cite in cites or []:
        pdf = find_pdf(datasheets_dir, cite.get("mpn", ""))
        if pdf is None:
            partial = True
            continue
        cmd = ["pdftotext"]
        page = cite.get("page")
        if isinstance(page, int) and page > 0:
            cmd += ["-f", str(page), "-l", str(page)]
        cmd += [str(pdf), "-"]
        try:
            text = subprocess.run(cmd, capture_output=True, text=True,
                                  check=True).stdout
        except (subprocess.CalledProcessError, OSError):
            partial = True
            continue
        if not _quote_in_text(cite.get("quote", ""), text):
            where = f"page {page} of" if page else "anywhere in"
            fails.append(f'quote not found {where} {pdf.name}: '
                         f'"{cite.get("quote", "")[:80]}"')
    return fails, partial


def check_computation(comp, project_dir):
    fails = []
    script = (comp or {}).get("script")
    if script and not (Path(project_dir) / script).is_file():
        fails.append(f"computation script not found: {script}")
    return fails


def gate_finding(finding, item_schema, comps, nets, datasheets_dir, project_dir):
    """Returns (kept_finding | None, quarantined_finding | None)."""
    # Strip all gate-stamped output fields so re-runs produce identical key order.
    _GATE_FIELDS = frozenset(
        ("quarantine_reason", "evidence_checked", "finding_id",
         "components", "nets", "pins"))
    f = {k: v for k, v in finding.items() if k not in _GATE_FIELDS}
    fails = [e.message for e in iter_errors(f, item_schema)]
    ev = f.get("evidence") or {}
    has_anchor = any(ev.get(k) for k in ANCHOR_KEYS)
    has_source = bool(ev.get("datasheet")) or bool(ev.get("computation"))
    if not has_anchor:
        fails.append("no design anchor: evidence must cite >=1 component/net/pin")
    if not has_source:
        fails.append("no evidence source: evidence must carry a datasheet "
                     "quote and/or a computation")
    partial = False
    if not fails:
        fails += check_anchors(ev, comps, nets)
        ds_fails, partial = check_datasheet(ev.get("datasheet"), datasheets_dir)
        fails += ds_fails
        fails += check_computation(ev.get("computation"), project_dir)
    if fails:
        q = dict(finding)
        q["quarantine_reason"] = "; ".join(fails)
        return None, q
    f["evidence_checked"] = "partial" if partial else "full"
    for key in ANCHOR_KEYS:
        if ev.get(key):
            f[key] = list(ev[key])
    return f, None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("deep_review_json")
    ap.add_argument("--analysis-dir", required=True)
    ap.add_argument("--run", default=None, help="run id (default: manifest current)")
    ap.add_argument("--datasheets-dir", default="datasheets")
    ap.add_argument("--project-dir", default=".")
    args = ap.parse_args()

    path = Path(args.deep_review_json)
    try:
        doc = json.loads(path.read_text())
        schema = json.loads(SCHEMA_PATH.read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"deep_review_gate: cannot load inputs: {e}", file=sys.stderr)
        return 2
    top_required = ("schema_version", "produced_for_run_id", "produced_at",
                    "findings", "quarantined")
    if not isinstance(doc, dict) or not all(k in doc for k in top_required):
        print("deep_review_gate: top-level shape invalid "
              f"(required keys: {', '.join(top_required)})", file=sys.stderr)
        return 2

    comps, nets = load_anchor_sets(args.analysis_dir, args.run)
    item_schema = schema["properties"]["findings"]["items"]

    kept, quarantined = [], []
    candidates = list(doc.get("findings") or []) + list(doc.get("quarantined") or [])
    for finding in candidates:
        if not isinstance(finding, dict):
            quarantined.append({"quarantine_reason": "not a JSON object",
                                "value": finding})
            continue
        ok, bad = gate_finding(finding, item_schema, comps, nets,
                               args.datasheets_dir, args.project_dir)
        if ok is not None:
            kept.append(ok)
        else:
            quarantined.append(bad)

    assign_deep_review_ids(kept)
    kept.sort(key=lambda f: (f.get("category", ""), f.get("finding_id", "")))
    quarantined.sort(key=lambda f: (str(f.get("category", "")),
                                    str(f.get("summary", ""))))
    doc["findings"] = kept
    doc["quarantined"] = quarantined
    path.write_text(json.dumps(doc, indent=2) + "\n")

    n_partial = sum(1 for f in kept if f.get("evidence_checked") == "partial")
    print(f"deep_review gate: {len(kept)} verified "
          f"({n_partial} partial), {len(quarantined)} quarantined")
    return 1 if quarantined else 0


if __name__ == "__main__":
    sys.exit(main())
