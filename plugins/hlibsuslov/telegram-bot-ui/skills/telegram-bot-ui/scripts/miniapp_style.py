#!/usr/bin/env python3
# run-checks: check-presets
"""Mini App design styles: named presets and custom profiles compiled to kit-token overrides.

  py -3 scripts/miniapp_style.py presets                    # list the styles and when to use them
  py -3 scripts/miniapp_style.py show fintech               # one style: intent, tokens, components, do / don't
  py -3 scripts/miniapp_style.py css fintech                # CSS for a preset
  py -3 scripts/miniapp_style.py css style.json             # CSS for a custom profile (paste after tma.css)
  py -3 scripts/miniapp_style.py check style.json           # validate + brand contrast in light and dark
  py -3 scripts/miniapp_style.py check-presets              # presets in styles.json match tma.css (run_checks)
  py -3 scripts/miniapp_style.py palettes                   # named brand palettes (Apple system colours) with contrast

A profile (style.json):
  {"base": "fintech", "radius": "round", "density": "default", "glass": true,
   "brand": {"light": "#2f6bff", "dark": "#2f6bff", "on": "#ffffff"}, "figure": "clamp(3rem, 16vw, 4.2rem)"}
  "brand" may also name a palette from data/mini-apps/palettes.json ("brand": "teal"): the fill and the text
  colour are picked per scheme so the pair reaches 4.5:1 (the default colour, else its increased-contrast
  variant with white text, else the default colour with black text). An existing project keeps its own colour.

What a style may change: shape, density, type emphasis, glass, and the colour of ONE brand moment per
screen. What it may not: the theme colours (G1 of the Telegram design guidelines); surfaces, text and the
accent stay the user's theme. Rules: references/mini-apps/design-system.md section 9.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLES = os.path.join(SKILL, "data", "mini-apps", "styles.json")
PALETTES = os.path.join(SKILL, "data", "mini-apps", "palettes.json")
KIT_CSS = os.path.join(SKILL, "examples", "mini-apps", "_kit", "tma.css")
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
RADIUS = {"sharp": 0.5, "default": 1.0, "round": 1.25}
DENSITY = {"compact": -8, "default": 0, "roomy": 8}
# Kit defaults the profile math starts from (tma.css :root).
KIT_DEFAULTS = {"--tma-r-group": 26, "--tma-r-inner": 14, "--tma-row": 52, "--tma-row-2": 68, "--tma-gap-section": 24}
CSS_VALUE = re.compile(r"^[A-Za-z0-9 .,%()+\-*/]+$")  # no braces, semicolons, quotes or url()


def load() -> dict:
    with open(STYLES, encoding="utf-8") as fh:
        return json.load(fh)


def _px(v: str | int) -> float | None:
    m = re.fullmatch(r"(\d+(?:\.\d+)?)px", str(v))
    return float(m.group(1)) if m else (float(v) if isinstance(v, (int, float)) else None)


def luminance(hex_color: str) -> float:
    def ch(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    n = int(hex_color[1:], 16)
    r, g, b = n >> 16, (n >> 8) & 255, n & 255
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def load_palettes() -> dict:
    with open(PALETTES, encoding="utf-8") as fh:
        return json.load(fh)


def palette_brand(name: str) -> dict | None:
    """A named palette as a brand pair: per scheme the first of (default + white), (increased contrast + white),
    (default + black) that reaches 4.5:1."""
    row = load_palettes()["system"].get(name)
    if not row:
        return None
    out = {}
    for scheme in ("light", "dark"):
        for fill, on in ((row[scheme], "#ffffff"), (row[f"ic_{scheme}"], "#ffffff"), (row[scheme], "#000000")):
            if contrast(fill, on) >= 4.5:
                out[scheme], out["on" if scheme == "light" else "on_dark"] = fill, on
                break
    return out


def resolve(profile: dict, data: dict) -> tuple[dict[str, str], list[str], list[str]]:
    """(tokens, errors, warnings) for a profile; a preset name is a profile with only `base`."""
    errors, warnings = [], []
    known = {"base", "radius", "density", "glass", "brand", "figure", "$comment"}
    profile = dict(profile)
    for k in profile:
        if k not in known:
            errors.append(f"unknown key {k!r} (known: {', '.join(sorted(known - {'$comment'}))})")
    base = profile.get("base", "native")
    if base not in data["presets"]:
        errors.append(f"base {base!r} is not a preset ({', '.join(data['presets'])})")
        return {}, errors, warnings
    tokens = dict(data["presets"][base]["tokens"])
    radius = profile.get("radius", "default")
    if radius not in RADIUS:
        errors.append(f"radius must be one of {', '.join(RADIUS)}")
    elif radius != "default":
        for key in ("--tma-r-group", "--tma-r-inner"):
            px = _px(tokens.get(key, KIT_DEFAULTS[key]))
            tokens[key] = f"{round(px * RADIUS[radius])}px"
    density = profile.get("density", "default")
    if density not in DENSITY:
        errors.append(f"density must be one of {', '.join(DENSITY)}")
    elif density != "default":
        for key in ("--tma-row", "--tma-row-2", "--tma-gap-section"):
            px = _px(tokens.get(key, KIT_DEFAULTS[key]))
            tokens[key] = f"{round(px + DENSITY[density])}px"
    for key in [k for k in tokens if k in KIT_DEFAULTS and (radius != "default" or density != "default")]:
        spec, px = data["tokens"][key], _px(tokens[key])
        lo, hi = spec["range"]
        if px is not None and not lo <= px <= hi:
            tokens[key] = f"{int(min(max(px, lo), hi))}px"
            warnings.append(f"{key} {px:g}px clamped to {tokens[key]} ({lo}-{hi} px)")
    for key, value in tokens.items():
        spec = data["tokens"].get(key)
        px = _px(value)
        if spec and spec.get("range") and px is not None and not spec["range"][0] <= px <= spec["range"][1]:
            errors.append(f"{key} {value} outside {spec['range'][0]}-{spec['range'][1]} px")
        if key in ("--tma-row", "--tma-row-2") and px is not None and px < 44:
            errors.append(f"{key} {value}: touch targets need at least 44 px")
    if "figure" in profile:
        if not isinstance(profile["figure"], str) or not CSS_VALUE.match(profile["figure"]):
            errors.append("figure must be a plain CSS size such as clamp(3rem, 15vw, 4rem)")
        else:
            tokens["--tma-figure-size"] = profile["figure"]
    brand = profile.get("brand")
    if isinstance(brand, str):
        named = palette_brand(brand)
        if named is None:
            errors.append(f"brand {brand!r} is not a palette ({', '.join(load_palettes()['system'])})")
            brand = None
        else:
            brand = profile["brand"] = named
    if brand is not None:
        if not isinstance(brand, dict) or not all(HEX.match(str(brand.get(k, ""))) for k in ("light", "dark", "on")) \
                or ("on_dark" in brand and not HEX.match(str(brand["on_dark"]))):
            errors.append('brand needs "light", "dark" and "on" as #RRGGBB (optional "on_dark"), or a palette name')
        else:
            for scheme in ("light", "dark"):
                on = brand.get("on_dark", brand["on"]) if scheme == "dark" else brand["on"]
                ratio = contrast(brand[scheme], on)
                if ratio < 4.5:
                    errors.append(f"brand {scheme} {brand[scheme]} with text {on}: contrast {ratio:.2f} < 4.5")
            warnings.append("brand colours one moment per screen (hero, promo); buttons, links and surfaces stay the theme's")
    if profile.get("glass") is False:
        warnings.append("glass off: floating controls become solid surfaces")
    elif "glass" in profile and not isinstance(profile["glass"], bool):
        errors.append("glass must be true or false")
    return tokens, errors, warnings


def css(profile: dict, data: dict) -> str:
    profile = dict(profile)
    if isinstance(profile.get("brand"), str) and palette_brand(profile["brand"]):
        profile["brand"] = palette_brand(profile["brand"])
    tokens, errors, _ = resolve(profile, data)
    if errors:
        raise ValueError("; ".join(errors))
    lines = [f"/* Mini App style: base {profile.get('base', 'native')} (scripts/miniapp_style.py). "
             "Load after tma.css; keep <html data-tma-style> unset when using this block. */"]
    body = [f"{k}: {v};" for k, v in tokens.items()]
    brand = profile.get("brand")
    if brand:
        body.append(f"--tma-brand: {brand['light']};")
        body.append(f"--tma-on-brand: {brand['on']};")
    lines.append(":root { " + " ".join(body) + " }" if body else ":root { }")
    if brand and (brand["dark"] != brand["light"] or brand.get("on_dark", brand["on"]) != brand["on"]):
        lines.append(f':root[data-tma-scheme="dark"] {{ --tma-brand: {brand["dark"]}; --tma-on-brand: {brand.get("on_dark", brand["on"])}; }}')
    if profile.get("glass") is False or (profile.get("base") == "dense" and profile.get("glass") is not True):
        lines.append(".tma-glass { background: var(--tma-surface); -webkit-backdrop-filter: none; "
                     "backdrop-filter: none; box-shadow: 0 1px 0 var(--tma-separator); }")
    if profile.get("base") == "dense":
        lines.append(':root[data-tma-platform="android"] .tma-list { border-radius: 0; '
                     "margin-inline: calc(-1 * var(--tma-safe-left)); }")
    return "\n".join(lines) + "\n"


def kit_presets() -> dict[str, dict[str, str]]:
    with open(KIT_CSS, encoding="utf-8") as fh:
        text = fh.read()
    out = {}
    for name, body in re.findall(r':root\[data-tma-style="(\w+)"\]\s*\{([^}]*)\}', text):
        decls = dict(re.findall(r"(--tma-[\w-]+)\s*:\s*([^;]+);", body))
        if decls:
            out[name] = {k: v.strip() for k, v in decls.items()}
    return out


def check_presets(data: dict) -> list[str]:
    errors = []
    kit = kit_presets()
    for name, preset in data["presets"].items():
        _, errs, _ = resolve({"base": name}, data)
        errors += [f"{name}: {e}" for e in errs]
        if name == "native":
            if preset["tokens"]:
                errors.append("native must have no token overrides")
            continue
        if kit.get(name) != preset["tokens"]:
            errors.append(f"tma.css preset {name} {kit.get(name)} != styles.json {preset['tokens']}")
    for name in kit:
        if name not in data["presets"]:
            errors.append(f"tma.css has preset {name} missing from styles.json")
    return errors


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Mini App design styles")
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("presets")
    sub.add_parser("check-presets")
    sub.add_parser("palettes")
    for name in ("show", "css", "check"):
        sub.add_parser(name).add_argument("target", help="preset name or a style.json path")
    args = ap.parse_args(argv)
    data = load()

    def profile_of(target: str) -> dict:
        if target in data["presets"]:
            return {"base": target}
        with open(target, encoding="utf-8") as fh:
            return json.load(fh)

    if args.cmd == "presets":
        rows = {k: {"title": v["title"], "use_for": v["use_for"]} for k, v in data["presets"].items()}
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=1))
        else:
            for k, v in data["presets"].items():
                print(f"{k:<8} {v['title']:<16} {', '.join(v['use_for'])}")
        return 0
    if args.cmd == "palettes":
        pal = load_palettes()
        rows = {k: palette_brand(k) for k in pal["system"]}
        if args.json:
            print(json.dumps({"source": pal["source"], "palettes": rows, "by_product": pal["by_product"]}, ensure_ascii=False, indent=1))
            return 0
        print(f"Apple system colours ({pal['source']}, values {pal['values_dated']}); one brand moment per screen")
        for k, b in rows.items():
            print(f"{k:<7} light {b['light']} on {b['on']} ({contrast(b['light'], b['on']):.1f}:1)   "
                  f"dark {b['dark']} on {b['on_dark']} ({contrast(b['dark'], b['on_dark']):.1f}:1)")
        print("by product: " + "; ".join(f"{k}: {', '.join(v)}" for k, v in pal["by_product"].items() if not k.startswith("$")))
        return 0
    if args.cmd == "check-presets":
        errors = check_presets(data)
        for e in errors:
            print(f"FAIL: {e}")
        if not errors:
            print(f"OK: {len(data['presets'])} Mini App style presets, tma.css in sync")
        return 1 if errors else 0
    if args.cmd == "show":
        p = data["presets"].get(args.target)
        if not p:
            print(f"no preset {args.target}; known: {', '.join(data['presets'])}")
            return 1
        if args.json:
            print(json.dumps(p, ensure_ascii=False, indent=1))
            return 0
        print(f"{args.target}: {p['title']}\n{p['intent']}\nUse for: {', '.join(p['use_for'])}")
        print("Tokens: " + (", ".join(f"{k} {v}" for k, v in p["tokens"].items()) or "none (kit defaults)"))
        for k, v in p["components"].items():
            print(f"  {k}: {v}")
        print("Do: " + "; ".join(p["do"]))
        print("Don't: " + "; ".join(p["dont"]))
        print(f'Apply: <html data-tma-style="{args.target}">' if args.target != "native" else "Apply: nothing (default)")
        return 0
    profile = profile_of(args.target)
    if args.cmd == "css":
        try:
            sys.stdout.write(css(profile, data))
        except ValueError as exc:
            print(f"invalid profile: {exc}")
            return 1
        return 0
    tokens, errors, warnings = resolve(profile, data)
    if args.json:
        print(json.dumps({"ok": not errors, "tokens": tokens, "errors": errors, "warnings": warnings}, indent=1))
    else:
        for w in warnings:
            print(f"WARN: {w}")
        for e in errors:
            print(f"FAIL: {e}")
        if not errors:
            print(f"OK: base {profile.get('base', 'native')}, {len(tokens)} token(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
