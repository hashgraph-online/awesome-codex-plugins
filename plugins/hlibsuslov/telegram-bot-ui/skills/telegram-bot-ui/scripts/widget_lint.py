"""Strict widget checks for the gallery and for widgets an agent writes (Bot API 10.4, profile 1).

Adds to tgkit.widgets.check_widget (size, state bytes, contexts, runtime gaps) the checks a
production-quality widget needs. Pattern-based: a clean report is evidence for the static
contract only, never proof that real Telegram clients render the widget as intended.

Rules and their status (W = Widgets guide https://core.telegram.org/bots/widgets, checked
2026-11-15; H = this skill's design heuristic):
  hard errors
    external-url     W  nothing external loads; openLink needs https (http:// is refused)
    svg-data-image   W  <img src="data:image/svg+xml"> is out of profile 1
    font-name        W  named fonts are removed; generic families only
    css-rules        W  at most 400 CSS rules and 32 @keyframes
    nodes            W  at most 2000 nodes (static markup counted; scripts may add more)
  warnings (the gallery treats them as failures)
    budget           W  "If you cannot measure, aim for 3800" compressed bytes
    raw-color        H  colours only as var(--tg-*) fallbacks, light-dark() pairs or neutral greys
    double-band      W  padding for the time band needs body{padding:0}, or the band doubles
    request-errors   W  a widget that asks must show every outcome (TIMEOUT, RATE_LIMITED...)
    state-events     W  a widget that reads state must redraw on chatDataChanged/publicDataChanged
    no-guard         W  window.TelegramWidget is undefined outside Telegram: check it
    drag-claim       W  pointermove drags need touch-action pan-y or none on the element
    reduced-motion   W  animations must respect prefers-reduced-motion
    resize-anchor    W  setResizeAnchor is missing in early apps: check typeof first
    storage-try      W  localStorage throws QuotaExceededError beyond 4 KB: wrap in try
    heavy            W  at most 16 heavy elements (blur, filter, opacity < 1) at once
    caption-mirror   H  a caption is required and should name the widget's main fact
    tap-request      W  request()/K.ask only in a real tap (click/pointerup), not in pointerdown
    innerhtml-state  W  text from state or answers goes through textContent, never innerHTML
    canvas-arc       H  an arc past 2*pi, or rect() then arc() in one path, draws a stray stripe in
                        Telegram (field report); dim, clip and redraw instead
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

BUDGET = 3800
GENERIC_FONTS = {"system-ui", "sans-serif", "serif", "monospace", "ui-sans-serif", "ui-serif",
                 "ui-monospace", "ui-rounded", "-apple-system", "inherit", "initial", "unset", "cursive",
                 "fantasy"}

_STYLE = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
_SCRIPT = re.compile(r"<script[^>]*>(.*?)</script>", re.S | re.I)
_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\([^)]*\)|\bhsla?\([^)]*\)")


@dataclass
class LintReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add(self, level: str, rule: str, msg: str) -> None:
        (self.errors if level == "error" else self.warnings).append(f"[{rule}] {msg}")


def styles(html: str) -> str:
    return "\n".join(_STYLE.findall(html))


def scripts(html: str) -> str:
    return "\n".join(_SCRIPT.findall(html))


def _strip_allowed_colors(css: str) -> str:
    """Remove colour literals that are theme-safe: var() fallbacks and light-dark() pairs."""
    out, i = [], 0
    while i < len(css):
        m = re.compile(r"\b(var|light-dark)\(").search(css, i)
        if not m:
            out.append(css[i:])
            break
        out.append(css[i:m.start()])
        depth, j = 0, m.end() - 1
        while j < len(css):
            if css[j] == "(":
                depth += 1
            elif css[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        i = j + 1
    return "".join(out)


def _neutral(color: str) -> bool:
    """rgba() greys with alpha < 1 read the same on light and dark bubbles."""
    m = re.match(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)", color)
    return bool(m and m.group(1) == m.group(2) == m.group(3) and float(m.group(4)) < 1)


def lint(html: str, *, caption: str | None = None, compressed: int | None = None,
         allowed_colors: set[str] | frozenset[str] = frozenset()) -> LintReport:
    """`allowed_colors`: hex literals of a design profile (chosen by a person, contrast-checked
    in both themes by widget_design.py); the raw-color rule accepts exactly those."""
    rep = LintReport()
    css, js = styles(html), scripts(html)

    # A tapped <a href="https://..."> is allowed (it opens through openLink); loads are not.
    for m in re.finditer(r"\bsrc\s*=\s*[\"']?\s*(?:https?:)?//|url\(\s*[\"']?\s*(?:https?:)?//|http://", html, re.I):
        rep.add("error", "external-url", f"external or http URL near {html[m.start():m.start() + 40]!r}")
        break
    if re.search(r"data:image/svg", html, re.I):
        rep.add("error", "svg-data-image", "data: SVG images are out; inline the <svg> element instead")
    for fam in re.findall(r"font-family\s*:\s*([^;}]+)", css, re.I):
        for name in (f.strip().strip("'\"").lower() for f in fam.split(",")):
            if name and name not in GENERIC_FONTS and not name.startswith("var("):
                rep.add("error", "font-name", f"font {name!r} is removed; use system-ui/ui-* families")
    rules = len(re.findall(r"\{", re.sub(r"@(media|supports)[^{]*\{", "", css)))
    if rules > 400:
        rep.add("error", "css-rules", f"{rules} CSS rules > 400")
    if len(re.findall(r"@keyframes", css)) > 32:
        rep.add("error", "css-rules", "more than 32 @keyframes")
    markup = _SCRIPT.sub("", _STYLE.sub("", html))
    nodes = len(re.findall(r"<[a-zA-Z]", markup)) + len(re.findall(r">[^<\s][^<]*<", markup))
    if nodes > 2000:
        rep.add("error", "nodes", f"about {nodes} static nodes > 2000")

    if compressed is not None and compressed > BUDGET:
        rep.add("warn", "budget", f"{compressed} compressed bytes > {BUDGET} working budget (hard limit 4096)")
    for c in _COLOR.findall(_strip_allowed_colors(css)):
        if not _neutral(c) and c.lower() not in allowed_colors:
            rep.add("warn", "raw-color", f"hard-coded colour {c} without a theme variable")
    if re.search(r"safe-area-inset-bottom", css) and not re.search(r"body\s*\{[^}]*padding\s*:\s*0", css):
        rep.add("warn", "double-band", "pads for the time band but body keeps its default padding")
    if re.search(r"\.request\s*\(|K\.ask\s*\(", js):
        kit = "K.ask" in js and "RATE_LIMITED" in html
        if not kit and not all(code in html for code in ("TIMEOUT", "RATE_LIMITED", "BUSY")):
            rep.add("warn", "request-errors", "requests without visible TIMEOUT/RATE_LIMITED/BUSY outcomes")
    if re.search(r"\b(chatData|publicData)\b", js) and not re.search(r"(chat|public)DataChanged", js):
        rep.add("warn", "state-events", "reads state but never listens for chatDataChanged/publicDataChanged")
    if "TelegramWidget" in js and not re.search(r"window\.TelegramWidget", js):
        rep.add("warn", "no-guard", "use window.TelegramWidget and check it: undefined outside Telegram")
    if "pointermove" in js and not re.search(r"touch-action\s*:\s*(pan-y|none)", html):
        rep.add("warn", "drag-claim", "pointermove without touch-action: pan-y|none - the chat takes the drag")
    if re.search(r"@keyframes|transition\s*:|\.animate\(", html) and "prefers-reduced-motion" not in html:
        rep.add("warn", "reduced-motion", "motion without a prefers-reduced-motion rule")
    if "setResizeAnchor" in js and "typeof" not in js:
        rep.add("warn", "resize-anchor", "check typeof TelegramWidget.setResizeAnchor === 'function'")
    if "localStorage" in js and "try" not in js:
        rep.add("warn", "storage-try", "localStorage.setItem can throw QuotaExceededError")
    heavy = len(re.findall(r"opacity\s*:\s*0?\.\d|filter\s*:|box-shadow\s*:[^;}]*\d+px\s+\d+px\s+[1-9]", css))
    if heavy > 16:
        rep.add("warn", "heavy", f"{heavy} heavy declarations; at most 16 heavy elements may be on screen")
    if not caption:
        rep.add("warn", "caption-mirror", "no caption: the chat list, notifications and old apps show only it")
    if re.search(r"pointerdown[\"']?\s*(,|=)[^}]*?(\.request\s*\(|K\.ask\s*\()", js):
        rep.add("warn", "tap-request", "request from a pointerdown handler; call it from click or pointerup")
    if re.search(r"\.innerHTML\s*\+?=[^;]*(chatData|publicData|\.result\b|K\.S\b)", js):
        rep.add("warn", "innerhtml-state", "state or answers rendered with innerHTML; use textContent")
    if (re.search(r"\.arc\s*\([^)]*,\s*(6\.[3-9]\d*|[7-9](\.\d+)?)\s*[,)]", js)
            or re.search(r"\.rect\s*\([^)]*\)\s*;?\s*\w+\.arc\s*\(", js)):
        rep.add("warn", "canvas-arc", "arc end past 2*pi or rect() then arc() in one path; use Math.PI*2, "
                "moveTo before arc, and dim-clip-redraw for cut-outs")
    return rep
