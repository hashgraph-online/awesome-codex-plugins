# Commands

All from `scripts/smallest-star/`. Frames go to a directory outside any synced folder.

```bash
# a still at a film time, a look-development view, or the normal buffer for debugging
bun render.ts --out /tmp/st --w 960 --h 540 --spp 16 --t 31.5
bun render.ts --out /tmp/st --w 960 --h 540 --spp 16 --dev dev_mouse:0.2
bun render.ts --out /tmp/st --w 640 --h 360 --spp 8 --quality draft --mode 2 --t 21.2

# override any state value for one render
bun render.ts --out /tmp/st --w 960 --h 540 --spp 16 --t 31.5 --set post.exposure=4 --set ff.glow=2

# whole-film contact sheet stills (13 s for 33 frames on an M4 Pro)
bun render.ts --out /tmp/sheet --w 480 --h 270 --spp 8 --quality draft --name s \
  --t 0.3,2.5,4.7,5.3,7.5,9.7,10.3,12.5,14.7,15.3,17.5,19.7,20.3,21.2,22.3,22.8,25,27.2,27.8,30,32.2,33,36.2,39.6,40.3,42.5,44.7,45.3,47.5,49.7,50.5,54,58.5

# a motion strip: every second frame of one second of hops
bun render.ts --out /tmp/mo --w 384 --h 216 --spp 5 --flatspp --quality draft --frames 792-823 --step 2

# final frames; run again after an interruption and it continues
bun render.ts --out /tmp/final --w 1280 --h 720 --spp 20 --frames 0-1439 --set post.grain=0
bun render.ts --out /tmp/final --w 1280 --h 720 --spp 20 --frames 1560-1679 --set post.grain=0

# making-of passes for the meeting shot: normals + albedo from one render, then one raw sample
bun render.ts --out /tmp/brk --w 1280 --h 720 --spp 8 --flatspp --frames 660-779 --modes 2,1 --name b
bun render.ts --out /tmp/brk --w 1280 --h 720 --spp 1 --flatspp --frames 660-779 --modes 4 --name n

# score, assembly, live page
python3 audio/score.py            # add --notes to print the composition bar by bar
python3 post/compose.py --frames /tmp/final --brk /tmp/brk --out out/the-smallest-star.mp4
python3 post/compose.py --frames /tmp/final --brk /tmp/brk --still 30,700,1400 --out /tmp/stills
python3 live/build.py /tmp
```

Modes: 0 film, 1 albedo, 2 normals, 3 depth, 4 samples without the denoiser.
Quality presets (`--quality`): `draft` (fewer march steps), `final` (one bounce), `ultra` (two bounces).

`post/compose.py` sets captions in macOS system fonts (Iowan Old Style, Helvetica Neue). On another system, change the two font paths at the top of the file.
