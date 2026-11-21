#!/usr/bin/env python3
"""Generate cover and per-type infographics via external image generation API.

Supports single-image mode (--prompt) and batch mode (--batch manifest.json).

Usage:
    # Single image
    python3 skills/gen-infographic/scripts/gen_infographic.py --prompt "9:16 portrait infographic, MorningAI ..." -o cover.png

    # Batch mode (multiple images from manifest)
    python3 skills/gen-infographic/scripts/gen_infographic.py --batch manifest.json

    # Pipe prompt via stdin
    echo "prompt text" | python3 skills/gen-infographic/scripts/gen_infographic.py --provider minimax

Manifest JSON format:
    [
      {"prompt": "9:16 portrait infographic, MorningAI ...", "output": "news_infographic_2026-04-14.png"},
      {"prompt": "9:16 portrait infographic, Model Updates ...", "output": "news_infographic_2026-04-14_model.png"}
    ]
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import env
from lib.util import log
from lib.image_gen import generate, generate_batch, list_providers, ImageGenError
from lib.image_stitch import stitch_images
from styles import (
    STYLE_PRESETS, DEFAULT_STYLE, CONTENT_DENSITY,
    SECTION_SUFFIX, SECTION_STYLE_OVERRIDES, STYLE_BG_COLORS,
)


_log = lambda msg: log("gen-infographic", msg)


def _inject_style(prompt: str, config: dict) -> str:
    """Inject style preset into prompt based on IMAGE_STYLE config."""
    style_name = (config.get("IMAGE_STYLE") or DEFAULT_STYLE).strip().lower()
    if style_name not in STYLE_PRESETS:
        _log(f"Warning: Unknown style '{style_name}', falling back to '{DEFAULT_STYLE}'")
        style_name = DEFAULT_STYLE

    style_block = STYLE_PRESETS[style_name] + CONTENT_DENSITY

    # Detect section prompts (used in --stitch mode) and append continuity rules
    is_section = "section" in prompt[:120].lower()
    if is_section:
        style_block += SECTION_SUFFIX
        extra = SECTION_STYLE_OVERRIDES.get(style_name, "")
        if extra:
            style_block += extra

    if "{STYLE_BLOCK}" in prompt:
        prompt = prompt.replace("{STYLE_BLOCK}", style_block)
    else:
        prompt = prompt.rstrip() + "\n\n" + style_block

    _log(f"Style: {style_name}{' (section mode)' if is_section else ''}")
    return prompt


def _run_single(args, config):
    """Single-image mode: one prompt → one image."""
    # Read prompt
    if args.prompt:
        prompt = args.prompt
    elif args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    elif not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()
    else:
        _log("Error: No prompt provided. Use --prompt, --prompt-file, or pipe to stdin.")
        sys.exit(1)

    if not prompt:
        _log("Error: Empty prompt")
        sys.exit(1)

    prompt = _inject_style(prompt, config)

    output_path = args.output or f"news_infographic_{args.date}.png"
    provider_name = config.get("IMAGE_GEN_PROVIDER", "none")
    _log(f"Provider: {provider_name}, Output: {output_path}")

    try:
        result = generate(prompt, output_path, config)
    except ImageGenError as e:
        _log(f"Error: {e}")
        sys.exit(1)

    if result:
        _log(f"Success: {result}")
        print(result)
    else:
        _log("Skipped (provider=none)")


def _run_batch(args, config):
    """Batch mode: manifest JSON → multiple images, optional stitch."""
    manifest_path = Path(args.batch)
    if not manifest_path.exists():
        _log(f"Error: Manifest file not found: {args.batch}")
        sys.exit(1)

    try:
        items = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        _log(f"Error: Failed to read manifest: {e}")
        sys.exit(1)

    if not isinstance(items, list):
        _log("Error: Manifest must be a JSON array of {\"prompt\": ..., \"output\": ...}")
        sys.exit(1)

    provider_name = config.get("IMAGE_GEN_PROVIDER", "none")
    _log(f"Batch mode: {len(items)} images, provider: {provider_name}")

    for item in items:
        if item.get("prompt", "").strip():
            item["prompt"] = _inject_style(item["prompt"], config)

    results = generate_batch(items, config)
    succeeded = [r for r in results if r]

    for path in succeeded:
        print(path)

    _log(f"Done: {len(succeeded)}/{len(items)} images generated")
    if not succeeded and provider_name != "none":
        sys.exit(1)

    # Stitch into a single long image
    if args.stitch and len(succeeded) >= 2:
        stitch_output = args.stitch_output or f"news_infographic_{args.date}_combined.png"
        style_name = (config.get("IMAGE_STYLE") or DEFAULT_STYLE).strip().lower()
        bg_color = STYLE_BG_COLORS.get(style_name, (245, 245, 240))
        try:
            combined = stitch_images(succeeded, stitch_output, bg_color=bg_color)
            print(combined)
            _log(f"Stitched image: {combined}")
        except (ImportError, ValueError) as e:
            _log(f"Stitch skipped: {e}")
    elif args.stitch:
        _log("Stitch skipped: need at least 2 images")


def main():
    parser = argparse.ArgumentParser(description="Generate infographics via external API")
    parser.add_argument("--prompt", "-p", default=None,
                        help="Image generation prompt text (single-image mode)")
    parser.add_argument("--prompt-file", default=None,
                        help="Path to file containing the prompt (single-image mode)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output PNG file path (default: news_infographic_{date}.png)")
    parser.add_argument("--batch", default=None,
                        help="Path to manifest JSON for batch generation")
    parser.add_argument("--provider", default=None,
                        choices=list_providers(),
                        help="Image generation provider (overrides IMAGE_GEN_PROVIDER env var)")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                        help="Date for default output filename (default: today)")
    parser.add_argument("--stitch", action="store_true",
                        help="Stitch batch images into a single vertical long image (requires Pillow)")
    parser.add_argument("--stitch-output", default=None,
                        help="Output path for stitched image (default: news_infographic_{date}_combined.png)")
    args = parser.parse_args()

    # Load config and apply provider override
    config = env.get_config()
    if args.provider:
        config["IMAGE_GEN_PROVIDER"] = args.provider

    if args.batch:
        _run_batch(args, config)
    else:
        _run_single(args, config)


if __name__ == "__main__":
    main()
