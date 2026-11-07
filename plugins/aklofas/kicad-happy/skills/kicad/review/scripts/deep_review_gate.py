#!/usr/bin/env python3
"""Evidence gate for Deep Review findings.

One command, zero ceremony:

    python3 skills/kicad/review/scripts/deep_review_gate.py \
        analysis/deep_review.json --analysis-dir analysis/

1. Validates each finding against deep_review.schema.json
   (_mini_jsonschema; per-finding — invalid findings are quarantined,
   not fatal) plus the cross-field rule the mini validator can't
   express: >=1 design anchor AND >=1 evidence source.
2. Checks citations: components/nets/pins exist in the analyzer JSON
   (a pin REF.PIN names a pin number or name that component has in the
   analyzer JSON, a floating pin included; a PCB-only part with a pad on
   no net has its pins unchecked); the cited datasheet page
   contains the quote (pdftotext when available; missing tool or PDF
   -> evidence_checked=partial, never quarantine); a computation's
   script path resolves against --project-dir. The gate never runs a
   computation, so a finding that cites one is evidence_checked=partial.
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
import os
import re
import secrets
import shutil
import subprocess
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))   # skills/kicad/scripts

from _mini_jsonschema import iter_errors            # noqa: E402
from analysis_cache import get_run                  # noqa: E402
from finding_schema import assign_deep_review_ids   # noqa: E402
from kicad_core.executables import find_executable  # noqa: E402

SCHEMA_PATH = (Path(__file__).resolve().parents[1] / "schemas"
               / "deep_review.schema.json")

ANCHOR_KEYS = ("components", "nets", "pins")


def resolve_run_dir(analysis_dir, run_id=None):
    """The run folder analysis/manifest.json names ('current' unless
    `run_id` is given), confined to a folder directly inside
    `analysis_dir`; `analysis_dir` itself for a flat layout or an
    unreadable manifest."""
    analysis_dir = Path(analysis_dir)
    manifest = analysis_dir / "manifest.json"
    if manifest.is_file():
        try:
            m = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError, RecursionError):
            m = None
        if isinstance(m, dict) and isinstance(m.get("runs"), dict):
            run = get_run(str(analysis_dir), run_id or m.get("current"), m)
            if run and Path(run[0]).is_dir():
                return Path(run[0])
    return analysis_dir


class _PinIds(set):
    """Pin numbers and names of one component; has_names is False when the
    analyzer JSON lists numbers only."""
    has_names = False

    def add_name(self, name):
        self.add(name)
        self.has_names = True


def load_anchor_sets(analysis_dir, run_id=None):
    """Component refs + net identities from the analyzer JSON.

    Resolves the run dir via analysis/manifest.json ('current' unless
    --run given); falls back to a flat analysis dir (schematic.json /
    pcb.json directly inside it) for ad-hoc layouts.
    A physical net carries up to three identities: schematic
    internal name, annotated display_name, PCB net name. All three are
    accepted as citations.
    Returns (components, nets, pins): sets of upper-case strings plus a
    map of upper-case ref -> upper-case pin numbers and names the gate can
    check. A ref with no checkable pins is absent: no source lists any, or
    it is a PCB-only footprint with a pad on no net (pad_nets omits those).
    Raises ValueError naming the file when one cannot be read as a JSON
    object.
    """
    run_dir = resolve_run_dir(analysis_dir, run_id)
    comps, nets, pins, open_refs = set(), set(), {}, set()
    sch = run_dir / "schematic.json"
    if sch.is_file():
        data = _load_object(sch)
        for c in _as_list(data.get("components")):
            if isinstance(c, dict) and c.get("reference"):
                ref = str(c["reference"]).upper()
                comps.add(ref)
                for key in ("pin_nets", "pin_uuids"):
                    if isinstance(c.get(key), dict):
                        pins.setdefault(ref, _PinIds()).update(str(n).upper() for n in c[key])
        sch_nets = data.get("nets")
        for name, info in (sch_nets.items() if isinstance(sch_nets, dict) else ()):
            nets.add(str(name).upper())
            if not isinstance(info, dict):
                continue
            if info.get("display_name"):
                nets.add(str(info["display_name"]).upper())
            for p in _as_list(info.get("pins")):
                if isinstance(p, dict) and p.get("component"):
                    ids = pins.setdefault(str(p["component"]).upper(), _PinIds())
                    if p.get("pin_number"):
                        ids.add(str(p["pin_number"]).upper())
                    if str(p.get("pin_name") or "").strip():
                        ids.add_name(str(p["pin_name"]).strip().upper())
    sch_pinned = {ref for ref, ids in pins.items() if ids}
    pcb = run_dir / "pcb.json"
    if pcb.is_file():
        data = _load_object(pcb)
        for fp in _as_list(data.get("footprints")):
            if isinstance(fp, dict) and fp.get("reference"):
                ref = str(fp["reference"]).upper()
                comps.add(ref)
                pad_nets = fp.get("pad_nets") if isinstance(fp.get("pad_nets"), dict) else {}
                ids = pins.setdefault(ref, _PinIds())
                for num, entry in pad_nets.items():
                    ids.add(str(num).upper())
                    if isinstance(entry, dict) and entry.get("pin"):
                        ids.add_name(str(entry["pin"]).strip().upper())
                # pad_nets omits a pad on no net, so a PCB-only part with one is unchecked
                if ref not in sch_pinned and not (
                        isinstance(fp.get("pad_count"), int) and fp["pad_count"] <= len(pad_nets)):
                    open_refs.add(ref)
        net_map = data.get("nets")
        if isinstance(net_map, dict):
            nets.update(str(v).upper() for v in net_map.values() if v)
        name_map = data.get("net_name_to_id")
        if isinstance(name_map, dict):
            nets.update(str(k).upper() for k in name_map if k)
    for ref in open_refs:
        pins.pop(ref, None)
    return comps, nets, {ref: ids for ref, ids in pins.items() if ids}


def write_text_atomic(path, text):
    """Write UTF-8 text through a temp file beside `path` and os.replace.
    An existing file keeps its mode, a new one gets the umask mode; a
    symlink at `path` is replaced by a regular file, never followed."""
    path = Path(path)
    exists = path.is_file() and not path.is_symlink()
    flags = (os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
             | getattr(os, "O_BINARY", 0))
    while True:
        tmp = path.parent / f".{path.name}.{secrets.token_hex(6)}.tmp"
        try:
            # 0o666 lets the kernel apply the umask to a new file
            fd = os.open(tmp, flags, 0o600 if exists else 0o666)
            break
        except FileExistsError:
            continue
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        if exists:
            shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _load_object(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError) as e:
        raise ValueError(f"{path}: {e}") from None
    if not isinstance(data, dict):
        raise ValueError(f"{path}: not a JSON object")
    return data


def _as_list(value):
    return value if isinstance(value, list) else []


def check_anchors(ev, comps, nets, pins):
    """Returns (failures, partial); a cited pin that cannot be checked is partial."""
    fails, partial = [], False
    for ref in ev.get("components") or []:
        if str(ref).upper() not in comps:
            fails.append(f"component {ref} not found in analyzer JSON")
    for net in ev.get("nets") or []:
        if str(net).upper() not in nets:
            fails.append(f"net {net} not found in analyzer JSON")
    for pin in ev.get("pins") or []:
        ref, _, num = str(pin).rpartition(".")
        if ref.upper() not in comps and "." in str(pin):
            # a dotted pin name such as P0.12: split at the first dot instead
            first, _, rest = str(pin).partition(".")
            if first.upper() in comps:
                ref, num = first, rest
        if not ref or not num:
            fails.append(f"pin {pin}: not a REF.PIN citation")
        elif ref.upper() not in comps:
            fails.append(f"pin {pin}: component {ref} not found in analyzer JSON")
        elif ref.upper() not in pins:
            partial = True
        elif num.upper() not in pins[ref.upper()]:
            ids = pins[ref.upper()]
            # with numbers only on record, a non-numeric citation may be a name
            if ids.has_names or num.isdigit():
                fails.append(f"pin {pin}: {ref} has no pin {num} in analyzer JSON")
            else:
                partial = True
    return fails, partial


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


_DASH_RE = re.compile("[\u2212\u2013\u2010\u2011]")
# +/- (spaces allowed around the slash) and +- with any dash
_PLUSMINUS_RE = re.compile(r"\+(?:\s*/\s*)?[-\u2014]")
# One token per comparison operator or per run of letters/digits. A run
# keeps a decimal point or comma between digits ("5.5", "1,000") or before
# the first digit (".5", but not a dot leader "....37" or "100Ω.5"); a
# leading minus that starts a number outside a word ("-40", "(−40"; not
# "SOT-23" or "3.3-5.5"); and a ± written against its number ("±15",
# "+/-15"); and the minus of an exponent such as "1e-3". So "15" is neither
# "-15" nor "±15", and "5" is not ".5". Unit letters such as µ and ω are
# letters.
_TOKEN_RE = re.compile(
    r"<=|>=|±(?!\.?[0-9])|<|>|="
    r"|(?:(?<![^\W_]|\.)-(?=\.?[0-9])|±(?=\.?[0-9]))?"
    r"(?:(?<![^\W_]|\.)\.(?=[0-9]))?"
    r"(?:[^\W_]|(?<=[0-9])[.,](?=[0-9])|(?<=[0-9]e)-(?=[0-9]))+")
# a ± set apart from the number it precedes (a space or a wrapped line)
_PLUSMINUS_GAP_RE = re.compile(r"±\s+(?=\.?[0-9])")
_LEADING_POINT_RE = re.compile(r"(?<![^\s±-])\.(?=[0-9])")


def _norm_text(s):
    # NFKC folds ligatures/fullwidth forms and µ into μ; other symbols and
    # punctuation (degree signs, dashes, curly quotes) are word breaks.
    s = unicodedata.normalize("NFKC", s).lower()
    s = _DASH_RE.sub("-", s)
    s = _PLUSMINUS_RE.sub("±", s).replace("≤", "<=").replace("≥", ">=")
    s = _PLUSMINUS_GAP_RE.sub("±", s)
    # ".5" is written "0.5" so both spellings compare equal
    return _LEADING_POINT_RE.sub("0.", " ".join(_TOKEN_RE.findall(s)))


def _squash(s):
    # Two numbers side by side stay apart ("0.9 1.0" is not "0.91.0"), and
    # so does a ± set apart from a word ("± x" is not "±x").
    return re.sub(r"(?<=[0-9]) (?=[-±0-9])|(?<=±) ", "|", _norm_text(s)).replace(" ", "")


# a whole run of dots is one marker, so a dot leader leaves no stray point
_ELISION_RE = re.compile(r"\.{3,}|…")


def _quote_segments(quote):
    """Split a (possibly elided) quote into segments on '...' / '…'.
    Must run BEFORE normalization -- _norm_text collapses elision
    markers into a plain word break, destroying the split points."""
    return [s for s in _ELISION_RE.split(quote) if s.strip()]


def _segments_match(segments, norm_fn, text):
    """True if every segment appears in `text` (normalized via
    `norm_fn`), in order -- each search starts where the previous
    segment's match ended. Normalized segments match whole
    tokens; squashed ones may not start or end inside a number."""
    t = norm_fn(text)
    if norm_fn is _norm_text:
        t = f" {t} "
    pos = 0
    for seg in segments:
        q = norm_fn(seg)
        if not q:
            continue
        if norm_fn is _norm_text:
            q = f" {q} "
            idx = t.find(q, pos)
        else:
            idx = _find_outside_numbers(t, q, pos)
        if idx == -1:
            return False
        pos = idx + len(q)
        if norm_fn is _norm_text:
            pos -= 1    # the closing space opens the next token
    return True


def _find_outside_numbers(t, q, pos):
    idx = t.find(q, pos)
    while idx != -1:
        before = t[idx - 1] if idx else ""
        after = t[idx + len(q):idx + len(q) + 1]
        inside = ((q[0].isdigit() and before and (before.isdigit() or before in ".,-±"))
                  or (q[0] == "." and before.isdigit())
                  or (q[-1].isdigit() and after and (after.isdigit() or after in ".,")))
        if not inside:
            return idx
        idx = t.find(q, idx + 1)
    return -1


def _quote_in_text(quote, text):
    """Containment tolerant of case, whitespace, punctuation, Unicode
    variants, PDF line-wrap hyphenation, and mid-quote elision
    ("..."/"…") -- each segment between elision markers
    must appear in the text in order. The squashed fallback absorbs
    boundary shifts ("5.5V" vs "5.5 V", "over-\\nvoltage" vs
    "overvoltage"). Numbers, signs, decimal points, comparison
    operators and unit letters must match; a quote with no letter or
    digit matches nothing."""
    segments = _quote_segments(quote) or [quote]
    if not any(re.search(r"\w", _norm_text(s)) for s in segments):
        return False
    return (_segments_match(segments, _norm_text, text)
            or _segments_match(segments, _squash, text))


def _nearest_match(quote, text, window=80, stride=40):
    """Deterministic nearest-match hint for a quarantined datasheet
    quote: locates the earliest elision segment that fails to
    match (by the same in-order rule as `_quote_in_text`), then scores
    `window`-char slices of the normalized text at a fixed `stride`
    against it via difflib.SequenceMatcher.ratio(). First-best wins on
    ties (replacement requires a strictly higher ratio)."""
    segments = _quote_segments(quote) or [quote]
    t = _norm_text(text)
    pos = 0
    missing = None
    for seg in segments:
        q = _norm_text(seg)
        if not q:
            continue
        idx = t.find(q, pos)
        if idx == -1:
            missing = q
            break
        pos = idx + len(q)
    if missing is None:
        missing = _norm_text(segments[0])
    if len(t) <= window:
        return t
    best_ratio, best = -1.0, t[:window]
    for i in range(0, len(t) - window + 1, stride):
        candidate = t[i:i + window]
        ratio = SequenceMatcher(None, missing, candidate).ratio()
        if ratio > best_ratio:
            best_ratio, best = ratio, candidate
    return best


def check_datasheet(cites, datasheets_dir):
    """Returns (failures, partial). Missing tool/PDF -> partial, not failure."""
    fails, partial = [], False
    tool = find_executable("pdftotext")
    have_tool = tool is not None
    for cite in cites or []:
        quote = cite.get("quote", "")
        page = cite.get("page")
        if not re.search(r"\w", _norm_text(quote)):
            fails.append(f'quote "{quote[:80]}" has no letter or digit to check')
            continue
        if page is not None and page < 1:
            fails.append(f"page {page} is not a page number (1 or more)")
            continue
        pdf = find_pdf(datasheets_dir, cite.get("mpn", "")) if have_tool else None
        if pdf is None:
            partial = True
            continue
        # UTF-8 is poppler's default; xpdf's pdftotext (some Windows installs) writes Latin-1
        cmd = [tool, "-enc", "UTF-8"]
        if page is not None:
            cmd += ["-f", str(page), "-l", str(page)]
        cmd += [str(pdf), "-"]
        try:
            proc = subprocess.run(cmd, capture_output=True, encoding="utf-8",
                                  errors="replace")
        except OSError:
            partial = True
            continue
        # Past the last page poppler's pdftotext exits 99 ("Wrong page range given"); xpdf's
        # exits 0 with no output at all, where any real page, even a blank one, gives a form feed
        if page is not None and (
                (proc.returncode == 99 and "page" in proc.stderr.lower())
                or (proc.returncode == 0 and proc.stdout == "")):
            fails.append(f"page {page} is past the end of {pdf.name}")
            continue
        if proc.returncode != 0:
            partial = True
            continue
        text = proc.stdout
        if not _quote_in_text(quote, text):
            where = f"page {page} of" if page else "anywhere in"
            reason = f'quote not found {where} {pdf.name}: "{quote[:80]}"'
            nearest = _nearest_match(quote, text)
            if nearest:
                reason += f'; nearest match: "...{nearest}..."'
            fails.append(reason)
    return fails, partial


def check_computation(comp, project_dir):
    """Returns (failures, partial). The gate never runs a computation, so
    a cited one is always partial; a cited script must still exist."""
    if not comp:
        return [], False
    script = comp.get("script")
    if script and not (Path(project_dir) / script).is_file():
        return [f"computation script not found: {script}"], True
    return [], True


def gate_finding(finding, item_schema, comps, nets, pins, datasheets_dir, project_dir):
    """Returns (kept_finding | None, quarantined_finding | None)."""
    # Strip all gate-stamped output fields so re-runs produce identical key order.
    _GATE_FIELDS = frozenset(
        ("quarantine_reason", "evidence_checked", "finding_id",
         "components", "nets", "pins"))
    f = {k: v for k, v in finding.items() if k not in _GATE_FIELDS}
    fails = [e.message for e in iter_errors(f, item_schema)]
    ev = f.get("evidence") or {}
    if not isinstance(ev, dict):
        ev = {}     # the schema error above already names it
    has_anchor = any(ev.get(k) for k in ANCHOR_KEYS)
    has_source = bool(ev.get("datasheet")) or bool(ev.get("computation"))
    if not has_anchor:
        fails.append("no design anchor: evidence must cite >=1 component/net/pin")
    if not has_source:
        fails.append("no evidence source: evidence must carry a datasheet "
                     "quote and/or a computation")
    partial = False
    if not fails:
        a_fails, a_partial = check_anchors(ev, comps, nets, pins)
        fails += a_fails
        ds_fails, ds_partial = check_datasheet(ev.get("datasheet"), datasheets_dir)
        comp_fails, comp_partial = check_computation(ev.get("computation"), project_dir)
        fails += ds_fails + comp_fails
        partial = a_partial or ds_partial or comp_partial
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
    ap.add_argument("--datasheets-dir", default=None,
                    help="folder of datasheet PDFs (default: <project-dir>/datasheets)")
    ap.add_argument("--project-dir", default=None,
                     help="project root for resolving computation script "
                          "paths (default: --analysis-dir's parent)")
    args = ap.parse_args()
    project_dir = args.project_dir
    if project_dir is None:
        # analysis/ conventionally lives directly inside the project
        # root -- anchor to it, not the invoking cwd, so the
        # gate works when run from elsewhere.
        project_dir = str(Path(args.analysis_dir).resolve().parent)
    datasheets_dir = args.datasheets_dir or str(Path(project_dir) / "datasheets")

    path = Path(args.deep_review_json)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError) as e:
        print(f"deep_review_gate: cannot load inputs: {e}", file=sys.stderr)
        return 2
    top_required = ("schema_version", "produced_for_run_id", "produced_at",
                    "findings", "quarantined")
    if not isinstance(doc, dict) or not all(k in doc for k in top_required):
        print("deep_review_gate: top-level shape invalid "
              f"(required keys: {', '.join(top_required)})", file=sys.stderr)
        return 2
    for key in ("findings", "quarantined"):
        if doc[key] is not None and not isinstance(doc[key], list):
            print(f"deep_review_gate: top-level shape invalid ({key} must be an array)",
                  file=sys.stderr)
            return 2

    try:
        comps, nets, pins = load_anchor_sets(args.analysis_dir, args.run)
    except ValueError as e:
        print(f"deep_review_gate: cannot load inputs: {e}", file=sys.stderr)
        return 2
    item_schema = schema["properties"]["findings"]["items"]

    kept, quarantined = [], []
    candidates = list(doc.get("findings") or []) + list(doc.get("quarantined") or [])
    for finding in candidates:
        if not isinstance(finding, dict):
            quarantined.append({"quarantine_reason": "not a JSON object",
                                "value": finding})
            continue
        ok, bad = gate_finding(finding, item_schema, comps, nets, pins,
                               datasheets_dir, project_dir)
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
    write_text_atomic(path, json.dumps(doc, indent=2) + "\n")

    n_partial = sum(1 for f in kept if f.get("evidence_checked") == "partial")
    print(f"deep_review gate: {len(kept)} verified "
          f"({n_partial} partial), {len(quarantined)} quarantined")
    return 1 if quarantined else 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # UTF-8 on a cp1252 pipe (Windows)
        if (getattr(_stream, "encoding", "") or "").lower().replace("-", "") != "utf8" \
                and hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.exit(main())
