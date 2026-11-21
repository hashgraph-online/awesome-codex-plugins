# Testing the judge

A check that stops firing looks exactly like a clean video, so test it against planted defects.

```bash
# Plant one defect per clip in your own footage. Each clip keeps its defect at a known time, and control_* clips stay clean.
uv run make_fixtures.py --clips a.mp4 b.mp4 --person one.mp4 --person-t 5 --other-person two.mp4 --other-t 28 \
  --dressed dressed.mp4 --dressed-t 0.1 --out fixtures/

# Run the judge on all of them and score it. A catch only counts if an event lands on the planted moment.
python3 run_bench.py fixtures/ runs/ --jobs 4
```

`--clips` takes two real clips of at least 12 s. Real footage is the point: it is what gives you false flags. `--person`, `--other-person` and `--dressed` are optional, and add the face, outfit and light tests.

Findings that also appear in the untouched `control_clean` clip are named once as real findings in your footage and are not counted against the judge. A control fails on a blocker or major flag. Minor flags are prompts for eyes, reported apart.

Results on 2026-11-03:

| Footage | Defects caught | Controls with no blocker or major flag |
|---|---|---|
| The clips the thresholds were tuned on | 25 of 25 | 10 of 10 |
| Held-out graphic ads, thresholds frozen | 18 of 22 | 6 of 8 |

Report the second kind of number. Keep some footage out of your tuning.

The bench runs with `--music-only`, so it does not cover voice. To test voice, make a line with any TTS, then run `uv run --with faster-whisper ../scripts/judge.py audio line.wav --out runs/v --script right.txt`, and again with a script that has words changed. On our test line the first read 0.0 word error and the second 0.188, naming each changed word.
