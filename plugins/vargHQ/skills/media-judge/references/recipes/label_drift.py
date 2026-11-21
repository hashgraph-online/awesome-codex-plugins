# Track a label and the world around it. If they part, the label has slid off.
# usage: label_drift.py clip.mp4 t0 t1 x y w h  (the label's box in the first frame, in pixels)
import sys
import cv2
import numpy as np

path, t0, t1, *b = sys.argv[1:]
x, y, w, h = map(int, b)
cap = cv2.VideoCapture(path)
cap.set(cv2.CAP_PROP_POS_MSEC, float(t0) * 1000)
ok, first = cap.read()
prev = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)
label = np.zeros_like(prev)
label[y:y + h, x:x + w] = 255
world = np.zeros_like(prev)
world[max(y - 2 * h, 0):y + 3 * h, max(x - 2 * h, 0):x + w + 2 * h] = 255
world[label > 0] = 0
lpts = cv2.goodFeaturesToTrack(prev, 40, 0.01, 3, mask=label)
wpts = cv2.goodFeaturesToTrack(prev, 80, 0.01, 5, mask=world)
apart = np.zeros(2)
peak = 0.0
lk = dict(winSize=(15, 15), maxLevel=2)
while cap.get(cv2.CAP_PROP_POS_MSEC) < float(t1) * 1000:
    ok, f = cap.read()
    if not ok:
        break
    cur = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
    w1, st, _ = cv2.calcOpticalFlowPyrLK(prev, cur, wpts, None, **lk)
    l1, sl, _ = cv2.calcOpticalFlowPyrLK(prev, cur, lpts, None, **lk)
    keep, keepl = st.ravel() == 1, sl.ravel() == 1
    if keep.sum() < 3 or keepl.sum() < 2:
        break
    apart += np.median(w1[keep] - wpts[keep], axis=0).ravel() - np.median(l1[keepl] - lpts[keepl], axis=0).ravel()
    peak = max(peak, float(np.hypot(*apart)))
    wpts, lpts, prev = w1[keep], l1[keepl], cur
print(f"label and surroundings parted by {peak:.1f} px, {peak / first.shape[1] * 100:.1f}% of the frame width")
