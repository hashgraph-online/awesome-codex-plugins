#!/usr/bin/env python3
"""Run Borzoi mini-model variant-effect prediction (fastpath).

Requires pre-downloaded model assets in --model-dir:
  params.json, model0_best.h5, hg38/targets.txt

Fetch these with:
  mkdir -p <model-dir>/hg38
  curl -L https://storage.googleapis.com/seqnn-share/borzoi/mini/human_gtex/f0/model0_best.h5 \
       -o <model-dir>/model0_best.h5
  curl -L https://storage.googleapis.com/seqnn-share/borzoi/mini/human_gtex/params.json \
       -o <model-dir>/params.json
  curl -L https://storage.googleapis.com/seqnn-share/borzoi/mini/human_gtex/hg38/targets.txt \
       -o <model-dir>/hg38/targets.txt
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


INTERVAL_RE = re.compile(r"(chr[\w]+):([0-9_,]+)-([0-9_,]+)", flags=re.IGNORECASE)
COORD_RE = re.compile(r"(chr[\w]+):([0-9_,]+)", flags=re.IGNORECASE)
VARIANT_RE = re.compile(r"(chr[\w]+):([0-9_,]+):?([ACGTNacgtn])>([ACGTNacgtn])", flags=re.IGNORECASE)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_int_token(raw: str) -> int:
    cleaned = re.sub(r"[_,\s]", "", raw)
    if not cleaned.isdigit():
        raise ValueError(f"Invalid integer token: {raw}")
    return int(cleaned)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Borzoi mini-model variant-effect prediction (fastpath)."
    )
    parser.add_argument("--chrom", default="chr12", help="Chromosome, default: chr12")
    parser.add_argument("--position", type=int, default=1_000_000, help="1-based position, default: 1000000")
    parser.add_argument("--ref", default=None, help="REF base. If omitted, fetched from UCSC.")
    parser.add_argument("--alt", default=None, help="ALT base. If omitted, uses to-G rule.")
    parser.add_argument(
        "--variant-spec",
        default=None,
        help="Canonical variant alias, e.g. chr12:1000000:T>G (overrides --chrom/--position/--ref/--alt).",
    )
    parser.add_argument("--assembly", default="hg38", help="Genome assembly for UCSC lookup, default: hg38")
    parser.add_argument(
        "--model-dir",
        required=True,
        help="Directory containing params.json, model0_best.h5, hg38/targets.txt.",
    )
    parser.add_argument(
        "--output-dir",
        default="output/borzoi",
        help="Output directory. Default: output/borzoi.",
    )
    parser.add_argument("--output-prefix", default=None, help="Custom output file prefix.")
    parser.add_argument(
        "--window-size",
        type=int,
        default=None,
        help="Optional input window size in bp. Defaults to model seq_length from params.json.",
    )
    parser.add_argument(
        "--max-plot-tracks",
        type=int,
        default=8,
        help="Max tracks to plot in trackplot. Default: 8.",
    )
    return parser.parse_args()


def fetch_ucsc_sequence(assembly: str, chrom: str, start_0based: int, end_0based: int) -> str:
    params = urllib.parse.urlencode({
        "genome": assembly,
        "chrom": chrom,
        "start": start_0based,
        "end": end_0based,
    })
    url = "https://api.genome.ucsc.edu/getData/sequence?" + params
    with urllib.request.urlopen(url, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    seq = str(payload.get("dna", "")).upper()
    if not seq:
        raise RuntimeError(f"UCSC returned no sequence: {payload}")
    return seq


def choose_alt(ref: str) -> str:
    return "T" if ref == "G" else "G"


def load_targets(targets_txt: Path) -> list[dict]:
    targets = []
    with targets_txt.open() as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            targets.append(row)
    return targets


def run_borzoi_forward(model, seqs_1hot: np.ndarray) -> np.ndarray:
    """Run Borzoi forward pass. Returns predictions array [batch, length, tracks]."""
    return model(seqs_1hot, dtype="float32")


def one_hot_encode(seq: str) -> np.ndarray:
    mapping = {"A": 0, "C": 1, "G": 2, "T": 3}
    arr = np.zeros((len(seq), 4), dtype=np.float32)
    for i, base in enumerate(seq):
        idx = mapping.get(base)
        if idx is not None:
            arr[i, idx] = 1.0
    return arr


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    chrom = args.chrom
    position = args.position
    ref = args.ref
    alt = args.alt
    normalization_steps: list[str] = []

    if args.variant_spec:
        m = VARIANT_RE.fullmatch(args.variant_spec.strip())
        if not m:
            raise SystemExit(f"Invalid --variant-spec: {args.variant_spec}")
        chrom = m.group(1)
        position = normalize_int_token(m.group(2))
        ref = m.group(3).upper()
        alt = m.group(4).upper()
        normalization_steps.append("variant-spec-overrides-chrom-position-ref-alt")

    model_dir = Path(args.model_dir)
    params_path = model_dir / "params.json"
    model_path = model_dir / "model0_best.h5"
    targets_path = model_dir / "hg38" / "targets.txt"

    for p in (params_path, model_path, targets_path):
        if not p.exists():
            raise SystemExit(f"Missing required model asset: {p}")

    with params_path.open() as fh:
        params = json.load(fh)

    model_seq_length = int(params.get("model", {}).get("seq_length", 0))
    window_size = args.window_size if args.window_size is not None else model_seq_length
    if model_seq_length and window_size != model_seq_length:
        print(
            f"[warn] overriding --window-size={window_size} to model seq_length={model_seq_length}",
            flush=True,
        )
        window_size = model_seq_length
    if window_size <= 0:
        raise ValueError("Unable to resolve a positive window size.")

    # Build window centered on variant
    half = window_size // 2
    win_start = max(0, position - 1 - half)  # convert to 0-based
    win_end = win_start + window_size

    print(f"[1/6] fetching REF sequence {chrom}:{win_start}-{win_end} from UCSC...", flush=True)
    ref_seq = fetch_ucsc_sequence(args.assembly, chrom, win_start, win_end)
    if len(ref_seq) != window_size:
        raise RuntimeError(f"Sequence length mismatch: expected {window_size}, got {len(ref_seq)}")

    variant_idx = position - 1 - win_start
    if ref is None:
        ref = ref_seq[variant_idx]
        normalization_steps.append("ref-fetched-from-ucsc")
    if alt is None:
        alt = choose_alt(ref)
        normalization_steps.append("alt-derived-by-to-G-rule")

    ref = ref.upper()
    alt = alt.upper()
    if ref_seq[variant_idx] != ref:
        raise RuntimeError(
            f"REF mismatch at {chrom}:{position}: expected {ref}, got {ref_seq[variant_idx]}"
        )
    if alt == ref:
        raise ValueError(f"ALT equals REF ({alt}); not a mutation.")

    alt_seq = ref_seq[:variant_idx] + alt + ref_seq[variant_idx + 1:]

    print("[2/6] loading Borzoi model...", flush=True)
    from baskerville import seqnn

    model = seqnn.SeqNN(params["model"])
    model.restore(str(model_path))
    print("[2/6] model loaded.", flush=True)

    print("[3/6] one-hot encoding sequences...", flush=True)
    ref_1hot = one_hot_encode(ref_seq)[np.newaxis]  # [1, L, 4]
    alt_1hot = one_hot_encode(alt_seq)[np.newaxis]

    print("[4/6] running REF forward pass...", flush=True)
    ref_preds = run_borzoi_forward(model, ref_1hot)[0]  # [L, tracks]
    print("[4/6] running ALT forward pass...", flush=True)
    alt_preds = run_borzoi_forward(model, alt_1hot)[0]

    sad = alt_preds - ref_preds  # [L, tracks]
    sad_scores = sad.mean(axis=0)  # per-track mean SAD

    print("[5/6] saving outputs...", flush=True)
    targets = load_targets(targets_path)

    prefix = args.output_prefix or f"borzoi_variant-effect_{chrom}_{position}_{ref}_to_{alt}"
    plot_path = out_dir / f"{prefix}_trackplot.png"
    tsv_path = out_dir / f"{prefix}_variant.tsv"
    npz_path = out_dir / f"{prefix}_tracks.npz"
    result_path = out_dir / f"{prefix}_result.json"

    # Save NPZ
    np.savez_compressed(npz_path, ref_preds=ref_preds, alt_preds=alt_preds, sad=sad)

    # Save TSV
    with tsv_path.open("w", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(["track_idx", "identifier", "description", "SAD"])
        for i, score in enumerate(sad_scores):
            t = targets[i] if i < len(targets) else {}
            writer.writerow([
                i,
                t.get("identifier", ""),
                t.get("description", ""),
                f"{score:.6g}",
            ])

    # Plot top tracks by absolute SAD
    top_n = min(args.max_plot_tracks, len(sad_scores))
    top_idx = np.argsort(np.abs(sad_scores))[::-1][:top_n]
    pred_len = ref_preds.shape[0]
    x = np.arange(pred_len)

    fig, axes = plt.subplots(top_n, 1, figsize=(18, max(2 * top_n, 6)), sharex=True)
    if top_n == 1:
        axes = [axes]
    for ax, idx in zip(axes, top_idx):
        t = targets[idx] if idx < len(targets) else {}
        label = t.get("description") or t.get("identifier") or f"track_{idx}"
        ax.fill_between(x, ref_preds[:, idx], alpha=0.6, label="REF")
        ax.fill_between(x, alt_preds[:, idx], alpha=0.6, label="ALT")
        ax.set_title(f"{label} (SAD={sad_scores[idx]:.4g})")
        ax.legend(loc="upper right", fontsize=7)
    axes[-1].set_xlabel(f"{chrom}:{win_start}-{win_end} ({args.assembly})")
    plt.suptitle(f"Borzoi variant effect: {chrom}:{position} {ref}>{alt}", fontsize=11)
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    plt.close(fig)

    result = {
        "skill_id": "borzoi-workflows",
        "task": "variant-effect",
        "run_time_utc": utc_now_iso(),
        "status": "success",
        "error": None,
        "model_dir": str(model_dir),
        "assembly": args.assembly,
        "chrom": chrom,
        "position_1based": position,
        "ref": ref,
        "alt": alt,
        "window_start_0based": win_start,
        "window_end_0based": win_end,
        "window_size": int(window_size),
        "coordinate_convention": {
            "position": "1-based",
            "window": "0-based [start, end)",
        },
        "input_normalization": {
            "variant_spec_raw": args.variant_spec,
            "chrom_raw": args.chrom,
            "position_raw": args.position,
            "ref_raw": args.ref,
            "alt_raw": args.alt,
            "normalization_steps": normalization_steps,
        },
        "resolved_inputs": {
            "assembly": args.assembly,
            "chrom": chrom,
            "position": position,
            "ref": ref,
            "alt": alt,
        },
        "num_tracks": int(sad_scores.shape[0]),
        "pred_length": int(pred_len),
        "ref_preds_shape": list(ref_preds.shape),
        "alt_preds_shape": list(alt_preds.shape),
        "sad_mean_across_tracks": float(np.mean(sad_scores)),
        "sad_max_abs_track_idx": int(top_idx[0]) if top_n > 0 else None,
        "plot_path": str(plot_path),
        "tsv_path": str(tsv_path),
        "npz_path": str(npz_path),
        "outputs": {
            "plot": str(plot_path),
            "tsv": str(tsv_path),
            "npz": str(npz_path),
            "result_json": str(result_path),
        },
    }

    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"[6/6] saved plot:   {plot_path}", flush=True)
    print(f"[6/6] saved TSV:    {tsv_path}", flush=True)
    print(f"[6/6] saved NPZ:    {npz_path}", flush=True)
    print(f"[6/6] saved result: {result_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
