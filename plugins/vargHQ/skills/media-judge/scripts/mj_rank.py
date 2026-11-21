"""Rank takes on facts. Blockers first, then flags, then the margin to the references. Never a taste number."""
from __future__ import annotations

import json
from pathlib import Path

SEVERITY = {
    "decode_errors": "blocker", "black_frames": "blocker", "frozen_frames": "blocker", "glitch_frames": "blocker", "seam_shots": "major",
    "repeated_frames": "major", "flicker": "major", "flash_safety": "blocker", "upload_banding": "major",
    "spelling": "major", "expected_text": "blocker", "counter_jiggle": "major", "text_scale": "minor", "object_scale": "minor", "leads_the_eye": "minor",
    "text_load": "major", "frame_load": "minor", "reading_time": "major", "text_contrast": "major", "text_size_floor": "minor", "safe_zone": "major",
    "motion_cause": "minor", "constant_drift": "minor", "camera_shake": "minor", "pinned_graphics": "minor", "label_drift": "minor",
    "face_identity": "blocker", "face_drift": "major", "outfit_change": "major", "face_light_change": "minor", "light_between_shots": "minor",
    "sound_on_cut": "major", "loudness": "major", "clipping": "major", "audio_dropouts": "major", "audio_length": "major", "music_facts": "minor", "level_jumps": "minor",
    "voice_script": "blocker", "soft_shot": "minor", "template_vs_references": "major", "spec": "blocker",
    "image_exposure": "minor", "image_sharpness": "minor",
}
SKIP_STATES = {"info", "not_run"}


def summarize(facts: dict, overrides: dict | None = None) -> dict:
    """overrides is what eyes settled: {"overturned": {"check": "why"}, "eyes": [{"severity": "major", "t": 7.2, "what": "..."}]}"""
    overrides = overrides or {}
    gone = overrides.get("overturned", {})
    rows = {"blocker": [], "major": [], "minor": []}
    ran = passed = 0
    not_run = []
    for c in facts["checks"]:
        if c["state"] == "not_run":
            not_run.append(c["check"])
            continue
        if c["state"] == "info":
            continue
        ran += 1
        if c["state"] == "clear" or c["check"] in gone:
            passed += 1
        else:
            rows[SEVERITY.get(c["check"], "minor")].append(c["check"])
    for f in overrides.get("eyes", []):
        rows[f.get("severity", "minor")].append("eyes: " + str(f.get("what", ""))[:80])
    margin = None
    for c in facts["checks"]:
        if c["check"] == "template_vs_references":
            margin = c["measured"].get("margin")
    ref = None
    for c in facts["checks"]:
        if c["check"] == "reference_match":
            bl = [r.get("blend") for r in c["measured"].get("references", []) if r.get("blend") is not None]
            ref = min(bl) if bl else None
    return {"file": Path(facts["file"]).name, "blockers": rows["blocker"], "majors": rows["major"], "minors": rows["minor"], "checks_ran": ran, "checks_clear": passed,
            "not_run": not_run, "overturned": gone, "clear_share": round(passed / ran, 3) if ran else None, "template_margin": margin, "reference_distance": ref,
            "ship_state": "stopped" if rows["blocker"] else ("needs a look" if rows["major"] else "no measured defect")}


def order_key(s: dict):
    return (len(s["blockers"]), len(s["majors"]), len(s["minors"]),
            -(s["template_margin"] if s["template_margin"] is not None else 0),
            s["reference_distance"] if s["reference_distance"] is not None else 0)


def why(a: dict, b: dict) -> str:
    for key, label in (("blockers", "blockers"), ("majors", "major flags"), ("minors", "minor flags")):
        if len(a[key]) != len(b[key]):
            only_b = sorted(set(b[key]) - set(a[key]))
            return f"{len(a[key])} {label} against {len(b[key])}" + (f" (only the lower one has: {', '.join(only_b)})" if only_b else "")
    if a["template_margin"] != b["template_margin"] and a["template_margin"] is not None and b["template_margin"] is not None:
        return f"reference margin {a['template_margin']} against {b['template_margin']}"
    if a["reference_distance"] != b["reference_distance"] and a["reference_distance"] is not None and b["reference_distance"] is not None:
        return f"reference distance {a['reference_distance']} against {b['reference_distance']}"
    return "tied on every fact, so a pairwise look decides"


def rank(paths: list[str]) -> dict:
    sums = []
    for p in paths:
        pth = Path(p)
        if pth.is_dir():
            pth = pth / "facts.json"
        over = pth.parent / "overrides.json"
        sums.append(summarize(json.loads(pth.read_text()), json.loads(over.read_text()) if over.exists() else None))
    sums.sort(key=order_key)
    table = []
    for i, s in enumerate(sums):
        r = {"rank": i + 1, **s}
        if i + 1 < len(sums):
            r["ahead_of_next_because"] = why(s, sums[i + 1])
        table.append(r)
    return {"ranking": table, "method": "Blockers first, then major flags, then minor flags, then the reference margin. Counts of measured defects, not a taste score."}


def rank_md(result: dict) -> str:
    lines = ["# Ranking", "", result["method"], "", "| # | File | State | Blockers | Major | Minor | Checks clear | Reference margin |", "|---|---|---|---|---|---|---|---|"]
    for r in result["ranking"]:
        lines.append(f"| {r['rank']} | {r['file']} | {r['ship_state']} | {len(r['blockers'])} | {len(r['majors'])} | {len(r['minors'])} | {r['checks_clear']} of {r['checks_ran']} | {r['template_margin'] if r['template_margin'] is not None else 'n/a'} |")
    lines.append("")
    for r in result["ranking"]:
        lines.append(f"**{r['rank']}. {r['file']}**")
        if r["blockers"]:
            lines.append(f"- Blockers: {', '.join(r['blockers'])}")
        if r["majors"]:
            lines.append(f"- Major: {', '.join(r['majors'])}")
        if r["minors"]:
            lines.append(f"- Minor: {', '.join(r['minors'])}")
        for k, why_ in r.get("overturned", {}).items():
            lines.append(f"- Overturned by eyes: {k} ({why_})")
        if r["not_run"]:
            lines.append(f"- Did not run: {', '.join(r['not_run'])}")
        if "ahead_of_next_because" in r:
            lines.append(f"- Ahead of the next one: {r['ahead_of_next_because']}")
        lines.append("")
    return "\n".join(lines)
