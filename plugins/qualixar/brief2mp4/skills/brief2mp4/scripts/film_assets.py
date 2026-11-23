"""film_assets.py: the assets stage: pictures, maps, sound effects and music for every beat, each recorded with its licence in ASSETS.json.

  archive pictures  a file the user gave (`asset:` in SCRIPT.md, recorded as supplied by the user) or a search by `query:`
                    through fetch_archive.py (public domain, CC0 and CC BY only). A beat whose picture cannot be had (no network,
                    nothing licensed found) becomes a typeset title beat and the report says so: film mode never invents a picture.
  maps              make_map.py from `region:`, `point:` and `route:`, as assets/maps/B02.svg; an inset locator map on a picture beat
  sound effects     sfx_synth.py: assets/sfx/*.wav and sfx.json (nothing to license)
  music             a track the user gives, a CC0 or CC BY track found through fetch_music.py, or MusicGen when the user installed it
                    (audiocraft: code MIT, model weights CC BY-NC, so non-commercial use only)

The storyboard comes back with each beat's `asset`, `map_file` and `inset_file` filled in. Standard library plus the scripts it calls.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_archive  # noqa: E402
import fetch_music  # noqa: E402
import make_map  # noqa: E402
import sfx_synth  # noqa: E402
from film_lib import FilmError, Project, save_json  # noqa: E402

PLATE = (1296, 740)
INSET = (420, 236)
MUSICGEN_INSTALL = "python3 -m pip install audiocraft"
MUSICGEN_NOTE = "Audiocraft code is MIT; the MusicGen model weights are CC BY-NC 4.0: non-commercial use only."
TODAY = datetime.date.today().isoformat


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _entry(project: Project, path: Path, kind: str, **fields) -> dict:
    base = {"file": project.rel(path), "kind": kind, "source": "", "source_url": "", "title": Path(path).name, "author": "", "licence": "", "licence_code": "",
            "licence_url": "", "attribution": "", "credit_required": False, "sha256": _sha(path), "retrieved": TODAY()}
    return {**base, **fields}


def supplied(project: Project, path: Path, kind: str) -> dict:
    return _entry(project, path, kind, source="user", author="supplied by the user", licence="supplied by the user (they confirm the right to use it)", licence_code="user")


def _inside(project: Project, path: Path, folder: Path) -> Path:
    """The file, copied into `folder` when it sits outside the project, so the project is self-contained."""
    path = Path(path)
    if not path.is_file():
        raise FilmError(f"asset not found: {path}")
    try:
        path.resolve().relative_to(project.root.resolve())
        return path
    except ValueError:
        folder.mkdir(parents=True, exist_ok=True)
        dest = folder / path.name
        shutil.copyfile(path, dest)
        return dest


def known_or_supplied(project: Project, path: Path, kind: str, prior: list[dict]) -> dict:
    """The entry ASSETS.json already holds for this file (same path or same SHA-256), else a new 'supplied by the user' one.

    A picture or track that an earlier run downloaded keeps its licence, author and credit when the stage runs again: only a
    file nobody has recorded yet is the user's own."""
    rel, sha = project.rel(path), _sha(path)
    same = [e for e in prior if e.get("kind") == kind and e.get("licence_code")]
    by_file = [e for e in same if e.get("file") == rel]
    by_sha = sorted((e for e in same if e.get("sha256") == sha), key=lambda e: e.get("licence_code") == "user")   # a credit beats "supplied"
    for e in by_file + by_sha:
        return {**e, "file": rel, "sha256": sha}
    return supplied(project, path, kind)


def archive_beat(project: Project, beat: dict, entries: list, warnings: list, fetch: bool, delay: float, prior: list[dict] | None = None) -> None:
    if beat["asset"]:
        path = _inside(project, project.p(beat["asset"]) if not Path(beat["asset"]).is_absolute() else Path(beat["asset"]), project.archive_dir)
        beat["asset"] = project.rel(path)
        if not any(e["file"] == beat["asset"] for e in entries):
            entries.append(known_or_supplied(project, path, "archive", prior or []))
        return
    found = []
    if fetch and beat["query"]:
        problems: list[str] = []
        found = fetch_archive.search(beat["query"], "both", 5, 1000, delay, warnings=problems)
        warnings += [f"{beat['id']}: {p}" for p in problems]
    if found:
        try:
            got = fetch_archive.download(found[0], project.archive_dir, project.assets, delay)
            beat["asset"] = got["file"]
            entries.append(got)
            return
        except fetch_archive.FetchError as err:
            warnings.append(f"{beat['id']}: the picture could not be downloaded ({err})")
    why = "fetching was skipped" if not fetch else "no public domain, CC0 or CC BY picture was found" if beat["query"] else "it has no picture"
    warnings.append(f"{beat['id']}: {why}: it is built as a typeset title beat. Add `asset:` with a picture you may use, or change `query:`")
    beat.update(kind="title", route="hyperframes:title", asset=None, inset=None)


def map_files(project: Project, beat: dict, entries: list, countries: list) -> None:
    for key, size, font, suffix in (("map", PLATE, 40, ""), ("inset", INSET, 24, "-inset")):
        spec = beat.get(key)
        if not spec:
            continue
        svg, meta = make_map.build_map(spec["region"], spec["points"], spec["routes"], size, countries, font, grid=key == "map")
        path = project.maps_dir / f"{beat['id']}{suffix}.svg"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg, encoding="utf-8", newline="\n")
        save_json(path.with_suffix(".json"), meta)
        beat[f"{key}_file"] = project.rel(path)
        entries.append(_entry(project, path, "map", source="Natural Earth", source_url="https://www.naturalearthdata.com", title=f"Map of {meta['region']}",
                              author="Natural Earth", licence="Public domain", licence_code="pdm", attribution="Map data: Natural Earth (public domain)"))


def sound_effects(project: Project, sb: dict, entries: list, seed: int) -> None:
    if not any(b.get("sound") for b in sb["beats"]):
        return
    if not (project.sfx_dir / "sfx.json").is_file():
        sfx_synth.write_all(project.sfx_dir, seed)
    entries.append(_entry(project, project.sfx_dir / "sfx.json", "sfx", source="brief2mp4 sfx_synth.py", title="Sound effects", author="synthesised in code",
                          licence="nothing to license (made from sine waves and seeded timing)", licence_code="synth"))


def musicgen(project: Project, prompt: str, seconds: float, python: str = sys.executable) -> Path:
    out = project.p("assets", "music", "musicgen")
    out.parent.mkdir(parents=True, exist_ok=True)
    code = ("from audiocraft.models import MusicGen\nfrom audiocraft.data.audio import audio_write\nimport sys\n"
            "m = MusicGen.get_pretrained('facebook/musicgen-small')\nm.set_generation_params(duration=min(30, float(sys.argv[2])))\n"
            "w = m.generate([sys.argv[1]])\naudio_write(sys.argv[3], w[0].cpu(), m.sample_rate, strategy='loudness')\n")
    done = subprocess.run([python, "-c", code, prompt, str(seconds), str(out)], capture_output=True, text=True)
    if done.returncode != 0:
        if "No module named" in done.stderr:
            raise FilmError(f"MusicGen is not installed. Install it with: {MUSICGEN_INSTALL}  ({MUSICGEN_NOTE}) Or use --music with your own track, or --music-query for CC0 and CC BY music.")
        raise FilmError(f"MusicGen failed: {done.stderr.strip()[-200:]}")
    return out.with_suffix(".wav")


def music(project: Project, entries: list, sb: dict, path: Path | None, query: str | None, prompt: str | None, prior: list[dict] | None = None) -> str | None:
    if path:
        dest = _inside(project, Path(path), project.p("assets", "music"))
        entries.append(known_or_supplied(project, dest, "music", prior or []))
        return project.rel(dest)
    if query:
        ns = argparse.Namespace(limit=5, category="music", min_seconds=max(30, sb["duration"] / 2), max_seconds=3600, retries=3, backoff=1.0)
        items = fetch_music.search(query, ns)
        if not items:
            raise FilmError(f"no CC0 or CC BY music found for '{query}': try other words, or give --music")
        dest, _ = fetch_music.download(items[0], str(project.p("assets", "music")), ns)
        item = items[0]
        lic = "CC0" if item["license"] == "cc0" else "Public domain" if item["license"] == "pdm" else f"CC BY {item.get('license_version', '')}".strip()
        entries.append(_entry(project, Path(dest), "music", source="openverse", source_url=item.get("foreign_landing_url", ""), title=item.get("title", ""),
                              author=item.get("creator") or "unknown", licence=lic, licence_code=item["license"], licence_url=item.get("license_url", ""),
                              attribution=item.get("attribution") or f'"{item.get("title", "")}" by {item.get("creator") or "unknown"}, {lic}',
                              credit_required=item["license"] == "by"))
        return project.rel(Path(dest))
    if prompt:
        dest = musicgen(project, prompt, sb["duration"])
        entries.append(_entry(project, dest, "music", source="MusicGen (audiocraft)", title=prompt[:60], author="generated", licence="MusicGen weights: CC BY-NC 4.0 (non-commercial use only)",
                              licence_code="cc-by-nc", attribution="Music generated with MusicGen (Meta). Non-commercial use only."))
        return project.rel(dest)
    return None


def run_assets(project: Project, sb: dict, fetch: bool = True, delay: float = 1.0, seed: int = 0, music_file: Path | None = None,
               music_query: str | None = None, music_prompt: str | None = None) -> dict:
    out = copy.deepcopy(sb)
    entries: list[dict] = []
    warnings: list[str] = []
    prior = fetch_archive.load_assets(project.assets)["assets"]
    countries = None
    for beat in out["beats"]:
        if beat["kind"] == "archive" or beat.get("asset") or beat.get("query"):
            archive_beat(project, beat, entries, warnings, fetch, delay, prior)
        if beat.get("map") or beat.get("inset"):
            countries = countries or make_map.load_countries()
            map_files(project, beat, entries, countries)
    sound_effects(project, out, entries, seed)
    out["music"] = music(project, entries, out, music_file, music_query, music_prompt, prior) if (music_file or music_query or music_prompt) else out.get("music")
    merged = [e for e in fetch_archive.load_assets(project.assets)["assets"] if e.get("kind") not in ("map", "sfx") and not any(x["file"] == e["file"] for x in entries)]
    for e in entries:
        merged = [m for m in merged if m["file"] != e["file"]] + [e]
    save_json(project.assets, {"version": 1, "assets": merged})
    out["warnings"] = merge_warnings(out.get("warnings", []), warnings)
    return out


def merge_warnings(old: list[str], new: list[str]) -> list[str]:
    """Earlier stages' warnings, then this run's, each once (running a stage again does not repeat its warnings)."""
    seen, merged = set(), []
    for w in list(old) + list(new):
        if w not in seen:
            seen.add(w)
            merged.append(w)
    return merged
