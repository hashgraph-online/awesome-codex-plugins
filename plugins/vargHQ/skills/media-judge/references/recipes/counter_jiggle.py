# A digit that keeps its value must not move while its neighbours count.
# usage: counter_jiggle.py clip.mp4 t0 t1 x0 y0 x1 y1  (the counter's box in pixels)
import sys
import cv2
import numpy as np

path, t0, t1, *box = sys.argv[1:]
x0, y0, x1, y1 = map(int, box)
cap = cv2.VideoCapture(path)
cap.set(cv2.CAP_PROP_POS_MSEC, float(t0) * 1000)
crops = []
while cap.get(cv2.CAP_PROP_POS_MSEC) < float(t1) * 1000:
    ok, f = cap.read()
    if not ok:
        break
    crops.append(cv2.cvtColor(f[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY))

_, ink = cv2.threshold(crops[0], 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
if ink[0].mean() > 127:
    ink = 255 - ink
n, _, stats, _ = cv2.connectedComponentsWithStats(ink, 8)
digits = sorted(tuple(int(v) for v in s[:4]) for s in stats[1:] if s[3] > 0.3 * ink.shape[0])

for x, y, w, h in digits:
    moves, px, held = [], float(x), 0
    for a, b in zip(crops, crops[1:]):
        left = int(round(px))
        tpl = a[y:y + h, left:left + w]
        win = b[y:y + h, max(left - 20, 0):left + w + 20]
        if tpl.shape != (h, w) or win.shape[1] < w:
            break
        res = cv2.matchTemplate(win, tpl, cv2.TM_CCOEFF_NORMED)
        _, score, _, loc = cv2.minMaxLoc(res)
        if score >= 0.92:                       # same digit as last frame
            dx = loc[0] + max(left - 20, 0) - left
            moves.append(dx)
            px += dx
            held += 1
    if held >= 0.25 * (len(crops) - 1):
        print(f"digit at x={x}: held {held} frames, shake {np.std(moves) / h * 100:.2f}% of its height")
