"""Locate external programs without ever picking one out of the current directory."""

import os
import shutil


def _on_windows() -> bool:
    return os.name == "nt"


def find_executable(name: str) -> "str | None":
    """Absolute path of program *name*, or None.

    On Windows only absolute PATH entries are searched, for name + ".exe":
    shutil.which and CreateProcess both try the current directory first, so a
    program inside a downloaded project would run. A program anywhere else
    needs an explicit path. Elsewhere this is shutil.which, made absolute.
    """
    if _on_windows():
        exe = name if name.lower().endswith(".exe") else name + ".exe"
        for entry in os.environ.get("PATH", "").split(os.pathsep):
            entry = entry.strip('"')
            if os.path.isabs(entry) and os.path.isfile(os.path.join(entry, exe)):
                return os.path.abspath(os.path.join(entry, exe))
        return None
    found = shutil.which(name)
    return os.path.abspath(found) if found else None
