#!/usr/bin/env python3
"""Generate and edit images through an OpenAI-compatible image API.

Credentials may be supplied explicitly or read from environment/Codex config.
Credential values are never printed or written to output files.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import secrets
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 and older
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:  # pragma: no cover - dependency-free fallback
        tomllib = None  # type: ignore[assignment]

DEFAULT_MODEL = "gpt-image-2"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
IMAGE_ID_PATTERN = re.compile(
    r"(?:image|dall[-_ ]?e|flux|diffusion|sdxl|stable[-_ ]?diffusion|"
    r"imagen|ideogram|recraft|kolors|seedream|banana)",
    re.IGNORECASE,
)


def die(message: str, code: int = 2) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


def _strip_inline_comment(value: str) -> str:
    quoted = False
    quote = ""
    for index, char in enumerate(value):
        if char in {"'", '"'}:
            if not quoted:
                quoted, quote = True, char
            elif quote == char:
                quoted = False
        elif char == "#" and not quoted:
            return value[:index].rstrip()
    return value.strip()


def _parse_scalar(value: str) -> Any:
    value = _strip_inline_comment(value)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value


def _parse_minimal_toml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    section: dict[str, Any] = root
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = root
            for part in line[1:-1].split("."):
                section = section.setdefault(part, {})
            continue
        if "=" in line:
            key, raw_value = line.split("=", 1)
            section[key.strip()] = _parse_scalar(raw_value)
    return root


def _load_config(config: Path) -> dict[str, Any]:
    if not config.exists():
        return {}
    try:
        text = config.read_text(encoding="utf-8")
        return tomllib.loads(text) if tomllib is not None else _parse_minimal_toml(text)
    except (OSError, ValueError) as exc:
        die(f"could not read config {config}: {exc}")
    return {}


def read_codex_credentials(config: Path) -> tuple[str | None, str | None, str | None]:
    data = _load_config(config)
    configured_model = data.get("image_model")
    configured_model = str(configured_model) if configured_model else None
    providers = data.get("model_providers", {})
    if not isinstance(providers, dict):
        providers = {}
    candidates: list[str] = []
    active = data.get("model_provider")
    if isinstance(active, str) and active:
        candidates.append(active)
    if "OpenAI" not in candidates:
        candidates.append("OpenAI")
    for name in candidates:
        provider = providers.get(name)
        if not isinstance(provider, dict):
            continue
        key = provider.get("OPENAI_API_KEY") or provider.get("api_key")
        base_url = provider.get("base_url")
        image_model = provider.get("image_model") or configured_model
        if key or base_url or image_model:
            return (
                str(key) if key else None,
                str(base_url) if base_url else None,
                str(image_model) if image_model else None,
            )
    return None, None, configured_model


def normalize_base_url(value: str | None) -> str:
    root = (value or DEFAULT_BASE_URL).strip().rstrip("/")
    return root if root.endswith("/v1") else root + "/v1"


def content_type(path: Path) -> str:
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "application/octet-stream")


def read_json(request: urllib.request.Request, timeout: int) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            details = json.loads(raw.decode("utf-8"))
            message = details.get("error", {}).get("message", "request failed")
        except (ValueError, UnicodeDecodeError):
            message = raw.decode("utf-8", "replace")[:500]
        die(f"image API returned HTTP {exc.code}: {message}")
    except urllib.error.URLError as exc:
        die(f"could not reach image API: {exc.reason}")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        die(f"image API returned invalid JSON: {exc}")
    if not isinstance(payload, dict):
        die("image API returned a non-object JSON response")
    return payload


def request_json(url: str, payload: dict[str, Any], api_key: str, timeout: int) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    return read_json(request, timeout)


def get_json(url: str, api_key: str, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    )
    return read_json(request, timeout)


def multipart_body(fields: dict[str, str], files: list[tuple[str, Path, str]]) -> tuple[bytes, str]:
    boundary = "----codex-image-plugin-" + secrets.token_hex(12)
    marker = boundary.encode("ascii")
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend([
            b"--" + marker + b"\r\n",
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
            value.encode("utf-8"),
            b"\r\n",
        ])
    for name, path, media_type in files:
        filename = path.name.replace('"', "")
        chunks.extend([
            b"--" + marker + b"\r\n",
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode(),
            f"Content-Type: {media_type}\r\n\r\n".encode(),
            path.read_bytes(),
            b"\r\n",
        ])
    chunks.append(b"--" + marker + b"--\r\n")
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def request_multipart(
    url: str,
    fields: dict[str, str],
    files: list[tuple[str, Path, str]],
    api_key: str,
    timeout: int,
) -> dict[str, Any]:
    body, media_type = multipart_body(fields, files)
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": media_type,
            "Accept": "application/json",
        },
    )
    return read_json(request, timeout)


def make_ring_mask(image: Path, mask: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFilter
    except ModuleNotFoundError as exc:
        die(f"Pillow is required for --mask-ring: {exc}")
    im = Image.open(image).convert("RGBA")
    width, height = im.size
    side = min(width, height)
    outer_pad, inner_pad = side * 0.075, side * 0.115
    cx, cy = width / 2, height / 2
    outer = (cx - side / 2 + outer_pad, cy - side / 2 + outer_pad, cx + side / 2 - outer_pad, cy + side / 2 - outer_pad)
    inner = (cx - side / 2 + inner_pad, cy - side / 2 + inner_pad, cx + side / 2 - inner_pad, cy + side / 2 - inner_pad)
    alpha = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(alpha)
    draw.ellipse(outer, fill=0)
    draw.ellipse(inner, fill=255)
    alpha = alpha.filter(ImageFilter.GaussianBlur(max(0.5, side / 180)))
    output = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    output.putalpha(alpha)
    mask.parent.mkdir(parents=True, exist_ok=True)
    output.save(mask)


def augment_prompt(args: argparse.Namespace) -> str:
    fields = [
        ("Use case", args.use_case),
        ("Primary request", args.prompt),
        ("Style", args.style),
        ("Composition", args.composition),
        ("Constraints", args.constraints),
    ]
    return "\n".join(f"{name}: {value}" for name, value in fields if value)


def ensure_output(path: Path, force: bool) -> None:
    if path.exists() and not force:
        die(f"output exists; pass --force to replace it: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)


def decode_response(response: dict[str, Any], output: Path, force: bool, timeout: int) -> list[Path]:
    data = response.get("data")
    if not isinstance(data, list) or not data:
        die("image API response did not contain a non-empty data list")
    saved: list[Path] = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            die("image API returned an invalid data item")
        target = output if len(data) == 1 else output.with_name(f"{output.stem}-{index}{output.suffix}")
        ensure_output(target, force)
        encoded = item.get("b64_json")
        url = item.get("url")
        if encoded:
            try:
                target.write_bytes(base64.b64decode(encoded))
            except (ValueError, TypeError) as exc:
                die(f"could not decode image data: {exc}")
        elif url:
            try:
                with urllib.request.urlopen(str(url), timeout=timeout) as source:
                    target.write_bytes(source.read())
            except (OSError, urllib.error.URLError) as exc:
                die(f"could not download generated image: {exc}")
        else:
            die("image API response item had neither b64_json nor url")
        saved.append(target)
    return saved


def image_models(response: dict[str, Any]) -> list[str]:
    data = response.get("data")
    if not isinstance(data, list):
        die("/models response did not contain a data list")
    result: list[str] = []
    for item in data:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            model_id = item["id"]
            metadata = json.dumps(item, ensure_ascii=False)
            if IMAGE_ID_PATTERN.search(model_id) or IMAGE_ID_PATTERN.search(metadata):
                result.append(model_id)
    return sorted(set(result))


def credential_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-url", "--url", dest="base_url", help="OpenAI-compatible API base URL")
    parser.add_argument("--api-key", help="API key; prefer OPENAI_API_KEY to avoid shell history")
    parser.add_argument("--config", default=str(Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "config.toml"))
    parser.add_argument("--timeout", type=int, default=180)


def common_image_args(parser: argparse.ArgumentParser) -> None:
    credential_args(parser)
    parser.add_argument("--model", default=None)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--size", default="auto")
    parser.add_argument("--quality", default="auto")
    parser.add_argument("--output-format", choices=["png", "jpeg", "webp"], default="png")
    parser.add_argument("--background", default=None)
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--use-case")
    parser.add_argument("--style")
    parser.add_argument("--composition")
    parser.add_argument("--constraints")


def resolve_credentials(args: argparse.Namespace) -> tuple[str | None, str]:
    config_key, config_url, config_model = read_codex_credentials(Path(args.config).expanduser())
    key = args.api_key or os.getenv("OPENAI_API_KEY") or config_key
    base_url = normalize_base_url(args.base_url or os.getenv("OPENAI_BASE_URL") or config_url)
    if hasattr(args, "model"):
        args.model = args.model or os.getenv("IMAGE_MODEL") or config_model or DEFAULT_MODEL
    if not key and not args.dry_run:
        die("missing API key; pass --api-key or set OPENAI_API_KEY")
    return key, base_url


def generation_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": args.model,
        "prompt": augment_prompt(args),
        "size": args.size,
        "quality": args.quality,
        "output_format": args.output_format,
        "n": args.n,
    }
    if args.background:
        payload["background"] = args.background
    return payload


def run_generate(args: argparse.Namespace, key: str | None, base_url: str) -> None:
    payload = generation_payload(args)
    if args.dry_run:
        print(json.dumps({"endpoint": f"{base_url}/images/generations", "payload": payload, "output": str(Path(args.out).expanduser().resolve())}, indent=2, sort_keys=True))
        return
    if not key:
        die("missing API key")
    response = request_json(f"{base_url}/images/generations", payload, key, args.timeout)
    for path in decode_response(response, Path(args.out).expanduser().resolve(), args.force, args.timeout):
        print(path)


def run_edit(args: argparse.Namespace, key: str | None, base_url: str) -> None:
    image_paths = [Path(path).expanduser().resolve() for path in args.image]
    for image in image_paths:
        if not image.is_file():
            die(f"input image not found: {image}")
    mask = Path(args.mask).expanduser().resolve() if args.mask else None
    output = Path(args.out).expanduser().resolve()
    if args.mask_ring:
        if len(image_paths) != 1:
            die("--mask-ring requires exactly one --image")
        mask = output.parent / f"{output.stem}-ring-mask.png"
        make_ring_mask(image_paths[0], mask)
    if mask and not mask.is_file():
        die(f"mask not found: {mask}")
    fields = generation_payload(args)
    fields.pop("n", None)
    fields = {name: str(value) for name, value in fields.items()}
    files = [("image[]", image, content_type(image)) for image in image_paths]
    if mask:
        files.append(("mask", mask, "image/png"))
    if args.dry_run:
        print(json.dumps({"endpoint": f"{base_url}/images/edits", "fields": fields, "images": [str(p) for p in image_paths], "mask": str(mask) if mask else None, "output": str(output)}, indent=2, sort_keys=True))
        return
    if not key:
        die("missing API key")
    response = request_multipart(f"{base_url}/images/edits", fields, files, key, args.timeout)
    for path in decode_response(response, output, args.force, args.timeout):
        print(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and edit images through an OpenAI-compatible image API")
    sub = parser.add_subparsers(dest="command", required=True)

    models = sub.add_parser("models", help="List image-capable models exposed by the endpoint")
    credential_args(models)
    models.add_argument("--image-only", action="store_true", help="Only print IDs that look image-capable")
    models.add_argument("--dry-run", action="store_true")

    generate = sub.add_parser("generate", help="Generate an image")
    common_image_args(generate)

    edit = sub.add_parser("edit", help="Edit one or more images")
    common_image_args(edit)
    edit.add_argument("--image", required=True, action="append")
    edit.add_argument("--mask")
    edit.add_argument("--mask-ring", action="store_true")

    args = parser.parse_args()
    key, base_url = resolve_credentials(args)
    if args.command == "models":
        if args.dry_run:
            print(json.dumps({"endpoint": f"{base_url}/models", "image_only": args.image_only}, indent=2, sort_keys=True))
            return
        if not key:
            die("missing API key")
        response = get_json(f"{base_url}/models", key, args.timeout)
        ids = image_models(response) if args.image_only else sorted(
            item["id"] for item in response.get("data", []) if isinstance(item, dict) and isinstance(item.get("id"), str)
        )
        print("\n".join(ids))
        return
    if args.command == "generate":
        if args.n < 1:
            die("--n must be at least 1")
        run_generate(args, key, base_url)
        return
    if args.command == "edit":
        run_edit(args, key, base_url)
        return
if __name__ == "__main__":
    main()
