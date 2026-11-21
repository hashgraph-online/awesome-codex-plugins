#!/usr/bin/env python3
"""Run SegmentNT on a genomic interval and save feature-probability tracks."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run SegmentNT inference on one genomic region and save a multi-track plot, "
            "a probability matrix (.npz), and metadata JSON."
        )
    )
    parser.add_argument("--model", default="segment_nt_multi_species")
    parser.add_argument("--species", default="human")
    parser.add_argument("--assembly", default="hg38")
    parser.add_argument(
        "--interval",
        default=None,
        help="Canonical alias for interval, e.g. chr19:6700000-6732768 (0-based [start, end)).",
    )
    parser.add_argument("--chrom", default="chr19")
    parser.add_argument("--start", type=int, default=6_700_000)
    parser.add_argument("--end", type=int, default=6_732_768)
    parser.add_argument(
        "--output-dir",
        default="output/segment-nt",
    )
    parser.add_argument("--output-prefix", default=None)
    parser.add_argument("--max-plotted-features", type=int, default=8)
    return parser.parse_args()


def token_count_without_cls(seq_len_bp: int, k_mer: int = 6) -> int:
    """SegmentNT tokenizer count for sequences without N."""
    return (seq_len_bp // k_mer) + (seq_len_bp % k_mer)


INTERVAL_RE = re.compile(r"(chr[\w]+):([0-9_,]+)-([0-9_,]+)", flags=re.IGNORECASE)


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


def choose_valid_length(seq_len_bp: int, k_mer: int = 6) -> int:
    """
    Find the nearest <= input length such that DNA token count (without CLS)
    is divisible by 4, as required by SegmentNT.
    """
    for delta in range(0, k_mer * 4 + 1):
        candidate = seq_len_bp - delta
        if candidate <= 0:
            break
        tokens_no_cls = token_count_without_cls(candidate, k_mer=k_mer)
        if tokens_no_cls % 4 == 0:
            return candidate
    raise SystemExit("Could not find a valid cropped length with token_count % 4 == 0")


def main() -> int:
    args = parse_args()
    chrom = args.chrom
    start = args.start
    end = args.end
    normalization_steps: list[str] = []

    if args.interval:
        chrom, start, end = parse_interval_spec(args.interval)
        normalization_steps.append("interval-overrides-chrom-start-end")

    if end <= start:
        raise SystemExit("--end must be greater than --start")

    import haiku as hk
    import jax
    import jax.numpy as jnp
    import matplotlib
    import matplotlib.pyplot as plt
    import numpy as np
    import requests
    import seaborn as sns
    from nucleotide_transformer.pretrained import get_pretrained_segment_nt_model

    matplotlib.use("Agg")
    jax.config.update("jax_platform_name", "cpu")

    print("[1/7] downloading sequence from UCSC API...", flush=True)
    url = (
        "https://api.genome.ucsc.edu/getData/sequence"
        f"?genome={args.assembly};chrom={chrom};start={start};end={end}"
    )
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    seq = resp.json()["dna"].upper()

    if "N" in seq:
        raise SystemExit("SegmentNT does not support 'N' in input sequence for this workflow.")

    raw_len = len(seq)
    valid_len = choose_valid_length(raw_len, k_mer=6)
    seq = seq[:valid_len]

    tokens_no_cls = token_count_without_cls(valid_len, k_mer=6)
    num_tokens_inference = tokens_no_cls + 1
    if tokens_no_cls % 4 != 0:
        raise SystemExit("Internal error: token_count_without_cls is not divisible by 4.")

    if valid_len > 30_000:
        rescaling_factor = num_tokens_inference / 2048.0
    else:
        rescaling_factor = None

    print(
        "[2/7] loading SegmentNT model "
        f"(model={args.model}, tokens={num_tokens_inference}, "
        f"rescaling_factor={rescaling_factor})...",
        flush=True,
    )
    parameters, forward_fn, tokenizer, config = get_pretrained_segment_nt_model(
        model_name=args.model,
        rescaling_factor=rescaling_factor,
        max_positions=num_tokens_inference,
    )

    print("[3/7] setting up Haiku/JAX inference...", flush=True)
    forward_fn = hk.transform(forward_fn)
    devices = jax.devices("cpu")
    num_devices = len(devices)
    apply_fn = jax.pmap(forward_fn.apply, devices=devices, donate_argnums=(0,))

    tokenized = tokenizer.batch_tokenize([seq])
    tokens_ids = [x[1] for x in tokenized]
    token_len = len(tokens_ids[0])
    if token_len != num_tokens_inference:
        raise SystemExit(
            f"Token length mismatch: expected {num_tokens_inference}, got {token_len}"
        )

    tokens = jnp.stack([jnp.asarray(tokens_ids, dtype=jnp.int32)] * num_devices, axis=0)
    keys = jax.device_put_replicated(jax.random.PRNGKey(0), devices=devices)
    parameters = jax.device_put_replicated(parameters, devices=devices)

    print("[4/7] running SegmentNT inference...", flush=True)
    outs = apply_fn(parameters, keys, tokens)
    logits = outs["logits"]

    print("[5/7] converting logits to feature probabilities...", flush=True)
    probs = np.asarray(jax.nn.softmax(logits, axis=-1))[..., -1]
    while probs.ndim > 2:
        probs = probs[0]
    if probs.ndim != 2:
        raise SystemExit(f"Unexpected probability shape after squeeze: {probs.shape}")

    feature_names = list(config.features)
    preferred = [
        "protein_coding_gene",
        "exon",
        "intron",
        "splice_donor",
        "splice_acceptor",
        "promoter",
        "enhancer",
        "CTCF_bound_site",
        "lncRNA",
    ]
    selected = [f for f in preferred if f in feature_names]
    if not selected:
        selected = feature_names[: max(1, args.max_plotted_features)]
    selected = selected[: max(1, args.max_plotted_features)]

    selected_probs = {name: probs[:, feature_names.index(name)] for name in selected}
    pred_len = next(iter(selected_probs.values())).shape[0]

    pred_start = start
    pred_end = start + valid_len
    x = np.linspace(pred_start, pred_end, num=pred_len, endpoint=False)

    print("[6/7] plotting selected tracks...", flush=True)
    fig, axes = plt.subplots(
        len(selected_probs),
        1,
        figsize=(20, max(1.5 * len(selected_probs), 6)),
        sharex=True,
    )
    if len(selected_probs) == 1:
        axes = [axes]
    for ax, (name, y) in zip(axes, selected_probs.items()):
        ax.fill_between(x, y)
        ax.set_title(name)
        sns.despine(ax=ax, top=True, right=True, bottom=True)
    axes[-1].set_xlabel(f"{chrom}:{pred_start}-{pred_end} ({args.assembly})")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.output_prefix:
        prefix = args.output_prefix
    else:
        prefix = (
            f"segmentnt_{args.species}_{args.assembly}_{chrom}_{start}_{end}"
        )

    plot_path = out_dir / f"{prefix}_trackplot.png"
    npz_path = out_dir / f"{prefix}_probs.npz"
    meta_path = out_dir / f"{prefix}_result.json"

    plt.tight_layout()
    plt.savefig(plot_path, dpi=180)
    plt.close(fig)

    np.savez_compressed(npz_path, probs=probs, feature_names=np.array(feature_names, dtype=object))

    meta = {
        "skill_id": "segment-nt",
        "task": "track-prediction",
        "model_name": args.model,
        "species": args.species,
        "species_note": "SegmentNT inference path here is not conditioned by a species token.",
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
            "model": args.model,
            "species": args.species,
            "assembly": args.assembly,
            "chrom": chrom,
            "start": start,
            "end": end,
        },
        "sequence_length_original": raw_len,
        "sequence_length_used": valid_len,
        "tokens_excluding_cls": tokens_no_cls,
        "num_tokens_inference": num_tokens_inference,
        "rescaling_factor": rescaling_factor,
        "prediction_start": pred_start,
        "prediction_end": pred_end,
        "logits_shape": list(np.asarray(logits).shape),
        "probs_shape": list(probs.shape),
        "num_features": len(feature_names),
        "plotted_features": selected,
        "plot_path": str(plot_path),
        "npz_path": str(npz_path),
        "outputs": {
            "plot": str(plot_path),
            "npz": str(npz_path),
            "result_json": str(meta_path),
        },
    }
    with meta_path.open("w") as f:
        json.dump(meta, f, indent=2)

    print(f"[7/7] saved plot: {plot_path}", flush=True)
    print(f"[7/7] saved matrix: {npz_path}", flush=True)
    print(f"[7/7] saved meta: {meta_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
