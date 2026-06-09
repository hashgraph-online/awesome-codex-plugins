#!/usr/bin/env python3
"""Fetch SenderKit's published OpenAPI spec and optionally compare a local copy."""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys
import tempfile
import urllib.error
import urllib.request


DEFAULT_URL = "https://www.senderkit.com/openapi.yaml"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_url(url: str, timeout: float) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "senderkit-skill-openapi-sync"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch SenderKit's OpenAPI spec.")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"OpenAPI URL. Default: {DEFAULT_URL}")
    parser.add_argument("--out", help="Write fetched spec to this path. Defaults to /tmp/senderkit-openapi.yaml")
    parser.add_argument("--compare", help="Compare fetched spec bytes with a local OpenAPI file")
    parser.add_argument("--timeout", type=float, default=15.0, help="HTTP timeout in seconds")
    args = parser.parse_args()

    try:
        remote = read_url(args.url, args.timeout)
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"ERROR: failed to fetch {args.url}: {exc}", file=sys.stderr)
        return 2

    out = pathlib.Path(args.out) if args.out else pathlib.Path(tempfile.gettempdir()) / "senderkit-openapi.yaml"
    out.write_bytes(remote)
    print(f"fetched: {args.url}")
    print(f"saved: {out}")
    print(f"remote_sha256: {sha256(remote)}")

    if args.compare:
        local_path = pathlib.Path(args.compare)
        local = local_path.read_bytes()
        local_hash = sha256(local)
        print(f"local: {local_path}")
        print(f"local_sha256: {local_hash}")
        if local == remote:
            print("status: in-sync")
            return 0
        print("status: drift-detected")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
