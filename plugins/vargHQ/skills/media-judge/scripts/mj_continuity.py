"""Item 9: a face, outfit or light that changed between shots."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from mj_common import check, ciede2000, fetch_model, fmt_t, grab, label_frame, not_run, th

YUNET = ("face_detection_yunet_2023mar.onnx", "https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx")
SFACE = ("face_recognition_sface_2021dec.onnx", "https://huggingface.co/opencv/face_recognition_sface/resolve/main/face_recognition_sface_2021dec.onnx")


class Faces:
    def __init__(self):
        d = fetch_model(*YUNET)
        r = fetch_model(*SFACE)
        self.ok = bool(d and r)
        if self.ok:
            self.det = cv2.FaceDetectorYN.create(str(d), "", (320, 320), 0.7, 0.3, 50)
            self.rec = cv2.FaceRecognizerSF.create(str(r), "")

    def find(self, img: np.ndarray) -> list[dict]:
        h, w = img.shape[:2]
        self.det.setInputSize((w, h))
        _, faces = self.det.detect(img)
        out = []
        for row in (faces if faces is not None else []):
            x, y, fw, fh = row[:4]
            if fw < th("face_min_px") or fh < th("face_min_px"):
                continue
            feat = self.rec.feature(self.rec.alignCrop(img, row)).reshape(-1)
            feat = feat / max(np.linalg.norm(feat), 1e-6)
            out.append({"box": [float(x), float(y), float(fw), float(fh)], "feat": feat, "score": float(row[14]), "landmarks": row[4:14].tolist()})
        return out


def _clip(img, x, y, w, h):
    H, W = img.shape[:2]
    x0, y0, x1, y1 = max(int(x), 0), max(int(y), 0), min(int(x + w), W), min(int(y + h), H)
    return img[y0:y1, x0:x1]


def _median_lab(bgr: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(bgr.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab).reshape(-1, 3)
    return np.median(lab, axis=0)


def continuity_checks(path: str, probe, shots: list[dict], ev: Path, one_character: bool, groups: list[list[int]] | None) -> list[dict]:
    covers = "9 a face, outfit or light that changed between shots"
    fc = Faces()
    if not fc.ok:
        return [not_run("face_identity", covers, "Could not download the OpenCV face models.")]
    width = min(probe.width, 1280)
    per_shot = []
    for s in shots:
        if s["duration"] < 0.15:
            continue
        faces_here = []
        fracs = (0.15, 0.5, 0.85) if s["duration"] > 1 else (0.5,)
        for frac in fracs:
            t = s["start"] + frac * s["duration"]
            f = grab(path, t, width)
            if f is None:
                continue
            for face in fc.find(f):
                x, y, w, h = face["box"]
                crop = _clip(f, x - 0.2 * w, y - 0.2 * h, 1.4 * w, 1.4 * h)
                torso = _clip(f, x - 0.4 * w, y + 1.25 * h, 1.8 * w, 1.8 * h)
                torso_rows = torso.shape[0] if torso.size else 0
                skin = _clip(f, x + 0.1 * w, y + 0.2 * h, 0.8 * w, 0.7 * h)
                left = _clip(f, x + 0.1 * w, y + 0.25 * h, 0.35 * w, 0.5 * h)
                right = _clip(f, x + 0.55 * w, y + 0.25 * h, 0.35 * w, 0.5 * h)
                face.update(t=round(t, 3), crop=crop, shot=s["index"], frac=frac,
                            torso=_median_lab(torso) if torso_rows >= 0.35 * h else None,
                            light=_median_lab(skin) if skin.size > 100 else None,
                            side=float(cv2.cvtColor(left, cv2.COLOR_BGR2GRAY).mean() - cv2.cvtColor(right, cv2.COLOR_BGR2GRAY).mean()) if left.size and right.size else 0.0)
                faces_here.append(face)
        per_shot.append({"shot": s, "faces": faces_here})

    all_faces = [f for p in per_shot for f in p["faces"]]
    if not all_faces:
        return [check("face_identity", covers, "info", {"faces_found": 0}, note="No face large enough in any shot.")]

    # cluster by the published SFace threshold
    same = th("sface_same_cos")
    clusters: list[dict] = []
    for f in all_faces:
        best, best_cos = None, -1.0
        for c in clusters:
            cos = float(np.dot(f["feat"], c["centroid"]))
            if cos > best_cos:
                best, best_cos = c, cos
        if best is not None and best_cos >= same:
            best["members"].append(f)
            feats = np.stack([m["feat"] for m in best["members"]])
            cen = feats.mean(axis=0)
            best["centroid"] = cen / max(np.linalg.norm(cen), 1e-6)
        else:
            clusters.append({"centroid": f["feat"], "members": [f]})
    big = [c for c in clusters if len({m["shot"] for m in c["members"]}) >= 1]
    big.sort(key=lambda c: -len(c["members"]))

    id_events, drift_events = [], []
    # Faces inside one shot that stop matching: the person morphs while the camera rolls.
    for p in per_shot:
        fs = sorted(p["faces"], key=lambda f: -f["box"][2])
        by_frac: dict[float, dict] = {}
        for f in fs:
            by_frac.setdefault(f["frac"], f)
        keys = sorted(by_frac)
        if len(keys) >= 2:
            a, b = by_frac[keys[0]], by_frac[keys[-1]]
            cos = float(np.dot(a["feat"], b["feat"]))
            if cos < same:
                drift_events.append({"t": a["t"], "t_end": b["t"], "kind": "face changed inside a shot", "shot": p["shot"]["index"], "cosine": round(cos, 3),
                                     "evidence": _pair(a, b, ev / f"id_inshot_{p['shot']['index']}.jpg")})
    # The face between neighbouring shots.
    seq = [(p, max(p["faces"], key=lambda f: f["box"][2])) for p in per_shot if p["faces"]]
    pairs = []
    for (p1, a), (p2, b) in zip(seq, seq[1:]):
        cos = float(np.dot(a["feat"], b["feat"]))
        pairs.append({"from_shot": p1["shot"]["index"], "to_shot": p2["shot"]["index"], "cosine": round(cos, 3), "same_person": cos >= same})
    if one_character:
        for (p1, a), (p2, b) in zip(seq, seq[1:]):
            cos = float(np.dot(a["feat"], b["feat"]))
            if cos < same:
                id_events.append({"t": a["t"], "t_end": b["t"], "kind": "face changed between shots", "from_shot": p1["shot"]["index"], "to_shot": p2["shot"]["index"],
                                  "cosine": round(cos, 3), "evidence": _pair(a, b, ev / f"id_{p1['shot']['index']}_{p2['shot']['index']}.jpg")})
    state = "flagged" if id_events else ("clear" if one_character or len(big) <= 1 else "info")
    res = [check("face_identity", covers, state,
                 {"faces_measured": len(all_faces), "identities": len(big), "shots_with_face": len(seq),
                  "identity_sizes": [len(c["members"]) for c in big][:10], "neighbour_pairs": pairs[:40], "one_character_expected": one_character},
                 id_events[:12], ["sface_same_cos"],
                 note="Without --one-character, new identities are reported, not flagged, because a film can have many people.")]

    res.append(check("face_drift", covers, "flagged" if drift_events else "clear", {"shots_with_two_or_more_samples": sum(1 for p in per_shot if len({f["frac"] for f in p["faces"]}) >= 2)},
                     drift_events[:12], ["sface_same_cos"],
                     note="A morphing face and a title drawn across a face both read this way, so open the pair."))

    # Outfit and light for one identity across shots.
    outfit_ev, light_ev, ot_rows = [], [], []
    for c in big[:6]:
        by_shot: dict[int, dict] = {}
        for m in c["members"]:
            # Prefer a sample that shows clothing.
            if m["shot"] not in by_shot or (by_shot[m["shot"]]["torso"] is None and m["torso"] is not None):
                by_shot[m["shot"]] = m
        ordered = [by_shot[k] for k in sorted(by_shot)]
        for a, b in zip(ordered, ordered[1:]):
            if groups:
                if not any(a["shot"] in g and b["shot"] in g for g in groups):
                    continue
            elif b["shot"] - a["shot"] > 2:  # Far-apart shots of one person are usually different scenes.
                continue
            if a["torso"] is not None and b["torso"] is not None:
                de = ciede2000(a["torso"], b["torso"])
                ot_rows.append({"from_shot": a["shot"], "to_shot": b["shot"], "outfit_delta_e": round(de, 1)})
                if de > th("outfit_delta_e"):
                    outfit_ev.append({"t": a["t"], "t_end": b["t"], "from_shot": a["shot"], "to_shot": b["shot"], "outfit_delta_e": round(de, 1),
                                      "evidence": _pair(a, b, ev / f"outfit_{a['shot']}_{b['shot']}.jpg", below=True)})
            if a["light"] is not None and b["light"] is not None:
                dl = abs(float(a["light"][0] - b["light"][0]))
                flip = abs(a["side"] - b["side"]) > th("light_side_delta")
                if dl > th("face_light_l") or flip:
                    light_ev.append({"t": a["t"], "t_end": b["t"], "from_shot": a["shot"], "to_shot": b["shot"], "face_L_delta": round(dl, 1),
                                     "side_light_before": round(a["side"], 1), "side_light_after": round(b["side"], 1), "key_light_moved": bool(flip),
                                     "evidence": _pair(a, b, ev / f"light_{a['shot']}_{b['shot']}.jpg")})
    res.append(check("outfit_change", covers, "flagged" if outfit_ev else ("clear" if ot_rows else "info"), {"pairs": ot_rows[:30]}, outfit_ev[:10], ["outfit_delta_e"],
                     note="Measures the colour below the chin, so a close-up with no clothing in frame is not a test. A costume change in the story is fine, so open the pair."))
    res.append(check("face_light_change", covers, "flagged" if light_ev else ("clear" if ot_rows else "info"), {"events": len(light_ev)}, light_ev[:10], ["face_light_l", "light_side_delta"],
                     note="Side light is left cheek minus right cheek. A head turn moves it too, so open the pair."))
    return res


def _pair(a: dict, b: dict, out: Path, below: bool = False) -> str | None:
    ca, cb = a.get("crop"), b.get("crop")
    if ca is None or cb is None or ca.size == 0 or cb.size == 0:
        return None
    h = 320
    ca = label_frame(cv2.resize(ca, (int(ca.shape[1] * h / ca.shape[0]), h)), fmt_t(a["t"]))
    cb = label_frame(cv2.resize(cb, (int(cb.shape[1] * h / cb.shape[0]), h)), fmt_t(b["t"]))
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), cv2.hconcat([ca, cb]), [cv2.IMWRITE_JPEG_QUALITY, 90])
    return str(out)


def shot_colour_jumps(path: str, shots: list[dict], ev: Path, groups: list[list[int]] | None) -> list[dict]:
    """Average colour per shot. Report the biggest jumps; with --groups they become flags."""
    labs = []
    for s in shots:
        if s["duration"] < 0.1:
            labs.append(None)
            continue
        f = grab(path, s["start"] + 0.5 * s["duration"], 320)
        labs.append(_median_lab(f) if f is not None else None)
    rows, events = [], []
    for a, b, la, lb in zip(shots, shots[1:], labs, labs[1:]):
        if la is None or lb is None:
            continue
        de = ciede2000(la, lb)
        rows.append({"from_shot": a["index"], "to_shot": b["index"], "delta_e": round(de, 1), "t": b["start"]})
        same_group = bool(groups) and any(a["index"] in g and b["index"] in g for g in groups)
        if same_group and de > th("group_delta_e"):
            events.append({"t": b["start"], "from_shot": a["index"], "to_shot": b["index"], "delta_e": round(de, 1)})
    return [check("light_between_shots", "9 a face, outfit or light that changed between shots", "flagged" if events else ("clear" if groups else "info"),
                  {"biggest_jumps": sorted(rows, key=lambda r: -r["delta_e"])[:8]}, events[:10], ["group_delta_e"],
                  note="Pass --groups with shots that share a scene to turn these numbers into a test.")]
