#!/usr/bin/env python3
"""Final assembly for The Smallest Star.

Reads the path-traced frames (1280x720 PNG), scales them to 1920x1080, lays the story captions,
title, making-of labels and end card over them, and pipes raw video into ffmpeg together with the
synthesized score. Everything on screen except the letterforms (a system font) is rendered by src/.

  python3 post/compose.py --frames DIR --brk DIR --out out/the-smallest-star.mp4
  python3 post/compose.py --frames DIR --still 60,700,1400 --out /tmp/stills     (write PNG stills instead)
"""
import argparse, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FPS = 24
W, H = 1920, 1080
HERE = os.path.dirname(os.path.abspath(__file__))
IOWAN = '/System/Library/Fonts/Supplemental/Iowan Old Style.ttc'
SANS = '/System/Library/Fonts/HelveticaNeue.ttc'


def font(size, face='italic'):
    idx = {'roman': 0, 'bold': 1, 'italic': 2, 'titling': 6}[face]
    return ImageFont.truetype(IOWAN, size, index=idx)


def sans(size, idx=0):
    try:
        return ImageFont.truetype(SANS, size, index=idx)
    except Exception:
        return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', size)


def text_layer(lines, fnt, fill=(255, 255, 255, 240), spacing=1.32, tracking=0, shadow=0.85, align='center', anchor_xy=(W // 2, H - 150), anchor='mb'):
    """lines: list of str (or list of (str, font, fill)). Returns (RGBA layer cropped, top-left xy)."""
    items = [(l, fnt, fill) if isinstance(l, str) else l for l in lines]
    tmp = ImageDraw.Draw(Image.new('RGBA', (8, 8)))

    def width(s, f):
        if not tracking:
            return tmp.textlength(s, font=f)
        return sum(tmp.textlength(ch, font=f) for ch in s) + tracking * (len(s) - 1)
    widths = [width(s, f) for s, f, _ in items]
    heights = [f.size * spacing for _, f, _ in items]
    tw, th = int(max(widths)) + 120, int(sum(heights)) + 120
    txt = Image.new('RGBA', (tw, th), (0, 0, 0, 0)); d = ImageDraw.Draw(txt)
    sh = Image.new('L', (tw, th), 0); ds = ImageDraw.Draw(sh)
    y = 60
    for (s, f, fl), w_, h_ in zip(items, widths, heights):
        x = 60 + (tw - 120 - w_) / 2 if align == 'center' else 60
        if tracking:
            cx = x
            for ch in s:
                d.text((cx, y), ch, font=f, fill=fl); ds.text((cx, y), ch, font=f, fill=255)
                cx += tmp.textlength(ch, font=f) + tracking
        else:
            d.text((x, y), s, font=f, fill=fl); ds.text((x, y), s, font=f, fill=255)
        y += h_
    blur = sh.filter(ImageFilter.GaussianBlur(9))
    tight = sh.filter(ImageFilter.GaussianBlur(2.5))
    layer = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    layer.paste((0, 0, 0, 255), (0, 0), blur.point(lambda v: int(min(255, v * 1.6) * shadow)))
    layer.alpha_composite(Image.merge('RGBA', [Image.new('L', (tw, th), 0)] * 3 + [tight.point(lambda v: int(v * shadow * 0.8))]))
    layer.alpha_composite(txt)
    ax, ay = anchor_xy
    x0 = ax - tw // 2 if align == 'center' else ax - 60
    y0 = {'mb': ay - th + 60, 'mt': ay - 60, 'mm': ay - th // 2}[anchor]
    return layer, (int(x0), int(y0))


def env(t, a, b, fi=0.5, fo=0.5):
    if t <= a or t >= b:
        return 0.0
    x = min(1.0, (t - a) / fi) if fi > 0 else 1.0
    y = min(1.0, (b - t) / fo) if fo > 0 else 1.0
    s = lambda v: v * v * (3 - 2 * v)
    return s(x) * s(y)


def build_overlays(narrated=False):
    O = []  # (layer, xy, t_in, t_out, fade_in, fade_out)
    cap = font(50, 'italic')

    def caption(text, a, b, y=H - 118):
        lines = text.split('\n')
        O.append((*text_layer(lines, cap, anchor_xy=(W // 2, y)), a, b, 0.6, 0.5))

    # title over the opening sky
    title = text_layer([('THE SMALLEST STAR', font(84, 'titling'), (255, 250, 235, 245))], None, tracking=14, anchor_xy=(W // 2 + 250, 430), anchor='mm')
    O.append((*title, 0.45, 2.75, 0.9, 0.6))
    sub = text_layer([('a fable, written and path traced in code by Claude Fable 5.2', font(40, 'italic'), (244, 246, 255, 245))], None, anchor_xy=(W // 2 + 250, 524), anchor='mm')
    O.append((*sub, 0.7, 2.75, 0.7, 0.6))

    # caption times follow the narration lines in timeline.json (the silent cut keeps the same times)
    caption('Once, a small firefly looked up at the stars.', 2.5, 6.1)
    caption('They were so bright. And it was so small.', 6.3, 9.9)
    caption('So it flew up to join them.', 10.7, 14.2)
    caption('But however high it climbed,\nthe stars came no closer.', 15.4, 19.6)
    caption('Down in the tall grass, a mouse had lost its way home.', 22.9, 27.1)
    caption('The firefly had only a little light.', 27.6, 30.2)
    caption('But a little light, close by, goes a long way.', 30.9, 35.2)
    caption('From its doorway, the mouse looked up,\nand saw the brightest star in the sky.', 50.5, 55.9)
    moral = text_layer([("You don't have to reach the stars to be one.", font(62, 'italic'), (255, 249, 225, 250))], None, anchor_xy=(W // 2, 468), anchor='mm')
    O.append((*moral, 56.2, 59.8, 1.0, 0.5))

    # making-of stages (coda, 60-65 s)
    lab = font(66, 'titling'); small = sans(38)
    stages = [
        ('SHAPES', 'pure math: distance fields, and one quadratic per blade of grass', 60.05, 61.25),
        ('COLOUR', 'procedural. no textures, no models, no assets', 61.25, 62.45),
        ('LIGHT', 'path traced: one sample per pixel looks like this', 62.45, 63.65),
        ('FILM', 'thirty samples, a denoiser, a grade. all one program', 63.65, 64.95),
    ]
    for name, desc, a, b in stages:
        O.append((*text_layer([(name, lab, (255, 250, 235, 250))], None, tracking=10, anchor_xy=(W // 2, 112), anchor='mm'), a, b, 0.25, 0.25))
        O.append((*text_layer([(desc, small, (232, 236, 250, 235))], None, anchor_xy=(W // 2, 188), anchor='mm'), a, b, 0.25, 0.25))
    O.append((*text_layer([('The renderer is a path tracer Claude Fable 5.2 wrote from scratch for this film.', sans(38), (240, 242, 252, 245))], None, anchor_xy=(W // 2, H - 92), anchor='mm'), 60.2, 64.9, 0.4, 0.3))

    # end card (65-70 s)
    O.append((*text_layer([('THE SMALLEST STAR', font(64, 'titling'), (255, 250, 235, 250))], None, tracking=12, anchor_xy=(W // 2, 270), anchor='mm'), 65.2, 69.7, 0.7, 0.6))
    credits = [
        ('Story, characters, light, score and renderer', font(46, 'italic'), (240, 242, 255, 245)),
        ('written as code by Claude Fable 5.2', font(46, 'italic'), (240, 242, 255, 245)),
        (' ', font(20, 'italic'), (0, 0, 0, 0)),
        ('No 3D software.  No models or textures.  No video or music AI.', sans(34), (214, 220, 240, 240)),
    ] + ([('Narration: an AI voice (ElevenLabs).', sans(30), (176, 184, 210, 235))] if narrated else []) + [
        (' ', font(26, 'italic'), (0, 0, 0, 0)),
        ('Make your own:  varg.ai/how-to', sans(40, 1), (255, 232, 150, 250)),
    ]
    O.append((*text_layer(credits, None, spacing=1.5, anchor_xy=(W // 2, 610), anchor='mm'), 65.6, 69.7, 0.8, 0.6))
    return O


def coda_frame(i, frames_dir, brk_dir):
    """Making-of wipe across the meeting shot: shapes -> colour -> 1 sample -> film."""
    tau = i / FPS
    src = 660 + i                       # the meeting shot starts at frame 660
    paths = [os.path.join(brk_dir, f'b_{src:05d}_m2.png'), os.path.join(brk_dir, f'b_{src:05d}_m1.png'),
             os.path.join(brk_dir, f'n_{src:05d}_m4.png'), os.path.join(frames_dir, f'f_{src:05d}.png')]
    ims = [Image.open(p).convert('RGB').resize((W, H), Image.LANCZOS) for p in paths]
    out = ims[0]
    ease = lambda v: v * v * (3 - 2 * v)
    for k, (a, b) in enumerate([(0.95, 1.55), (2.15, 2.75), (3.35, 3.95)]):
        if tau <= a:
            break
        f = ease(min(1.0, (tau - a) / (b - a)))
        x = int(round(f * (W + 8)))
        if x > 0:
            out = out.copy(); out.paste(ims[k + 1].crop((0, 0, min(x, W), H)), (0, 0))
            if x < W:
                ImageDraw.Draw(out).rectangle([x - 3, 0, x, H], fill=(255, 244, 200))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames', required=True); ap.add_argument('--brk', default=''); ap.add_argument('--out', required=True)
    ap.add_argument('--still', default=''); ap.add_argument('--audio', default=os.path.join(HERE, '..', 'audio', 'score.wav'))
    ap.add_argument('--narrated', action='store_true'); ap.add_argument('--total', type=int, default=1680); ap.add_argument('--crf', default='17')
    a = ap.parse_args()
    if a.narrated:
        a.audio = os.path.join(HERE, '..', 'audio', 'mix_narrated.wav')
    O = build_overlays(a.narrated)

    def frame(i):
        t = (i + 0.5) / FPS
        if 1440 <= i < 1560:
            im = coda_frame(i - 1440, a.frames, a.brk)
        else:
            im = Image.open(os.path.join(a.frames, f'f_{i:05d}.png')).convert('RGB').resize((W, H), Image.LANCZOS)
        if i >= 1560:
            im = Image.eval(im, lambda v: int(v * 0.8))
        base = im.convert('RGBA')
        for layer, xy, t0, t1, fi, fo in O:
            al = env(t, t0, t1, fi, fo)
            if al <= 0.003:
                continue
            l = layer if al > 0.997 else Image.merge('RGBA', (*layer.split()[:3], layer.split()[3].point(lambda v: int(v * al))))
            base.alpha_composite(l, dest=(max(xy[0], 0), max(xy[1], 0)))
        # last half second: fade to black
        if t > 69.5:
            k = max(0.0, 1 - (t - 69.5) / 0.5)
            base = Image.eval(base, lambda v: int(v * k))
        return base.convert('RGB')

    if a.still:
        os.makedirs(a.out, exist_ok=True)
        for s in a.still.split(','):
            i = int(s); frame(i).save(os.path.join(a.out, f'still_{i:05d}.jpg'), quality=90)
            print('still', i)
        return
    # light temporal filter for the sparkle in out-of-focus stars, then sharpen, then grain on top
    vf = 'atadenoise=0a=0.03:0b=0.06:1a=0.03:1b=0.06:2a=0.03:2b=0.06:s=5,unsharp=5:5:0.35:5:5:0.0,noise=c0s=4:c0f=t+u,format=yuv420p'
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-i', a.audio, '-vf', vf, '-c:v', 'libx264', '-preset', 'slow', '-crf', a.crf, '-maxrate', '14M', '-bufsize', '28M', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
           '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart',
           '-c:a', 'aac', '-b:a', '256k', '-shortest', a.out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(a.total):
        p.stdin.write(frame(i).tobytes())
        if i % 120 == 0:
            print('frame', i, flush=True)
    p.stdin.close(); p.wait()
    print('wrote', a.out)


if __name__ == '__main__':
    main()
