#!/usr/bin/env python3
"""retime.py: re-time the picture to the voice. STORYBOARD.json durations are rewritten from the measured line durations.

  python3 retime.py STORYBOARD.json TIMINGS.json [--grid grid.json] [--fps 30]

The voice is never stretched; the picture adapts to it. The warnings the storyboard and assets stages saved are kept
(retime's own are added once, and replaced when it runs again); the voice stage's notes go in `retime.notes` for the report. Every line is placed so a short breath separates it from the
one before, and each beat cut falls in the middle of the breath between its last line and the next beat's first:

  lead 0.30 s before the first word, 0.30 s between lines of one beat, 0.45 s between beats, 0.80 s between acts,
  a 1.8 s hold on the last frame (references/formats.md: the final message holds), a beat held at least 2.0 s and at least
  (caption words / 3) + 0.5 s so its words can be read.

Breaths are measured from the speech, not the file, so a line cut with padding (split_takes.py) and a stand-in line
with none are treated alike. With --grid (beat_grid.py analyze output), each cut moves LATER, up to --snap-max seconds,
to the next music beat (act changes to the next downbeat when the grid has them), and everything after it follows, so
the voice is only ever given a longer pause, never cut. Cut times are rounded to whole frames last. The sound cues in
the storyboard get a film-time `t` here, which mix.py reads. Standard library only.
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from film_lib import FilmError, load_json, save_json  # noqa: E402

DEFAULTS = dict(gap_line=0.30, gap_beat=0.45, gap_act=0.80, lead=0.30, end_hold=1.8, min_beat=2.0)


def _frame(t: float, fps: float) -> float:
    return round(t * fps) / fps


def _snap_up(t: float, points: list[float], max_shift: float) -> float:
    for g in points:
        if g >= t - 1e-9:
            return g if g - t <= max_shift else t
    return t


def _hold(beat: dict, min_beat: float) -> float:
    return max(min_beat, len(str(beat.get("caption", "")).split()) / 3.0 + 0.5)


def _check(sb: dict, lines: dict) -> list[str]:
    used = [lid for b in sb["beats"] for lid in b["lines"]]
    missing = [lid for lid in used if lid not in lines]
    if missing:
        raise FilmError("no voice for line(s) " + ", ".join(missing) + ": run the voice stage (film.py voice) or split_takes.py first")
    return [f"voice line {lid} is in TIMINGS.json but in no beat: it is not used" for lid in lines if lid not in used]


def _resolve_cues(beat: dict) -> list[dict]:
    out = []
    for cue in beat.get("sound", []):
        at = cue.get("at", "start")
        if at == "start":
            t = beat["start"]
        elif at == "end":
            t = beat["end"]
        elif at.startswith("line:") and at[5:] in beat["line_starts"]:
            t = beat["line_starts"][at[5:]] + beat["_speech_start"][at[5:]]
        else:
            raise FilmError(f"{beat['id']}: sound cue '{cue.get('cue')}' has at='{at}': use start, end or line:L01 (a line of this beat)")
        out.append({**cue, "t": round(t + float(cue.get("offset", 0.0)), 4)})
    return out


def retime(storyboard: dict, timings: dict, fps: float | None = None, grid: dict | None = None, snap_max: float = 0.5, **opts) -> dict:
    sb = copy.deepcopy(storyboard)
    o = {**DEFAULTS, **opts}
    fps = fps or sb.get("fps", 30)
    lines = timings["lines"]
    warnings = _check(sb, lines)
    beats_grid = sorted((grid or {}).get("beats", []))
    downbeats = sorted((grid or {}).get("downbeats", [])) or beats_grid
    speech_end, file_end, beat_start = None, 0.0, 0.0
    for i, beat in enumerate(sb["beats"]):
        nxt = sb["beats"][i + 1] if i + 1 < len(sb["beats"]) else None
        starts, speech = {}, {}
        for k, lid in enumerate(beat["lines"]):
            t = lines[lid]
            if speech_end is None:
                want = o["lead"]
            elif k == 0:
                want = beat_start + _gap(sb["beats"][i - 1], beat, o) / 2
            else:
                want = speech_end + o["gap_line"]
            fs = max(want - t["speech_start"], file_end)                     # never earlier than the breath asks, never over the last file
            starts[lid], speech[lid] = round(fs, 4), t["speech_start"]
            speech_end, file_end = fs + t["speech_end"], fs + t["duration"]
        beat.update(start=round(beat_start, 4), line_starts=starts, _speech_start=speech)
        if nxt is None:
            end = max(speech_end + o["end_hold"], beat_start + _hold(beat, o["min_beat"]))
        else:
            gap = _gap(beat, nxt, o)
            end = max(speech_end + gap / 2, beat_start + _hold(beat, o["min_beat"]))
            pts = downbeats if nxt["act"] != beat["act"] else beats_grid
            end = _snap_up(end, pts, snap_max) if pts else end
        end = max(_frame(end, fps), beat_start + 1 / fps)
        beat.update(end=round(end, 4), duration=round(end - beat_start, 4))
        beat_start = end
    for beat in sb["beats"]:
        beat["sound"] = _resolve_cues(beat) if beat.get("sound") else []
        beat.pop("_speech_start")
    sb["acts"] = [{**a, "start": min(b["start"] for b in sb["beats"] if b["act"] == a["id"]), "end": max(b["end"] for b in sb["beats"] if b["act"] == a["id"])} for a in sb["acts"]]
    earlier = [w for w in sb.get("warnings", []) if w not in (sb.get("retime") or {}).get("warnings", [])]   # this stage's last run is replaced
    voice_notes = list(timings.get("notes", [])) + list(timings.get("warnings", []))
    sb.update(duration=round(beat_start, 4), retimed=True, fps=fps, warnings=_unique(earlier + warnings),
              retime={**o, "grid": bool(beats_grid), "snap_max": snap_max if beats_grid else None, "warnings": warnings, "notes": voice_notes})
    return sb


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    return [w for w in items if not (w in seen or seen.add(w))]


def _gap(a: dict, b: dict, o: dict) -> float:
    return o["gap_act"] if a["act"] != b["act"] else o["gap_beat"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("storyboard", help="STORYBOARD.json (rewritten in place)")
    ap.add_argument("timings", help="TIMINGS.json from split_takes.py or the voice stage")
    ap.add_argument("--grid", help="beat_grid.py analyze output: cuts snap later onto its beats and downbeats")
    ap.add_argument("--snap-max", type=float, default=0.5, help="the longest a cut may be pushed later to reach a beat (default 0.5 s)")
    ap.add_argument("--fps", type=float)
    for k, v in DEFAULTS.items():
        ap.add_argument("--" + k.replace("_", "-"), type=float, default=v, help=f"seconds (default {v})")
    args = ap.parse_args(argv)
    try:
        sb = load_json(Path(args.storyboard), "STORYBOARD.json")
        tm = load_json(Path(args.timings), "TIMINGS.json")
        grid = load_json(Path(args.grid), "the beat grid") if args.grid else None
        out = retime(sb, tm, args.fps, grid, args.snap_max, **{k: getattr(args, k) for k in DEFAULTS})
    except (FilmError, KeyError) as err:
        print(f"FAIL  retime: {err if isinstance(err, FilmError) else 'storyboard or timings are missing the field ' + str(err)}")
        return 1
    save_json(Path(args.storyboard), out)
    for w in out["warnings"]:
        print(f"WARN  {w}")
    print(f"PASS  {len(out['beats'])} beats re-timed to the voice: {out['duration']:.2f} s ({round(out['duration'] * out['fps'])} frames) -> {args.storyboard}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
