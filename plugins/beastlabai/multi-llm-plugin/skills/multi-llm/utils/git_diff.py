"""Diff hunks and file contents captured as a code review's embedded context.

Split out of :mod:`utils.git_utils`, which re-exports every name defined here
for reading only: patch one of them here, in ``utils.git_diff``, never through
``git_utils``. Every git command is built by ``git_utils.git_argv`` or run
through ``git_utils._run_git`` / ``_run_git_process``, so the hardening
documented there (and in docs/development/providers.md) applies unchanged:
this module spells no git argv of its own. Those helpers are looked up on the
current ``git_utils`` at each call (:func:`_git_utils`), never imported by
name, so a patch of one there reaches these commands too.
"""

import importlib
import io
import os
import re
import subprocess
import sys
import time
from types import ModuleType
from typing import Any, Dict, Iterable, List, Optional


def _git_utils() -> ModuleType:
    """The ``git_utils`` module now in ``sys.modules``, looked up at each call.
    Holding no reference of its own, this module cannot keep using a
    ``git_utils`` that a failed import and its retry replaced, and a patch of a
    runner there reaches every command here."""
    return importlib.import_module(".git_utils", __package__)


# ---------------------------------------------------------------------------
# Diff hunk capture and file content capture utilities
# ---------------------------------------------------------------------------

# Budget constants for embedded context data
_MAX_LINES_PER_FILE = 200
_MAX_TOTAL_BYTES = 500 * 1024  # 500KB
_GIT_TIMEOUT_SECONDS = 10

# Rough amortized width of one diff line (prefix char + content + newline),
# used only to convert a byte budget into a line-count cap — see
# _per_file_line_cap.
_ASSUMED_BYTES_PER_DIFF_LINE = 80


def _per_file_line_cap(file_count: int) -> int:
    """Per-file line budget for ``_parse_unified_diff``, scaled by how many
    files share ``_MAX_TOTAL_BYTES``.

    ``_MAX_LINES_PER_FILE`` used to be a flat cap applied to every file
    regardless of how many were being reviewed, so a single ~1,400-line file
    (the common case for a whole-file review) got the same 200-line cap as
    one file among fifty — 86% of it silently dropped — while the byte
    budget that actually bounds total output sat almost unused. Scale the
    cap with the remaining budget split across the files being diffed, so a
    lone file is allowed most of the budget and a large fan-out still gets a
    floor of ``_MAX_LINES_PER_FILE``.
    """
    if file_count <= 0:
        return _MAX_LINES_PER_FILE
    per_file_bytes = _MAX_TOTAL_BYTES / file_count
    return max(_MAX_LINES_PER_FILE, int(per_file_bytes / _ASSUMED_BYTES_PER_DIFF_LINE))


def _is_binary_file(path: str) -> bool:
    """Heuristic check for binary file content.

    Reads the first 8KB and looks for null bytes.
    """
    try:
        with open(path, "rb") as f:
            chunk = f.read(8192)
        return b"\x00" in chunk
    except (OSError, IOError):
        return False


def _parse_unified_diff(diff_text: str, max_lines: int = _MAX_LINES_PER_FILE) -> Dict[str, Any]:
    """Parse unified diff text for a single file into structured hunk data.

    Args:
        diff_text: unified diff for one file.
        max_lines: cap on captured add/remove/context lines (see
            ``_per_file_line_cap`` for how callers scale this).

    Returns a dict with keys:
      - hunks: list of hunk objects (header + lines)
      - old_path / new_path: for renamed files
      - binary: True if the diff indicates a binary file
      - deleted: True if the file was deleted
      - truncated_at: int if lines were capped
      - total_lines: int, present only alongside truncated_at — the full
        count of add/remove/context lines the diff actually has, so a
        reader can say "showing first N of <total_lines>" instead of "?"

    Each hunk contains:
      - header: the @@ line
      - lines: list of {type, old_line, new_line, content}
    """
    lines = diff_text.split("\n")
    result: Dict[str, Any] = {
        "hunks": [],
        "old_path": None,
        "new_path": None,
        "binary": False,
        "deleted": False,
    }

    total_content_lines = 0
    total_lines = 0
    truncated = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect binary file marker
        if line.startswith("Binary files") or line.startswith("GIT binary patch"):
            result["binary"] = True
            return result

        # Detect rename
        if line.startswith("rename from "):
            result["old_path"] = line[len("rename from "):]
        elif line.startswith("rename to "):
            result["new_path"] = line[len("rename to "):]

        # Detect old/new paths from --- / +++ headers
        if line.startswith("--- a/"):
            result["old_path"] = result["old_path"] or line[6:]
        elif line.startswith("--- /dev/null"):
            # New file – no old path
            pass
        elif line.startswith("+++ b/"):
            result["new_path"] = result["new_path"] or line[6:]
        elif line.startswith("+++ /dev/null"):
            result["deleted"] = True

        # Parse hunk header
        hunk_match = re.match(
            r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)", line
        )
        if hunk_match:
            old_start = int(hunk_match.group(1))
            new_start = int(hunk_match.group(3))
            hunk_header_text = line

            hunk: Dict[str, Any] = {
                "header": hunk_header_text,
                "lines": [],
            }

            old_line = old_start
            new_line = new_start

            i += 1
            while i < len(lines):
                hline = lines[i]

                # Stop at next hunk, next file header, or end
                if (
                    hline.startswith("@@ ")
                    or hline.startswith("diff --git")
                    or hline.startswith("--- a/")
                    or hline.startswith("--- /dev/null")
                ):
                    break

                # Count every real content line up front (even once
                # truncated) so a truncated result can still report how
                # many lines it dropped.
                if hline.startswith("+") or hline.startswith("-") or hline.startswith(" "):
                    total_lines += 1

                if truncated:
                    i += 1
                    continue

                if total_content_lines >= max_lines:
                    truncated = True
                    result["truncated_at"] = max_lines
                    i += 1
                    continue

                if hline.startswith("+"):
                    hunk["lines"].append({
                        "type": "add",
                        "old_line": None,
                        "new_line": new_line,
                        "content": hline[1:],
                    })
                    new_line += 1
                    total_content_lines += 1
                elif hline.startswith("-"):
                    hunk["lines"].append({
                        "type": "remove",
                        "old_line": old_line,
                        "new_line": None,
                        "content": hline[1:],
                    })
                    old_line += 1
                    total_content_lines += 1
                elif hline.startswith(" "):
                    hunk["lines"].append({
                        "type": "context",
                        "old_line": old_line,
                        "new_line": new_line,
                        "content": hline[1:],
                    })
                    old_line += 1
                    new_line += 1
                    total_content_lines += 1
                elif hline.startswith("\\ No newline at end of file"):
                    # Marker line – skip, don't count toward budget
                    pass
                else:
                    # Unknown line in hunk (e.g., empty trailing line) – skip
                    pass

                i += 1

            result["hunks"].append(hunk)
            continue  # Don't increment i again – already positioned

        i += 1

    if truncated:
        result["total_lines"] = total_lines

    return result


def _split_diff_by_file(raw_diff: str) -> Dict[str, str]:
    """Split a multi-file unified diff into per-file chunks.

    Returns a dict mapping file paths to their diff text.
    The key is the new-side path (b/ path) from the diff header.
    """
    file_diffs: Dict[str, str] = {}
    current_path: Optional[str] = None
    current_lines: List[str] = []

    for line in raw_diff.split("\n"):
        if line.startswith("diff --git"):
            # Save previous file's diff
            if current_path is not None:
                file_diffs[current_path] = "\n".join(current_lines)

            # Extract path from "diff --git a/path b/path"
            parts = line.split(" b/", 1)
            current_path = parts[1] if len(parts) > 1 else None
            current_lines = [line]
        else:
            current_lines.append(line)

    # Save last file
    if current_path is not None:
        file_diffs[current_path] = "\n".join(current_lines)

    return file_diffs


def capture_diff_hunks(
    base_ref: str,
    file_paths: List[str],
    head_ref: Optional[str] = None,
    cwd: Optional[str] = None,
) -> Dict[str, Any]:
    """Capture structured diff hunks for specified files against a base ref.

    Runs ``git diff base_ref -- <files>`` and parses the unified diff output
    into structured per-file data consumed by the PR-style report template.

    Args:
        base_ref: Git ref to diff against (commit SHA, branch name, HEAD~N),
            or the empty-tree id on a root range, where every file is added.
        file_paths: List of file paths to capture diffs for.  Only files in
            this list are processed (scoped to suggestion-referenced files).
        head_ref: The commit a commit review ends at. With it the diff is
            ``git diff base_ref head_ref -- <files>``: two commits, whatever
            the working tree holds, so there is no "includes uncommitted
            changes" notice (plans/review-commits.md §2.5). ``None`` diffs
            against the working tree, as always.
        cwd: Where git runs; a caller passes the repository root, since the
            paths are root-relative. ``None`` is the process's cwd.

    Returns:
        A dict with:
          - Per file-path key: structured hunk data (see ``_parse_unified_diff``).
          - ``_notices``: list of notice strings (e.g., uncommitted changes).
          - ``_error``: error string when git is unavailable.

    Edge cases handled:
      - Binary files → ``{binary: true}``
      - Renamed files → ``old_path`` and ``new_path`` included
      - Deleted files → ``deleted: true``, content retrieved via ``git show
        <base_ref>:<path>`` (the content the change removed)
      - Invalid base_ref → empty dict with warning
      - Git not available → empty dict with notice
      - 10-second timeout enforced
      - Per-file line cap, scaled by file count (floor 200 lines; see
        ``_per_file_line_cap``) so a single-file review is not held to the
        same cap as a large fan-out
      - 500KB total budget
    """
    if not file_paths:
        return {}

    result: Dict[str, Any] = {}
    notices: List[str] = []
    where: Dict[str, str] = {"cwd": cwd} if cwd is not None else {}

    # --- Check for uncommitted changes (a two-commit diff has none) ---
    if head_ref is None:
        try:
            status_result = subprocess.run(
                _git_utils().git_argv("status", "--porcelain", cwd=cwd),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=_GIT_TIMEOUT_SECONDS,
                **where,
            )
            if status_result.returncode == 0 and status_result.stdout.strip():
                notices.append("Diff includes uncommitted changes")
        except FileNotFoundError:
            result["_notices"] = ["Git not available -- code context shown from file content only."]
            print(
                "Warning: git is not available (not installed or not in PATH)",
                file=sys.stderr,
            )
            return result
        except subprocess.TimeoutExpired:
            notices.append("git status timed out")
        except OSError:
            result["_notices"] = ["Git not available -- code context shown from file content only."]
            print(
                "Warning: git is not available (OS error)",
                file=sys.stderr,
            )
            return result

    # --- Run git diff ---
    sides = [base_ref] if head_ref is None else [base_ref, head_ref]
    try:
        diff_result = _git_utils()._run_git_process(
            [*_git_utils().attribute_source_args(head_ref), "diff", *sides, "--", *file_paths],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        result["_notices"] = ["Git not available -- code context shown from file content only."]
        print(
            "Warning: git is not available (not installed or not in PATH)",
            file=sys.stderr,
        )
        return result
    except subprocess.TimeoutExpired:
        notices.append("diff capture timed out")
        result["_notices"] = notices
        return result
    except OSError:
        result["_notices"] = ["Git not available -- code context shown from file content only."]
        print(
            "Warning: git is not available (OS error)",
            file=sys.stderr,
        )
        return result

    if diff_result.returncode != 0:
        # Invalid base_ref or other git error
        what = f"base_ref '{base_ref}'" if head_ref is None else (
            f"'{base_ref}..{head_ref}'"
        )
        print(
            f"Warning: git diff failed for {what}: "
            f"{diff_result.stderr.strip()}",
            file=sys.stderr,
        )
        result["_notices"] = notices
        return result

    raw_diff = diff_result.stdout

    # --- Split and parse per-file diffs ---
    per_file_diffs = _split_diff_by_file(raw_diff)
    total_bytes = 0
    # Scaled once per call: a review of one file should not be held to the
    # same flat 200-line cap as a review of fifty (see _per_file_line_cap).
    line_cap = _per_file_line_cap(len(file_paths))

    start_time = time.monotonic()

    for fpath in file_paths:
        # Timeout check
        if time.monotonic() - start_time > _GIT_TIMEOUT_SECONDS:
            notices.append("diff capture timed out")
            break

        file_diff_text = per_file_diffs.get(fpath)
        if file_diff_text is None:
            # File may not have changes in the diff – skip silently
            continue

        # Budget check
        diff_bytes = len(file_diff_text.encode("utf-8", errors="replace"))
        if total_bytes + diff_bytes > _MAX_TOTAL_BYTES:
            result[fpath] = {"truncated": True}
            notices.append(
                f"Size budget exceeded at {fpath} – remaining files omitted"
            )
            break

        total_bytes += diff_bytes

        parsed = _parse_unified_diff(file_diff_text, max_lines=line_cap)
        result[fpath] = parsed

    # --- Handle deleted files: retrieve last-known content ---
    # From the old side, `base_ref`, whether the new side is the working tree
    # or `head_ref`: that is the content the change removed. The path is put
    # in git's form first (a relative POSIX path is unchanged by it).
    for fpath in file_paths:
        if fpath in result and isinstance(result[fpath], dict) and result[fpath].get("deleted"):
            try:
                show_result = subprocess.run(
                    _git_utils().git_argv("show", f"{base_ref}:{_git_utils().git_path(fpath, cwd=cwd)}", cwd=cwd),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=_GIT_TIMEOUT_SECONDS,
                    **where,
                )
                if show_result.returncode == 0:
                    result[fpath]["last_known_content"] = show_result.stdout
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass  # Best effort – content unavailable

    if notices:
        result["_notices"] = notices

    return result


def capture_file_snapshots(
    file_paths: List[str],
) -> Dict[str, List[str]]:
    """Capture file content for multiple files at a point in time.

    Call this at the START of a review phase (before model invocations begin)
    to snapshot file content.  The returned dict can be passed as
    ``file_snapshots`` to ``generate_html_report()`` and ultimately to
    ``capture_file_context()``, ensuring the report reflects file state at
    review start rather than at report-generation time.

    Args:
        file_paths: List of file paths (absolute or relative to cwd) to
            snapshot.

    Returns:
        Dict mapping each readable, non-binary file path to a list of its
        lines (with trailing newlines stripped).  Files that do not exist,
        are binary, or cannot be read are silently omitted.
    """
    snapshots: Dict[str, List[str]] = {}
    for fpath in file_paths:
        if not fpath or not os.path.isfile(fpath):
            continue
        if _is_binary_file(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                snapshots[fpath] = [
                    ln.rstrip("\n").rstrip("\r") for ln in f.readlines()
                ]
        except (OSError, IOError):
            continue
    return snapshots


def capture_file_snapshots_at(
    ref: str, paths: Iterable[str], *, cwd: Optional[str] = None,
) -> Dict[str, List[str]]:
    """:func:`capture_file_snapshots` read at commit *ref* instead of disk.

    The same shape — ``{path: lines}``, keyed by each path as given, lines
    split as a text-mode read splits them (universal newlines) with line
    endings stripped, binary files (a NUL byte in the first 8 KB) left out —
    so a commit review hands the report the code it reviewed, not whatever
    the working tree holds by the time the report is written
    (plans/review-commits.md §2.5, "HTML report"). A path absent at *ref*
    (deleted or renamed by the range), a directory or submodule there, and
    every path when *ref* is no commit are left out, just as an unreadable
    file is today. One ``git cat-file --batch`` call over all the paths, each
    put in git's form (:func:`git_path`) first; *cwd* is the repository root.
    """
    wanted: Dict[str, List[str]] = {}
    for path in dict.fromkeys(paths):
        if path and "\n" not in path:
            wanted.setdefault(_git_utils().git_path(path, cwd=cwd), []).append(path)
    if not wanted:
        return {}
    try:
        stdout, _, rc = _git_utils()._run_git(
            "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}",
            check=False, cwd=cwd,
        )
    except (OSError, ValueError):
        return {}
    sha = stdout.strip()
    if rc != 0 or not sha:
        return {}
    names = list(wanted)
    where: Dict[str, str] = {"cwd": cwd} if cwd is not None else {}
    try:
        result = subprocess.run(
            _git_utils().git_argv("cat-file", "--batch", cwd=cwd),
            input="".join(f"{sha}:{name}\n" for name in names).encode(
                "utf-8", errors="surrogateescape"
            ),
            capture_output=True, **where,
        )
    except (OSError, ValueError):
        return {}
    if result.returncode != 0:
        return {}
    snapshots: Dict[str, List[str]] = {}
    data = result.stdout
    offset = 0
    for name in names:
        newline = data.find(b"\n", offset)
        if newline < 0:
            break
        header = data[offset:newline].decode("utf-8", errors="replace")
        offset = newline + 1
        if header.endswith(" missing"):
            continue
        fields = header.split()
        if len(fields) < 3 or not fields[2].isdigit():
            break  # not git's answer shape: trust nothing after it
        kind, size = fields[1], int(fields[2])
        body = data[offset:offset + size]
        offset += size + 1  # the content, then git's own LF after it
        if kind != "blob" or b"\x00" in body[:8192]:
            continue
        text = body.decode("utf-8", errors="replace")
        lines = [
            line.rstrip("\n").rstrip("\r")
            for line in io.StringIO(text, newline=None).readlines()
        ]
        for path in wanted[name]:
            snapshots[path] = list(lines)
    return snapshots


def capture_file_context(
    file_path: str,
    line_range: List[int],
    context_lines: int = 5,
    file_snapshots: Optional[Dict[str, List[str]]] = None,
) -> Optional[List[Dict[str, Any]]]:
    """Read lines around a line range from a file.

    Returns an array of ``{line_number: int, content: str}`` objects covering
    ``context_lines`` before and after the specified ``line_range``.

    When ``file_snapshots`` is provided and contains ``file_path``, the
    pre-captured snapshot is used instead of reading the file from disk.
    This allows callers to capture file content at the START of a review
    phase (via ``capture_file_snapshots()``) and avoid stale data if files
    are modified between review start and report generation.

    When no snapshot is available, falls back to reading the file from disk
    at call time.  For accurate context when files may have been modified
    after review start, prefer providing ``file_snapshots`` or using
    ``capture_diff_hunks`` with a ``base_ref`` (which uses git history).

    Args:
        file_path: Path to the file on disk (absolute or relative to cwd).
        line_range: Two-element list ``[start_line, end_line]`` (1-indexed,
            inclusive).
        context_lines: Number of extra lines to include before ``start_line``
            and after ``end_line``.  Defaults to 5.
        file_snapshots: Optional dict mapping file paths to pre-captured
            line lists (as returned by ``capture_file_snapshots()``).  When
            the file is found in this dict, its snapshot is used instead of
            reading from disk.

    Returns:
        List of ``{line_number, content}`` dicts, or ``None`` if the file
        does not exist or is binary.
    """
    if not file_path or not line_range:
        return None

    # Try snapshot first
    if file_snapshots and file_path in file_snapshots:
        all_lines = file_snapshots[file_path]
    else:
        # Fall back to reading from disk
        if not os.path.isfile(file_path):
            return None

        # Check for binary content
        if _is_binary_file(file_path):
            return None

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                all_lines = [
                    ln.rstrip("\n").rstrip("\r") for ln in f.readlines()
                ]
        except (OSError, IOError):
            return None

    if not all_lines:
        return None

    start_line = line_range[0]
    end_line = line_range[1] if len(line_range) > 1 else start_line

    # Clamp to valid range
    context_start = max(1, start_line - context_lines)
    context_end = end_line + context_lines

    # Clamp end to file length
    context_end = min(context_end, len(all_lines))

    result = []
    for i in range(context_start - 1, context_end):
        if i < 0 or i >= len(all_lines):
            continue
        result.append({
            "line_number": i + 1,
            "content": all_lines[i],
        })

    return result if result else None
