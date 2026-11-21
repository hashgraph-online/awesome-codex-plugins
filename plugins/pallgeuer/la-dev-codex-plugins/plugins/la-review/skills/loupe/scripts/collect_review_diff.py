#!/usr/bin/env python3
"""Collect Loupe review-scope diffs into a temporary artifact file.

This Python script must support Python 3.6+.
"""

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

DEFAULT_REVIEW_SCOPE = "uncommitted changes (staged + unstaged + untracked)"
BINARY_PAYLOAD_NOTE = "Binary patch payloads are excluded; binary changes appear only as compact Git diff markers."


class GitCommandError(RuntimeError):
    """Failure raised when a required Git command cannot complete."""


def parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    """Parse the helper command line."""
    parser = argparse.ArgumentParser(description="Collect the default Loupe review diff into an artifact file.")
    parser.add_argument("scope", help="Review scope text.")
    parser.add_argument("--output", required=True, help="Path where the collected diff artifact should be written.")
    args = parser.parse_args(argv)
    args.review_scope = args.scope.strip()
    if args.review_scope != DEFAULT_REVIEW_SCOPE:
        parser.error("collect_review_diff.py only supports the default scope: {}".format(DEFAULT_REVIEW_SCOPE))
    return args


def run_git(args: Sequence[str], *, cwd: Optional[str] = None, allowed_returncodes: Tuple[int, ...] = (0,)) -> bytes:
    """Run Git and return stdout bytes."""
    completed = subprocess.run(["git", *list(args)], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if completed.returncode not in allowed_returncodes:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise GitCommandError("git {} failed with exit code {}{}".format(" ".join(args), completed.returncode, ": " + stderr if stderr else ""))
    return completed.stdout


def untracked_paths(git_root: str) -> List[str]:
    """Return untracked, non-ignored paths relative to the Git root."""
    output = run_git(["ls-files", "--others", "--exclude-standard", "-z"], cwd=git_root)
    return [path.decode("utf-8", errors="surrogateescape") for path in output.split(b"\0") if path]


def diff_chunks(git_root: str) -> List[bytes]:
    """Return Git diff chunks for the default Loupe review scope."""
    chunks = [
        run_git(["diff", "--no-ext-diff", "--no-textconv", "--cached", "--"], cwd=git_root),
        run_git(["diff", "--no-ext-diff", "--no-textconv", "--"], cwd=git_root),
    ]
    chunks.extend(run_git(["diff", "--no-ext-diff", "--no-textconv", "--no-index", "--", "/dev/null", path], cwd=git_root, allowed_returncodes=(0, 1)) for path in untracked_paths(git_root))
    return chunks


def write_diff_artifact(chunks: Sequence[bytes], output_path: str) -> int:
    """Write diff chunks and return the artifact byte count."""
    byte_count = 0
    wrote_chunk = False
    with pathlib.Path(output_path).open("wb") as output_file:
        for chunk in chunks:
            if not chunk:
                continue
            if wrote_chunk and not chunk.startswith(b"\n"):
                output_file.write(b"\n")
                byte_count += 1
            output_file.write(chunk)
            byte_count += len(chunk)
            if not chunk.endswith(b"\n"):
                output_file.write(b"\n")
                byte_count += 1
            wrote_chunk = True
    return byte_count


def collect_default_diff(output_path: str) -> Dict[str, Any]:
    """Collect the default review diff and return artifact metadata."""
    git_root = run_git(["rev-parse", "--show-toplevel"]).decode("utf-8", errors="replace").strip()
    byte_count = write_diff_artifact(diff_chunks(git_root), output_path)
    return {
        "review_scope": DEFAULT_REVIEW_SCOPE,
        "git_root": git_root,
        "diff_path": str(pathlib.Path(output_path).resolve()),
        "byte_count": byte_count,
        "binary_payloads_included": False,
        "note": BINARY_PAYLOAD_NOTE,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Collect the requested review diff and emit artifact metadata JSON."""
    args = parse_args(argv)
    try:
        print(json.dumps(collect_default_diff(args.output), indent=2))
    except (GitCommandError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
