"""Data views for bot messages: tables, leaderboards, progress bars, KPI lines, and the split
of a long report or notification into self-describing parts (references/data-views.md).

Every function returns ready text (regular-message HTML) or Rich blocks; nothing is sent here.
Rules it enforces (status H = heuristic, API = Bot API limit):
* API   a regular message is 4096 UTF-16 units after parsing; a Rich Message 32768 chars and
        20 table columns. Parts are measured on the HTML source, which is never shorter than
        the parsed text, so a part that passes here passes in Telegram.
* H     a table splits only between rows; every part repeats the header and says "(2/3)";
        the summary goes first, so a reader who opens only part 1 knows the outcome.
* H     a monospace (<pre>) table aligns by display width: wide (CJK) chars and emoji count 2,
        combining marks 0. Emoji in <pre> still drift on some clients: keep statuses as words
        there, and put emoji marks in the non-monospace lines around it.
* H     numbers group thousands, align right, and keep one unit per column (in the header).
"""
from __future__ import annotations

import unicodedata
from typing import Any

from . import rich
from .text import escape_html, utf16_len

MESSAGE_LIMIT = 4096
RICH_LIMIT = rich.LIMITS["chars"]
ROWS_PER_RICH_PART = rich.LIMITS["blocks"] - 20   # table rows count as blocks (500 per message)
BARS = {"blocks": ("▰", "▱"), "bar": ("█", "░"), "dots": ("●", "○")}
MEDALS = ("🥇", "🥈", "🥉")
STATUS = {0: "🟢", 1: "🟡", 2: "🔴", 3: "⚪"}
GROUP = {"en": ",", "ru": " ", "uk": " ", "de": ".", "es": ".", "fr": " "}
DECIMAL = {"en": ".", "ru": ",", "uk": ",", "de": ",", "es": ",", "fr": ","}
CONTINUED = {"en": "continued", "ru": "продолжение", "uk": "продовження"}


# ------------------------------------------------------------------ atoms

def number(n: float | int, lang: str = "en", digits: int = 0) -> str:
    """1234567.8 -> '1,234,568' (en) / '1 234 568' (ru, narrow no-break space)."""
    sign = "−" if n < 0 else ""
    whole, _, frac = f"{abs(n):.{digits}f}".partition(".")
    sep = GROUP.get(lang, ",")
    groups = []
    while len(whole) > 3:
        groups.insert(0, whole[-3:])
        whole = whole[:-3]
    groups.insert(0, whole)
    return sign + sep.join(groups) + (DECIMAL.get(lang, ".") + frac if frac else "")


def money(minor: int, currency: str, lang: str = "en", digits: int = 2) -> str:
    """Minor units -> '€12,400.50' (en) / '12 400,50 €' (ru). Stars and coins: digits=0."""
    sym = {"EUR": "€", "USD": "$", "GBP": "£", "RUB": "₽", "UAH": "₴", "XTR": "⭐", "TON": "TON"}.get(currency, currency)
    value = number(minor / 10 ** digits, lang, digits)
    return f"{sym}{value}" if lang == "en" and len(sym) == 1 and sym != "⭐" else f"{value} {sym}"


def delta(current: float, previous: float, lang: str = "en") -> str:
    """Change as '▲ 12%' / '▼ 3.5%' / '= 0%'; from zero: '▲ new'."""
    if previous == 0:
        return "= 0%" if current == 0 else ("▲ new" if current > 0 else "▼ new")
    pct = (current - previous) / abs(previous) * 100
    if round(pct, 1) == 0:
        return "= 0%"
    digits = 0 if abs(pct) >= 10 else 1
    return ("▲ " if pct > 0 else "▼ ") + number(abs(pct), lang, digits) + "%"


def progress(done: float, total: float, *, width: int = 10, style: str = "blocks", percent: bool = True) -> str:
    """'▰▰▰▰▱▱▱▱▱▱ 40%'. Never shows 100% before done == total, nor 0% once anything is done."""
    full, empty = BARS[style]
    width = max(3, min(width, 20))
    ratio = 0.0 if total <= 0 else max(0.0, min(done / total, 1.0))
    cells = round(ratio * width)
    if 0 < ratio < 1:
        cells = min(max(cells, 1), width - 1)
    pct = int(ratio * 100) if ratio < 1 else 100   # floor: 99.6% reads 99%, not a false 100%
    if 0 < ratio and pct == 0:
        pct = 1
    return full * cells + empty * (width - cells) + (f" {pct}%" if percent else "")


def sparkline(values: list[float]) -> str:
    """'▁▂▅▇▃' for a trend in one line of text; a flat series is a flat line, not noise."""
    if not values:
        return ""
    lo, hi = min(values), max(values)
    ticks = "▁▂▃▄▅▆▇█"
    if hi == lo:
        return ticks[3] * len(values)
    return "".join(ticks[round((v - lo) / (hi - lo) * 7)] for v in values)


def status(code: int, label: str) -> str:
    """'🟢 Paid' - the colour is never the only signal: the word stays."""
    return f"{STATUS.get(code, STATUS[3])} {label}"


def width(s: str) -> int:
    """Display width in a monospace block: wide and emoji 2, combining and joiners 0."""
    w = 0
    for ch in s:
        if unicodedata.combining(ch) or ch in "‍️︎":
            continue
        cp = ord(ch)
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") or 0x1F300 <= cp <= 0x1FAFF else 1
    return w


def _pad(s: str, n: int, right: bool) -> str:
    gap = " " * max(0, n - width(s))
    return gap + s if right else s + gap


def _clip(s: str, n: int) -> str:
    if width(s) <= n:
        return s
    out = ""
    for ch in s:
        if width(out + ch) > n - 1:
            break
        out += ch
    return out + "…"


# ------------------------------------------------------------------ tables

def mono_lines(header: list[str], rows: list[list[str]], *, right: frozenset[int] = frozenset(),
               max_col: int = 18, gap: int = 2) -> list[str]:
    """A space-aligned table for <pre>: header, a rule, rows. Cells are clipped to max_col."""
    data = [[_clip(str(c), max_col) for c in r] for r in [header, *rows]]
    widths = [max(width(r[i]) for r in data) for i in range(len(header))]
    line = lambda r: (" " * gap).join(_pad(c, widths[i], i in right) for i, c in enumerate(r)).rstrip()  # noqa: E731
    return [line(data[0]), "─" * (sum(widths) + gap * (len(widths) - 1)), *(line(r) for r in data[1:])]


def _title(title: str, i: int, n: int, lang: str) -> str:
    if n == 1:
        return f"<b>{escape_html(title)}</b>"
    more = f" · {CONTINUED.get(lang, CONTINUED['en'])}" if i else ""
    return f"<b>{escape_html(title)}</b> ({i + 1}/{n}){more}"


def table_parts(title: str, header: list[str], rows: list[list[Any]], *, summary: str = "", footer: str = "",
                right: frozenset[int] = frozenset(), lang: str = "en", limit: int = MESSAGE_LIMIT,
                max_col: int = 18) -> list[str]:
    """The fallback rung (no Rich Messages: Bot API below 10.1, an SDK without sendRichMessage, a
    surface that takes only regular text): the table as regular HTML messages with a <pre> grid. One part when it fits; otherwise parts that
    break between rows, each with the title "(i/n)" and the header repeated. `summary` (HTML) goes
    on part 1 above the table, `footer` (HTML: totals, legend, next step) on the last part."""
    cells = [[str(c) for c in r] for r in rows]
    lines = mono_lines(header, cells, right=right, max_col=max_col)
    head, body = lines[:2], lines[2:]

    def render(chunk: list[str], i: int, n: int) -> str:
        top = [_title(title, i, n, lang)] + ([summary] if summary and i == 0 else [])
        pre = "<pre>" + escape_html("\n".join(head + chunk)) + "</pre>"
        return "\n".join(top + [pre] + ([footer] if footer and i == n - 1 else []))

    # Pack greedily with the worst-case title "(99/99) · continued"; then renumber.
    chunks: list[list[str]] = []
    cur: list[str] = []
    for ln in body:
        if cur and utf16_len(render(cur + [ln], 1, 99)) + utf16_len(footer) + utf16_len(summary) > limit:
            chunks.append(cur)
            cur = []
        cur.append(ln)
    chunks.append(cur)
    n = len(chunks)
    parts = [render(c, i, n) for i, c in enumerate(chunks)]
    if any(utf16_len(p) > limit for p in parts):
        raise ValueError("one row with the header, summary and footer is longer than the limit: "
                         "shorten the summary or cells, or send the report as a file")
    return parts


def rich_table_parts(title: str, header: list[str], rows: list[list[Any]], *, summary: str = "", footer: str = "",
                     numeric: frozenset[int] = frozenset(), compact: bool | None = None, lang: str = "en",
                     limit: int = RICH_LIMIT) -> list[list[dict[str, Any]]]:
    """The default: a table as Rich Message blocks (sendRichMessage, references/tables.md). Over 20
    columns is refused (transpose or split by columns); a long table splits between rows (also by
    the 500-block limit: every row is a block) with the heading "(i/n)" and the header repeated.
    `summary` (plain text) is a paragraph on part 1, `footer` one on the last part."""
    if len(header) > rich.LIMITS["table_columns"]:
        raise ValueError(f"{len(header)} columns: Rich tables take {rich.LIMITS['table_columns']}; transpose or split")
    compact = len(header) >= 4 if compact is None else compact
    cells = [[str(c) for c in r] for r in rows]
    fixed = len(title) + len(summary) + len(footer) + 64
    size = lambda rs: sum(len(c) + 1 for r in [header, *rs] for c in r) + fixed  # noqa: E731
    chunks: list[list[list[str]]] = []
    cur: list[list[str]] = []
    for r in cells:
        if cur and (size(cur + [r]) > limit or len(cur) + 2 > ROWS_PER_RICH_PART):
            chunks.append(cur)
            cur = []
        cur.append(r)
    chunks.append(cur)
    n = len(chunks)
    more = CONTINUED.get(lang, CONTINUED["en"])
    parts = []
    for i, c in enumerate(chunks):
        head = title if n == 1 else f"{title} ({i + 1}/{n})" + (f" · {more}" if i else "")
        blocks: list[dict[str, Any]] = [{"type": "heading", "size": 3, "text": head}]
        if summary and i == 0:
            blocks.append({"type": "paragraph", "text": summary})
        blocks.append(rich.table(header, c, compact=compact, numeric_cols=numeric))
        if footer and i == n - 1:
            blocks.append({"type": "paragraph", "text": footer})
        parts.append(blocks)
    return parts


# ------------------------------------------------------------------ leaderboards, KPI

def leaderboard(entries: list[tuple[str, float]], *, me: str | None = None, top: int = 10, unit: str = "",
                lang: str = "en") -> str:
    """Ranked HTML lines: medals for 1-3, '#4' after, ties share a rank, the viewer in bold; when
    the viewer is below the top, a '⋯' gap and their own line. Names are escaped."""
    ranked = sorted(entries, key=lambda e: -e[1])
    lines, rank, prev = [], 0, None
    ranks: list[int] = []
    for i, (_, score) in enumerate(ranked):
        if score != prev:
            rank, prev = i + 1, score
        ranks.append(rank)

    def line(i: int) -> str:
        name, score = ranked[i]
        r = ranks[i]
        mark = MEDALS[r - 1] if r <= 3 else f"#{r}"
        text = f"{mark} {escape_html(name)} · {number(score, lang)}{(' ' + unit) if unit else ''}"
        return f"<b>{text}</b>" if name == me else text

    lines = [line(i) for i in range(min(top, len(ranked)))]
    mine = next((i for i, e in enumerate(ranked) if e[0] == me), None)
    if mine is not None and mine >= top:
        lines += ["⋯", line(mine)]
    return "\n".join(lines)


def kpi_lines(items: list[dict[str, Any]], lang: str = "en") -> str:
    """'Revenue: <b>€12,400</b> ▲ 8%' per item: {label, value (str), current?, previous?}."""
    out = []
    for it in items:
        d = f" {delta(it['current'], it['previous'], lang)}" if "current" in it and "previous" in it else ""
        out.append(f"{escape_html(it['label'])}: <b>{escape_html(str(it['value']))}</b>{d}")
    return "\n".join(out)
