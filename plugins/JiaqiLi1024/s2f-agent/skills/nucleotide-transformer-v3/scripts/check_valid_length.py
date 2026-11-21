#!/usr/bin/env python3
"""Check whether an NTv3 sequence length satisfies the downsampling constraint."""

import argparse


def infer_num_downsamples(model_name: str) -> int:
    """Infer downsampling depth from common NTv3 model naming conventions."""
    lower_name = model_name.lower()
    if "5downsample" in lower_name:
        return 5
    return 7


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate NTv3 sequence lengths. Main 7-downsample models require "
            "length divisible by 128; 5-downsample models require length divisible by 32."
        )
    )
    parser.add_argument("length", type=int, help="Sequence length in nucleotides.")
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help=(
            "Optional NTv3 model name or HF id. If provided and --num-downsamples "
            "is omitted, downsampling depth is inferred from naming convention."
        ),
    )
    parser.add_argument(
        "--num-downsamples",
        type=int,
        default=None,
        help="Number of downsampling layers. Overrides --model inference when set.",
    )
    args = parser.parse_args()

    if args.length <= 0:
        raise SystemExit("length must be positive")
    if args.num_downsamples is not None and args.num_downsamples < 0:
        raise SystemExit("num-downsamples must be non-negative")

    if args.num_downsamples is not None:
        num_downsamples = args.num_downsamples
        source = "explicit"
    elif args.model:
        num_downsamples = infer_num_downsamples(args.model)
        source = f"model={args.model}"
    else:
        num_downsamples = 7
        source = "default"

    divisor = 2 ** num_downsamples
    remainder = args.length % divisor

    if remainder == 0:
        print(
            f"valid: length={args.length} is divisible by {divisor} "
            f"(num_downsamples={num_downsamples}, source={source})"
        )
        return 0

    lower = args.length - remainder
    upper = lower + divisor
    print(
        f"invalid: length={args.length} is not divisible by {divisor} "
        f"(num_downsamples={num_downsamples}, source={source})"
    )
    print(f"nearest_lower_valid={lower}")
    print(f"nearest_upper_valid={upper}")
    print("guidance=crop_to_lower_or_pad_with_N_to_upper")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
