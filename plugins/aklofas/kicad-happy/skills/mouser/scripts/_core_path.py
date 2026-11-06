"""Put the core skills' script directories on sys.path (v3 arc, ARCHITECTURE.md).

Optional skills may import the core (kicad + datasheets) and nothing else.
Import this module first in any script that needs core code:

    import _core_path  # noqa: F401
    from kicad_core.values import parse_value
"""
import sys
from pathlib import Path

_SKILLS = Path(__file__).resolve().parents[2]
CORE_DIRS = (
    _SKILLS / "kicad" / "scripts",
    _SKILLS / "datasheets" / "scripts",
    _SKILLS / "datasheets",
)


def ensure_core_on_path() -> None:
    for d in reversed(CORE_DIRS):
        s = str(d)
        if d.is_dir() and s not in sys.path:
            sys.path.insert(0, s)


ensure_core_on_path()
