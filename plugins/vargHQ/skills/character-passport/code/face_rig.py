"""Parametric SVG face rig driven by FACS action units (AU, 0..1).
Same face, same proportions, only the AUs change -> a consistent expression sheet.
Usage: python3 face_rig.py  -> writes face_sheet.svg (render to PNG with any headless browser).
Expression recipes follow the EMFACS prototypes for Ekman's basic emotions."""

EXPRESSIONS = {
    "neutral":   {},
    "happy":     {"AU6": 0.8, "AU12": 1.0, "AU25": 0.4},                       # cheek raiser + lip corner puller
    "sad":       {"AU1": 1.0, "AU4": 0.5, "AU15": 0.9, "AU17": 0.4},           # inner brow up + corners down
    "angry":     {"AU4": 1.0, "AU5": 0.4, "AU7": 0.8, "AU23": 0.8},            # brows down/in, lids tight, lips pressed
    "surprised": {"AU1": 1.0, "AU2": 1.0, "AU5": 1.0, "AU26": 1.0},            # brows up, lids wide, jaw drop
    "disgusted": {"AU9": 1.0, "AU10": 0.8, "AU15": 0.5, "AU4": 0.4, "AU7": 0.4},  # nose wrinkle + upper lip raise
}

SKIN, LINE, HAIR, IRIS, LIP = "#e9b99a", "#3a2a22", "#4a3426", "#5a7a52", "#b8615a"


def face(au, ox, oy):
    a = lambda k: au.get(k, 0.0)
    s = []
    # head, ears, hair: fixed geometry = the "model sheet" part that never changes
    s.append(f'<g transform="translate({ox},{oy})" stroke="{LINE}" stroke-width="3" stroke-linecap="round" fill="none">')
    for ex in (-118, 118):
        s.append(f'<ellipse cx="{ex}" cy="10" rx="18" ry="30" fill="{SKIN}"/>')
    s.append(f'<ellipse cx="0" cy="0" rx="115" ry="140" fill="{SKIN}"/>')
    s.append(f'<path d="M-114,-20 C-130,-200 130,-200 114,-20 C104,-86 64,-112 0,-110 C-64,-112 -104,-86 -114,-20Z" fill="{HAIR}"/>')

    # cheeks (AU6 pushes them up and makes them rounder)
    cy = 45 - 14 * a("AU6")
    for cx in (-62, 62):
        s.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{22 + 6 * a("AU6")}" ry="{12 + 5 * a("AU6")}" fill="#e79a86" stroke="none" opacity="{0.25 + 0.35 * a("AU6")}"/>')

    for side in (-1, 1):
        ex, ey = 45 * side, -10
        # eyelids: AU5 opens, AU7 tightens, AU6 pushes lower lid up
        up = 16 + 10 * a("AU5") - 8 * a("AU7") - 5 * a("AU6") - 4 * a("AU4")
        lo = 12 - 6 * a("AU6") - 4 * a("AU7") + 3 * a("AU5")
        w = 26
        s.append(f'<path d="M{ex - w},{ey} Q{ex},{ey - 2 * up} {ex + w},{ey} Q{ex},{ey + 2 * lo} {ex - w},{ey}Z" fill="#fff"/>')
        r = min(11, (up + lo) * 0.55)
        s.append(f'<circle cx="{ex}" cy="{ey + (lo - up) * 0.25}" r="{r:.1f}" fill="{IRIS}" stroke="none"/>')
        s.append(f'<circle cx="{ex}" cy="{ey + (lo - up) * 0.25}" r="{r * 0.45:.1f}" fill="#111" stroke="none"/>')
        s.append(f'<path d="M{ex - w - 2},{ey} Q{ex},{ey - 2 * up} {ex + w + 2},{ey}" stroke-width="4"/>')  # upper lid line

        # brows: AU1 raises inner end, AU2 raises outer end, AU4 lowers + pulls inner end toward the nose
        by = -52 - 10 * a("AU5")
        inner_x = ex - side * (22 - 8 * a("AU4"))
        inner_y = by - 24 * a("AU1") + 16 * a("AU4")
        outer_x = ex + side * 30
        outer_y = by - 14 * a("AU2") + 6 * a("AU1") * (1 - a("AU2")) - 4 * a("AU4")
        mid_y = (inner_y + outer_y) / 2 - 8 + 6 * a("AU1") * (1 - a("AU2"))
        s.append(f'<path d="M{inner_x},{inner_y} Q{ex},{mid_y} {outer_x},{outer_y}" stroke="#2a1b13" stroke-width="9"/>')
        if a("AU4") > 0.3:  # vertical frown lines between the brows
            s.append(f'<path d="M{side * 8},{by + 8} l{side * 2},14" stroke-width="2" opacity="{a("AU4")}"/>')

    # nose (AU9 adds wrinkle lines and lifts the wings)
    s.append(f'<path d="M-4,10 Q-14,{48 - 4 * a("AU9")} 0,{50 - 3 * a("AU9")} Q14,{48 - 4 * a("AU9")} 4,10" />')
    if a("AU9") > 0:
        for side in (-1, 1):
            s.append(f'<path d="M{side * 10},18 q{side * 8},-4 {side * 14},2" stroke-width="2" opacity="{a("AU9")}"/>')

    # mouth: corners (AU12 up, AU15 down), width (AU12, AU20 widen, AU23 narrow), opening (AU25, AU26), upper lip (AU10)
    my = 82 + 4 * a("AU17") - 4 * a("AU10")
    half = 36 + 10 * a("AU12") + 10 * a("AU20") - 10 * a("AU23")
    corner = my - 18 * a("AU12") + 16 * a("AU15")
    open_ = 4 * a("AU25") + 28 * a("AU26") + 10 * a("AU12") * a("AU25")
    upper = my - 6 * a("AU10") - 2 * a("AU17")
    lower = my + open_ + 10 * a("AU12") - 6 * a("AU15")
    if open_ > 1.5:
        s.append(f'<path d="M{-half},{corner} Q0,{upper - 6 * a("AU10")} {half},{corner} Q0,{lower + open_ * 0.8} {-half},{corner}Z" fill="#6b2b2b" stroke-width="3"/>')
        if a("AU12") > 0.5:  # teeth show in a big smile
            s.append(f'<path d="M{-half * 0.7},{corner + 2} Q0,{upper + 4} {half * 0.7},{corner + 2} L{half * 0.6},{corner + 8} Q0,{upper + 12} {-half * 0.6},{corner + 8}Z" fill="#fff" stroke="none"/>')
    else:
        lip_w = 5 - 3 * a("AU23")
        s.append(f'<path d="M{-half},{corner} Q0,{(upper + lower) / 2 + 10 * a("AU12") - 8 * a("AU15")} {half},{corner}" stroke="{LIP}" stroke-width="{lip_w}"/>')
    if a("AU17") > 0.2:  # chin boss
        s.append(f'<path d="M-18,{my + 30} q18,-8 36,0" stroke-width="2" opacity="{a("AU17")}"/>')
    s.append("</g>")
    return "\n".join(s)


def sheet(cols=3, cw=320, ch=380):
    names = list(EXPRESSIONS)
    rows = (len(names) + cols - 1) // cols
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{cols * cw}" height="{rows * ch}" viewBox="0 0 {cols * cw} {rows * ch}">',
           f'<rect width="100%" height="100%" fill="#ece9e2"/>']
    for i, n in enumerate(names):
        x, y = (i % cols) * cw, (i // cols) * ch
        out.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" fill="{"#e2ded6" if (i % cols + i // cols) % 2 else "#ece9e2"}"/>')
        out.append(face(EXPRESSIONS[n], x + cw / 2, y + ch / 2 + 15))
        aus = " ".join(f"{k}{'' if v == 1 else f'({v})'}" for k, v in EXPRESSIONS[n].items()) or "all AU = 0"
        out.append(f'<text x="{x + 14}" y="{y + 26}" font-family="Helvetica, Arial" font-weight="700" font-size="16" letter-spacing="1.5" fill="#333">{n.upper()}</text>')
        out.append(f'<text x="{x + 14}" y="{y + ch - 14}" font-family="Menlo, monospace" font-size="11" fill="#666">{aus}</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    open("face_sheet.svg", "w").write(sheet())
    print("wrote face_sheet.svg")
