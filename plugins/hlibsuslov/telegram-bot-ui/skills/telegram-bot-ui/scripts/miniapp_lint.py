#!/usr/bin/env python3
# run-checks: examples/mini-apps --strict
"""Lint a Telegram Mini App's source for security mistakes, non-native patterns and AI-slop.

  py -3 scripts/miniapp_lint.py examples/mini-apps            # a folder (html, css, js, ts, jsx, tsx, py)
  py -3 scripts/miniapp_lint.py app/index.html app/style.css   # files
  py -3 scripts/miniapp_lint.py examples/mini-apps --json      # machine-readable
  py -3 scripts/miniapp_lint.py examples/mini-apps --strict    # warnings fail too

Pattern-based and offline. A clean report is evidence for the static contract only, never proof that
real Telegram clients render the app as intended. Files under a `server/` or `bot/` folder and `.py`
files count as server code; the rest is client code. `dist/` and `node_modules/` are skipped.

Rules (G = Telegram design guidelines rule, S = security.md, A = anti-slop.md; every rule is explained
in references/mini-apps/anti-slop.md#linter-rules):
  errors
    MA01 bot-token        S   a bot token or BOT_TOKEN in client code
    MA02 unsafe-server    S   initDataUnsafe read in server code: verify initData instead
    MA03 native-dialog    G3  alert() / confirm() / prompt(): use showAlert / showConfirm / showPopup
    MA04 script-order     G8  telegram-web-app.js missing from <head>, or another script runs before it
  warnings
    MA05 raw-color        G1  colour literal outside a var() fallback, light-dark(), a --tma-fb-* palette or a neutral alpha grey
    MA06 vh               G2  100vh / dvh / svh outside a var(--tg-viewport-*) fallback
    MA07 fixed-cta        G3  own fixed bottom button: use the MainButton (mark a browser fallback data-tma-fallback)
    MA08 safe-area        G6  requestFullscreen without --tg-safe-area / --tg-content-safe-area insets in CSS
    MA09 transition-all   G4  transition: all, animate-pulse, animate-ping
    MA10 infinite         G4  an infinite animation on something that is not a loader
    MA11 gradient-text    A   background-clip: text
    MA12 glass-fallback   A   backdrop-filter without a reduced-transparency or @supports fallback
    MA13 emoji-ui         A   any Unicode emoji in visible markup or in a UI string; only "⭐ 250" in plain-text-only
                              surfaces (MainButton text, popups) is allowed: markup draws the Stars sign as an SVG
    MA14 local-storage    S   localStorage / sessionStorage: CloudStorage / DeviceStorage, secrets in SecureStorage
    MA15 version-gate     G3  a Telegram.WebApp member newer than 6.0 used with no isVersionAtLeast in the file
    MA16 web-font         A   @font-face or a web-font CDN for UI text: system font
    MA17 reduced-motion   G4  motion in CSS and no prefers-reduced-motion rule anywhere
    MA18 ready            G8  the app never calls ready()
    MA19 own-back         G3  history.back(), an own back button or an own sticky / fixed top bar: BackButton, Telegram's header
    MA20 web-login        S   "Login with Telegram" widget inside a Mini App: initData already identifies the user
    MA21 hover-only       G2  content revealed on :hover only
    MA22 small-text       G5  font-size below 11 px
    MA23 viewport-meta    G2  HTML entry without <meta name="viewport">
    MA24 label            G5  <input> without a label or aria-label, <img> without alt
    MA25 pay-form         P   own card fields (autocomplete cc-*, card number / CVV inputs): the provider's sheet collects cards
  payment warnings (P = references/mini-apps/payments.md)
    MA26 client-price     P   price / amount / total sent to a checkout, invoice or order endpoint: the server prices the cart
    MA27 paid-unlock      P   unlocking on invoice status "paid" without asking the server (watchOrder or /orders)
  Telegram's own elements (T = references/mini-apps/telegram-elements.md)
    MA28 currency-label   T   "XTR", "Toncoin" or "12 TON" shown to users: "⭐ 250", "12 GRAM"
    MA29 trust-mark       T   an own verified / Premium badge (class, id, aria-label, title): Telegram draws those (error)
  rework tells (R = references/mini-apps/rework.md)
    MA30 nav-drawer       R   hamburger, drawer or sidebar navigation: a tab bar (2-5) and BackButton
    MA31 hype-copy        R   greetings, "!" in headings and buttons, hype words: plain statements
    MA32 glow             R   coloured glow shadows (blur >= 20 px) or :hover scale effects
    MA33 client-identity  S   initDataUnsafe sent to the server: send the raw initData (Authorization: tma <initData>) (error)
    MA34 caps-label       R   uppercase labels with letter-spacing: sentence case in the type roles
    MA35 nested-surface   R   a surface inside a surface (card in card, list in card, tinted box in a card): one level
  device (D = references/mini-apps/haptics-and-device.md)
    MA36 haptic-stream    D   haptics inside scroll / pointermove / input handlers or timers: one haptic per user moment
    MA37 sensor-stop      D   a motion sensor or tma.motion() started and never stopped in the file: battery and privacy
  accessibility and language (L = references/mini-apps/accessibility-and-language.md)
    MA38 icon-name        L   a button or link with only an icon inside and no aria-label: screen readers say "button"
    MA39 physical-side    L   margin / padding -left / -right, text-align or float left / right: logical properties mirror in RTL
  forms (F = references/mini-apps/forms-and-data.md)
    MA40 number-input     F   type="number": text + inputmode="decimal" / "numeric" (comma locales, codes, screen readers)
    MA41 autofocus        F   autofocus on a field: the keyboard covers the screen before the user has seen it
  decoration in place of structure (A)
    MA42 side-stripe      A   a coloured border of 2 px or more on one side of a card, row or callout
    MA43 hard-shadow      A   an offset shadow with no blur (4px 4px 0): a costume, not depth
    MA44 eyebrow          A   an eyebrow / kicker / overline label above a heading: the heading alone
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REF = "references/mini-apps/anti-slop.md#linter-rules"
EXTS = (".html", ".htm", ".css", ".js", ".mjs", ".ts", ".tsx", ".jsx", ".py")
SKIP = {"dist", "node_modules", ".git", "__pycache__"}
RULES = {
    "MA01": ("error", "bot-token"), "MA02": ("error", "unsafe-server"), "MA03": ("error", "native-dialog"),
    "MA04": ("error", "script-order"), "MA05": ("warn", "raw-color"), "MA06": ("warn", "vh"),
    "MA07": ("warn", "fixed-cta"), "MA08": ("warn", "safe-area"), "MA09": ("warn", "transition-all"),
    "MA10": ("warn", "infinite"), "MA11": ("warn", "gradient-text"), "MA12": ("warn", "glass-fallback"),
    "MA13": ("warn", "emoji-ui"), "MA14": ("warn", "local-storage"), "MA15": ("warn", "version-gate"),
    "MA16": ("warn", "web-font"), "MA17": ("warn", "reduced-motion"), "MA18": ("warn", "ready"),
    "MA19": ("warn", "own-back"), "MA20": ("warn", "web-login"), "MA21": ("warn", "hover-only"),
    "MA22": ("warn", "small-text"), "MA23": ("warn", "viewport-meta"), "MA24": ("warn", "label"),
    "MA25": ("error", "pay-form"), "MA26": ("warn", "client-price"), "MA27": ("warn", "paid-unlock"),
    "MA28": ("warn", "currency-label"), "MA29": ("error", "trust-mark"),
    "MA30": ("warn", "nav-drawer"), "MA31": ("warn", "hype-copy"), "MA32": ("warn", "glow"),
    "MA33": ("error", "client-identity"), "MA34": ("warn", "caps-label"), "MA35": ("warn", "nested-surface"),
    "MA36": ("warn", "haptic-stream"), "MA37": ("warn", "sensor-stop"),
    "MA38": ("warn", "icon-name"), "MA39": ("warn", "physical-side"),
    "MA40": ("warn", "number-input"), "MA41": ("warn", "autofocus"),
    "MA42": ("warn", "side-stripe"), "MA43": ("warn", "hard-shadow"), "MA44": ("warn", "eyebrow"),
}
TOKEN = re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b|\bBOT_TOKEN\b|\bTELEGRAM_BOT_TOKEN\b")
COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?|oklch|oklab|lab|lch)\([^)]*\)")
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U0001F000-\U0001F2FF\u2600-\u27BF\u2B50\u2B55]")
# "XTR 250", "250 XTR", "Toncoin" (not "formerly Toncoin"), "12.5 TON": names users should not see on screen
CURRENCY_SHOWN = re.compile(r"\bXTR\s*\d|\d[\d.,\s]*XTR\b|(?<!formerly )\bToncoin\b|\d[\d.,]*\s*TON\b")
TRUST_MARK = re.compile(r"(?:\bclass|\bid|className)\s*[=:]\s*[\"'`][^\"'`]*\b(?:verified|verification|premium)[-_]?(?:badge|mark|check|tick|icon)\b"
                        r"|(?:aria-label|title)\s*=\s*[\"'](?:verified|premium)\b", re.I)
NAV_DRAWER = re.compile(r"(?:\bclass|\bid|className)\s*[=:]\s*[\"'`][^\"'`]*\b(?:hamburger|burger|drawer|sidebar|side-menu|offcanvas|off-canvas|nav-toggle)\b|☰", re.I)
HYPE = re.compile(r"\b(?:welcome back|hey there|unleash|crush it|supercharge|skyrocket|game[- ]?changer|next[- ]level|revolutioni[sz]e|ultimate|seamless(?:ly)?|effortless(?:ly)?|level up)\b|!!", re.I)
STARS_AMOUNT = re.compile(r"⭐️?\s*(?:\d|\$\{)")  # the Telegram Stars currency sign before an amount is not decoration
TG_SCRIPT = re.compile(r"<script\b[^>]*\bsrc=[\"']https://telegram\.org/js/telegram-web-app\.js", re.I)
STYLE_BLOCK = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
COMMENT_CSS = re.compile(r"/\*.*?\*/", re.S)
COMMENT_JS = re.compile(r"/\*.*?\*/|(?<![:\"'\\])//[^\n]*", re.S)


@dataclass
class Finding:
    rule: str
    level: str
    name: str
    file: str
    line: int
    msg: str

    def text(self) -> str:
        return f"{self.file}:{self.line}: [{self.rule} {self.name}] {self.msg}"


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "warn"]


def gated_members() -> dict[str, str]:
    """Method and object names of Telegram.WebApp newer than 6.0, from the offline catalog."""
    try:
        import webapp_lookup
        api = webapp_lookup.WebAppApi()
    except (OSError, ImportError, ValueError):
        return {}
    out = {}
    for key, ver in api.gates().items():
        m = api.cat["members"][key]
        if m["owner"] == "WebApp" and m["kind"] in ("method", "object"):
            out[m["name"]] = ver
    out["SecondaryButton"] = "7.10"
    return out


def _line(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _strip_allowed_colors(css: str) -> str:
    """Blank out theme-safe colour spots (var() fallbacks, light-dark(), --tma-fb-* / --fb-* values) keeping offsets."""
    chars = list(css)

    def blank(a: int, b: int) -> None:
        for i in range(a, b):
            if chars[i] != "\n":
                chars[i] = " "

    for m in re.finditer(r"\b(var|light-dark)\(", css):
        depth, j = 0, m.end() - 1
        while j < len(css):
            if css[j] == "(":
                depth += 1
            elif css[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if m.group(1) == "var":
            comma = css.find(",", m.end(), j)
            if comma > 0:
                blank(comma, j)
        else:
            blank(m.start(), j)
    for m in re.finditer(r"--(?:tma-fb|fb)-[\w-]+\s*:[^;}]*", css):
        blank(m.start(), m.end())
    return "".join(chars)


def _neutral(color: str) -> bool:
    m = re.match(r"rgba?\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)\s*(?:[/,]\s*([\d.]+%?))?\s*\)", color)
    if not m or not m.group(4):
        return False
    alpha = float(m.group(4).rstrip("%")) / (100 if m.group(4).endswith("%") else 1)
    return m.group(1) == m.group(2) == m.group(3) and alpha < 1


SURFACE = re.compile(r"(?:^|\s)(?:tma-card|tma-list|tma-kv|tma-plan|[\w-]*card(?:-inner)?|[\w-]*panel|[\w-]*surface|[\w-]*-box)(?=\s|$)")


def nested_surfaces(text: str) -> list[tuple[int, str, str]]:
    """(offset, outer class, inner class) for each element with a surface class inside another one."""
    from html.parser import HTMLParser

    found: list[tuple[int, str, str]] = []
    lines = [0]
    for ln in text.split("\n"):
        lines.append(lines[-1] + len(ln) + 1)

    class P(HTMLParser):
        stack: list[tuple[str, str | None]] = []

        def handle_starttag(self, tag, attrs):
            if tag in ("br", "img", "input", "meta", "link", "hr", "source", "use", "path", "circle", "rect"):
                return
            cls = dict(attrs).get("class") or ""
            m = SURFACE.search(cls)
            surf = m.group(0).strip() if m else None
            outer = next((c for _, c in reversed(self.stack) if c), None)
            if surf and outer:
                line, col = self.getpos()
                found.append((lines[line - 1] + col, outer, surf))
            self.stack.append((tag, surf))

        def handle_endtag(self, tag):
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    break

    p = P()
    p.stack = []
    p.feed(re.sub(r"<(script|style)\b.*?</\1>", lambda m: " " * len(m.group(0)), text, flags=re.S | re.I))
    return found


def _css_rules(css: str):
    for m in re.finditer(r"([^{}@;]+)\{([^{}]*)\}", css):
        yield m.group(1).strip(), m.group(2), m.start()


def is_server(path: str, root: str | None = None) -> bool:
    """Server code by folder name, judged on the path RELATIVE to the lint root (a project that itself lives
    under C:/work/api/... is not all server code)."""
    rel = os.path.relpath(path, root) if root else os.path.basename(path)
    parts = set(re.split(r"[\\/]", rel.lower())[:-1])
    return path.endswith(".py") or bool(parts & {"server", "bot", "api", "backend"})


def lint_files(paths: list[str], root: str | None = None) -> Report:
    rep = Report()
    files: dict[str, str] = {}
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as fh:
            files[p] = fh.read()
    gates = gated_members()

    def add(rule: str, path: str, text: str, pos: int, msg: str) -> None:
        level, name = RULES[rule]
        rel = os.path.relpath(path, root) if root else path
        rep.findings.append(Finding(rule, level, name, rel.replace(os.sep, "/"), _line(text, pos), msg))

    all_css, client_js = [], []
    uses_webapp = False
    calls_ready = False
    for path, text in files.items():
        ext = os.path.splitext(path)[1].lower()
        server = is_server(path, root)
        in_kit = "_kit" in re.split(r"[\\/]", os.path.relpath(path, root) if root else path)
        css_parts: list[tuple[str, int]] = []
        if ext == ".css":
            css_parts.append((text, 0))
        if ext in (".html", ".htm"):
            css_parts += [(m.group(1), m.start(1)) for m in STYLE_BLOCK.finditer(text)]
        js = text if ext in (".js", ".mjs", ".ts", ".tsx", ".jsx") else ""
        if ext in (".html", ".htm"):
            # keep inline script bodies at their offsets so findings report the right line
            keep = [m.span(1) for m in re.finditer(r"<script\b(?![^>]*\bsrc=)[^>]*>(.*?)</script>", text, re.S | re.I)]
            chars = [" " if c != "\n" else c for c in text]
            for a, b in keep:
                chars[a:b] = text[a:b]
            js = "".join(chars) if keep else ""
        code = COMMENT_JS.sub(lambda m: " " * len(m.group(0)), js) if js else ""
        if "Telegram.WebApp" in text or "createTma" in text or "@tma.js" in text:
            uses_webapp = uses_webapp or not server
        # the kit's own tg.ready() wrapper does not count: the app must call it (tma.ready() / WebApp.ready())
        if not in_kit and re.search(r"\.ready\s*\(\s*\)", code):
            calls_ready = True

        # ---- security
        if not server and ext != ".py":
            for m in TOKEN.finditer(text):
                add("MA01", path, text, m.start(), "bot token in client code: it stays on the server, read from the environment")
                break
        if server:
            for m in re.finditer(r"initDataUnsafe", text):
                add("MA02", path, text, m.start(), "server reads initDataUnsafe; verify the raw initData (HMAC or Ed25519) and use that")
                break
        if code and not server:
            for m in re.finditer(r"(?<![\w.])(?:window\.)?(alert|confirm|prompt)\s*\(", code):
                if re.search(r"function\s+$", code[max(0, m.start() - 12):m.start()]):
                    continue  # a declaration (the kit's own confirm wrapper), not the browser dialog
                add("MA03", path, text, m.start(), f"{m.group(1)}() blocks the WebView; use showAlert / showConfirm / showPopup")
            for m in re.finditer(r"\b(localStorage|sessionStorage)\b", code):
                add("MA14", path, text, m.start(), f"{m.group(1)}: user data in CloudStorage / DeviceStorage, tokens in SecureStorage or memory")
                break
            for m in re.finditer(r"history\.back\s*\(", code):
                add("MA19", path, text, m.start(), "history.back(): drive Telegram's BackButton from one navigation stack")
            client_js.append((path, code))
        if not server and ext in (".html", ".htm", ".js", ".mjs", ".ts", ".tsx", ".jsx"):
            card = re.search(r"autocomplete\s*=\s*[\"']cc-|\b(name|id)\s*=\s*[\"'][^\"']*(card-?number|cardnumber|\bcvv\b|\bcvc\b)", text, re.I)
            if card:
                add("MA25", path, text, card.start(), "own card fields: open the server's invoice link with openInvoice")
        if code and not server:
            m = re.search(r"fetch\(\s*[`'\"][^`'\"]*(checkout|invoice|orders?)\b[^`'\"]*[`'\"]\s*,\s*\{.{0,400}?\b(price|amount|total)\b\s*:",
                          code, re.S | re.I)
            if m:
                add("MA26", path, text, m.start(), f"'{m.group(2)}' sent to a {m.group(1)} endpoint: send ids and quantities, price on the server")
            paid = re.search(r"(===?|==)\s*['\"]paid['\"]|['\"]paid['\"]\s*(===?|==)", code)
            if paid and not re.search(r"watchOrder|/orders?\b|orderStatus|getOrder", code):
                add("MA27", path, text, paid.start(), "invoice status 'paid' is a hint: ask the server for the order before unlocking")
        # ---- rework tells: navigation drawers, hype copy, the user's identity taken from the client
        if not server and ext in (".html", ".htm", ".js", ".mjs", ".ts", ".tsx", ".jsx"):
            nav = NAV_DRAWER.search(text)
            if nav:
                add("MA30", path, text, nav.start(), "hamburger / drawer navigation: a tab bar (2-5 roots) and BackButton for depth")
        if not server and ext in (".html", ".htm"):
            hits = 0
            for m in re.finditer(r"<(h[1-6]|button|a|p|span|div|small|li)\b[^>]*>([^<]*)", text, re.I):
                words = m.group(2)
                why = HYPE.search(words)
                if not why and m.group(1).lower() in ("h1", "h2", "h3", "h4", "h5", "h6", "button") and "!" in words:
                    why = re.search("!", words)
                if why:
                    add("MA31", path, text, m.start(), f"{words.strip()[:40]!r}: plain statement, no greetings, hype or exclamation marks")
                    hits += 1
                    if hits == 5:
                        break
        if code and not server:
            ident = re.search(r"(?:JSON\.stringify|body\s*:)[^;\n]{0,200}initDataUnsafe", code)
            if ident:
                add("MA33", path, text, ident.start(), "initDataUnsafe sent to the server: send the raw initData and verify it there (security.md)")
        # ---- forms: number inputs and autofocus (markup and JSX / template strings)
        if not server and not in_kit and ext in (".html", ".htm", ".js", ".mjs", ".ts", ".tsx", ".jsx"):
            num = re.search(r"<input\b[^>]*\btype\s*=\s*[{\"']*number\b", text, re.I) \
                or re.search(r"\btype\s*:\s*['\"]number['\"]", text)
            if num:
                add("MA40", path, text, num.start(), "type=\"number\": type=\"text\" with inputmode=\"decimal\" or \"numeric\", "
                    "parsed with the user's locale")
            af = re.search(r"<(?:input|textarea|select)\b[^>]*\bautoFocus?\b", text, re.I)
            if af:
                add("MA41", path, text, af.start(), "autofocus opens the keyboard over the screen on launch: focus on the user's tap")

        # ---- device: haptics in streams of events, sensors left running
        if code and not server:
            stream = re.search(r"(?:addEventListener\(\s*['\"](?:scroll|wheel|pointermove|mousemove|touchmove|input|resize)['\"]|\bon(?:scroll|pointermove|mousemove|touchmove|input)\s*=|setInterval\s*\(|requestAnimationFrame\s*\()"
                               r"(?:[^\n]|\n[ \t]+){0,240}?(?:impactOccurred|notificationOccurred|selectionChanged|haptic\.(?:tap|impact|select|notify|success|warning|error))", code)
            if stream:
                add("MA36", path, text, stream.start(), "haptic inside a scroll / move / input handler or a timer: play it once per user moment")
            started = re.search(r"(?:Accelerometer|Gyroscope|DeviceOrientation)\??\.start\s*\(|\bmotion\(\s*['\"](?:accelerometer|gyroscope|orientation)", code)
            if started and not in_kit and not re.search(r"(?:Accelerometer|Gyroscope|DeviceOrientation)\??\.stop\s*\(|\bstop\w*\s*\(\s*\)|\bstop\w*!?\(\)|stop\w*\?\.\(\)", code):
                add("MA37", path, text, started.start(), "a motion sensor starts and is never stopped: stop it when the screen closes")
        # ---- Telegram's own elements: currency names users see, marks only Telegram draws
        if not server and ext in (".html", ".htm"):
            shown = re.sub(r"<(script|style)\b.*?</\1>|<[^>]+>", lambda m: " " * len(m.group(0)), text, flags=re.S | re.I)
            for cur in list(CURRENCY_SHOWN.finditer(shown))[:10]:  # every occurrence: the baseline must count them all
                add("MA28", path, text, cur.start(), f"{cur.group(0).strip()!r} on screen: Stars as '⭐ 250', grams as '12 GRAM' (telegram-elements.md)")
        if code and not server:
            hits = 0
            # template literals may span lines; quoted strings may not
            for lit in re.finditer(r"`([^`]*)`|'([^'\n]*)'|\"([^\"\n]*)\"", code):
                body = next(g for g in lit.groups() if g is not None)
                for cur in list(CURRENCY_SHOWN.finditer(body)) + list(re.finditer(r"\}\s*(?:XTR|TON)\b", body)):
                    add("MA28", path, text, lit.start() + 1 + cur.start(), f"{cur.group(0).strip()!r} in a label: Stars as '⭐ 250', grams as '12 GRAM'")
                    hits += 1
                if hits >= 10:
                    break
            for cur in re.finditer(r"\+\s*['\"`]\s*(?:XTR|TON)\b", code):
                add("MA28", path, text, cur.start(), "a price glued to 'XTR' / 'TON': Stars as '⭐ 250', grams as '12 GRAM'")
        if not server and ext in (".html", ".htm", ".js", ".mjs", ".ts", ".tsx", ".jsx"):
            mark = TRUST_MARK.search(text)
            if mark:
                add("MA29", path, text, mark.start(), "own verified / Premium mark: Telegram draws trust marks; say it in text (telegram-elements.md T7-T8)")
        if not server and re.search(r"telegram-widget\.js|oauth\.telegram\.org|Login with Telegram", text, re.I):
            m = re.search(r"telegram-widget\.js|oauth\.telegram\.org|Login with Telegram", text, re.I)
            add("MA20", path, text, m.start(), "web login inside a Mini App: initData already identifies the user")

        # ---- HTML structure
        if ext in (".html", ".htm") and not server:
            head = text.split("</head>", 1)[0]
            uses = "Telegram.WebApp" in text or "./dist/" in text or re.search(r"<script\b[^>]*type=[\"']module", text)
            m = TG_SCRIPT.search(head)
            if uses and not m:
                add("MA04", path, text, 0, "telegram-web-app.js is not in <head>")
            elif m and re.search(r"<script\b", head[:m.start()], re.I):
                add("MA04", path, text, m.start(), "another <script> runs before telegram-web-app.js")
            if "<html" in text.lower() and not re.search(r'name=["\']viewport["\']', head, re.I):
                add("MA23", path, text, 0, "no <meta name=\"viewport\">")
            # every emoji in visible text, the Stars sign included: markup has the SVG glyph (.tma-star)
            visible = re.sub(r"<!--.*?-->|<(script|style)\b.*?</\1>|<[^>]+>", lambda m: " " * len(m.group(0)), text, flags=re.S | re.I)
            for n, m in enumerate(EMOJI.finditer(visible)):
                if n == 10:
                    break
                line = visible[visible.rfind("\n", 0, m.start()) + 1:visible.find("\n", m.start())].strip()
                add("MA13", path, text, m.start(), f"emoji {m.group(0)!r} in {line[:40]!r}: a kit line icon (open SVG set) or "
                    "text; the Stars sign is the .tma-star SVG")
            eyebrow = re.search(r"class\s*=\s*[\"'][^\"']*\b(?:eyebrow|kicker|overline|pretitle|supertitle)\b", text, re.I)
            if eyebrow:
                add("MA44", path, text, eyebrow.start(), "eyebrow label above a heading: delete it and let the heading speak")
            for pos, outer, inner in nested_surfaces(text)[:5]:
                add("MA35", path, text, pos, f"{inner!r} inside {outer!r}: one surface level; rows or plain content inside a card")
            own_back = re.search(r"history\.back\s*\(|<(?:button|a)\b[^>]*(?:class|id)=[\"'][^\"']*\b(?:back-btn|btn-back|back-button|nav-back)\b", text, re.I)
            if own_back:
                add("MA19", path, text, own_back.start(), "own back control: Telegram's BackButton, driven by one navigation stack")
            for m in re.finditer(r"<(button|a)\b([^>]*)>(.*?)</\1>", text, re.S | re.I):
                attrs, inner = m.group(2), m.group(3)
                if re.search(r"aria-label(?:ledby)?\s*=|\btitle\s*=", attrs, re.I) or "tma-sr-only" in inner \
                        or re.search(r"<img\b[^>]*\balt=[\"'][^\"']+", inner, re.I):
                    continue
                if re.search(r"<(?:svg|img|i|span)\b", inner, re.I) and not re.sub(r"<[^>]+>|&nbsp;|\s", "", inner):
                    add("MA38", path, text, m.start(), f"<{m.group(1)}> with only an icon: aria-label names the action "
                        "(\"Search\", \"Close\"), the icon gets aria-hidden=\"true\"")
            labels = set(re.findall(r"<label\b[^>]*\bfor=[\"']([^\"']+)", text, re.I))
            for m in re.finditer(r"<input\b([^>]*)>", text, re.I):
                attrs = m.group(1)
                if re.search(r"type=[\"'](hidden|submit|button)", attrs, re.I):
                    continue
                idm = re.search(r"\bid=[\"']([^\"']+)", attrs)
                wrapped = text.rfind("<label", 0, m.start()) > text.rfind("</label>", 0, m.start())
                if not (re.search(r"aria-label(ledby)?=", attrs) or (idm and idm.group(1) in labels) or wrapped):
                    add("MA24", path, text, m.start(), "<input> without a label, aria-label or aria-labelledby")
            for m in re.finditer(r"<img\b(?![^>]*\balt=)[^>]*>", text, re.I):
                add("MA24", path, text, m.start(), "<img> without alt (alt=\"\" for decoration)")
            if re.search(r"fonts\.googleapis\.com|fonts\.gstatic\.com|use\.typekit", text):
                m = re.search(r"fonts\.googleapis\.com|fonts\.gstatic\.com|use\.typekit", text)
                add("MA16", path, text, m.start(), "web font for UI text: Telegram's system font loads instantly and matches the client")

        # ---- emoji in UI strings (JS): only "⭐ <amount>" for plain-text surfaces (MainButton, popups)
        if code and not server and not in_kit and ".test." not in os.path.basename(path):  # the kit's starsText() builds the plain-text form
            hits = 0
            for lit in re.finditer(r"`([^`]*)`|'([^'\n]*)'|\"([^\"\n]*)\"", code):
                body = next(g for g in lit.groups() if g is not None)
                plain_surface = re.search(r"(?:\btext|message|title)\s*:\s*$|(?:setText|showAlert|showConfirm|showPopup)\s*\(\s*$",
                                          code[max(0, lit.start() - 40):lit.start()])
                e = EMOJI.search(body if not plain_surface else STARS_AMOUNT.sub("", body))
                if e:
                    add("MA13", path, text, lit.start(), f"emoji {e.group(0)!r} in a UI string {body.strip()[:30]!r}: an SVG icon in markup, "
                        "plain words in button text (iconCustomEmojiId 9.5 for a custom emoji)")
                    hits += 1
                    if hits == 10:
                        break

        # ---- CSS
        for css, offset in css_parts:
            clean = COMMENT_CSS.sub(lambda m: " " * len(m.group(0)), css)
            if not in_kit:
                for sel, body, pos in _css_rules(clean):
                    stripe = re.search(r"border-(?:left|right|inline-start|inline-end)\s*:\s*([2-9]|\d{2,})(?:\.\d+)?px\s+solid", body)
                    if stripe and re.search(r"card|item|row|cell|callout|alert|notice|note|quote|tip|warning", sel, re.I) \
                            and not re.search(r"quote|blockquote", sel, re.I):
                        add("MA42", path, text, offset + pos, f"side stripe on {sel.strip()[:40]!r}: a tag, an icon or the section header says what it is")
                    hard = re.search(r"box-shadow\s*:[^;]*?(?<![\d.])-?[1-9]\d*px\s+-?\d+px\s+0(?:px)?\s+(?!\d)", body)
                    if hard and "inset" not in hard.group(0):
                        add("MA43", path, text, offset + pos, f"hard offset shadow on {sel.strip()[:40]!r}: theme surfaces, or a soft shadow for floating things")
                for n, m in enumerate(re.finditer(r"(?<![-\w])(?:margin|padding)-(?:left|right)\s*:|\b(?:text-align|float)\s*:\s*(?:left|right)\b", clean)):
                    if n == 3:
                        break
                    add("MA39", path, text, offset + m.start(), f"{m.group(0).rstrip(':').strip()!r} stays put in Arabic, Hebrew and Persian: "
                        "margin-inline-start / -end, padding-inline-*, text-align: start / end")
            all_css.append(clean)
            # selectors are not colours (#add, #face): blank them, keep offsets
            no_selectors = re.sub(r"[^{}]*\{", lambda m: " " * (len(m.group(0)) - 1) + "{", clean)
            allowed = _strip_allowed_colors(no_selectors)
            for m in COLOR.finditer(allowed):
                if not _neutral(m.group(0)):
                    add("MA05", path, text, offset + m.start(), f"hard-coded colour {m.group(0)}: a --tg-theme-* role or a derived color-mix()")
            stripped_vh = re.sub(r"var\([^()]*(?:\([^()]*\)[^()]*)*\)", lambda m: m.group(0) if "100" not in m.group(0) else " " * len(m.group(0)), clean)
            for m in re.finditer(r"\b100[dsl]?vh\b", stripped_vh):
                add("MA06", path, text, offset + m.start(), "100vh jumps with Telegram's sheet: var(--tg-viewport-stable-height)")
            for sel, body, pos in _css_rules(clean):
                if re.search(r"position\s*:\s*fixed", body) and re.search(r"\bbottom\s*:", body) \
                        and re.search(r"btn|button|cta|checkout|submit|buy|pay", sel, re.I) and "data-tma-fallback" not in sel:
                    add("MA07", path, text, offset + pos, f"fixed bottom button {sel[:40]!r}: MainButton / SecondaryButton")
                if re.search(r"\binfinite\b", body) and not re.search(r"skeleton|spinner|shimmer|loading|loader|progress|spin|sparkle", sel, re.I):
                    add("MA10", path, text, offset + pos, f"infinite animation on {sel[:40]!r}: animate only live or loading things")
                if "tma-" not in sel and re.search(r"(^|[\s.#,>])(top-?bar|nav-?bar|app-?bar|app-header|site-header|header)\b", sel, re.I) \
                        and re.search(r"position\s*:\s*(sticky|fixed)", body) and re.search(r"\btop\s*:\s*0", body):
                    add("MA19", path, text, offset + pos, f"own top bar {sel[:40]!r}: Telegram draws the header; a large title in the page, BackButton for depth")
                if re.search(r"text-transform\s*:\s*uppercase", body) and re.search(r"letter-spacing\s*:\s*[.\d]", body):
                    add("MA34", path, text, offset + pos, f"uppercase tracked label {sel[:40]!r}: sentence case in caption or footnote")
                if ":hover" in sel and re.search(r"transform\s*:[^;]*scale", body):
                    add("MA32", path, text, offset + pos, f"{sel[:40]!r} scales on hover: touch has no hover; pressed state only")
                for sh in re.finditer(r"box-shadow\s*:([^;]*)", body):
                    lengths = re.sub(r"[\w-]+\([^()]*(?:\([^()]*\)[^()]*)*\)|#[0-9a-fA-F]{3,8}\b", " ", sh.group(1))
                    blur = [float(t[2]) for t in (re.findall(r"-?\d*\.?\d+", part) for part in lengths.split(",")) if len(t) >= 3]
                    tinted = [c for c in COLOR.findall(sh.group(1)) if not _neutral(c) and c.lower() not in ("#000", "#000000")]
                    tinted += re.findall(r"var\(--(?:tma-(?:accent|brand)|tg-theme-button-color)", sh.group(1))
                    if tinted and blur and max(blur) >= 20:
                        add("MA32", path, text, offset + pos, f"coloured glow on {sel[:40]!r}: flat surfaces, a hairline or a neutral shadow")
                        break
                if ":hover" in sel and re.search(r"(display\s*:\s*(block|flex|grid)|visibility\s*:\s*visible|opacity\s*:\s*1\b)", body):
                    add("MA21", path, text, offset + pos, f"{sel[:40]!r} reveals content on hover only; touch has no hover")
            for m in re.finditer(r"transition\s*:\s*all\b|transition-all\b|animate-(pulse|ping)\b", clean):
                add("MA09", path, text, offset + m.start(), f"{m.group(0)}: name the properties (transform, opacity, colour)")
            for m in re.finditer(r"background-clip\s*:\s*text", clean):
                add("MA11", path, text, offset + m.start(), "gradient text: emphasis by weight and size")
            if re.search(r"backdrop-filter", clean) and not re.search(r"prefers-reduced-transparency|@supports\s+not", clean):
                m = re.search(r"backdrop-filter", clean)
                add("MA12", path, text, offset + m.start(), "glass without a solid fallback for reduced transparency, Android LOW and no-blur WebViews")
            for m in re.finditer(r"@font-face", clean):
                add("MA16", path, text, offset + m.start(), "@font-face for UI text: system font (a brand face only on one moment)")
            for m in re.finditer(r"font-size\s*:\s*(\d+(?:\.\d+)?)px", clean):
                if float(m.group(1)) < 11:
                    add("MA22", path, text, offset + m.start(), f"font-size {m.group(1)}px: nothing below 11 px")

    # ---- project-level checks
    css_all = "\n".join(all_css)
    js_all = "\n".join(c for _, c in client_js)
    if re.search(r"@keyframes|transition\s*:|animation\s*:", css_all) and "prefers-reduced-motion" not in css_all:
        path = next((p for p in files if p.endswith(".css")), next(iter(files), ""))
        if path:
            add("MA17", path, files[path], 0, "motion without a prefers-reduced-motion rule")
    if re.search(r"requestFullscreen\s*\(", js_all) and not re.search(r"--tg-(content-)?safe-area-inset|--tma-safe", css_all):
        path = next(p for p, c in client_js if "requestFullscreen" in c)
        add("MA08", path, files[path], files[path].find("requestFullscreen"), "fullscreen without safe-area and content-safe-area padding")
    if uses_webapp and not calls_ready:
        path = next((p for p, _ in client_js), next(iter(files), ""))
        if path:
            add("MA18", path, files[path], 0, "ready() is never called: Telegram shows its loading screen until the page fully loads")
    for path, code in client_js:
        # Gates: Telegram.WebApp.isVersionAtLeast, the kit's has('x.y'), @tma.js/sdk's isAvailable()/ifAvailable()
        if not gates or re.search(r"isVersionAtLeast|versionAtLeast|\bhas\(\s*['\"]\d|\.isAvailable\(\)|\.ifAvailable\(", code):
            continue
        used = sorted({m.group(1) for m in re.finditer(r"\.(" + "|".join(map(re.escape, gates)) + r")\b", code)})
        if used:
            add("MA15", path, files[path], files[path].find(used[0]),
                "ungated: " + ", ".join(f"{u} ({gates[u]})" for u in used[:6]) + " - older clients throw or ignore it")
    return rep


def collect(targets: list[str]) -> tuple[list[str], str | None]:
    files = []
    root = None
    for t in targets:
        if os.path.isdir(t):
            root = root or os.path.abspath(t)
            for dirpath, dirs, names in os.walk(t):
                dirs[:] = sorted(d for d in dirs if d not in SKIP)
                files += [os.path.join(dirpath, n) for n in sorted(names) if n.lower().endswith(EXTS)]
        elif os.path.isfile(t):
            files.append(t)
    return files, root


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Mini App lint (offline, pattern-based)")
    ap.add_argument("targets", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="warnings fail too")
    args = ap.parse_args(argv)
    targets = []
    skill = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for t in args.targets:  # run_checks passes skill-relative paths
        targets.append(t if os.path.exists(t) else os.path.join(skill, t))
    files, root = collect(targets)
    if not files:
        print("no Mini App files found")
        return 2
    rep = lint_files(files, root)
    if args.json:
        print(json.dumps({"files": len(files), "errors": [f.__dict__ for f in rep.errors],
                          "warnings": [f.__dict__ for f in rep.warnings], "reference": REF}, indent=1))
    else:
        for f in rep.findings:
            print(("ERROR " if f.level == "error" else "WARN  ") + f.text())
        print(f"{len(files)} file(s): {len(rep.errors)} error(s), {len(rep.warnings)} warning(s). Rules: {REF}")
    if rep.errors or (args.strict and rep.warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
