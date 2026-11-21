#!/usr/bin/env python3
"""Run Borzoi mini-model track prediction (fastpath).

Requires pre-downloaded model assets in --model-dir:
  params.json, model0_best.h5, hg38/targets.txt

Example:
  python skills/borzoi-workflows/scripts/run_borzoi_track_prediction.py \
    --interval chr19:6700000-6732768 \
    --assembly hg38 \
    --model-dir output/borzoi_fast \
    --output-dir case-study/borzoi \
    --output-prefix borzoi_track_chr19_6700000_6732768
"""

from __future__ import annotations

import argparse
import csv
import json
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


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_int_token(raw: str) -> int:
    cleaned = re.sub(r"[_,\s]", "", raw)
    if not cleaned.isdigit():
        raise ValueError(f"Invalid integer token: {raw}")
    return int(cleaned)


def parse_interval(interval: str) -> tuple[str, int, int]:
    matched = INTERVAL_RE.fullmatch(interval.strip())
    if not matched:
        raise ValueError(f"Invalid --interval: {interval}")
    chrom = matched.group(1)
    start = normalize_int_token(matched.group(2))
    end = normalize_int_token(matched.group(3))
    if end <= start:
        raise ValueError(f"Interval end must be greater than start: {interval}")
    return chrom, start, end


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Borzoi mini-model track prediction (fastpath).")
    parser.add_argument(
        "--interval",
        required=True,
        help="Genomic interval in chr:start-end format (0-based [start,end) recommended).",
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
    params = urllib.parse.urlencode(
        {
            "genome": assembly,
            "chrom": chrom,
            "start": start_0based,
            "end": end_0based,
        }
    )
    url = "https://api.genome.ucsc.edu/getData/sequence?" + params
    with urllib.request.urlopen(url, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    seq = str(payload.get("dna", "")).upper()
    if not seq:
        raise RuntimeError(f"UCSC returned no sequence: {payload}")
    return seq


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


def infer_output_window(
    win_start: int,
    window_size: int,
    pred_len: int,
    model_stride: int | None = None,
    model_target_crop: int | None = None,
) -> tuple[int, int, int | float]:
    if pred_len <= 0:
        raise ValueError("pred_len must be positive")
    if model_stride is not None and model_target_crop is not None:
        output_start = win_start + (model_target_crop * model_stride)
        output_end = output_start + (pred_len * model_stride)
        return output_start, output_end, int(model_stride)

    stride_float = window_size / pred_len
    stride_rounded = int(round(stride_float))
    if abs(stride_float - stride_rounded) < 1e-6:
        stride: int | float = stride_rounded
        output_span = pred_len * stride_rounded
    else:
        stride = stride_float
        output_span = window_size
    crop_bp = max(0, window_size - output_span)
    output_start = win_start + (crop_bp // 2)
    output_end = output_start + output_span
    return output_start, output_end, stride


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    chrom, interval_start, interval_end = parse_interval(args.interval)

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

    center = (interval_start + interval_end) // 2
    half = window_size // 2
    win_start = max(0, center - half)
    win_end = win_start + window_size

    print(f"[1/6] fetching sequence {chrom}:{win_start}-{win_end} from UCSC...", flush=True)
    seq = fetch_ucsc_sequence(args.assembly, chrom, win_start, win_end)
    if len(seq) != window_size:
        raise RuntimeError(f"Sequence length mismatch: expected {window_size}, got {len(seq)}")

    print("[2/6] loading Borzoi model...", flush=True)
    from baskerville import seqnn

    model = seqnn.SeqNN(params["model"])
    model.restore(str(model_path))
    print("[2/6] model loaded.", flush=True)

    print("[3/6] one-hot encoding sequence...", flush=True)
    seq_1hot = one_hot_encode(seq)[np.newaxis]  # [1, L, 4]

    print("[4/6] running forward pass...", flush=True)
    preds = run_borzoi_forward(model, seq_1hot)[0]  # [L, tracks]
    pred_len = preds.shape[0]
    num_tracks = preds.shape[1]
    model_stride = None
    model_target_crop = None
    if getattr(model, "model_strides", None):
        model_stride = int(model.model_strides[0])
    if getattr(model, "target_crops", None):
        model_target_crop = int(model.target_crops[0])
    output_start, output_end, stride = infer_output_window(
        win_start,
        window_size,
        pred_len,
        model_stride=model_stride,
        model_target_crop=model_target_crop,
    )
    track_scores = preds.mean(axis=0)

    print("[5/6] saving outputs...", flush=True)
    targets = load_targets(targets_path)
    top_n = min(args.max_plot_tracks, len(track_scores))
    top_idx = np.argsort(np.abs(track_scores))[::-1][:top_n]

    prefix = args.output_prefix or f"borzoi_track_{chrom}_{interval_start}_{interval_end}"
    npz_path = out_dir / f"{prefix}_track_prediction.npz"
    tsv_path = out_dir / f"{prefix}_top_tracks.tsv"
    plot_path = out_dir / f"{prefix}_trackplot.png"
    result_path = out_dir / f"{prefix}_result.json"

    np.savez_compressed(
        npz_path,
        preds=preds,
        track_scores=track_scores,
        top_idx=top_idx,
        input_window=np.array([win_start, win_end], dtype=np.int64),
        output_window=np.array([output_start, output_end], dtype=np.int64),
        interval=np.array([interval_start, interval_end], dtype=np.int64),
    )

    with tsv_path.open("w", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(["rank", "track_idx", "identifier", "description", "mean_signal", "abs_mean_signal"])
        for rank, idx in enumerate(top_idx, start=1):
            target = targets[idx] if idx < len(targets) else {}
            score = float(track_scores[idx])
            writer.writerow(
                [
                    rank,
                    int(idx),
                    target.get("identifier", ""),
                    target.get("description", ""),
                    f"{score:.6g}",
                    f"{abs(score):.6g}",
                ]
            )

    x = np.linspace(output_start, output_end, num=pred_len, endpoint=False)
    fig, axes = plt.subplots(top_n, 1, figsize=(18, max(2 * top_n, 6)), sharex=True)
    if top_n == 1:
        axes = [axes]
    for ax, idx in zip(axes, top_idx):
        target = targets[idx] if idx < len(targets) else {}
        label = target.get("description") or target.get("identifier") or f"track_{idx}"
        ax.fill_between(x, preds[:, idx], alpha=0.75, label=label)
        ax.axvspan(interval_start, interval_end, alpha=0.12, color="red", label="requested interval")
        ax.set_title(f"{label} (mean={track_scores[idx]:.4g})")
        ax.legend(loc="upper right", fontsize=7)
    axes[-1].set_xlabel(f"{chrom}:{output_start}-{output_end} ({args.assembly})")
    plt.suptitle(f"Borzoi track prediction: {chrom}:{interval_start}-{interval_end}", fontsize=11)
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    plt.close(fig)

    result = {
        "skill_id": "borzoi-workflows",
        "task": "track-prediction",
        "run_time_utc": utc_now_iso(),
        "status": "success",
        "error": None,
        "model_dir": str(model_dir),
        "assembly": args.assembly,
        "chrom": chrom,
        "requested_interval": [interval_start, interval_end],
        "input_window": [win_start, win_end],
        "output_window": [output_start, output_end],
        "window_size": int(window_size),
        "coordinate_convention": {
            "interval": "0-based [start, end)",
            "window": "0-based [start, end)",
        },
        "pred_shape": list(preds.shape),
        "pred_length": int(pred_len),
        "num_tracks": int(num_tracks),
        "stride": stride,
        "top_track_idx": int(top_idx[0]) if top_n > 0 else None,
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
