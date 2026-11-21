#!/usr/bin/env python3
"""Finalize file tracking after implementation completes.

Usage:
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util finalize-tracking --state-file <path_to_state.json>

The census itself is ``utils/tracking.py``; this script is its command. Every
name of ``utils.tracking`` reads through this module too, for reading only: the
code that uses a name reads it in ``utils.tracking``, so patch it there, never
here (docs/development/dispatcher.md#import-layers).
"""

import sys
from pathlib import Path
from typing import Any, List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import tracking as _tracking  # noqa: E402
from utils.stream_bootstrap import bootstrap_streams  # noqa: E402
from utils.tracking import main  # noqa: E402


def __getattr__(name: str) -> Any:
    """Any other name of ``utils.tracking``, read from its owner at each access."""
    try:
        return getattr(_tracking, name)
    except AttributeError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None


def __dir__() -> List[str]:
    return sorted({*globals(), *dir(_tracking)})


if __name__ == "__main__":
    bootstrap_streams()  # every script entry bootstraps its streams; main does it again
    sys.exit(main(sys.argv[1:]))
