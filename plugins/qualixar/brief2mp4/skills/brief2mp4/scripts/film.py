#!/usr/bin/env python3
"""film.py: film mode. One brief in a project folder, a finished explainer or documentary out, every stage's file on disk.

  python3 film.py run --project my-film                  # every stage in order
  python3 film.py run --project my-film --from retime    # from one stage on (each stage reads the files the earlier ones wrote)
  python3 film.py run --project my-film --skip assets,render
  python3 film.py voice --project my-film --voice take --take take.wav      # one stage alone
  python3 film.py --list

Stages, with the file each writes (references/formats.md, "Explainer and documentary (film mode)"):
  story       BRIEF.md -> STORY.md        logline, audience, takeaway, act structure, pace (a scaffold: edit it; never overwritten)
  script      checks SCRIPT.md            narration lines with ids, on-screen words, a source URL per line or UNVERIFIED (you or your agent write it)
  storyboard  SCRIPT.md -> STORYBOARD.json  beats, kind, route, camera, transition and its meaning, sound cues, acts
  assets      -> ASSETS.json, assets/     pictures, maps, effects, music, each with its licence (--no-fetch works offline)
  voice       -> TIMINGS.json, audio/lines/  --voice standin (drafts) | take (your recording) | f5-tts (if installed)
  retime      STORYBOARD.json             durations rewritten from the measured voice (--grid beat_grid.py output snaps cuts to the music)
  build       -> project/, project_acts/  the archive desk look as HyperFrames projects (--burn-captions)
  captions    -> final.srt, captions.json word-timed from the same timings
  mix         -> audio/mix.wav            voice, music ducked under it, effects pinned by their peak, -14 LUFS
  render      -> final.mp4                acts side by side, joined, finished (--quality draft|delivery); refuses UNVERIFIED lines
  check       -> checks.json, checks/     delivery, seams, layout, placeholder text, a still per beat
  report      -> REPORT.md                checks, credits, UNVERIFIED lines, open items

Any stage can be run again alone. A stage that fails prints one FAIL line saying what to do and stops the run.
"""
from __future__ import annotations

import argparse
import http.client
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import film_assets  # noqa: E402
import film_build  # noqa: E402
import film_captions  # noqa: E402
import film_check  # noqa: E402
import film_render  # noqa: E402
import film_report  # noqa: E402
import film_story  # noqa: E402
import film_storyboard  # noqa: E402
import film_voice  # noqa: E402
import mix as mixer  # noqa: E402
import retime as retimer  # noqa: E402
from fetch_music import FetchError  # noqa: E402
from film_lib import FilmError, Project, load_json, parse_fps, save_json  # noqa: E402
from film_script import check_script, read_script, unverified  # noqa: E402

STAGES = ["story", "script", "storyboard", "assets", "voice", "retime", "build", "captions", "mix", "render", "check", "report"]


def say(kind: str, text: str) -> None:
    print(f"{kind}  {text}")


def story_fields(p: Project) -> dict:
    return film_story.read_story_fields(p.story.read_text(encoding="utf-8")) if p.story.is_file() else {}


def stage_story(p: Project, a) -> None:
    made = film_story.write_story(p.brief, p.story, a.force)
    say("PASS" if made else "INFO", "STORY.md written from BRIEF.md: edit it" if made else "STORY.md already exists: kept as it is (--force rewrites it)")


def stage_script(p: Project, a) -> None:
    script = read_script(p.script) if p.script.is_file() else None
    if script is None:
        raise FilmError("SCRIPT.md not found: write it from STORY.md (blocks '## L01' with say:, screen:, source:, see `python3 film_script.py`'s docstring or "
                        "references/formats.md), then run `film.py script`")
    errors, warnings = check_script(script)
    if errors:
        raise FilmError("SCRIPT.md has problems: " + "; ".join(errors))
    total = sum(l["seconds"] for l in script.lines)
    want = float(story_fields(p).get("length", "0 s").split()[0] or 0)
    for w in warnings:
        say("WARN", w)
    if want and abs(total - want) > 0.25 * want:
        say("WARN", f"the script reads for about {total:.0f} s at {script.pace:g} wpm; STORY.md asks for {want:.0f} s")
    say("PASS", f"{len(script.lines)} lines, about {total:.0f} s at {script.pace:g} wpm, {len(warnings)} unverified")


def stage_storyboard(p: Project, a) -> None:
    script = read_script(p.script)
    errors, _ = check_script(script)
    if errors:
        raise FilmError("SCRIPT.md has problems: " + "; ".join(errors))
    brief_text = p.brief.read_text(encoding="utf-8") if p.brief.is_file() else ""
    brief = film_story.parse_brief(brief_text + "\n" + (p.story.read_text(encoding="utf-8") if p.story.is_file() else ""))
    fps, rate = parse_fps(a.fps or 30)
    sb = film_storyboard.build_storyboard(script, brief, brief_text, fps, a.acts, a.look)
    sb["fps_rate"] = rate
    save_json(p.storyboard, sb)
    for w in sb["warnings"]:
        say("WARN", w)
    say("PASS", f"{len(sb['beats'])} beats in {len(sb['acts'])} act(s), about {sb['duration']:.0f} s before the voice is measured -> STORYBOARD.json")


def stage_assets(p: Project, a) -> None:
    sb = film_assets.run_assets(p, load_json(p.storyboard, "STORYBOARD.json"), not a.no_fetch, a.delay, a.seed, Path(a.music) if a.music else None, a.music_query, a.musicgen)
    save_json(p.storyboard, sb)
    for w in sb["warnings"]:
        say("WARN", w)
    n = len(load_json(p.assets)["assets"])
    say("PASS", f"{n} assets recorded with their licences in ASSETS.json")


def stage_voice(p: Project, a) -> None:
    script = read_script(p.script)
    voice = a.voice or story_fields(p).get("voice") or "standin"
    if voice == "take":
        if not a.take:
            raise FilmError("the voice is your recording: pass --take take.wav (and --words words.json or --model ggml-base.en.bin if the pauses between lines are short), or use --voice standin for a draft")
        result = film_voice.from_take(p.script, Path(a.take), p.lines_dir, p.timings, Path(a.words) if a.words else None, a.model)
        for n in result.get("notes", []):
            say("INFO", n)
        for w in result["warnings"]:
            say("WARN", w)
    elif voice == "f5-tts":
        film_voice.f5(script, p.lines_dir, p.timings, Path(a.ref_audio or ""), a.ref_text or "", a.f5_model)
        say("INFO", film_voice.F5_NOTE)
    elif voice == "standin":
        film_voice.standin(script, p.lines_dir, p.timings)
        say("WARN", "stand-in voice: a buzz that follows the words, for drafts. Record your voice or use F5-TTS for the real film")
    else:
        raise FilmError(f"unknown voice '{voice}': use standin, take or f5-tts")
    t = load_json(p.timings)
    say("PASS", f"{len(t['lines'])} lines, {sum(l['duration'] for l in t['lines'].values()):.1f} s of voice from {t['source']} -> TIMINGS.json")


def stage_retime(p: Project, a) -> None:
    grid = load_json(Path(a.grid), "the beat grid") if a.grid else None
    sb = load_json(p.storyboard, "STORYBOARD.json")
    if a.fps:                                      # a new rate here applies from now on; otherwise the storyboard's rate is kept
        sb["fps"], sb["fps_rate"] = parse_fps(a.fps)
    sb = retimer.retime(sb, load_json(p.timings, "TIMINGS.json"), sb.get("fps"), grid, a.snap_max)
    save_json(p.storyboard, sb)
    for w in sb["warnings"]:
        say("WARN", w)
    say("PASS", f"re-timed to the voice: {sb['duration']:.2f} s ({round(sb['duration'] * sb['fps'])} frames)")


def stage_build(p: Project, a) -> None:
    sb, tm = load_json(p.storyboard, "STORYBOARD.json"), load_json(p.timings, "TIMINGS.json")
    assets = load_json(p.assets) if p.assets.is_file() else {"assets": []}
    cues = film_captions.caption_cues(sb, tm) if a.burn_captions else None
    full = film_build.build_project(p, sb, tm, assets, p.project, None, a.burn_captions, cues)
    jobs = [{"act": "all", "dir": "project", "start": full["start"], "frames": full["frames"], "seconds": full["seconds"]}]
    if len(sb["acts"]) > 1:
        jobs = []
        for act in sb["acts"]:
            info = film_build.build_project(p, sb, tm, assets, p.p("project_acts", act["id"]), act["id"], a.burn_captions, cues, vendor_from=p.project)
            jobs.append({"act": act["id"], "dir": p.rel(p.p("project_acts", act["id"])), "start": info["start"], "frames": info["frames"], "seconds": info["seconds"]})
    save_json(p.p("BUILD.json"), {"version": 1, "burn_captions": a.burn_captions, "projects": jobs})
    lint = lint_projects(p, jobs)
    say("PASS", f"{len(jobs)} HyperFrames project(s) built" + (f"; lint: {lint}" if lint else ""))


def lint_projects(p: Project, jobs: list[dict]) -> str:
    npx = shutil.which("npx")
    if not npx:
        return "skipped (npx not found)"
    bad = 0
    for job in jobs:
        done = subprocess.run([npx, "--yes", film_build.HF_PACKAGE, "lint", str(p.p(job["dir"]))], capture_output=True, text=True, encoding="utf-8")
        bad += 0 if done.returncode == 0 else 1
    return "0 errors" if not bad else f"{bad} project(s) with errors: run `npx {film_build.HF_PACKAGE} lint` in it"


def stage_captions(p: Project, a) -> None:
    cues = film_captions.caption_cues(load_json(p.storyboard, "STORYBOARD.json"), load_json(p.timings, "TIMINGS.json"))
    p.p("final.srt").write_text(film_captions.to_srt(cues), encoding="utf-8", newline="\n")
    save_json(p.p("captions.json"), cues)
    say("PASS", f"{len(cues)} word-timed captions -> final.srt (and captions.json)")


def stage_mix(p: Project, a) -> None:
    sb = load_json(p.storyboard, "STORYBOARD.json")
    music = Path(a.music) if a.music else (p.p(sb["music"]) if sb.get("music") else None)
    r = mixer.mix(p.storyboard, p.timings, p.sfx_dir, p.mix, music)
    if r.get("music_plays", 0) > 1:
        say("WARN", f"the music is shorter than the film: it plays {r['music_plays']} times, crossfaded at each join. A longer track sounds better")
    say("PASS", f"mix: {r['lufs']} LUFS, {r['true_peak']} dBTP, {r['cues']} cue(s), " + ("music ducked under the voice" if music else "no music"))


def stage_render(p: Project, a) -> None:
    bad = unverified(read_script(p.script))
    if bad and not a.allow_unverified:
        raise FilmError(f"{len(bad)} line(s) have no source ({', '.join(bad)}): cut them, add a `source:` URL after checking, or pass --allow-unverified (they are listed in REPORT.md)")
    r = film_render.render_film(p, a.quality, a.workers)
    say("PASS", f"{p.final.name}: {r['duration']:.2f} s from {len(r['acts'])} act(s) at {r['quality']} quality" + (f"; trimmed to the plan: {', '.join(r['trimmed'])}" if r["trimmed"] else ""))


def stage_check(p: Project, a) -> None:
    r = film_check.check_film(p)
    for name in ("delivery", "clutter", "ocr", "contact_sheet"):
        say(*check_summary(name, r[name]))
    if not r["ok"]:
        film_report.write_report(p)              # the report matters most when a check failed: write it before stopping
        raise FilmError("a check failed: see checks.json and REPORT.md, fix the worst miss, re-render only that stage and check again")


def check_summary(name: str, result: dict) -> tuple[str, str]:
    """(PASS | FAIL | SKIP, the line that says why): the first FAIL line of a failed check, the SKIP line of a skipped one."""
    kind = {"pass": "PASS", "fail": "FAIL", "skipped": "SKIP"}.get(result.get("status"), "PASS" if result["ok"] else "FAIL")
    lines = result["lines"]
    levels = ("PASS", "FAIL", "WARN", "SKIP", "INFO", "INCOMPLETE", "RESULT")
    body = lambda l: l.split(": ", 1)[1] if ": " in l and not l.startswith(levels) else l      # clutter lines start "A1: "
    want = {"FAIL": ("FAIL",), "SKIP": ("SKIP", "INCOMPLETE")}.get(kind, ())
    pick = next((l for l in lines if want and body(l).startswith(want)), None)
    return kind, f"{name}: " + (pick or (lines[-1] if lines else "no output"))


def stage_report(p: Project, a) -> None:
    say("PASS", f"{film_report.write_report(p).name} written")
    say("INFO", film_report.STAR)


FUNCS = {"story": stage_story, "script": stage_script, "storyboard": stage_storyboard, "assets": stage_assets, "voice": stage_voice, "retime": stage_retime,
         "build": stage_build, "captions": stage_captions, "mix": stage_mix, "render": stage_render, "check": stage_check, "report": stage_report}


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", nargs="?", choices=STAGES + ["run"], help="a stage, or run for all of them in order")
    ap.add_argument("--project", default=".", help="the project folder (default: here)")
    ap.add_argument("--from", dest="start", choices=STAGES, help="with run: start at this stage")
    ap.add_argument("--to", dest="end", choices=STAGES, help="with run: stop after this stage")
    ap.add_argument("--skip", default="", help="with run: comma-separated stages to leave out")
    ap.add_argument("--list", action="store_true", help="print the stages")
    ap.add_argument("--fps", help="storyboard (and retime, to change it): frame rate, e.g. 24, 25, 30, 29.97 or 30000/1001 (default 30); "
                                    "every later stage uses the storyboard's rate")
    ap.add_argument("--force", action="store_true", help="story: rewrite an existing STORY.md")
    ap.add_argument("--acts", type=int, help="storyboard: how many acts (default: one per 45 s)")
    ap.add_argument("--look", help="storyboard: the look (film mode builds the archive desk)")
    ap.add_argument("--no-fetch", action="store_true", help="assets: do not search for pictures (a beat with no picture becomes a title beat)")
    ap.add_argument("--delay", type=float, default=1.0, help="assets: seconds between requests to Commons and Openverse")
    ap.add_argument("--seed", type=int, default=0, help="assets: seed for the synthesised effects")
    ap.add_argument("--music", help="assets and mix: a music file")
    ap.add_argument("--music-query", help="assets: find CC0 or CC BY music (fetch_music.py)")
    ap.add_argument("--musicgen", help="assets: a MusicGen prompt, if audiocraft is installed (CC BY-NC weights: non-commercial)")
    ap.add_argument("--voice", choices=["standin", "take", "f5-tts"], help="voice: the source (default: STORY.md's voice: line, else standin)")
    ap.add_argument("--take", help="voice: your recording")
    ap.add_argument("--words", help="voice: word timings JSON for the take")
    ap.add_argument("--model", help="voice: a whisper.cpp model for whisper-cli")
    ap.add_argument("--ref-audio", help="voice f5-tts: a clean 5-12 s clip of the voice")
    ap.add_argument("--ref-text", help="voice f5-tts: what the clip says")
    ap.add_argument("--f5-model", default="F5TTS_v1_Base")
    ap.add_argument("--grid", help="retime: beat_grid.py analyze output")
    ap.add_argument("--snap-max", type=float, default=0.5)
    ap.add_argument("--burn-captions", action="store_true", help="build: burn captions into the picture (the credit line is dropped to stay under four text blocks)")
    ap.add_argument("--quality", choices=["draft", "looks", "delivery"], default="delivery")
    ap.add_argument("--workers", type=int, help="render: Chrome workers per act (default: 12 shared between the acts, at most 8 each)")
    ap.add_argument("--allow-unverified", action="store_true")
    return ap


def plan(a) -> list[str]:
    if a.stage != "run":
        return [a.stage]
    skip = {s.strip() for s in a.skip.split(",") if s.strip()}
    unknown = skip - set(STAGES)
    if unknown:
        raise FilmError(f"--skip names unknown stage(s): {', '.join(sorted(unknown))} (stages: {', '.join(STAGES)})")
    lo, hi = STAGES.index(a.start) if a.start else 0, STAGES.index(a.end) if a.end else len(STAGES) - 1
    return [s for s in STAGES[lo:hi + 1] if s not in skip]


def main(argv: list[str] | None = None) -> int:
    ap = parser()
    a = ap.parse_args(argv)
    if a.list or not a.stage:
        print("\n".join(STAGES))
        return 0 if a.list else 2
    p = Project(Path(a.project).resolve())
    try:
        stages = plan(a)
        for name in stages:
            if a.stage == "run":
                print(f"== {name}")
            FUNCS[name](p, a)
    except (FilmError, FetchError, ValueError, OSError, subprocess.SubprocessError, http.client.HTTPException) as err:
        print(f"FAIL  film: {err}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
