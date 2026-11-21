#!/usr/bin/env python3
"""Gate check: does the project folder contain this phase's required artifacts, and are they filled in?

  python3 phase_gate.py <project_dir> <phase|all>       phases: positioning naming refs cards style features frames web ui assets qa video gtm growth ship

Prints PASS/FAIL per artifact and exits 1 on any FAIL. Run it at the START of a phase (are the previous phase's artifacts real?)
and at the END (did I produce mine?). A file counts only if it exists, is >300 bytes and has no 'TODO' / empty template fields.
Beyond "file is real", extra checks encode what the user keeps repeating (references/user-repeated-demands.md):
  refs   >=8 cards, >=4 non-App types, >=2 github/award, every card has a reverse prompt   (D1)
         + refs/style-names.md (>=20 terms), every card has creative operator + 3 derived variants (D20 D21)
  style  >=3 reverse-prompt cards, bible has 要/不要 + 反例, project CLAUDE.md has 审美红线     (D2 D3)
  features/growth  must name the aha moment                                                  (D4)
  frames 06b visual craft, run BEFORE any UI code: >=3 technique sheets (hero/type scale/whitespace/signature),
         >=3 existing *-vs-ref.jpg style-frame comparisons, >=1 [product-native] direction, a 'Picked:' line   (D25)
  web    website / landing page / any web preview = phase 6 too: same frames checks under docs/site/, plus a 'Register:' line
         (克制 or 风格化, taken from the refs the user liked) and git proof that technique-sheets.md was committed BEFORE the
         first commit touching the site code dir (default site/; override "web_code"; after a rejection set "web_restart": <rev>)   (D25 D38)
  ui     "不如它" table >=3 rows, no N/10 score used as verdict, + every frames + cards check     (D5 D25 D27)
  cards  docs/creative-cards.md: every card has 意图/算子/参数轴(>=3)/衍生(3)/融合; no card = no build (D20 D27)
  video  must state the transition method (转场) + docs/marketing-to-product.md maps every claim (D7 D30)
  assets every asset row carries a source/授权 word                                          (D11 D19)
Paths are the skill's convention (see references/*.md); override in <project>/.prolaunch.json: {"positioning": ["docs/pos.md"]}.
"""
import json, pathlib, re, sys

GATES = {
    "positioning": ["docs/positioning.md"],
    "naming":      ["docs/naming.md", "docs/trademark.md"],
    "refs":        ["refs/style-refs/INDEX.md", "docs/competitors.md"],
    "cards":       ["docs/creative-cards.md"],
    "style":       ["docs/style-bible.md"],
    "features":    ["docs/feature-map.md"],
    "frames":      ["docs/technique-sheets.md", "docs/style-frames.md"],
    "web":         ["docs/site/technique-sheets.md", "docs/site/style-frames.md"],
    "ui":          ["docs/ui-log.md"],
    "assets":      ["docs/asset-list.md"],
    "qa":          ["docs/qa-walkthrough.md"],
    "video":       ["docs/video-brief.md", "docs/marketing-to-product.md"],
    "gtm":         ["docs/gtm.md", "docs/manual-tasks.md"],
    "growth":      ["docs/metrics.md"],
    "ship":        ["docs/ship-checklist.md", "docs/lessons.md"],
}


def ok(p):
    if not p.exists():
        return False, "missing"
    t = p.read_text(errors="ignore")
    if len(t) < 300:
        return False, "too short (<300 bytes)"
    for bad in ("TODO", ": \n", ":  \n"):
        if bad in t:
            return False, f"unfilled ({bad.strip() or 'empty field'})"
    return True, "ok"


def cards(root):
    p = root / "refs/style-refs/INDEX.md"
    if not p.exists():
        return []
    parts = re.split(r"(?m)^### ", p.read_text(errors="ignore"))[1:]
    return parts


def field(card, key):
    m = re.search(r"(?m)^- " + key + r"[^:\n]*:[ \t]*(.*)$", card)
    return m.group(1).strip() if m else ""


def read(root, rel):
    p = root / rel
    return p.read_text(errors="ignore") if p.exists() else ""


def extra_refs(root):
    cs = cards(root)
    out = []
    types = [field(c, "type").lower() for c in cs]
    n_nonapp = sum(1 for x in types if x and x not in ("app", "competitor"))
    n_open = sum(1 for x in types if x in ("github", "award", "opensource"))
    n_rev = sum(1 for c in cs if len(field(c, "reverse prompt")) > 20)
    out.append((len(cs) >= 8, f"cards>=8 (have {len(cs)})"))
    out.append((n_nonapp >= 4, f"non-App types>=4 (have {n_nonapp}; fill '- type:' with github/award/game/art/social/app)"))
    out.append((n_open >= 2, f"github/award>=2 (have {n_open})"))
    out.append((len(cs) > 0 and n_rev == len(cs), f"every card has a reverse prompt ({n_rev}/{len(cs)})"))
    nm = read(root, "refs/style-names.md")
    n_terms = sum(1 for l in nm.splitlines() if l.count("|") >= 3 and not re.match(r"^\s*\|[\s:|-]+\|?\s*$", l)) - 1
    out.append((n_terms >= 20, f"refs/style-names.md style-name table >=20 terms (have {max(n_terms,0)})  [D21]"))
    n_op = sum(1 for c in cs if len(field(c, "creative operator")) > 8)
    n_var = sum(1 for c in cs if len(field(c, "derived variants")) > 20)
    out.append((len(cs) > 0 and n_op == len(cs), f"every card has a creative operator ({n_op}/{len(cs)})  [D20]"))
    out.append((len(cs) > 0 and n_var == len(cs), f"every card has 3 derived variants ({n_var}/{len(cs)})  [D20]"))
    return out


def extra_style(root):
    bible = read(root, "docs/style-bible.md")
    n_rev = sum(1 for c in cards(root) if len(field(c, "reverse prompt")) > 20)
    return [
        (n_rev >= 3, f"reverse-prompt cards>=3 (have {n_rev})"),
        ("不要" in bible and "要" in bible and "反例" in bible, "style-bible has 要/不要 and 反例"),
        ("审美红线" in read(root, "CLAUDE.md"), "project CLAUDE.md has 审美红线"),
    ]


def aha(rel):
    return lambda root: [("aha" in read(root, rel).lower(), f"{rel} names the aha moment")]


def extra_ui(root):
    t = read(root, "docs/ui-log.md")
    after = t.split("不如它")[-1] if "不如它" in t else ""
    n = sum(1 for l in after.splitlines() if l.count("|") >= 3 and not re.match(r"^\s*\|[\s:|-]+\|?\s*$", l))
    score = re.search(r"\b\d+(\.\d)?\s*/\s*10\b", t)
    return [
        ("不如它" in t and n >= 3, f"'哪里不如它' table has >=3 rows (have {max(n,0)})"),
        (not score, "no N/10 self-score in ui-log"),
    ] + extra_craft(root) + extra_cards(root)


def extra_craft(root, base="docs"):
    """06b visual craft: technique sheets, 3 style frames each beside a reference, a pick before UI code."""
    ts = read(root, f"{base}/technique-sheets.md")
    sheets = re.split(r"(?m)^### ", ts)[1:]
    n_full = sum(1 for s in sheets if all(len(field(s, k)) > 3 for k in ("hero", "type scale", "whitespace", "signature move")))
    sf = read(root, f"{base}/style-frames.md")
    vs = sorted(set(re.findall(r"[\w./-]+-vs-ref\.jpg", sf)))
    vs_ok = [v for v in vs if (root / v).exists() or (root / base / "style-frames" / pathlib.Path(v).name).exists()]
    pick = re.search(r"(?mi)^\W*picked:[ \t]*(\S.*)$", sf)
    return [
        (n_full >= 3, f"technique-sheets.md: >=3 references with hero/type scale/whitespace/signature move filled (have {n_full})  [D25]"),
        (len(vs_ok) >= 3, f"style-frames.md links >=3 existing *-vs-ref.jpg comparisons (have {len(vs_ok)}/{len(vs)})  [D25]"),
        ("[product-native]" in sf, "style-frames.md has >=1 [product-native] direction  [D25]"),
        (bool(pick), "style-frames.md has a 'Picked:' line (no UI code before it)  [D25]"),
    ]


def first_commit(root, path, since=None, added=True):
    import subprocess
    cmd = ["git", "-C", str(root), "log", "--format=%ct"] + (["--diff-filter=A"] if added else []) + ([f"{since}..HEAD"] if since else []) + ["--", path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    times = [int(x) for x in r.stdout.split()] if r.returncode == 0 else []
    return min(times) if times else None


def extra_web(root):
    """Websites follow pro-motion's web order (single source of rules): run its web_gate.py and report its lines."""
    import subprocess
    gate = pathlib.Path.home() / ".claude/skills/pro-motion/scripts/web_gate.py"
    if not gate.exists():
        return [(False, f"missing {gate} (install pro-motion; web rules live there)")]
    args = [sys.executable, str(gate), str(root)]
    cfg = root / ".prolaunch.json"
    if cfg.exists():
        c = json.loads(cfg.read_text())
        if c.get("web_code"): args += ["--code", c["web_code"]]
        if c.get("web_restart"): args += ["--restart", c["web_restart"]]
    r = subprocess.run(args, capture_output=True, text=True)
    lines = [l.strip(" -✗✓") for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    return [(r.returncode == 0, "pro-motion web_gate: " + l + "  [D38]") for l in lines] or [(r.returncode == 0, "pro-motion web_gate")]


def extra_video(root):
    m2p = read(root, "docs/marketing-to-product.md")
    rows = [l for l in m2p.splitlines() if l.count("|") >= 4 and not re.match(r"^\s*\|[\s:|-]+\|?\s*$", l)][1:]
    return [("转场" in read(root, "docs/video-brief.md"), "video-brief states the 转场 method"),
            (len(rows) >= 1 and all(re.search(r"已有|已实现|待办|删除|改片", r) for r in rows),
             f"marketing-to-product: every claim row has 状态 已有/待办/删除/改片 ({len(rows)} rows)  [D30]")]


def extra_cards(root):
    """Creative card gate (D27): ### per card, fields '- 意图:' '- 算子:' '- 参数轴:' '- 衍生:' '- 融合:'."""
    t = read(root, "docs/creative-cards.md")
    cs = re.split(r"(?m)^### ", t)[1:]
    out = [(len(cs) >= 1, f"creative-cards.md has >=1 card (have {len(cs)})")]
    for c in cs:
        name = c.splitlines()[0].strip()[:24]
        op = field(c, "算子")
        axes = [x for x in re.split(r"[/／、,，]", field(c, "参数轴")) if x.strip()]
        der = [x for x in re.split(r"[；;]", field(c, "衍生")) if x.strip()]
        miss = [k for k in ("意图", "算子", "融合") if len(field(c, k)) < 4]
        good = not miss and len(axes) >= 3 and len(der) >= 3 and len(op) >= 6
        why = f"card '{name}': 轴{len(axes)}/3 衍生{len(der)}/3" + (f" 缺{','.join(miss)}" if miss else "")
        out.append((good, why + "  [D27]"))
    return out


def extra_assets(root):
    t = read(root, "docs/asset-list.md")
    return [(bool(re.search(r"授权|license|licence|出处|source", t, re.I)), "asset-list records source/授权")]


EXTRA = {"refs": extra_refs, "cards": extra_cards, "style": extra_style, "features": aha("docs/feature-map.md"),
         "growth": aha("docs/metrics.md"), "frames": extra_craft, "web": extra_web, "ui": extra_ui, "video": extra_video, "assets": extra_assets}


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    root, phase = pathlib.Path(sys.argv[1]), sys.argv[2]
    gates = dict(GATES)
    cfg = root / ".prolaunch.json"
    cfg_over = {}
    if cfg.exists():
        cfg_over = json.loads(cfg.read_text())
        gates.update(cfg_over)
    phases = list(gates) if phase == "all" else [phase]
    bad = 0
    for ph in phases:
        for rel in gates.get(ph, []):
            good, why = ok(root / rel)
            bad += not good
            print(f"{'PASS' if good else 'FAIL'}  {ph:<12}{rel}  ({why})")
        if ph in EXTRA and ph not in cfg_over:
            for good, why in EXTRA[ph](root):
                bad += not good
                print(f"{'PASS' if good else 'FAIL'}  {ph:<12}[demand] {why}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
