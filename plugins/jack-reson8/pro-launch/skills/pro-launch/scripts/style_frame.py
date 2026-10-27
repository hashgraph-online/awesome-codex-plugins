#!/usr/bin/env python3
"""Style frames from REAL product renders + deliberate type (no code-drawn art), and ref-vs-frame comparisons.
Adapted from the Tutti launch-film keyframes (tutti-applemg/tools/keyframes.py) that Jack accepted.

  python3 style_frame.py frame   spec.json                 # render every frame in the spec
  python3 style_frame.py compare --ref ref.jpg --frame A.jpg --label "Apple · Hello, MacBook Neo" \
                                 --short "ref hero fills 60%, ours 38%" --short "..." --short "..." --out A-vs-ref.jpg
  python3 style_frame.py sheet   A.jpg B.jpg C.jpg --labels A B C --out pick.jpg     # side-by-side board for the user to pick

compare refuses to run with fewer than 3 --short lines: the "where it falls short" text is burned into the image (06b gate).
Spec (JSON): {"size":[1080,1920], "frames":[{"out":"docs/style-frames/A.jpg","bg":"#F5F5F7","layers":[...]}]}
Layer types (all coords in px of the frame; "x":"c" centres):
  image  {src, box:[x,y,w,h], radius:44, shadow:50, fit:"cover"|"contain"}       a real screenshot / render / photo
  grid   {srcs:[...], box:[x,y,w,h], cols:3, gap:18, radius:22}                    many real outputs at once
  pills  {srcs:[...], box:[x,y,w,h], heights:[0..1,...]}                           cover-cropped columns (EQ / light bars)
  text   {text, y, x:"c"|px|{r:px}, size, weight, color, font:path|"mono", lh}     SF Pro variable; CJK → Hiragino; "\n" = new line
  block  {box, bg, radius, border, pad, text, size, font, color, lh}               panel of real output set as type
  island {y:36, w:370, h:108}                                                     Dynamic Island capsule
  clock  {time:"9:41", date:"Saturday 24 October", y:220, color:"#FFF"}           lock-screen clock
  notif  {y, icon, app, title, body, dark:false}                                  notification banner (system chrome only)
System chrome (island/clock/notif) is layout, not art: icons and imagery inside it must still be real files.
"""
import argparse, json, os, re, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SF, CJK = "/System/Library/Fonts/SFNS.ttf", "/System/Library/Fonts/Hiragino Sans GB.ttc"
MONO = "/System/Library/Fonts/SFNSMono.ttf"
# Hiragino tops out at W6 and reads thin next to SF Heavy; prefer Noto Sans SC (OFL, variable 100-900) when installed:
# curl -L -o ~/Library/Fonts/NotoSansSC-VF.ttf "https://github.com/google/fonts/raw/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf"
NOTO = os.path.expanduser("~/Library/Fonts/NotoSansSC-VF.ttf")
CJK_W = {"Light": 300, "Regular": 400, "Medium": 500, "Semibold": 600, "Bold": 700, "Heavy": 900, "Black": 900}


def font(sz, weight="Bold", text="", path=None):
    if path == "mono" and not re.search(r"[぀-ヿ㐀-鿿가-힯]", text):
        f = ImageFont.truetype(MONO, sz)
        f.set_variation_by_name(weight if weight in ("Light", "Regular", "Medium", "Semibold", "Bold", "Heavy") else "Regular")
        return f
    if path and path != "mono":
        return ImageFont.truetype(path, sz)
    if re.search(r"[぀-ヿ㐀-鿿가-힯]", text) and os.path.exists(NOTO):
        f = ImageFont.truetype(NOTO, sz)
        f.set_variation_by_axes([CJK_W.get(weight, 700)])
        return f
    if re.search(r"[぀-ヿ㐀-鿿가-힯]", text):
        return ImageFont.truetype(CJK, sz, index=1 if weight in ("Semibold", "Bold", "Heavy", "Black") else 0)
    f = ImageFont.truetype(SF, sz)
    f.set_variation_by_name(weight)
    return f


def rgba(c, a=255):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def fit(im, w, h, mode="cover"):
    s = (max if mode == "cover" else min)(w / im.width, h / im.height)
    im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    if mode == "contain":
        return im
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def paste(cv, im, x, y, rad=0, shadow=0, sa=80):
    w, h = im.size
    if shadow:
        s = Image.new("RGBA", cv.size, (0, 0, 0, 0))
        ImageDraw.Draw(s).rounded_rectangle((x, y + shadow // 2, x + w, y + h + shadow // 2), rad, fill=(20, 20, 30, sa))
        cv.alpha_composite(s.filter(ImageFilter.GaussianBlur(shadow)))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w, h), rad, fill=255)
    im = im.convert("RGBA")
    im.putalpha(m)
    cv.alpha_composite(im, (x, y))


def text(cv, L):
    """One or more lines ("\n"); x: "c" centre, a number = left edge, or {"r": right edge}. lh = line height factor."""
    d, W = ImageDraw.Draw(cv), cv.width
    sz = L.get("size", 120)
    for i, ln in enumerate(L["text"].split("\n")):
        f = font(sz, L.get("weight", "Bold"), ln, L.get("font"))
        w = d.textlength(ln, font=f)
        x = L.get("x", "c")
        x = (W - w) / 2 if x == "c" else (x["r"] - w if isinstance(x, dict) else x)
        d.text((x, L["y"] + i * sz * L.get("lh", 1.25)), ln, font=f, fill=rgba(L.get("color", "#111111")))


def layer(cv, L):
    t, W = L["type"], cv.width
    if t == "image":
        x, y, w, h = L["box"]
        im = fit(Image.open(L["src"]), w, h, L.get("fit", "cover"))
        if L.get("fit") == "contain":
            x, y = x + (w - im.width) // 2, y + (h - im.height) // 2
        paste(cv, im, x, y, L.get("radius", 44), L.get("shadow", 0), L.get("shadow_alpha", 80))
    elif t == "grid":
        x0, y0, bw, bh = L["box"]
        n, cols, g = len(L["srcs"]), L.get("cols", 3), L.get("gap", 18)
        rows = -(-n // cols)
        cw, ch = (bw - (cols - 1) * g) // cols, (bh - (rows - 1) * g) // rows
        for i, s in enumerate(L["srcs"]):
            paste(cv, fit(Image.open(s), cw, ch), x0 + (i % cols) * (cw + g), y0 + (i // cols) * (ch + g), L.get("radius", 22))
    elif t == "pills":
        x0, y0, bw, bh = L["box"]
        n = len(L["srcs"])
        pw = L.get("w", bw // (n * 2 - 1))
        g = (bw - n * pw) // max(1, n - 1)
        for i, s in enumerate(L["srcs"]):
            h = int(bh * L.get("heights", [1] * n)[i])
            paste(cv, fit(Image.open(s), pw, h), x0 + i * (pw + g), y0 + bh - h, pw // 2)
    elif t == "text":
        text(cv, L)
    elif t == "block":   # a panel holding real output as type (a transcript, an audit, before/after copy)
        x, y, w, h = L["box"]
        ImageDraw.Draw(cv).rounded_rectangle((x, y, x + w, y + h), L.get("radius", 28), fill=rgba(L.get("bg", "#FFFFFF"), L.get("bg_alpha", 255)),
                                             outline=rgba(L["border"]) if L.get("border") else None, width=L.get("border_w", 2))
        pad = L.get("pad", 40)
        text(cv, {**L, "x": x + pad, "y": y + pad, "text": L["text"]})
    elif t == "island":
        w, h = L.get("w", 370), L.get("h", 108)
        ImageDraw.Draw(cv).rounded_rectangle(((W - w) // 2, L.get("y", 36), (W + w) // 2, L.get("y", 36) + h), h // 2, fill=(0, 0, 0, 255))
    elif t == "clock":
        c = L.get("color", "#FFFFFF")
        text(cv, {"text": L.get("date", "Saturday 24 October"), "y": L.get("y", 220), "size": 52, "weight": "Semibold", "color": c})
        text(cv, {"text": L.get("time", "9:41"), "y": L.get("y", 220) + 60, "size": 300, "weight": "Bold", "color": c})
    elif t == "notif":
        x, y, w, h = 40, L["y"], W - 80, 200
        dark = L.get("dark", False)
        bg = cv.crop((x, y, x + w, y + h)).filter(ImageFilter.GaussianBlur(30))
        veil = Image.new("RGBA", (w, h), (30, 30, 34, 150) if dark else (250, 250, 252, 170))
        bg.alpha_composite(veil)
        paste(cv, bg, x, y, 52)
        if L.get("icon"):
            paste(cv, fit(Image.open(L["icon"]), 96, 96), x + 36, y + 52, 22)
        fg, sub = ("#FFFFFF", "#D8D8DC") if dark else ("#111111", "#3C3C43")
        d = ImageDraw.Draw(cv)
        d.text((x + 160, y + 44), L.get("title", ""), font=font(40, "Semibold", L.get("title", "")), fill=rgba(fg))
        d.text((x + 160, y + 102), L.get("body", ""), font=font(38, "Regular", L.get("body", "")), fill=rgba(sub))
        d.text((x + w - 120, y + 44), L.get("when", "now"), font=font(32, "Regular"), fill=rgba(sub))
    else:
        sys.exit(f"unknown layer type: {t}")


def cmd_frame(a):
    spec = json.load(open(a.spec))
    W, H = spec.get("size", [1080, 1920])
    for fr in spec["frames"]:
        cv = Image.new("RGBA", (W, H), rgba(fr.get("bg", "#F5F5F7")))
        if fr.get("bg_image"):
            cv.alpha_composite(fit(Image.open(fr["bg_image"]), W, H).convert("RGBA"))
        for L in fr["layers"]:
            layer(cv, L)
        cv.convert("RGB").save(fr["out"], quality=92)
        print("wrote", fr["out"])


def cmd_compare(a):
    if len(a.short) < 3:
        sys.exit("compare needs >=3 --short lines ('where it falls short' — concrete, element-level, no scores)")
    if any(re.search(r"\b\d+(\.\d)?\s*/\s*10\b", s) for s in a.short):
        sys.exit("no N/10 scores in --short; write what is worse than the reference")
    W = a.width
    rf, kf = Image.open(a.ref).convert("RGB"), Image.open(a.frame).convert("RGB")
    rf = rf.resize((W, int(rf.height * W / rf.width)))
    kf = kf.resize((W, int(kf.height * W / kf.width)))
    cap, line = font(34, "Semibold", "参考"), font(32, "Regular", "参考")
    hint = 70 + 50 * len(a.short)
    o = Image.new("RGB", (W, rf.height + kf.height + 60 + hint), (255, 255, 255))
    o.paste(rf, (0, 0))
    d = ImageDraw.Draw(o)
    d.text((24, rf.height + 12), f"↑ 参考：{a.label}    ↓ 我们的风格帧", font=cap, fill=(60, 60, 60))
    o.paste(kf, (0, rf.height + 60))
    y = rf.height + 60 + kf.height + 20
    d.text((24, y), "哪里不如它：", font=cap, fill=(196, 30, 46))
    for i, s in enumerate(a.short):
        d.text((24, y + 50 + 50 * i), f"{i + 1}. {s}", font=line, fill=(30, 30, 30))
    o.save(a.out, quality=88)
    print("wrote", a.out)


def cmd_sheet(a):
    ims = [Image.open(p).convert("RGB") for p in a.images]
    h = a.height
    ims = [im.resize((int(im.width * h / im.height), h)) for im in ims]
    g, top = 30, 80
    o = Image.new("RGB", (sum(i.width for i in ims) + g * (len(ims) + 1), h + top + g), (245, 245, 247))
    d, x = ImageDraw.Draw(o), g
    labels = a.labels or [chr(65 + i) for i in range(len(ims))]
    for im, lab in zip(ims, labels):
        o.paste(im, (x, top))
        d.text((x, 18), lab, font=font(44, "Bold", lab), fill=(17, 17, 17))
        x += im.width + g
    o.save(a.out, quality=88)
    print("wrote", a.out)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    f = s.add_parser("frame"); f.add_argument("spec"); f.set_defaults(fn=cmd_frame)
    c = s.add_parser("compare")
    c.add_argument("--ref", required=True); c.add_argument("--frame", required=True); c.add_argument("--label", required=True)
    c.add_argument("--short", action="append", default=[]); c.add_argument("--out", required=True); c.add_argument("--width", type=int, default=1080)
    c.set_defaults(fn=cmd_compare)
    h = s.add_parser("sheet"); h.add_argument("images", nargs="+"); h.add_argument("--labels", nargs="*")
    h.add_argument("--out", required=True); h.add_argument("--height", type=int, default=1100); h.set_defaults(fn=cmd_sheet)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
