# Find what stays still on the glass while the scene moves behind it.
# usage: pinned.py clip.mp4 t0 t1
import sys
import cv2
import numpy as np

path, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
cap = cv2.VideoCapture(path)
cap.set(cv2.CAP_PROP_POS_MSEC, t0 * 1000)
frames = []
while cap.get(cv2.CAP_PROP_POS_MSEC) < t1 * 1000:
    ok, f = cap.read()
    if not ok:
        break
    frames.append(cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (480, 270)).astype(np.float32))
st = np.stack(frames[:: max(1, len(frames) // 40)])

# Inter-decile spread per pixel. One bad frame cannot fake a moving scene.
spread = (np.percentile(st, 90, axis=0) - np.percentile(st, 10, axis=0)) / 2.56
print(f"scene motion {np.percentile(spread, 60):.1f} (under 8 means this shot cannot test pinning)")
detail = cv2.GaussianBlur(np.abs(cv2.Laplacian(st.mean(axis=0), cv2.CV_32F)), (0, 0), 3)
mask = ((spread < 2.5) & (detail > 4)).astype(np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
for i in range(1, n):
    x, y, w, h, area = stats[i]
    if 0.0015 < area / mask.size < 0.35:
        ring = cv2.dilate((labels == i).astype(np.uint8), np.ones((31, 31), np.uint8)).astype(bool) & (labels != i)
        if spread[ring].mean() > 3 * max(spread[labels == i].mean(), 0.5):
            print(f"stuck at x={x / 480:.2f} y={y / 270:.2f} w={w / 480:.2f} h={h / 270:.2f}: inside {spread[labels == i].mean():.1f}, around {spread[ring].mean():.1f}")
