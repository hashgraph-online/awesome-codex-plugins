#!/bin/bash
# Encode like the platform, then measure banding on both copies. CAMBI: 0 is none, about 5 starts to annoy, 24 is the worst seen.
in="$1"
ffmpeg -y -v error -i "$in" -map 0:v:0 -vf "scale=1280:720,format=yuv420p" \
  -c:v libx264 -preset veryfast -b:v 2048k -maxrate 3072k -bufsize 4096k upload.mp4
for f in "$in" upload.mp4; do
  ffmpeg -v error -i "$f" -i "$in" -lavfi \
    "[0:v]scale=1280:720,format=yuv420p[a];[1:v]scale=1280:720,format=yuv420p[b];[a][b]libvmaf=feature=name=cambi:log_fmt=json:log_path=cambi.json:n_subsample=3" \
    -f null -
  python3 -c "
import json, sys
fr = json.load(open('cambi.json'))['frames']
c = [x['metrics']['cambi'] for x in fr]
print(f'$f: mean CAMBI {sum(c) / len(c):.2f}, worst {max(c):.2f} at frame {fr[c.index(max(c))][\"frameNum\"]}')"
done
