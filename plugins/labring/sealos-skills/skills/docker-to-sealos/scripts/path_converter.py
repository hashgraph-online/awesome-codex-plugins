#!/usr/bin/env python3
"""
Sealos Path to vn- Name Converter

This script converts file paths to Sealos vn- naming convention for use in:
- ConfigMap data keys
- Volume names
- VolumeClaimTemplates metadata names

Conversion rules:
- Convert to lowercase
- Replace every non [a-z0-9] character sequence with 'vn-'
- Prefix the final name with 'vn-'
- Reject empty or non-alphanumeric-only paths
- Truncate names longer than 63 chars with a stable hash suffix
"""

import re
import sys
import hashlib


MAX_K8S_NAME_LEN = 63


def _normalize_path_to_suffix(path: str) -> str:
    """
    Normalize a path-like string to a Kubernetes-safe suffix.

    Rules:
    - Trim surrounding whitespace
    - Lowercase all characters
    - Treat any non [a-z0-9] character as a separator
    - Join segments with "vn-"
    """
    if path is None:
        raise ValueError("Path cannot be None")

    raw = path.strip()
    if not raw:
        raise ValueError("Path cannot be empty")

    # Special-case root-like paths ("/", "////", etc.)
    if re.fullmatch(r"/+", raw):
        return "root"

    normalized = raw.strip("/").lower()
    segments = [seg for seg in re.split(r"[^a-z0-9]+", normalized) if seg]
    if not segments:
        raise ValueError("Path must contain at least one alphanumeric character")

    return "vn-".join(segments)


def _truncate_with_hash(name: str, original: str) -> str:
    """
    Ensure the generated name does not exceed Kubernetes DNS-1123 label length.
    """
    if len(name) <= MAX_K8S_NAME_LEN:
        return name

    digest = hashlib.sha1(original.encode("utf-8")).hexdigest()[:8]
    keep_len = MAX_K8S_NAME_LEN - len(digest) - 1  # "-" + hash
    prefix = name[:keep_len].rstrip("-")
    if not prefix:
        prefix = "vn"

    return f"{prefix}-{digest}"


def path_to_vn_name(path: str) -> str:
    """
    Convert a file path to Sealos vn- naming convention.

    Args:
        path: File path (e.g., "/etc/nginx/conf.d/default.conf")

    Returns:
        vn- formatted, Kubernetes-safe name.

    Examples:
        >>> path_to_vn_name("/etc/nginx/conf.d/default.conf")
        'vn-etcvn-nginxvn-confvn-dvn-defaultvn-conf'

        >>> path_to_vn_name("/var/lib/headscale")
        'vn-varvn-libvn-headscale'

        >>> path_to_vn_name("/app/config.yml")
        'vn-appvn-configvn-yml'

        >>> path_to_vn_name("/var/lib/My_App")
        'vn-varvn-libvn-myvn-app'
    """
    suffix = _normalize_path_to_suffix(path)
    vn_name = f"vn-{suffix}"
    return _truncate_with_hash(vn_name, path)


def vn_name_to_path(vn_name: str) -> str:
    """
    Convert a vn- name back to a file path (best effort).
    Note: This is ambiguous as we can't determine if 'vn-' was originally '/', '-', or '.'

    Args:
        vn_name: vn- formatted name

    Returns:
        Approximate file path
    """
    # Remove leading 'vn-'
    if vn_name.startswith('vn-'):
        vn_name = vn_name[3:]

    # Replace 'vn-' with '/' (most common case)
    path = vn_name.replace('vn-', '/')

    # Add leading '/'
    if not path.startswith('/'):
        path = '/' + path

    return path


def run_self_test() -> int:
    """Run a minimal regression suite for conversion edge cases."""
    cases = [
        ("/etc/nginx/nginx.conf", "vn-etcvn-nginxvn-nginxvn-conf"),
        ("/var/lib/My_App", "vn-varvn-libvn-myvn-app"),
        ("/data/cache@prod", "vn-datavn-cachevn-prod"),
        ("/", "vn-root"),
    ]

    for raw, expected in cases:
        actual = path_to_vn_name(raw)
        if actual != expected:
            print(f"FAIL: {raw} -> {actual}, expected {expected}")
            return 1

    for raw in ("", "____"):
        try:
            path_to_vn_name(raw)
        except ValueError:
            pass
        else:
            print(f"FAIL: expected ValueError for input: {raw!r}")
            return 1

    print("Self-test passed.")
    return 0


def main():
    """Command-line interface for path conversion."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Convert path to vn-name:")
        print("    python path_converter.py /etc/nginx/conf.d/default.conf")
        print()
        print("  Run self-test:")
        print("    python path_converter.py --self-test")
        print()
        print("  Convert vn-name to path:")
        print("    python path_converter.py --reverse vn-etcvn-nginxvn-confvn-dvn-defaultvn-conf")
        sys.exit(1)

    try:
        if sys.argv[1] == '--self-test':
            sys.exit(run_self_test())
        if sys.argv[1] == '--reverse':
            if len(sys.argv) < 3:
                print("Error: Please provide a vn-name to convert")
                sys.exit(1)
            vn_name = sys.argv[2]
            result = vn_name_to_path(vn_name)
            print(f"vn-name: {vn_name}")
            print(f"Path:    {result}")
        else:
            path = sys.argv[1]
            result = path_to_vn_name(path)
            print(f"Path:    {path}")
            print(f"vn-name: {result}")
    except ValueError as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == '__main__':
    main()
