#!/usr/bin/env python3
"""Plan the rework of an existing Mini App into classic Telegram design.

  py -3 scripts/miniapp_rework.py plan <app>            # ordered rework plan: findings by stage with replacements
  py -3 scripts/miniapp_rework.py colours <app>         # every colour literal with a suggested kit role
  py -3 scripts/miniapp_rework.py type <app>            # font sizes and families mapped to the type roles
  py -3 scripts/miniapp_rework.py plan <app> --json     # the same as JSON (for agents and diffs)

It reads what the lint reads (HTML, CSS, JS/TS) and joins three sources: the lint findings
(scripts/miniapp_lint.py), the replacement map (data/mini-apps/rework-map.json) and the type scale
(data/mini-apps/components.json). Suggestions are heuristics: confirm each one against the screen.
Walkthrough: references/mini-apps/rework.md.
"""
from __future__ import annotations

import argparse
import colorsys
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import miniapp_lint as lint  # noqa: E402

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(SKILL, "data", "mini-apps", "rework-map.json")
COMPONENTS = os.path.join(SKILL, "data", "mini-apps", "components.json")
DECOR_PROPS = ("box-shadow", "text-shadow", "filter", "backdrop-filter")


def load_map() -> dict:
    with open(MAP, encoding="utf-8") as fh:
        return json.load(fh)


def type_scale() -> list[tuple[str, int]]:
    with open(COMPONENTS, encoding="utf-8") as fh:
        roles = json.load(fh)["typography"]["roles"]
    return sorted(((r, int(v.split("/")[0])) for r, v in roles.items()), key=lambda x: -x[1])


def read_sources(app: str) -> list[tuple[str, str, str]]:
    """(path, extension, text) for the files the lint would read, without server code."""
    files, root = lint.collect([app])
    out = []
    for p in files:
        if lint.is_server(p, root):
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            out.append((p, os.path.splitext(p)[1].lower(), fh.read()))
    return out


def css_of(ext: str, text: str) -> str:
    if ext == ".css":
        return lint.COMMENT_CSS.sub("", text)
    if ext in (".html", ".htm"):
        blocks = [m.group(1) for m in lint.STYLE_BLOCK.finditer(text)]
        inline = re.findall(r"\bstyle=\"([^\"]*)\"", text)
        return lint.COMMENT_CSS.sub("", "\n".join(blocks + [f"[inline]{{{s}}}" for s in inline]))
    return ""


def declarations(css: str):
    """(selector, property, value) for every declaration."""
    for sel, body, _ in lint._css_rules(css):
        for decl in body.split(";"):
            if ":" in decl:
                prop, value = decl.split(":", 1)
                yield sel.strip(), prop.strip().lower(), value.strip()


# ------------------------------------------------------------------ colours
def parse_colour(c: str) -> tuple[float, float, float, float] | None:
    c = c.strip().lower()
    m = re.fullmatch(r"#([0-9a-f]{3,8})", c)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(ch * 2 for ch in h)
        if len(h) not in (6, 8):
            return None
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return r, g, b, a
    m = re.fullmatch(r"rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)\s*(?:[/,]\s*([\d.]+%?))?\s*\)", c)
    if m:
        r, g, b = (float(m.group(i)) / 255 for i in (1, 2, 3))
        a = m.group(4)
        alpha = 1.0 if a is None else float(a.rstrip("%")) / (100 if a.endswith("%") else 1)
        return r, g, b, alpha
    return None


def suggest_role(rgba, props: set[str], brand: bool) -> str:
    """A kit role for a colour literal, from its lightness, saturation and where it is used."""
    r, g, b, a = rgba
    h, light, sat = colorsys.rgb_to_hls(r, g, b)
    text = bool(props & {"color", "fill", "caret-color"})
    border = any(p.startswith("border") or p.startswith("outline") for p in props)
    if props and props <= set(DECOR_PROPS) | {"background", "background-image"} and not (props - set(DECOR_PROPS)):
        return "drop: decoration (shadow, glow, filter)"
    if sat < 0.12 or light <= 0.2 or light >= 0.97:  # near-black navy or near-white tints read as neutrals
        if a < 1:
            return "--tma-separator / --tma-fill" if a <= 0.25 else "--tma-overlay (scrims only)"
        if light >= 0.94:
            if text and len(props) > 1:
                return "--tma-surface for backgrounds; --tma-on-accent for text on a filled button"
            return "--tma-on-accent (text on a filled button)" if text else "--tma-surface (cards, lists) or --tma-bg"
        if light >= 0.85:
            return "--tma-separator" if border else "--tma-page (grouped background) or --tma-fill"
        if light <= 0.25:
            return "--tma-text" if text else "--tma-bg (dark comes from the user's theme: never hard-code a dark surface)"
        return "--tma-hint" if text else ("--tma-separator" if border else "--tma-fill")
    hue = h * 360
    if (hue < 15 or hue > 345) and sat > 0.4 and 0.3 < light < 0.75:
        return "--tma-danger"
    if 90 <= hue <= 160 and sat > 0.3 and 0.25 < light < 0.7:
        return "--tma-success"
    if light >= 0.88:
        return "--tma-tonal (a tint of the accent) or --tma-page"
    if brand:
        return "brand candidate: --tma-brand on ONE moment (miniapp_style.py profile); buttons take --tma-accent"
    if text:
        return "--tma-link / --tma-accent-text, or drop"
    return "drop, or --tma-accent if it marks the primary action"


def colours(sources) -> list[dict]:
    uses: dict[str, dict] = {}
    for path, ext, text in sources:
        for sel, prop, value in declarations(css_of(ext, text)):
            gradient = "gradient(" in value
            for c in lint.COLOR.findall(value):
                key = c.lower().replace(" ", "")
                u = uses.setdefault(key, {"colour": c, "count": 0, "props": set(), "selectors": [], "files": set(), "gradient": False})
                u["count"] += 1
                u["props"].add("box-shadow" if prop == "box-shadow" else prop)
                u["gradient"] |= gradient
                u["files"].add(os.path.basename(path))
                if sel not in u["selectors"]:
                    u["selectors"].append(sel)
    parsed = {k: parse_colour(u["colour"]) for k, u in uses.items()}
    chroma = Counter({k: u["count"] for k, u in uses.items()
                      if parsed[k] and colorsys.rgb_to_hls(*parsed[k][:3])[2] >= 0.12 and parsed[k][3] == 1
                      and 0.2 < colorsys.rgb_to_hls(*parsed[k][:3])[1] < 0.88})
    brand = chroma.most_common(1)[0][0] if chroma else None
    out = []
    for k, u in sorted(uses.items(), key=lambda kv: -kv[1]["count"]):
        rgba = parsed[k]
        if not rgba:
            role = "decide: unsupported colour syntax"
        elif u["gradient"] and not (u["props"] - {"background", "background-image"} - set(DECOR_PROPS)):
            role = "drop: gradient (a tonal brand moment at most, design-system.md section 9)"
        else:
            role = suggest_role(rgba, u["props"], k == brand)
            page = any(re.fullmatch(r"(html|body|:root|main|\.app|#app|\.page)", sel) for sel in u["selectors"])
            if page and u["props"] & {"background", "background-color"} and role.startswith(("--tma-surface", "--tma-tonal")):
                role = "--tma-page (grouped screens) or --tma-bg (flat screens): the page background"
        out.append({"colour": u["colour"], "count": u["count"], "used_as": sorted(u["props"]),
                    "selectors": u["selectors"][:4], "files": sorted(u["files"]), "role": role})
    return out


# ------------------------------------------------------------------ type
def to_px(value: str) -> float | None:
    m = re.match(r"\s*([\d.]+)(px|rem|em|pt)?\b", value)
    if not m:
        return None
    n, unit = float(m.group(1)), m.group(2) or "px"
    return {"px": n, "rem": n * 16, "em": n * 16, "pt": n * 4 / 3}[unit]


def typography(sources) -> dict:
    scale = type_scale()
    sizes: dict[float, dict] = {}
    families = Counter()
    for path, ext, text in sources:
        for sel, prop, value in declarations(css_of(ext, text)):
            if prop == "font-size":
                px = to_px(value)
                if px:
                    s = sizes.setdefault(px, {"px": px, "selectors": []})
                    s["selectors"].append(sel)
            elif prop in ("font-family", "font"):
                fam = value.split(",")[0].strip().strip("'\"")
                if prop == "font":
                    q = re.search(r"['\"]([^'\"]+)['\"]", value)
                    fam = q.group(1) if q else ""
                if fam and not re.match(r"(system-ui|-apple-system|inherit|sans-serif|var\()", fam, re.I):
                    families[fam] += 1
        for m in re.finditer(r"fonts\.googleapis\.com/css2?\?family=([A-Za-z+]+)", text):
            families[m.group(1).replace("+", " ")] += 1
    rows = []
    for px, s in sorted(sizes.items(), key=lambda kv: -kv[0]):
        rpx = min({v for _, v in scale}, key=lambda v: abs(v - px))
        role = " / ".join(r for r, v in scale if v == rpx)
        note = "below 11 px: caption2 is the floor (MA22)" if px < 11 else ""
        rows.append({"px": round(px, 1), "role": role, "role_px": rpx, "kit": " / ".join(f".tma-text-{r}" for r in role.split(" / ")),
                     "selectors": s["selectors"][:4], "note": note})
    return {"sizes": rows, "families": [{"family": f, "count": n, "action": "drop: the system font (--tma-font); MA16"}
                                        for f, n in families.most_common()]}


# ------------------------------------------------------------------ plan
def plan(app: str) -> dict:
    data = load_map()
    files, root = lint.collect([app])
    rep = lint.lint_files(files, root)
    sources = read_sources(app)
    by_rule = defaultdict(list)
    for f in rep.findings:
        by_rule[f.rule].append(f)
    stages: dict[int, list] = defaultdict(list)
    for rule, found in by_rule.items():
        row = data["rules"].get(rule, {"stage": 6, "telegram": "see anti-slop.md", "kit": "-", "ref": "anti-slop.md"})
        stages[row["stage"]].append({
            "rule": rule, "name": lint.RULES[rule][1], "level": lint.RULES[rule][0], "count": len(found),
            "where": [f"{x.file}:{x.line}" for x in found[:3]], "telegram": row["telegram"], "kit": row["kit"], "ref": row["ref"]})
    for p in data["patterns"]:
        hits = [(os.path.relpath(path, root or app).replace(os.sep, "/"), lint._line(text, m.start()))
                for path, _, text in sources for m in [re.search(p["detect"], text, re.I)] if m]
        if hits:
            stages[2 if p["id"] in ("sticky-header", "modal", "toast", "top-tabs") else 4 if p["id"] in ("tailwind", "shadcn") else 5].append({
                "rule": p["id"], "name": "pattern", "level": "pattern", "count": len(hits),
                "where": [f"{f}:{ln}" for f, ln in hits[:3]], "telegram": p["telegram"], "kit": p["kit"], "ref": p["ref"]})
    for rows in stages.values():
        rows.sort(key=lambda r: (r["level"] != "error", r["rule"]))
    return {
        "app": app, "files": len(files), "errors": len(rep.errors), "warnings": len(rep.warnings),
        "stages": [{"stage": n, "title": data["stages"][str(n)], "items": stages[n]} for n in sorted(stages)],
        "manual": data["manual"], "colours": colours(sources), "type": typography(sources),
    }


def print_plan(p: dict) -> None:
    print(f"# Rework plan: {p['app']}\n")
    print(f"Baseline: {p['files']} files, {p['errors']} errors, {p['warnings']} warnings (miniapp_lint.py). "
          "Fix in stage order; structure before style. Contracts stay frozen (routes, startapp values, storage keys).\n")
    for st in p["stages"]:
        print(f"## Stage {st['stage']}. {st['title']}\n")
        for it in st["items"]:
            print(f"- [ ] **{it['rule']} {it['name']}** ×{it['count']} ({', '.join(it['where'])})")
            print(f"      → {it['telegram']}  ·  kit: {it['kit']}  ·  {it['ref']}")
        print()
    print("## Always, whatever the lint says\n")
    for m in p["manual"]:
        print(f"- [ ] {m}")
    print("\n## Colour map (literal → kit role)\n")
    for c in p["colours"]:
        print(f"- `{c['colour']}` ×{c['count']} as {', '.join(c['used_as'])} → {c['role']}")
    brand = next((c["colour"] for c in p["colours"] if c["role"].startswith("brand candidate")), None)
    if brand:
        profile = json.dumps({"base": "native", "brand": {"light": brand, "dark": brand, "on": "#ffffff"}})
        print(f"\nBrand: keep `{brand}` for one moment per screen. Write style.json `{profile}`, run "
              "`py -3 scripts/miniapp_style.py check style.json` (contrast in both themes), then `css style.json`.")
    print("\n## Type map (size → role)\n")
    for s in p["type"]["sizes"]:
        print(f"- {s['px']:g}px → {s['role']} ({s['role_px']}px, `{s['kit']}`){'  ' + s['note'] if s['note'] else ''}")
    for f in p["type"]["families"]:
        print(f"- font `{f['family']}` → {f['action']}")
    print("\nThen: rebuild on the kit, lint --strict, preview both themes and platforms, report before/after counts.")


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Plan a Mini App rework into classic Telegram design")
    ap.add_argument("cmd", choices=["plan", "colours", "type"])
    ap.add_argument("app")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if not os.path.isdir(args.app):
        print(f"not a folder: {args.app}", file=sys.stderr)
        return 2
    if args.cmd == "plan":
        result = plan(args.app)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=1))
        else:
            print_plan(result)
        return 0
    sources = read_sources(args.app)
    result = colours(sources) if args.cmd == "colours" else typography(sources)
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
