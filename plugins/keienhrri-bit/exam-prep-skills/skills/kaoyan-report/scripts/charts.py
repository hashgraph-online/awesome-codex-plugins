"""报告里的 SVG 图，配色与 report.css 一致。图模块里 `from charts import *`，再写 FIGS = {名字: 函数}。

例：
    from charts import *

    def score():
        return bars([("第 1 问", 4, ACC, " / 4"), ("第 2 问", 3, PART, " / 5")], vmax=6, ticks=[0, 2, 4, 6])

    FIGS = {"score": score}

正文里放 <!--FIG:score-->。
"""
from html import escape

__all__ = ["INK", "INK2", "MUTED", "HAIR", "ACC", "ACC_L", "REF", "PART", "GOOD", "BAD", "WARN", "t", "bars", "segments"]

INK, INK2, MUTED, HAIR, ACC, ACC_L, REF = "#1c1c1a", "#52514e", "#898781", "#e1e0d9", "#2a78d6", "#e6e5df", "#a3a29c"
PART, GOOD, BAD, WARN = "#b9d3f3", "#1baf7a", "#c23535", "#eda100"
FONT = 'font-family="Noto Sans SC, Noto Sans CJK SC, PingFang SC, Microsoft YaHei, sans-serif"'


def t(x, y, s, size=11, fill=INK, anchor="start", weight=None):
    w = f' font-weight="{weight}"' if weight else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}"{w}>{escape(str(s))}</text>'


def bars(rows, vmax, ticks, refs=(), unit="", label_w=150, fmt=lambda v: f"{v:g}"):
    """横条图。rows=(名, 值, 颜色, 备注[, (区间低, 区间高)])；refs=(值, 文字[, 'start'|'end'])画竖虚线。"""
    x0, W, step = label_w, 640 - label_w - 70, 30
    X = lambda v: x0 + W * v / vmax  # noqa: E731
    bottom = 18 + step * len(rows)
    o = [f'<svg viewBox="0 0 680 {bottom + 22}" xmlns="http://www.w3.org/2000/svg" {FONT}>']
    for v in ticks:
        o.append(f'<line x1="{X(v):.1f}" y1="14" x2="{X(v):.1f}" y2="{bottom}" stroke="{HAIR}"/>')
        o.append(t(X(v), bottom + 15, f"{v}{unit}", 10, MUTED, "middle"))
    for v, lab, *anc in refs:
        o.append(f'<line x1="{X(v):.1f}" y1="12" x2="{X(v):.1f}" y2="{bottom}" stroke="{INK}" stroke-width="1.1" stroke-dasharray="4 3"/>')
        a = anc[0] if anc else "middle"
        o.append(t(X(v) + {"end": -3, "start": 3}.get(a, 0), 9, lab, 9.5, INK, a))
    for i, (name, v, col, note, *rng) in enumerate(rows):
        y = 18 + i * step
        o.append(t(0, y + 13, name, 11, INK, weight=700))
        o.append(f'<rect x="{x0}" y="{y}" width="{max(X(v) - x0, 2):.1f}" height="17" rx="2" fill="{col}"/>')
        end = X(v)
        if rng:
            lo, hi = rng[0]
            ym = y + 8.5
            o.append(f'<line x1="{X(lo):.1f}" y1="{ym}" x2="{X(hi):.1f}" y2="{ym}" stroke="{INK}" stroke-width="1.2"/>')
            for xv in (lo, hi):
                o.append(f'<line x1="{X(xv):.1f}" y1="{ym - 5}" x2="{X(xv):.1f}" y2="{ym + 5}" stroke="{INK}" stroke-width="1.2"/>')
            end = max(end, X(hi))
        o.append(t(end + 6, y + 13, f"{fmt(v)}{unit}{note}", 10.5, INK))
    o.append("</svg>")
    return "\n".join(o)


def segments(parts, total, unit="", height=22):
    """一条分段横条（如考场 180 分钟怎么分）。parts=(起, 止, 文字, 颜色)。"""
    x0, W = 10, 660
    X = lambda v: x0 + W * v / total  # noqa: E731
    o = [f'<svg viewBox="0 0 680 {height + 36}" xmlns="http://www.w3.org/2000/svg" {FONT}>']
    for a, b, lab, col in parts:
        o.append(f'<rect x="{X(a) + 1:.1f}" y="4" width="{X(b) - X(a) - 2:.1f}" height="{height}" rx="2" fill="{col}"/>')
        o.append(t((X(a) + X(b)) / 2, 4 + height / 2 + 4, lab, 9.5, "#ffffff" if col in (ACC, INK, INK2) else INK, "middle", 700))
    for v in sorted({p[0] for p in parts} | {p[1] for p in parts}):
        o.append(t(X(v), height + 20, f"{v}{unit}", 9.5, MUTED, "middle"))
    o.append("</svg>")
    return "\n".join(o)
