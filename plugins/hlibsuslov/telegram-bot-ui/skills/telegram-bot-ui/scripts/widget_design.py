#!/usr/bin/env python3
"""Widget design profiles: a small JSON (`design.json`) that restyles any kit widget without
touching its markup, script or texts, compiled to a few CSS rules at build time.

  py -3 scripts/widget_design.py presets                 # list the ready-made profiles
  py -3 scripts/widget_design.py check design.json       # validate + contrast in both themes
  py -3 scripts/widget_design.py css design.json [SRC]   # the CSS a build would inject
  py -3 scripts/build_widget.py SRC --design design.json --lang ru --strict

How it stays inside the widget rules (references/widget-design-system.md#14-design-profiles):
* Colours redefine the kit tokens (`--k-*`) and the client button variables (`--tg-button-*`)
  on the root block `.k`, never on html/body. A colour left unset is Telegram's own, per theme.
  "theme" mode writes `light-dark(light, dark)`, so one build follows the chat's scheme live.
* Shape and size rules are emitted only for parts the widget actually has (chips, bars,
  counter, image, primary buttons), so an unused option costs zero bytes.
* Button and chip rules use zero-specificity `:where()` and come right after the kit tokens:
  a widget's own rule (rating stars, a flex row of actions) still wins over the profile.
* Motion animates transform and background-position only (never opacity or filters: those
  count towards the 16 "heavy" elements), and the kit's prefers-reduced-motion rule stops it.

An empty profile (`{}` or preset "telegram") compiles to nothing: the widget looks native.
"""
from __future__ import annotations

import json
import re
import sys
from typing import Any

VERSION = 1
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

# Colour slots: what each one paints, the kit token it redefines, Telegram's own value.
SLOTS: dict[str, dict[str, Any]] = {
    "bg": {"label": "Block background", "vars": [], "tg": None},
    "bg2": {"label": "Second background colour (gradient)", "vars": [], "tg": None},
    "text": {"label": "Title and main text", "vars": ["--k-tx"], "tg": "var(--tg-theme-text-color,#000)"},
    "hint": {"label": "Secondary text", "vars": ["--k-hint"], "tg": "var(--tg-theme-hint-color,#707579)"},
    "button": {"label": "Button", "vars": ["--k-btn"], "tg": "var(--tg-theme-button-color,#2481cc)"},
    "buttonText": {"label": "Button label", "vars": ["--k-btx"], "tg": "var(--tg-theme-button-text-color,#fff)"},
    "surface": {"label": "Chips, cards, counter, tracks", "vars": ["--k-sec"],
                "tg": "var(--tg-theme-secondary-bg-color,#f1f1f4)"},
    "border": {"label": "Block border", "vars": [], "tg": "var(--k-sep)"},
    "separator": {"label": "Separators", "vars": ["--k-sep"], "tg": "var(--tg-theme-section-separator-color,#e0e0e0)"},
    "accent": {"label": "Links and accent", "vars": ["--k-acc", "--k-link"], "tg": "var(--tg-theme-accent-text-color,#2481cc)"},
    "success": {"label": "Success", "vars": ["--k-ok"], "tg": "light-dark(#2e8b3e,#5ec46e)"},
    "warning": {"label": "Warning", "vars": ["--k-warn"], "tg": "light-dark(#a86400,#f0a73a)"},
    "danger": {"label": "Errors and destructive", "vars": ["--k-bad"], "tg": "var(--tg-theme-destructive-text-color,#e53935)"},
}

# Telegram's default palettes (the preview's light and dark themes): contrast checks and the
# editor's "unset" swatches. Success/warning are the kit's light-dark() pairs.
TG = {
    "light": {"bg": "#ffffff", "text": "#000000", "hint": "#707579", "button": "#2481cc", "buttonText": "#ffffff",
              "surface": "#f1f1f4", "accent": "#2481cc", "danger": "#e53935", "separator": "#e7e7ea",
              "border": "#e7e7ea", "success": "#2e8b3e", "warning": "#a86400"},
    "dark": {"bg": "#212d3b", "text": "#ffffff", "hint": "#7d8b99", "button": "#50a8eb", "buttonText": "#ffffff",
             "surface": "#2b3a4b", "accent": "#64b5ef", "danger": "#ee686f", "separator": "#0f161e",
             "border": "#0f161e", "success": "#5ec46e", "warning": "#f0a73a"},
}

ENUMS = {
    ("block", "align"): ("start", "center", "end"),
    ("button", "style"): ("native", "filled", "outline", "soft", "text"),
    ("button", "height"): ("low", "normal", "high"),
    ("button", "width"): ("auto", "half", "full"),
    ("button", "align"): ("start", "center", "end"),
    ("chips", "selected"): ("filled", "outline"),
    ("title", "size"): ("s", "m", "l", "xl"),
    ("title", "align"): ("start", "center", "end"),
    ("body", "size"): ("s", "m"),
    ("meta", "size"): ("s", "m"),
    ("meta", "align"): ("start", "center", "end"),
    ("counter", "style"): ("filled", "outline"),
}
RANGES = {
    ("block", "radius"): (0, 32), ("block", "border"): (0, 4), ("block", "padding"): (4, 32), ("block", "inset"): (0, 16),
    ("button", "radius"): (0, 24), ("chips", "radius"): (0, 20), ("surface", "radius"): (0, 24),
    ("counter", "radius"): (0, 20), ("bar", "height"): (2, 12), ("bar", "radius"): (0, 6), ("image", "radius"): (0, 32),
}
BOOLS = {("image", "backdrop")}
GROUPS = sorted({g for g, _ in (*ENUMS, *RANGES, *BOOLS)})
MOTION = ("none", "calm", "lively")

PRESETS: dict[str, dict[str, Any]] = {
    "telegram": {"label": "Telegram", "note": "The chat's own colours and shapes. Nothing is added.", "design": {}},
    "card": {"label": "Card", "note": "A framed card inside the bubble, square-ish buttons.", "design": {
        "colors": {"mode": "theme", "light": {"bg": "#f6f7f9", "border": "#e3e6eb", "surface": "#eceef2"},
                   "dark": {"bg": "#1b2430", "border": "#2c3a4b", "surface": "#263241"}},
        "block": {"radius": 14, "border": 1, "padding": 14, "inset": 6},
        "button": {"style": "filled", "radius": 10, "height": "normal"},
        "chips": {"radius": 10}, "surface": {"radius": 12}}},
    "soft": {"label": "Soft", "note": "Pastel surfaces, pill buttons, a calm entrance.", "design": {
        "colors": {"mode": "theme",
                   "light": {"bg": "#eef3ff", "text": "#1b2a4a", "hint": "#5b6b8c", "button": "#3d6dff",
                             "buttonText": "#ffffff", "surface": "#dfe7fb", "accent": "#3d6dff"},
                   "dark": {"bg": "#1a2236", "text": "#e8eeff", "hint": "#97a3c2", "button": "#86a3ff",
                            "buttonText": "#0c1222", "surface": "#29324a", "accent": "#9db4ff"}},
        "block": {"radius": 20, "padding": 16, "inset": 6},
        "button": {"style": "filled", "radius": 24, "height": "high"},
        "surface": {"radius": 16}, "counter": {"style": "filled", "radius": 20}, "motion": "calm"}},
    "contrast": {"label": "Contrast", "note": "Black and white, thick lines, readable in sunlight.", "design": {
        "colors": {"mode": "theme",
                   "light": {"bg": "#ffffff", "text": "#000000", "hint": "#3c3c43", "button": "#000000",
                             "buttonText": "#ffffff", "surface": "#ececec", "border": "#000000", "separator": "#000000"},
                   "dark": {"bg": "#000000", "text": "#ffffff", "hint": "#d1d1d6", "button": "#ffffff",
                            "buttonText": "#000000", "surface": "#232323", "border": "#ffffff", "separator": "#ffffff"}},
        "block": {"radius": 6, "border": 2, "padding": 14, "inset": 4},
        "button": {"style": "filled", "radius": 6, "height": "high"},
        "chips": {"radius": 6, "selected": "outline"}, "title": {"size": "l"}, "surface": {"radius": 6}}},
    "lines": {"label": "Lines", "note": "No fills: outlined buttons and chips on the chat's colours.", "design": {
        "button": {"style": "outline", "radius": 12},
        "chips": {"radius": 12, "selected": "outline"}, "counter": {"style": "outline", "radius": 12},
        "block": {"border": 1, "radius": 14, "padding": 12, "inset": 4}}},
    "showcase": {"label": "Showcase", "note": "One dark gradient in both themes, a lime button that catches the eye.",
                 "design": {
        "colors": {"mode": "shared", "shared": {"bg": "#14171e", "bg2": "#252b3b", "text": "#f3f4f6", "hint": "#9aa3b2",
                                                 "button": "#d4f36b", "buttonText": "#14171c", "surface": "#2a3040",
                                                 "border": "#2f344c", "separator": "#2f344c", "accent": "#d4f36b"}},
        "block": {"radius": 18, "border": 1, "padding": 16, "inset": 6},
        "button": {"style": "filled", "radius": 12, "height": "high"},
        "title": {"size": "l"}, "surface": {"radius": 12}, "motion": "calm"}},
}


# ---------------------------------------------------------------- validation

def validate(design: Any) -> list[str]:
    """Shape errors (unknown keys, wrong types, out-of-range values). Empty list = valid."""
    if not isinstance(design, dict):
        return ["design must be a JSON object"]
    errs: list[str] = []
    known = {"version", "preset", "colors", "motion", *GROUPS}
    errs += [f"unknown key {k!r}" for k in design if k not in known]
    if design.get("version", VERSION) != VERSION:
        errs.append(f"version must be {VERSION}")
    if "motion" in design and design["motion"] not in MOTION:
        errs.append(f"motion must be one of {', '.join(MOTION)}")
    if "preset" in design and design["preset"] not in PRESETS and design["preset"] != "custom":
        errs.append(f"unknown preset {design['preset']!r}")
    c = design.get("colors", {})
    if not isinstance(c, dict):
        errs.append("colors must be an object")
    else:
        if c.get("mode", "theme") not in ("theme", "shared"):
            errs.append("colors.mode must be theme or shared")
        for part in ("light", "dark", "shared"):
            p = c.get(part, {})
            if not isinstance(p, dict):
                errs.append(f"colors.{part} must be an object")
                continue
            for slot, val in p.items():
                if slot not in SLOTS:
                    errs.append(f"colors.{part}: unknown slot {slot!r}")
                elif val is not None and not (isinstance(val, str) and HEX.match(val)):
                    errs.append(f"colors.{part}.{slot} must be #rrggbb")
        errs += [f"colors: unknown key {k!r}" for k in c if k not in ("mode", "light", "dark", "shared")]
    for g in GROUPS:
        sec = design.get(g)
        if sec is None:
            continue
        if not isinstance(sec, dict):
            errs.append(f"{g} must be an object")
            continue
        for k, v in sec.items():
            if (g, k) in ENUMS:
                if v not in ENUMS[(g, k)]:
                    errs.append(f"{g}.{k} must be one of {', '.join(ENUMS[(g, k)])}")
            elif (g, k) in RANGES:
                lo, hi = RANGES[(g, k)]
                if not isinstance(v, (int, float)) or isinstance(v, bool) or not lo <= v <= hi:
                    errs.append(f"{g}.{k} must be a number {lo}..{hi}")
            elif (g, k) in BOOLS:
                if not isinstance(v, bool):
                    errs.append(f"{g}.{k} must be true or false")
            else:
                errs.append(f"unknown key {g}.{k}")
    return errs


def palette(design: dict, theme: str) -> dict[str, str]:
    """Colours the profile sets for one theme ("light"/"dark"); unset slots are absent."""
    c = design.get("colors") or {}
    src = c.get("shared") if c.get("mode") == "shared" else c.get(theme)
    return {k: v for k, v in (src or {}).items() if v}


# ---------------------------------------------------------------- contrast

def _lum(hex_: str) -> float:
    def ch(v: int) -> float:
        s = v / 255
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a: str, b: str) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _mix(a: str, b: str) -> str:
    return "#" + "".join(f"{(int(a[i:i + 2], 16) + int(b[i:i + 2], 16)) // 2:02x}" for i in (1, 3, 5))


def contrast_report(design: dict) -> list[dict]:
    """WCAG ratios of the pairs people read, per theme, with Telegram's default palette standing
    in for unset slots. `ok` is False below 4.5:1 (text) or 3:1 (secondary text, labels)."""
    btn = (design.get("button") or {}).get("style", "native")
    out = []
    for theme in ("light", "dark"):
        own = palette(design, theme)
        p = {**TG[theme], **own}
        bg = _mix(p["bg"], p["bg2"]) if p.get("bg2") else p["bg"]
        pairs = [("Main text on the block", p["text"], bg, 4.5), ("Secondary text on the block", p["hint"], bg, 3.0),
                 ("Text on chips and cards", p["text"], p["surface"], 4.5)]
        if btn in ("native", "filled"):
            pairs.append(("Button label on the button", p["buttonText"], p["button"], 3.0))
        elif btn == "soft":
            pairs.append(("Button label on a soft button", p["button"], p["surface"], 3.0))
        else:
            pairs.append(("Button colour on the block", p["button"], bg, 3.0))
        mine = set(own.values())
        for name, fg, back, need in pairs:
            if fg not in mine and back not in mine and not own.get("bg2"):
                continue  # Telegram's own pair: not the profile's to fix
            r = contrast(fg, back)
            out.append({"theme": theme, "pair": name, "fg": fg, "bg": back, "ratio": round(r, 2), "need": need,
                        "ok": r >= need})
    return out


def warnings(design: dict) -> list[str]:
    w = [f"{r['theme']} theme: {r['pair']} {r['ratio']}:1 (needs {r['need']}:1)"
         for r in contrast_report(design) if not r["ok"]]
    block = design.get("block") or {}
    has_bg = any(palette(design, t).get("bg") for t in ("light", "dark"))
    if has_bg and not block.get("inset"):
        w.append("a block background with no inset paints the whole bubble; Telegram recommends keeping the "
                 "bubble's own colour around it (block.inset 4-8)")
    return w


# ---------------------------------------------------------------- compile

def _has(src: str, cls: str) -> bool:
    return bool(re.search(rf"(?<![\w-]){re.escape(cls)}(?![\w-])", src))


def _color(design: dict, slot: str) -> str | None:
    """CSS value for a slot: plain hex (shared), light-dark() (per theme), None if unset."""
    c = design.get("colors") or {}
    if c.get("mode") == "shared":
        return (c.get("shared") or {}).get(slot)
    lt, dk = (c.get("light") or {}).get(slot), (c.get("dark") or {}).get(slot)
    if not lt and not dk:
        return None
    fb = SLOTS[slot]["tg"] or "transparent"
    return f"light-dark({lt or fb},{dk or fb})"


def _px(v: float) -> str:
    return f"{v:g}px" if v else "0"


# Primary buttons in kit widgets: a plain <button> (K.h gives it class=""), .wd or .gr. Buttons a
# widget draws itself (stars, rows, calendar days) carry their own class and are left alone.
PRIMARY = ":where(.k button:is(:not([class]),[class=''],.wd,.gr))"

_ALIGN = {"start": "start", "center": "center", "end": "end"}
_TITLE = {"s": "1em", "m": "1.07em", "l": "1.25em", "xl": "1.45em"}
_BTN_H = {"low": "32px", "normal": "36px", "high": "44px"}


def compile_css(design: dict, src: str = "") -> str:
    """CSS for a profile. `src` is the widget's HTML (after kit inlining): rules for parts it does
    not have and tokens it never reads are left out. Without `src`, everything is emitted."""
    def has(cls: str) -> bool:
        return not src or _has(src, cls)

    def reads(var: str) -> bool:
        return not src or f"var({var}" in src

    root: list[str] = []
    rules: list[str] = []
    for slot, meta in SLOTS.items():
        val = _color(design, slot)
        if val:
            root += [f"{v}:{val}" for v in meta["vars"] if reads(v) or v in ("--k-tx", "--k-btn", "--k-btx")]
    if _color(design, "text"):
        root.append("color:var(--k-tx)")
    bg, bg2 = _color(design, "bg"), _color(design, "bg2")
    if bg and bg2:
        root.append(f"background:linear-gradient(160deg,{bg},{bg2})")
    elif bg or bg2:
        root.append(f"background:{bg or bg2}")

    b = design.get("block") or {}
    if b.get("border"):
        root.append(f"border:{_px(b['border'])} solid {_color(design, 'border') or 'var(--k-sep)'}")
    if "radius" in b:
        root.append(f"border-radius:{_px(b['radius'])}")
    if "padding" in b:
        p = _px(b["padding"])
        root.append(f"padding:{p} {p} max({p},env(safe-area-inset-bottom),var(--tg-content-safe-area-inset-bottom,0px))")
    if b.get("inset"):
        root.append(f"margin:{_px(b['inset'])}")
    if b.get("align"):
        root.append(f"text-align:{_ALIGN[b['align']]}")
        rules.append(f":where(.k) :is(.rw,.fw){{justify-content:{_ALIGN[b['align']]}}}" if has("rw") or has("fw") else "")

    body = design.get("body") or {}
    if body.get("size") == "s":
        root.append("font-size:.93em")
    s = design.get("surface") or {}
    if "radius" in s and reads("--k-r"):
        root.append(f"--k-r:{_px(s['radius'])}")

    # Buttons: the client draws a plain <button> from these variables; restyling through them
    # keeps its pressed and disabled states. Rules use :where() so a widget's own rule wins.
    bt = design.get("button") or {}
    style = bt.get("style", "native")
    has_btn = "<button" in src or "\"button\"" in src or not src
    btn_bg, btn_tx = _color(design, "button"), _color(design, "buttonText")
    btn = btn_bg or SLOTS["button"]["tg"]
    if has_btn:
        if style in ("native", "filled"):
            if btn_bg:
                root.append("--tg-button-bg:var(--k-btn)")
            if btn_tx:
                root.append("--tg-button-text:var(--k-btx)")
        elif style == "outline":
            root += ["--tg-button-bg:transparent", f"--tg-button-text:{btn}"]
            rules.append(PRIMARY + "{box-shadow:inset 0 0 0 1.5px currentColor}")
        elif style == "soft":
            root += [f"--tg-button-bg:{_color(design, 'surface') or SLOTS['surface']['tg']}", f"--tg-button-text:{btn}"]
        elif style == "text":
            root += ["--tg-button-bg:transparent", f"--tg-button-text:{btn}"]
        if "radius" in bt:
            root.append(f"--tg-button-radius:{_px(bt['radius'])}")
        if bt.get("height"):
            root.append(f"--tg-button-height:{_BTN_H[bt['height']]}")
        decl = []
        if bt.get("width") == "full":
            decl.append("width:100%")
        elif bt.get("width") == "half":
            decl.append("width:50%")
        elif bt.get("width") == "auto":
            decl.append("width:auto")
        if bt.get("align"):
            decl += ["display:block", {"start": "margin-inline:0 auto", "center": "margin-inline:auto",
                                       "end": "margin-inline:auto 0"}[bt["align"]]]
        if decl:
            rules.append(f"{PRIMARY}{{{';'.join(decl)}}}")

    t = design.get("title") or {}
    if has("tt") and (t.get("size") or t.get("align")):
        d = ([f"font-size:{_TITLE[t['size']]}"] if t.get("size") else []) + \
            ([f"text-align:{_ALIGN[t['align']]}"] if t.get("align") else [])
        rules.append(f".k .tt{{{';'.join(d)}}}")
    m = design.get("meta") or {}
    if has("mt") and (m.get("size") or m.get("align")):
        d = (["font-size:.8em"] if m.get("size") == "s" else []) + \
            ([f"text-align:{_ALIGN[m['align']]}"] if m.get("align") else [])
        if d:
            rules.append(f".k .mt{{{';'.join(d)}}}")

    ch = design.get("chips") or {}
    if has("ch"):
        if "radius" in ch:
            rules.append(f":where(.k) .ch{{border-radius:{_px(ch['radius'])}}}")
        if ch.get("selected") == "outline":
            rules.append(".k .ch.on{background:transparent;color:var(--k-btn);box-shadow:inset 0 0 0 1.5px var(--k-btn)}")

    co = design.get("counter") or {}
    if has("qt") and has("ch") and co:
        d = []
        if co.get("style") == "outline":
            d += ["background:transparent", "box-shadow:inset 0 0 0 1.5px var(--k-sec)"]
        if "radius" in co:
            d.append(f"border-radius:{_px(co['radius'])}")
        if d:
            rules.append(f".k .qt .ch{{{';'.join(d)}}}")

    br = design.get("bar") or {}
    if has("br") and br:
        if "height" in br:
            rules.append(f".k .br{{height:{_px(br['height'])}}}")
        if "radius" in br:
            rules.append(f".k .br,.k .br>i{{border-radius:{_px(br['radius'])}}}")

    im = design.get("image") or {}
    if has("im") and im:
        d = []
        if "radius" in im:
            d += [f"border-radius:{_px(im['radius'])}", "overflow:hidden"]
        if im.get("backdrop") is False:
            d.append("background:none")
        if d:
            rules.append(f".k .im{{{';'.join(d)}}}")

    motion = design.get("motion", "none")
    if motion in ("calm", "lively"):
        root.append("animation:k-in .4s")
        rules.append("@keyframes k-in{0%{transform:translateY(8px)}}")
    if motion == "lively" and has_btn:
        # A glint crosses the button every 5 s: at 0% and 100% the 300%-wide gradient shows only
        # its transparent ends; the implicit `to` keyframe is the rule's own position (0).
        rules.append(PRIMARY + "{background-image:linear-gradient(105deg,#0000 40%,#fff5,#0000 60%);"
                     "background-size:300%;animation:k-sh 5s infinite}@keyframes k-sh{0%,70%{background-position:100%}}")

    css = (f".k{{{';'.join(root)}}}" if root else "") + "".join(r for r in rules if r)
    return css


def colors_used(design: dict) -> set[str]:
    """Hex literals the profile writes (the lint's raw-colour rule accepts them: the person
    chose them and contrast_report() checks them against both themes)."""
    out = set()
    c = design.get("colors") or {}
    for part in ("light", "dark", "shared"):
        out |= {v.lower() for v in (c.get(part) or {}).values() if v}
    if design.get("motion") == "lively":
        out |= {"#0000", "#fff5"}  # the shine: transparent and a white glint, same in both themes
    return out


def apply_preset(name: str) -> dict:
    d = json.loads(json.dumps(PRESETS[name]["design"]))
    d["version"] = VERSION
    d["preset"] = name
    return d


def catalog() -> dict:
    """Everything an editor needs to draw the controls (served to the Studio)."""
    return {"version": VERSION, "slots": {k: v["label"] for k, v in SLOTS.items()},
            "enums": {f"{g}.{k}": list(v) for (g, k), v in ENUMS.items()},
            "ranges": {f"{g}.{k}": list(v) for (g, k), v in RANGES.items()}, "motion": list(MOTION),
            "presets": {k: {"label": v["label"], "note": v["note"], "design": apply_preset(k)} for k, v in PRESETS.items()},
            "telegram": TG}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in ("presets", "check", "css"):
        print(__doc__.split("\n\n")[0])
        print("usage: widget_design.py presets | check FILE | css FILE [SRC]")
        return 0 if args[:1] in (["-h"], ["--help"]) else 2
    if args[0] == "presets":
        for k, v in PRESETS.items():
            print(f"{k:10} {v['label']}: {v['note']}")
        return 0
    with open(args[1], encoding="utf-8") as fh:
        design = json.load(fh)
    errs = validate(design)
    for e in errs:
        print(f"FAIL: {e}")
    if errs:
        return 1
    if args[0] == "check":
        for w in warnings(design):
            print(f"WARN: {w}")
        print("OK" if not warnings(design) else "OK with warnings")
        return 0
    src = ""
    if len(args) > 2:
        with open(args[2], encoding="utf-8") as fh:
            src = fh.read()
    print(compile_css(design, src))
    return 0


if __name__ == "__main__":
    sys.exit(main())
