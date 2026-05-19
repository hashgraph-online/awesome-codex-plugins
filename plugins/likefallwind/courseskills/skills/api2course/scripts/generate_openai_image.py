#!/usr/bin/env python3
"""Generate one slide image with the OpenAI Image API.

The script intentionally uses only the Python standard library so the skill can
run in a clean environment. It reads the API key from OPENAI_API_KEY.
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path


DEFAULT_BASE_URL = "https://api.openai.com/v1"


def read_prompt(args: argparse.Namespace) -> str:
    parts: list[str] = []
    for prompt_file in args.prompt_file:
        parts.append(Path(prompt_file).read_text(encoding="utf-8"))
    for prompt in args.prompt:
        parts.append(prompt)
    prompt = "\n\n".join(part.strip() for part in parts if part.strip()).strip()
    if not prompt:
        sys.exit("Provide --prompt-file or --prompt.")
    return prompt


def api_headers(content_type: str) -> dict[str, str]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("OPENAI_API_KEY is not set.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": content_type,
    }
    organization = os.environ.get("OPENAI_ORG_ID") or os.environ.get("OPENAI_ORGANIZATION")
    project = os.environ.get("OPENAI_PROJECT_ID") or os.environ.get("OPENAI_PROJECT")
    if organization:
        headers["OpenAI-Organization"] = organization
    if project:
        headers["OpenAI-Project"] = project
    return headers


def request_json(url: str, payload: dict[str, object], timeout: int) -> dict[str, object]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=api_headers("application/json"), method="POST")
    return openai_request(req, timeout)


def request_multipart(url: str, fields: list[tuple[str, str]], files: list[Path], timeout: int) -> dict[str, object]:
    boundary = f"----api2course-{uuid.uuid4().hex}"
    chunks: list[bytes] = []

    def add_text(name: str, value: str) -> None:
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(value.encode("utf-8"))
        chunks.append(b"\r\n")

    def add_file(name: str, path: Path) -> None:
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            (
                f'Content-Disposition: form-data; name="{name}"; '
                f'filename="{path.name}"\r\nContent-Type: {content_type}\r\n\r\n'
            ).encode("utf-8")
        )
        chunks.append(path.read_bytes())
        chunks.append(b"\r\n")

    for name, value in fields:
        add_text(name, value)
    for path in files:
        add_file("image[]", path)
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))

    body = b"".join(chunks)
    req = urllib.request.Request(
        url,
        data=body,
        headers=api_headers(f"multipart/form-data; boundary={boundary}"),
        method="POST",
    )
    return openai_request(req, timeout)


def openai_request(req: urllib.request.Request, timeout: int) -> dict[str, object]:
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        sys.exit(f"OpenAI API returned HTTP {exc.code}:\n{detail}")
    except urllib.error.URLError as exc:
        sys.exit(f"OpenAI API request failed: {exc.reason}")

    elapsed = time.monotonic() - started
    data = json.loads(raw)
    request_id = getattr(response, "headers", {}).get("x-request-id") if "response" in locals() else None
    if request_id:
        print(f"x-request-id: {request_id}", file=sys.stderr)
    print(f"OpenAI image request completed in {elapsed:.1f}s", file=sys.stderr)
    return data


def extract_image_bytes(data: dict[str, object]) -> bytes:
    image_items = data.get("data")
    if not isinstance(image_items, list) or not image_items:
        sys.exit(f"No image data returned:\n{json.dumps(data, ensure_ascii=False, indent=2)}")
    first = image_items[0]
    if not isinstance(first, dict) or not isinstance(first.get("b64_json"), str):
        sys.exit(f"No data[0].b64_json returned:\n{json.dumps(data, ensure_ascii=False, indent=2)}")
    return base64.b64decode(first["b64_json"])


def build_common_fields(args: argparse.Namespace) -> list[tuple[str, str]]:
    fields = [
        ("model", args.model),
        ("prompt", read_prompt(args)),
        ("size", args.size),
        ("quality", args.quality),
        ("output_format", args.output_format),
        ("background", args.background),
    ]
    if args.output_compression is not None:
        fields.append(("output_compression", str(args.output_compression)))
    if args.moderation:
        fields.append(("moderation", args.moderation))
    return fields


def generate(args: argparse.Namespace) -> dict[str, object]:
    base_url = os.environ.get("OPENAI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    reference_images = [Path(path) for path in args.reference_image]
    missing = [str(path) for path in reference_images if not path.is_file()]
    if missing:
        sys.exit(f"Reference image not found: {', '.join(missing)}")

    if reference_images:
        url = f"{base_url}/images/edits"
        return request_multipart(url, build_common_fields(args), reference_images, args.timeout)

    url = f"{base_url}/images/generations"
    payload: dict[str, object] = {name: value for name, value in build_common_fields(args)}
    return request_json(url, payload, args.timeout)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--prompt-file",
        action="append",
        default=[],
        help="UTF-8 text file containing prompt text. May be passed multiple times.",
    )
    parser.add_argument(
        "--prompt",
        action="append",
        default=[],
        help="Prompt text appended after prompt files. May be passed multiple times.",
    )
    parser.add_argument("--out", required=True, help="Output image path.")
    parser.add_argument("--model", default=os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2"))
    parser.add_argument("--size", default=os.environ.get("OPENAI_IMAGE_SIZE", "1536x864"))
    parser.add_argument("--quality", default=os.environ.get("OPENAI_IMAGE_QUALITY", "high"))
    parser.add_argument("--output-format", default=os.environ.get("OPENAI_IMAGE_FORMAT", "png"))
    parser.add_argument("--background", default=os.environ.get("OPENAI_IMAGE_BACKGROUND", "auto"))
    parser.add_argument("--output-compression", type=int, default=None)
    parser.add_argument("--moderation", choices=["auto", "low"], default=None)
    parser.add_argument(
        "--reference-image",
        action="append",
        default=[],
        help="Optional style/reference image. May be passed multiple times. Uses /v1/images/edits.",
    )
    parser.add_argument("--timeout", type=int, default=int(os.environ.get("OPENAI_IMAGE_TIMEOUT", "180")))
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    image_bytes = extract_image_bytes(generate(args))
    out.write_bytes(image_bytes)
    print(f"Saved image: {out}")


if __name__ == "__main__":
    main()
