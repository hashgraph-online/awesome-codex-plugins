#!/usr/bin/env python3
"""Run NTv3 post-trained track prediction on a genomic interval and save a plot."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run NTv3 post-trained inference for one genomic window and save "
            "a combined track plot + metadata JSON."
        )
    )
    parser.add_argument(
        "--model",
        default="InstaDeepAI/NTv3_100M_post",
        help="Hugging Face model id. Default: InstaDeepAI/NTv3_100M_post",
    )
    parser.add_argument("--species", default="human", help="Species condition token.")
    parser.add_argument("--assembly", default="hg38", help="Genome assembly for UCSC API.")
    parser.add_argument(
        "--interval",
        default=None,
        help="Canonical alias for interval, e.g. chr19:6700000-6732768 (0-based [start, end)).",
    )
    parser.add_argument("--chrom", default="chr19", help="Chromosome name.")
    parser.add_argument("--start", type=int, default=6_700_000, help="Start coordinate.")
    parser.add_argument("--end", type=int, default=6_732_768, help="End coordinate.")
    parser.add_argument(
        "--hf-token",
        default=None,
        help="Hugging Face token. If omitted, reads HF_TOKEN from env.",
    )
    parser.add_argument(
        "--output-dir",
        default="output/ntv3",
        help="Directory for output plot and metadata JSON.",
    )
    parser.add_argument(
        "--output-prefix",
        default=None,
        help=(
            "Custom output file prefix. Default: "
            "ntv3_<species>_<assembly>_<chrom>_<start>_<end>"
        ),
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda", "mps"],
        default="auto",
        help="Inference device. Default: auto.",
    )
    parser.add_argument(
        "--dtype",
        choices=["auto", "float32", "float16", "bfloat16"],
        default="auto",
        help="Inference dtype. Default: auto.",
    )
    parser.add_argument(
        "--disable-xet",
        action="store_true",
        help="Set HF_HUB_DISABLE_XET=1 for Hub download fallback.",
    )
    parser.add_argument(
        "--max-fallback-tracks",
        type=int,
        default=8,
        help="Number of fallback bigwig tracks when preferred ids are unavailable.",
    )
    parser.add_argument(
        "--save-npz",
        action="store_true",
        help="Save raw logits arrays to <prefix>_track_prediction.npz for downstream analysis.",
    )
    return parser.parse_args()


def choose_device(torch_mod, req: str) -> str:
    has_mps = (
        hasattr(torch_mod, "backends")
        and hasattr(torch_mod.backends, "mps")
        and torch_mod.backends.mps.is_available()
    )
    if req == "cpu":
        return "cpu"
    if req == "cuda":
        if not torch_mod.cuda.is_available():
            raise SystemExit("--device=cuda requested but CUDA is not available")
        return "cuda"
    if req == "mps":
        if not has_mps:
            raise SystemExit("--device=mps requested but MPS is not available")
        return "mps"

    if torch_mod.cuda.is_available():
        return "cuda"
    if has_mps:
        return "mps"
    return "cpu"


def choose_dtype(torch_mod, req: str, device: str):
    if req == "float32":
        return torch_mod.float32
    if req == "float16":
        return torch_mod.float16
    if req == "bfloat16":
        return torch_mod.bfloat16

    if device == "cuda":
        major, _ = torch_mod.cuda.get_device_capability(0)
        return torch_mod.bfloat16 if major >= 8 else torch_mod.float16
    if device == "mps":
        return torch_mod.float32
    return torch_mod.float32


DNA_RE = re.compile(r"[^ACGTN]")
INTERVAL_RE = re.compile(r"(chr[\w]+):([0-9_,]+)-([0-9_,]+)", flags=re.IGNORECASE)


def sanitize_dna(sequence: str) -> str:
    """Uppercase and replace non-ACGTN characters with N."""
    return DNA_RE.sub("N", sequence.upper())


def normalize_int_token(raw: str) -> int:
    cleaned = re.sub(r"[_,\s]", "", raw)
    if not cleaned.isdigit():
        raise ValueError(f"Invalid integer token: {raw}")
    return int(cleaned)


def parse_interval_spec(spec: str) -> tuple[str, int, int]:
    text = spec.strip()
    match = INTERVAL_RE.fullmatch(text)
    if not match:
        raise ValueError(
            f"Invalid --interval format: {spec}. Expected like chr19:6700000-6732768."
        )
    chrom = match.group(1)
    start = normalize_int_token(match.group(2))
    end = normalize_int_token(match.group(3))
    return chrom, start, end


def main() -> int:
    args = parse_args()
    chrom = args.chrom
    start = args.start
    end = args.end
    normalization_steps: list[str] = []

    if args.disable_xet:
        os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    hf_token = args.hf_token or os.getenv("HF_TOKEN")
    if not hf_token:
        raise SystemExit("HF token missing. Set HF_TOKEN or pass --hf-token.")

    if args.interval:
        chrom, start, end = parse_interval_spec(args.interval)
        normalization_steps.append("interval-overrides-chrom-start-end")

    if end <= start:
        raise SystemExit("--end must be greater than --start")

    import matplotlib

    matplotlib.use("Agg")

    import matplotlib.pyplot as plt
    import numpy as np
    import requests
    import seaborn as sns
    import torch
    from transformers import AutoConfig, AutoModel, AutoTokenizer

    device = choose_device(torch, args.device)
    requested_device = device
    if device == "mps":
        # Upstream NTv3 remote code currently calls torch.autocast(device_type=...),
        # and torch 2.2 on MPS can raise "unsupported autocast device_type 'mps'".
        # Keep CLI compatibility while ensuring execution remains stable.
        print("[1/6] requested device=mps; falling back to cpu for NTv3 runtime compatibility", flush=True)
        device = "cpu"
    dtype = choose_dtype(torch, args.dtype, device)

    print(f"[1/6] device={device}, dtype={dtype}", flush=True)
    print("[2/6] loading config/tokenizer/model from HF...", flush=True)

    config = AutoConfig.from_pretrained(args.model, trust_remote_code=True, token=hf_token)
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True, token=hf_token)
    model = AutoModel.from_pretrained(args.model, trust_remote_code=True, token=hf_token)

    num_downsamples = int(getattr(config, "num_downsamples", 7))
    divisor = 2 ** num_downsamples
    keep_fraction = float(getattr(config, "keep_target_center_fraction", 0.375))

    if device == "cuda":
        model = model.to(device=device, dtype=dtype)
    else:
        model = model.to(device=device)
    model.eval()

    url = (
        "https://api.genome.ucsc.edu/getData/sequence"
        f"?genome={args.assembly};chrom={chrom};start={start};end={end}"
    )
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    seq = sanitize_dna(resp.json()["dna"])

    orig_len = len(seq)
    seq = seq[: (len(seq) // divisor) * divisor]
    seq_len = len(seq)
    if seq_len == 0:
        raise SystemExit(
            f"Sequence length is zero after cropping to multiple of {divisor}. "
            "Use a longer interval."
        )

    print(
        f"[3/6] model loaded; num_downsamples={num_downsamples} divisor={divisor} "
        f"keep_fraction={keep_fraction}",
        flush=True,
    )
    print(f"[3/6] sequence original={orig_len}, cropped={seq_len}", flush=True)
    print("[4/6] tokenizing + inference...", flush=True)

    batch = tokenizer([seq], add_special_tokens=False, return_tensors="pt")
    input_ids = batch["input_ids"].to(device)
    try:
        species_ids = model.encode_species(args.species).to(device)
    except Exception as exc:
        supported_species = getattr(model, "supported_species", None)
        if supported_species is not None:
            raise SystemExit(
                f"Unknown species '{args.species}'. Supported species: {supported_species}"
            ) from exc
        raise

    with torch.no_grad():
        outs = model(input_ids=input_ids, species_ids=species_ids)

    if "bigwig_tracks_logits" not in outs or "bed_tracks_logits" not in outs:
        raise SystemExit(
            "Model outputs do not include track heads. Use a post-trained NTv3 checkpoint "
            "(for example InstaDeepAI/NTv3_100M_post)."
        )

    bigwig = outs["bigwig_tracks_logits"].detach().float().cpu().numpy()[0]
    bed_logits = outs["bed_tracks_logits"].detach().float().cpu().numpy()[0]
    logits = outs["logits"].detach().float().cpu().numpy()[0]

    print("[4/6] inference done", flush=True)
    print(
        f"[5/6] shapes logits={logits.shape}, bigwig={bigwig.shape}, bed={bed_logits.shape}",
        flush=True,
    )

    bigwig_by_species = getattr(config, "bigwigs_per_species", {})
    if args.species not in bigwig_by_species:
        raise SystemExit(
            f"Species '{args.species}' missing in config.bigwigs_per_species. "
            f"Available: {list(bigwig_by_species.keys())}"
        )
    bigwig_names = bigwig_by_species[args.species]
    bed_element_names = getattr(config, "bed_elements_names", [])

    preferred_tracks = {
        "K562 RNA-seq": "ENCSR056HPM",
        "K562 DNAse": "ENCSR921NMD",
        "K562 H3k4me3": "ENCSR000DWD",
        "K562 CTCF": "ENCSR000AKO",
        "HepG2 RNA-seq": "ENCSR561FEE_P",
        "HepG2 DNAse": "ENCSR000EJV",
        "HepG2 H3k4me3": "ENCSR000AMP",
        "HepG2 CTCF": "ENCSR000BIE",
    }

    tracks_to_plot = {k: v for k, v in preferred_tracks.items() if v in bigwig_names}
    if not tracks_to_plot:
        max_tracks = max(1, args.max_fallback_tracks)
        for i, tid in enumerate(bigwig_names[:max_tracks]):
            tracks_to_plot[f"{args.species}_track_{i + 1}"] = tid

    preferred_elements = [
        "protein_coding_gene",
        "exon",
        "intron",
        "splice_donor",
        "splice_acceptor",
    ]
    elements_to_plot = [e for e in preferred_elements if e in bed_element_names]
    if not elements_to_plot:
        elements_to_plot = bed_element_names[:5]

    bigwig_tracks = {}
    for label, tid in tracks_to_plot.items():
        idx = bigwig_names.index(tid)
        bigwig_tracks[label] = bigwig[:, idx]

    exp = np.exp(bed_logits - bed_logits.max(axis=-1, keepdims=True))
    probs = exp / exp.sum(axis=-1, keepdims=True)

    bed_probs = {}
    for elem in elements_to_plot:
        elem_idx = bed_element_names.index(elem)
        bed_probs[elem] = probs[:, elem_idx, 1]

    window_len = seq_len
    predicted_len = int(bigwig.shape[0])
    center_offset = max((window_len - predicted_len) // 2, 0)
    prediction_start = start + center_offset
    prediction_end = prediction_start + predicted_len

    all_tracks = {**bigwig_tracks, **bed_probs}
    if not all_tracks:
        raise SystemExit(
            "No tracks available to plot. Check species, model checkpoint, and track metadata."
        )

    fig, axes = plt.subplots(
        len(all_tracks),
        1,
        figsize=(20, max(1.4 * len(all_tracks), 6)),
        sharex=True,
    )
    if len(all_tracks) == 1:
        axes = [axes]

    x = np.linspace(prediction_start, prediction_end, num=next(iter(all_tracks.values())).shape[0])
    for ax, (title, y) in zip(axes, all_tracks.items()):
        ax.fill_between(x, y)
        ax.set_title(title)
        sns.despine(ax=ax, top=True, right=True, bottom=True)
    axes[-1].set_xlabel(f"{chrom}:{prediction_start}-{prediction_end} ({args.assembly})")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.output_prefix:
        prefix = args.output_prefix
    else:
        prefix = (
            f"ntv3_{args.species}_{args.assembly}_{chrom}_{start}_{end}"
        )

    plot_path = out_dir / f"{prefix}_trackplot.png"
    meta_path = out_dir / f"{prefix}_result.json"
    npz_path = out_dir / f"{prefix}_track_prediction.npz"

    plt.tight_layout()
    plt.savefig(plot_path, dpi=180)
    plt.close(fig)

    if args.save_npz:
        np.savez_compressed(
            npz_path,
            logits=logits,
            bigwig_tracks_logits=bigwig,
            bed_tracks_logits=bed_logits,
            bigwig_track_ids=np.array(bigwig_names, dtype=object),
            bed_element_names=np.array(bed_element_names, dtype=object),
            chrom=np.array([chrom], dtype=object),
            start=np.array([start], dtype=np.int64),
            end=np.array([end], dtype=np.int64),
            prediction_start=np.array([prediction_start], dtype=np.int64),
            prediction_end=np.array([prediction_end], dtype=np.int64),
            coordinate_convention=np.array(["[start, end) zero-based"], dtype=object),
        )

    meta = {
        "skill_id": "nucleotide-transformer-v3",
        "task": "track-prediction",
        "model_name": args.model,
        "species": args.species,
        "assembly": args.assembly,
        "chrom": chrom,
        "start": start,
        "end": end,
        "coordinate_convention": "[start, end) zero-based",
        "input_normalization": {
            "interval_raw": args.interval,
            "chrom_raw": args.chrom,
            "start_raw": args.start,
            "end_raw": args.end,
            "normalization_steps": normalization_steps,
        },
        "resolved_inputs": {
            "species": args.species,
            "assembly": args.assembly,
            "chrom": chrom,
            "start": start,
            "end": end,
            "requested_device": requested_device,
        },
        "sequence_length_original": orig_len,
        "sequence_length_used": seq_len,
        "num_downsamples": num_downsamples,
        "divisor": divisor,
        "keep_target_center_fraction": keep_fraction,
        "prediction_start": prediction_start,
        "prediction_end": prediction_end,
        "device": device,
        "dtype": str(dtype),
        "logits_shape": list(logits.shape),
        "bigwig_shape": list(bigwig.shape),
        "bed_shape": list(bed_logits.shape),
        "tracks_plotted": list(all_tracks.keys()),
        "plot_path": str(plot_path),
        "outputs": {
            "plot": str(plot_path),
            "npz": str(npz_path) if args.save_npz else None,
            "result_json": str(meta_path),
        },
    }

    with meta_path.open("w") as f:
        json.dump(meta, f, indent=2)

    print(f"[6/6] saved plot: {plot_path}", flush=True)
    if args.save_npz:
        print(f"[6/6] saved npz: {npz_path}", flush=True)
    print(f"[6/6] saved meta: {meta_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
