#!/usr/bin/env python3
"""Pure exact-text preview and state checks. Never writes notes or launches commands."""
import difflib
import hashlib
from pathlib import Path, PurePosixPath
import sys

from json_protocol import emit_report, read_request


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def lf_lines(text):
    # Unified diff lines end at LF, not at Unicode separators or other controls.
    parts = text.split('\n')
    return [part + '\n' for part in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def preview(before, old, new):
    if not all(isinstance(value, str) for value in (before, old, new)):
        raise ValueError('before, old, new must be literal UTF-8 text')
    if not old or before.find(old) < 0 or before.find(old, before.find(old) + 1) >= 0:
        raise ValueError('old must match exactly once; resolve the target with more context')
    start = before.index(old)
    after = before[:start] + new + before[start + len(old):]
    lines = difflib.unified_diff(lf_lines(before), lf_lines(after),
                                fromfile='before', tofile='proposed')
    diff = ''.join(line if line.endswith('\n') else
                   line + '\n\\ No newline at end of file\n' for line in lines)
    return {'before_sha256': digest(before), 'after_sha256': digest(after),
            'content': after, 'diff': diff}


def state(current, before, expected):
    """None means proven absent, never an unreadable/failed CLI response."""
    if current == expected:
        return 'already-applied'
    if current == before:
        return 'ready'
    return 'conflict'


def contained_target(root, relative):
    vault = Path(root)
    path = PurePosixPath(relative)
    if (not vault.is_absolute() or not vault.is_dir() or not relative
            or path.is_absolute() or '\\' in relative or ':' in relative
            or any(part in ('', '.', '..') for part in relative.split('/'))):
        raise ValueError('require existing absolute vault root and exact vault-relative path')
    vault = vault.resolve()
    candidate = vault.joinpath(*path.parts)
    target = candidate.resolve()
    if not target.is_relative_to(vault) or target == vault:
        raise ValueError('target escapes the resolved vault root (including symlinks)')
    if target != candidate:
        raise ValueError('target uses a filesystem alias; resolve and review the actual path')
    if target.is_file() and target.stat().st_nlink > 1:
        raise ValueError('target has multiple hard links; use a note with a unique filesystem path')
    return target


def main():
    try:
        request = read_request()
        if not isinstance(request, dict) or set(request) != {'before', 'old', 'new'}:
            raise ValueError('expected exactly {"before": text, "old": text, "new": text}')
        report = preview(**request)
    except (ValueError, TypeError, UnicodeError) as error:
        return emit_report({'status': 'blocked', 'error': str(error)}, 1)
    return emit_report(report, 0)


if __name__ == '__main__':
    sys.exit(main())
