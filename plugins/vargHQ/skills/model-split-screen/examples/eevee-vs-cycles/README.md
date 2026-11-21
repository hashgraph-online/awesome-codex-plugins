# Example: Eevee vs Cycles, same Python scene

This skill's own test. The starter film from `blender-code-film` (`scripts/film.py`) rendered twice with
nothing changed but the engine, then laid out with `split.py`. Numbers are in `runs.json` (measured with
`/usr/bin/time` on an Apple Silicon Mac, Blender 5.3.0).

```bash
F=../../../blender-code-film/scripts
blender -b --factory-startup -P $F/film.py -- --no-haze --percent 50 --out render/eevee
blender -b --factory-startup -P $F/film.py -- --no-haze --engine cycles --samples 48 --percent 50 --out render/cycles
$F/mux.sh render/eevee eevee.mp4 && $F/mux.sh render/cycles cycles.mp4

python3 ../../scripts/split.py \
  --left eevee.mp4  --left-name "Eevee"  --left-stats "0.7 s a frame · 2 min 29 s" \
  --right cycles.mp4 --right-name "Cycles" --right-stats "2.3 s a frame · 8 min 19 s" \
  --title "Same Python scene, two render engines" \
  --prompt "A lantern orb drifts up a low-poly forest valley at dusk" -o split.mp4

python3 ../../scripts/split.py … --layout stack --blind 3 --winner right \
  --title "Which one is the path tracer?" -o split-9x16.mp4
```

The haze is off in both: with it, one Cycles still took 3 min 16 s, so the comparison would have been
about volumes, not engines. Change one thing between the two runs, and say which.
