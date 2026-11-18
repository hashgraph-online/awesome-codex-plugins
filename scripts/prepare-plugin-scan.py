#!/usr/bin/env python3
"""Mirror the cloned source HEAD into a fresh bundle for the catalog scanner."""

import argparse
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

import generate_plugins_json as generator


def prepare_bundle(source: Path, output: Path, owner: str, repo: str, name: str) -> Path:
    source, output = source.resolve(), output.resolve()
    for part in (owner, repo):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", part) or part in {".", ".."}:
            raise ValueError("owner and repository must be GitHub path components")
    if output.exists():
        raise ValueError("scan output must be a new directory")
    if source == output or source in output.parents or output in source.parents:
        raise ValueError("scan output must be outside the contributed repository")
    with tempfile.TemporaryDirectory(prefix="catalog-scan-source-") as scratch:
        archive_path = Path(scratch) / "source.zip"
        subprocess.run([
            "git", "-C", str(source), "archive", "--format=zip", "--prefix=source/",
            "--output", str(archive_path), "HEAD",
        ], check=True)
        generator.PLUGINS_ROOT = output
        with zipfile.ZipFile(archive_path) as archive:
            generator.mirror_plugin_bundle(
                {"owner": owner, "repo": repo, "name": name}, archive=archive,
            )
    bundle = output / owner / repo
    if not (bundle / ".codex-plugin/plugin.json").is_file():
        raise ValueError("generated bundle has no scanner-compatible manifest")
    return bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("owner")
    parser.add_argument("repo")
    parser.add_argument("name")
    args = parser.parse_args()
    print(prepare_bundle(args.source, args.output, args.owner, args.repo, args.name))


if __name__ == "__main__":
    main()
