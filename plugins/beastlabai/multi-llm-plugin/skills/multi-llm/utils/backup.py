"""Backup utility for salvage operations.

Creates backups of existing output files before salvage operations overwrite them.
"""

if __name__ == "__main__" and not __package__:
    # Run by path: put the skill root on sys.path, found from this file's real
    # location as Python finds sys.path[0], then call the package module's entry
    # point with sys.argv untouched, so the program name stays the one typed
    # (docs/development/dispatcher.md#import-safety).
    import os
    import sys

    _UTILS_DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path[:] = [os.path.dirname(_UTILS_DIR)] + [
        p for p in sys.path if os.path.realpath(p) != _UTILS_DIR]
    from utils.backup import main

    sys.exit(main(sys.argv[1:]))

import os
import shutil
import sys
from datetime import datetime
from typing import Optional

from .stream_bootstrap import bootstrap_streams


def generate_backup_path(file_path: str) -> str:
    """Generate backup path with timestamp.

    Example: foo.json -> foo-BEFORE-SALVAGE-2026-02-04T143022.json
    """
    base, ext = os.path.splitext(file_path)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H%M%S")
    return f"{base}-BEFORE-SALVAGE-{timestamp}{ext}"


def backup_before_write(file_path: str) -> Optional[str]:
    """Create backup of file if it exists.

    Returns:
        Backup path if file existed and was backed up, None otherwise.
    """
    if not os.path.exists(file_path):
        return None

    backup_path = generate_backup_path(file_path)
    shutil.copy2(file_path, backup_path)
    return backup_path


# CLI entry point for subagents
def main(argv=None) -> int:
    bootstrap_streams()
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("Usage: python -m utils.backup <file_path>", file=sys.stderr)
        return 1

    result = backup_before_write(args[0])
    if result:
        print(f"Backed up to: {result}")
    else:
        print("No backup needed (file does not exist)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
