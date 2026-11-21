# Read every frame. Sampling misses the fault you are looking for.
import sys
import cv2
import numpy as np

cap = cv2.VideoCapture(sys.argv[1])
fps = cap.get(cv2.CAP_PROP_FPS)
frames = []
while True:
    ok, frame = cap.read()
    if not ok:
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frames.append(cv2.resize(gray, (320, 180), interpolation=cv2.INTER_AREA).astype(np.float32))
g = np.stack(frames)
step = np.abs(g[1:] - g[:-1]).mean(axis=(1, 2))   # change from one frame to the next
skip = np.abs(g[2:] - g[:-2]).mean(axis=(1, 2))   # change across one frame

for i in range(1, len(g) - 1):
    t = i / fps
    # Black: dark and flat, with light on at least one side. A fade has no sudden edge.
    if g[i].mean() < 16 and g[i].std() < 6 and (g[i - 1].mean() > 32 or g[i + 1].mean() > 32):
        print(f"{t:6.2f}s black frame")
    # Glitch: differs from both neighbours, while the neighbours match each other.
    local = np.median(step[max(0, i - 12):i + 12])
    a, b = step[i - 1], step[i]
    if min(a, b) > max(6, 4 * local) and skip[i - 1] < 0.35 * min(a, b):
        print(f"{t:6.2f}s glitch frame (jump {a:.1f} then {b:.1f}, neighbours differ by {skip[i - 1]:.1f})")

# Frozen: nothing moves for 0.4 s, with motion before and after.
i = 0
while i < len(step):
    if step[i] < 0.06:
        j = i
        while j + 1 < len(step) and step[j + 1] < 0.06:
            j += 1
        before = np.median(step[max(0, i - 12):i]) if i else 0
        after = np.median(step[j + 1:j + 13]) if j + 1 < len(step) else 0
        if (j - i + 1) / fps >= 0.4 and before > 0.5 and after > 0.5:
            print(f"{i / fps:6.2f}s frozen for {(j - i + 1) / fps:.2f}s")
        i = j + 1
    else:
        i += 1
