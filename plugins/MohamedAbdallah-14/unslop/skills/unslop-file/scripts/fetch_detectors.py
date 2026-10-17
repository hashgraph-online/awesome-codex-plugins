"""Bootstrap: download and cache AI-text detector weights.

Runs as a standalone script. Downloads the model into the HuggingFace cache
($HF_HOME or ~/.cache/huggingface), after which `detector.py` can load offline.

Usage:
  python3 -m unslop.scripts.fetch_detectors            # fetches TMR (default, ~500MB)
  python3 -m unslop.scripts.fetch_detectors --all      # fetches TMR + Desklib (~2GB)
  python3 -m unslop.scripts.fetch_detectors --detector desklib

Not called from the hot path. Opt-in so a fresh install doesn't force a
multi-gigabyte download on first `unslop` invocation.
"""

from __future__ import annotations

import argparse
import sys


def _fetch(model_id: str) -> int:
    try:
        from transformers import (  # noqa: F401
            AutoConfig,
            AutoModel,
            AutoModelForSequenceClassification,
            AutoTokenizer,
        )
    except ImportError as exc:
        print(
            f"Missing dependency: {exc.name}. Install with:\n"
            "  pip install torch transformers huggingface_hub safetensors",
            file=sys.stderr,
        )
        return 1
    print(f"Fetching {model_id} ...")
    try:
        AutoTokenizer.from_pretrained(model_id)
    except Exception as exc:
        print(f"  tokenizer fetch failed: {exc}", file=sys.stderr)
        return 2
    try:
        # TMR is a standard sequence classifier; Desklib has a custom head
        # loaded via safetensors inside detector.py. Either way the encoder
        # weights download through AutoModel / from_config.
        if "tmr" in model_id.lower():
            AutoModelForSequenceClassification.from_pretrained(model_id)
        else:
            from huggingface_hub import hf_hub_download

            AutoConfig.from_pretrained(model_id)
            hf_hub_download(model_id, "model.safetensors")
    except Exception as exc:
        print(f"  model fetch failed: {exc}", file=sys.stderr)
        return 2
    print(f"  {model_id} cached.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--detector",
        default="tmr",
        choices=("tmr", "desklib"),
        help="Which detector to fetch. TMR is the default (smaller).",
    )
    p.add_argument(
        "--all",
        action="store_true",
        help="Fetch both TMR and Desklib. About 2GB total on first run.",
    )
    args = p.parse_args(argv)

    ids: list[str] = []
    if args.all:
        ids = ["Oxidane/tmr-ai-text-detector", "desklib/ai-text-detector-v1.01"]
    elif args.detector == "tmr":
        ids = ["Oxidane/tmr-ai-text-detector"]
    elif args.detector == "desklib":
        ids = ["desklib/ai-text-detector-v1.01"]

    rc = 0
    for model_id in ids:
        rc |= _fetch(model_id)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
