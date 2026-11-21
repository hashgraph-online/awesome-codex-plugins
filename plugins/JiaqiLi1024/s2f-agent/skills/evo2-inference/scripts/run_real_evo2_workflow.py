#!/usr/bin/env python3
"""Run real Evo2 hosted inference workflows and generate plots.

This script executes:
1) Forward + embedding + generation on a hg38 interval.
2) Variant-effect style comparison (REF vs ALT) on another hg38 locus.

Notes:
- Uses Nvidia hosted Evo2 API.
- Reads API key from NVCF_RUN_KEY or EVO2_API_KEY.
- Uses Evo2 7B endpoint because Evo2 40B forward may be temporarily degraded.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import time
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import requests


ENSEMBL_BASE = "https://rest.ensembl.org/sequence/region/human"
UCSC_BASE = "https://api.genome.ucsc.edu/getData/sequence"
EVO2_MODEL = "evo2-7b"
EVO2_BASE = f"https://health.api.nvidia.com/v1/biology/arc/{EVO2_MODEL}"
EVO2_GENERATE_FALLBACK_BASE = "https://health.api.nvidia.com/v1/biology/arc/evo2-40b"
EVO2_FORWARD_FALLBACK_BASE = "https://health.api.nvidia.com/v1/biology/arc/evo2-40b"
INTERVAL_RE = re.compile(r"(chr[\w]+):([0-9_,]+)-([0-9_,]+)", flags=re.IGNORECASE)
COORD_RE = re.compile(r"(chr[\w]+):([0-9_,]+)", flags=re.IGNORECASE)


def normalize_int_token(raw: str) -> int:
    cleaned = re.sub(r"[_,\s]", "", raw)
    if not cleaned.isdigit():
        raise ValueError(f"Invalid integer token: {raw}")
    return int(cleaned)


def parse_interval_0based(spec: str) -> tuple[str, int, int]:
    text = spec.strip()
    match = INTERVAL_RE.fullmatch(text)
    if not match:
        raise ValueError(
            f"Invalid --interval format: {spec}. Expected like chr19:6700000-6732768."
        )
    chrom = match.group(1)
    start = normalize_int_token(match.group(2))
    end = normalize_int_token(match.group(3))
    if end <= start:
        raise ValueError("Interval end must be greater than start")
    return chrom, start, end


def parse_coordinate_1based(spec: str) -> tuple[str, int]:
    text = spec.strip()
    match = COORD_RE.fullmatch(text)
    if not match:
        raise ValueError(
            f"Invalid --variant-coordinate format: {spec}. Expected like chr12:1000000."
        )
    chrom = match.group(1)
    position = normalize_int_token(match.group(2))
    if position <= 0:
        raise ValueError("Variant position must be positive (1-based).")
    return chrom, position


def normalize_chrom_for_workflow(chrom: str) -> str:
    if chrom.lower().startswith("chr"):
        return chrom[3:]
    return chrom


def fetch_hg38_sequence(chrom: str, start_1based: int, end_1based: int) -> str:
    """Fetch sequence from Ensembl GRCh38 (hg38), inclusive 1-based coords."""
    if start_1based <= 0 or end_1based < start_1based:
        raise ValueError("Invalid coordinate range")
    url = (
        f"{ENSEMBL_BASE}/{chrom}:{start_1based}..{end_1based}:1"
        "?coord_system_version=GRCh38"
    )
    seq = ""
    for attempt in range(1, 4):
        resp = requests.get(url, headers={"Content-Type": "text/plain"}, timeout=120)
        if resp.status_code == 200:
            seq = resp.text.strip().upper()
            break
        time.sleep(1.5 * attempt)

    if not seq:
        # Fallback: UCSC API uses 0-based half-open coords.
        ucsc_params = {
            "genome": "hg38",
            "chrom": f"chr{chrom}" if not chrom.startswith("chr") else chrom,
            "start": start_1based - 1,
            "end": end_1based,
        }
        ucsc_resp = requests.get(UCSC_BASE, params=ucsc_params, timeout=120)
        if ucsc_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to fetch sequence from Ensembl and UCSC. "
                f"Ensembl URL: {url}; UCSC status: {ucsc_resp.status_code}"
            )
        seq = ucsc_resp.json().get("dna", "").strip().upper()

    expected_len = end_1based - start_1based + 1
    if len(seq) != expected_len:
        raise RuntimeError(
            f"Sequence length mismatch: expected {expected_len}, got {len(seq)}"
        )
    return seq


def evo2_forward(api_key: str, sequence: str, output_layer: str) -> np.ndarray:
    """Call Evo2 forward endpoint and decode a single requested output layer.

    Tries evo2-7b first, then falls back to evo2-40b when forward on 7b is degraded.
    """
    payload = {"sequence": sequence, "output_layers": [output_layer]}
    bases = [EVO2_BASE, EVO2_FORWARD_FALLBACK_BASE]
    all_errors = []

    for base in bases:
        resp = None
        last_err = None
        for attempt in range(1, 4):
            print(f"[forward] try base={base.rsplit('/', 1)[-1]} attempt={attempt}", flush=True)
            try:
                resp = requests.post(
                    f"{base}/forward",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=payload,
                    timeout=180,
                )
            except requests.RequestException as exc:
                last_err = f"base={base}, attempt={attempt}, request_error={type(exc).__name__}: {exc}"
                time.sleep(1.5 * attempt)
                continue
            if resp.status_code == 200:
                data_b64 = resp.json()["data"]
                raw = base64.b64decode(data_b64)
                with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                    names = zf.namelist()
                    target = None
                    for name in names:
                        if name.startswith(f"{output_layer}.") and name.endswith(".npy"):
                            target = name
                            break
                    if target is None:
                        raise RuntimeError(
                            f"Layer {output_layer} not found in forward response from {base}"
                        )
                    return np.load(io.BytesIO(zf.read(target)))

            last_err = (
                f"base={base}, attempt={attempt}, status={resp.status_code}, body={resp.text}"
            )
            time.sleep(1.5 * attempt)

        if last_err:
            all_errors.append(last_err)
        else:
            all_errors.append(f"base={base}, unknown error")

    raise RuntimeError("Forward request failed: " + " | ".join(all_errors))


def evo2_generate(
    api_key: str,
    sequence: str,
    num_tokens: int = 64,
    top_k: int = 1,
) -> tuple[dict, str]:
    payload = {
        "sequence": sequence,
        "num_tokens": num_tokens,
        "top_k": top_k,
        "enable_sampled_probs": True,
    }
    bases = [EVO2_BASE, EVO2_GENERATE_FALLBACK_BASE]
    all_errors = []

    for base in bases:
        resp = None
        last_err = None
        for attempt in range(1, 3):
            print(f"[interval] generate try base={base.rsplit('/', 1)[-1]} attempt={attempt}", flush=True)
            resp = requests.post(
                f"{base}/generate",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
                timeout=45,
            )
            if resp.status_code == 200:
                model_used = base.rsplit("/", 1)[-1]
                return resp.json(), model_used
            last_err = f"base={base}, attempt={attempt}, status={resp.status_code}, body={resp.text}"
            time.sleep(1.5 * attempt)
        all_errors.append(last_err or f"base={base}, unknown error")

    raise RuntimeError("Generate request failed: " + " | ".join(all_errors))


def compute_chunked_tracks(api_key: str, sequence: str, chunk_size: int) -> tuple[np.ndarray, np.ndarray]:
    """Compute forward and embedding tracks for long sequences via chunking.

    Returns:
    - forward_top1_track: per-position max logit from unembed output.
    - embedding_norm_track: per-position L2 norm from embedding layer.
    """
    f_tracks = []
    e_tracks = []

    total_chunks = (len(sequence) + chunk_size - 1) // chunk_size
    for chunk_i, left in enumerate(range(0, len(sequence), chunk_size), start=1):
        right = min(left + chunk_size, len(sequence))
        chunk = sequence[left:right]
        print(
            f"[interval] chunk {chunk_i}/{total_chunks} start={left} end={right} len={len(chunk)}",
            flush=True,
        )

        unembed = evo2_forward(api_key, chunk, "unembed")  # [1, L, 512]
        forward_top1 = unembed[0].max(axis=-1)
        f_tracks.append(forward_top1)

        embeddings = evo2_forward(api_key, chunk, "embedding_layer")  # [1, L, 4096]
        emb_norm = np.linalg.norm(embeddings[0], axis=-1)
        e_tracks.append(emb_norm)

    return np.concatenate(f_tracks), np.concatenate(e_tracks)


def variant_alt_base(reference_base: str) -> str:
    """Rule requested by user: mutate to G; if REF is already G then mutate to T."""
    return "T" if reference_base == "G" else "G"


def run_interval_workflow(
    api_key: str,
    chrom: str,
    start_0based: int,
    end_0based: int,
    output_dir: Path,
    chunk_size: int,
) -> dict:
    """Run forward + embedding + generation on a genomic interval."""
    # Convert [start, end) 0-based -> 1-based inclusive.
    start_1based = start_0based + 1
    end_1based = end_0based
    sequence = fetch_hg38_sequence(chrom, start_1based, end_1based)

    print("[interval] fetching hg38 sequence", flush=True)
    forward_track, embedding_track = compute_chunked_tracks(
        api_key=api_key,
        sequence=sequence,
        chunk_size=chunk_size,
    )

    generation_prompt = sequence[-512:]
    print(
        f"[interval] running generation with prompt_len={len(generation_prompt)} (suffix of target interval)",
        flush=True,
    )
    generation, generation_model = evo2_generate(
        api_key, generation_prompt, num_tokens=64, top_k=1
    )
    generated_seq = generation.get("sequence", "")
    sampled_probs = np.array(generation.get("sampled_probs", []), dtype=float)

    genomic_x = np.arange(start_0based, end_0based, dtype=int)
    fig, axes = plt.subplots(3, 1, figsize=(15, 10), sharex=False)

    axes[0].plot(genomic_x, forward_track, color="#1f77b4", linewidth=0.8)
    axes[0].set_title(f"Evo2 Forward (top-1 logits) on hg38 {chrom}:{start_0based:,}-{end_0based:,}")
    axes[0].set_ylabel("Top-1 logit")
    axes[0].grid(alpha=0.25)

    axes[1].plot(genomic_x, embedding_track, color="#ff7f0e", linewidth=0.8)
    axes[1].set_title("Evo2 Embedding Layer Norm")
    axes[1].set_ylabel("L2 norm")
    axes[1].grid(alpha=0.25)

    if sampled_probs.size > 0:
        axes[2].bar(np.arange(sampled_probs.size), sampled_probs, color="#2ca02c")
        axes[2].set_ylim(0, 1.0)
        axes[2].set_ylabel("Sampled prob")
        axes[2].set_xlabel("Generated token index")
        axes[2].set_title(f"Generation sampled_probs (generated {len(generated_seq)} chars)")
    else:
        axes[2].text(
            0.02,
            0.5,
            "No sampled_probs returned by API",
            transform=axes[2].transAxes,
            fontsize=11,
        )
        axes[2].set_axis_off()

    plt.tight_layout()
    plot_path = output_dir / "evo2_chr19_forward_embedding_generation.png"
    fig.savefig(plot_path, dpi=180)
    plt.close(fig)

    return {
        "skill_id": "evo2-inference",
        "task": "embedding",
        "model": EVO2_MODEL,
        "assembly": "hg38",
        "chrom": chrom,
        "start_0based": start_0based,
        "end_0based": end_0based,
        "sequence_length": len(sequence),
        "generation_prompt_length": len(generation_prompt),
        "forward_track_mean": float(np.mean(forward_track)),
        "forward_track_std": float(np.std(forward_track)),
        "embedding_track_mean": float(np.mean(embedding_track)),
        "embedding_track_std": float(np.std(embedding_track)),
        "generation_sequence": generated_seq,
        "generation_model_used": generation_model,
        "generation_sampled_probs_mean": float(np.mean(sampled_probs)) if sampled_probs.size else None,
        "plot_path": str(plot_path),
        "outputs": {
            "plot": str(plot_path),
            "npz": None,
            "result_json": None,
        },
    }


def run_variant_workflow(
    api_key: str,
    chrom: str,
    position_1based: int,
    output_dir: Path,
    window_len: int,
) -> dict:
    """Run REF vs ALT variant-effect style analysis and plot results."""
    if window_len % 2 != 0:
        raise ValueError("window_len must be even")

    ref_base = fetch_hg38_sequence(chrom, position_1based, position_1based)
    alt_base = variant_alt_base(ref_base)

    half = window_len // 2
    start_1based = position_1based - half + 1
    end_1based = start_1based + window_len - 1
    ref_window = fetch_hg38_sequence(chrom, start_1based, end_1based)
    variant_index = position_1based - start_1based

    if ref_window[variant_index] != ref_base:
        raise RuntimeError("Reference base mismatch at variant index")

    alt_window = (
        ref_window[:variant_index] + alt_base + ref_window[variant_index + 1 :]
    )

    print("[variant] running forward REF/ALT", flush=True)
    ref_unembed = evo2_forward(api_key, ref_window, "unembed")[0]
    alt_unembed = evo2_forward(api_key, alt_window, "unembed")[0]
    ref_top1 = ref_unembed.max(axis=-1)
    alt_top1 = alt_unembed.max(axis=-1)
    delta_top1 = alt_top1 - ref_top1

    print("[variant] running embeddings REF/ALT", flush=True)
    ref_emb = evo2_forward(api_key, ref_window, "embedding_layer")[0]
    alt_emb = evo2_forward(api_key, alt_window, "embedding_layer")[0]
    delta_emb_norm = np.linalg.norm(alt_emb - ref_emb, axis=-1)

    genomic_x = np.arange(start_1based, end_1based + 1, dtype=int)

    fig, axes = plt.subplots(3, 1, figsize=(15, 10), sharex=True)
    axes[0].plot(genomic_x, ref_top1, label=f"REF ({ref_base})", color="#4c78a8", linewidth=0.9)
    axes[0].plot(genomic_x, alt_top1, label=f"ALT ({alt_base})", color="#e45756", linewidth=0.9, alpha=0.9)
    axes[0].axvline(position_1based, color="black", linestyle="--", linewidth=1.0)
    axes[0].set_title(f"Evo2 Variant Effect Proxy on hg38 {chrom}:{position_1based:,}")
    axes[0].set_ylabel("Top-1 logit")
    axes[0].legend(loc="upper right")
    axes[0].grid(alpha=0.25)

    axes[1].plot(genomic_x, delta_top1, color="#72b7b2", linewidth=0.9)
    axes[1].axvline(position_1based, color="black", linestyle="--", linewidth=1.0)
    axes[1].set_ylabel("ALT - REF (logit)")
    axes[1].set_title("Forward Delta Track")
    axes[1].grid(alpha=0.25)

    axes[2].plot(genomic_x, delta_emb_norm, color="#f58518", linewidth=0.9)
    axes[2].axvline(position_1based, color="black", linestyle="--", linewidth=1.0)
    axes[2].set_ylabel("||ALT - REF||")
    axes[2].set_xlabel(f"Genomic coordinate ({chrom}, hg38)")
    axes[2].set_title("Embedding Delta Norm Track")
    axes[2].grid(alpha=0.25)

    plt.tight_layout()
    plot_path = output_dir / "evo2_chr12_variant_effect.png"
    fig.savefig(plot_path, dpi=180)
    plt.close(fig)

    return {
        "skill_id": "evo2-inference",
        "task": "variant-effect",
        "model": EVO2_MODEL,
        "assembly": "hg38",
        "chrom": chrom,
        "position_1based": position_1based,
        "reference_base": ref_base,
        "alternate_base": alt_base,
        "window_start_1based": start_1based,
        "window_end_1based": end_1based,
        "window_len": window_len,
        "delta_top1_at_variant": float(delta_top1[variant_index]),
        "delta_emb_norm_at_variant": float(delta_emb_norm[variant_index]),
        "plot_path": str(plot_path),
        "outputs": {
            "plot": str(plot_path),
            "npz": None,
            "result_json": None,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run real Evo2 hosted workflows with plots.")
    parser.add_argument(
        "--output-dir",
        default="output/evo2",
        help="Directory for generated plots and JSON outputs.",
    )
    parser.add_argument(
        "--interval-chunk-size",
        type=int,
        default=1024,
        help="Chunk size used for long-interval forward/embedding requests.",
    )
    parser.add_argument(
        "--variant-window-len",
        type=int,
        default=2048,
        help="Window length around variant for REF/ALT comparison (even number).",
    )
    parser.add_argument(
        "--interval",
        default="chr19:6700000-6732768",
        help="Canonical interval alias for interval workflow, 0-based [start, end).",
    )
    parser.add_argument(
        "--variant-coordinate",
        default="chr12:1000000",
        help="Canonical coordinate alias for variant workflow, 1-based single-site coordinate.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    api_key = os.getenv("NVCF_RUN_KEY") or os.getenv("EVO2_API_KEY")
    if not api_key:
        raise SystemExit("Missing API key: set NVCF_RUN_KEY or EVO2_API_KEY")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    interval_chrom_raw, interval_start_0based, interval_end_0based = parse_interval_0based(
        args.interval
    )
    variant_chrom_raw, variant_position_1based = parse_coordinate_1based(args.variant_coordinate)
    interval_chrom = normalize_chrom_for_workflow(interval_chrom_raw)
    variant_chrom = normalize_chrom_for_workflow(variant_chrom_raw)

    print(f"[run] model={EVO2_MODEL}", flush=True)
    interval_result = run_interval_workflow(
        api_key=api_key,
        chrom=interval_chrom,
        start_0based=interval_start_0based,
        end_0based=interval_end_0based,
        output_dir=output_dir,
        chunk_size=args.interval_chunk_size,
    )

    print("[run] interval workflow done", flush=True)
    variant_result = run_variant_workflow(
        api_key=api_key,
        chrom=variant_chrom,
        position_1based=variant_position_1based,
        output_dir=output_dir,
        window_len=args.variant_window_len,
    )

    result = {
        "coordinate_convention": {
            "interval": "0-based [start, end)",
            "variant_position": "1-based",
        },
        "input_normalization": {
            "interval_raw": args.interval,
            "variant_coordinate_raw": args.variant_coordinate,
            "interval_chrom_raw": interval_chrom_raw,
            "variant_chrom_raw": variant_chrom_raw,
            "normalization_steps": [
                "interval-coordinate-parsed",
                "variant-coordinate-parsed",
                "chrom-normalized-by-removing-chr-prefix-for-ensembl-paths",
            ],
        },
        "resolved_inputs": {
            "interval": {
                "chrom": interval_chrom,
                "start_0based": interval_start_0based,
                "end_0based": interval_end_0based,
            },
            "variant": {
                "chrom": variant_chrom,
                "position_1based": variant_position_1based,
                "window_len": args.variant_window_len,
            },
        },
        "interval_forward_embeddings_generation": interval_result,
        "variant_effect_proxy": variant_result,
    }
    json_path = output_dir / "evo2_real_workflow_results.json"
    # backfill result_json now that path is known
    result["interval_forward_embeddings_generation"]["outputs"]["result_json"] = str(json_path)
    result["variant_effect_proxy"]["outputs"]["result_json"] = str(json_path)
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"model={EVO2_MODEL}")
    print(f"interval_plot={interval_result['plot_path']}")
    print(f"variant_plot={variant_result['plot_path']}")
    print(f"results_json={json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
    print("[run] variant workflow done", flush=True)
