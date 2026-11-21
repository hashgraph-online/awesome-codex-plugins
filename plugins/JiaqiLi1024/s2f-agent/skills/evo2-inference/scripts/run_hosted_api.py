#!/usr/bin/env python3
"""Run Evo2 generation through Nvidia hosted API from a local machine."""

import argparse
import json
import os
from typing import Any

import requests


DEFAULT_API_URL = "https://health.api.nvidia.com/v1/biology/arc/evo2-40b/generate"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Call Evo2 hosted API without local CUDA/GPU dependencies. "
            "Set NVCF_RUN_KEY (or EVO2_API_KEY) before running."
        )
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("EVO2_API_URL") or os.getenv("URL") or DEFAULT_API_URL,
        help=f"Hosted API URL. Default: {DEFAULT_API_URL}",
    )
    parser.add_argument(
        "--sequence",
        default=os.getenv("EVO2_SEQUENCE", "ACTGACTGACTGACTG"),
        help="DNA prompt sequence.",
    )
    parser.add_argument(
        "--num-tokens",
        type=int,
        default=int(os.getenv("EVO2_NUM_TOKENS", "8")),
        help="Number of tokens to generate. Default: 8.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=int(os.getenv("EVO2_TOP_K", "1")),
        help="Top-k sampling parameter. Default: 1.",
    )
    parser.add_argument(
        "--enable-sampled-probs",
        action="store_true",
        help="Request sampled probabilities from the API.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="HTTP timeout seconds. Default: 60.",
    )
    parser.add_argument(
        "--output-json",
        default="",
        help="Optional output path to save the full JSON response.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print request payload without sending HTTP request.",
    )
    return parser


def _load_api_key() -> str:
    return os.getenv("NVCF_RUN_KEY") or os.getenv("EVO2_API_KEY") or ""


def _print_preview(payload: dict[str, Any], api_url: str) -> None:
    print(f"api_url={api_url}")
    print(f"sequence_length={len(payload['sequence'])}")
    print(f"num_tokens={payload['num_tokens']}")
    print(f"top_k={payload['top_k']}")
    print(f"enable_sampled_probs={payload['enable_sampled_probs']}")


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.num_tokens <= 0:
        raise SystemExit("num-tokens must be positive")
    if args.top_k <= 0:
        raise SystemExit("top-k must be positive")
    if not args.sequence:
        raise SystemExit("sequence must not be empty")

    payload = {
        "sequence": args.sequence,
        "num_tokens": args.num_tokens,
        "top_k": args.top_k,
        "enable_sampled_probs": args.enable_sampled_probs,
    }
    _print_preview(payload, args.api_url)

    if args.dry_run:
        print("mode=dry_run")
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    api_key = _load_api_key()
    if not api_key:
        raise SystemExit(
            "Missing API key. Set NVCF_RUN_KEY (recommended) or EVO2_API_KEY first."
        )

    response = requests.post(
        url=args.api_url,
        headers={"Authorization": f"Bearer {api_key}"},
        json=payload,
        timeout=args.timeout,
    )

    print(f"http_status={response.status_code}")
    text_preview = response.text[:500].replace("\n", " ")
    print(f"response_preview={text_preview}")

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"saved_response={args.output_json}")

    if response.status_code >= 400:
        raise SystemExit("Hosted API request failed. Check API key, URL, and payload.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
