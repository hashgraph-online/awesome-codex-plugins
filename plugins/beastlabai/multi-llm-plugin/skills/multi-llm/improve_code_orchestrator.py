#!/usr/bin/env python3
"""``--improve-code``: review the code changes with every model, then apply the
validated fixes, unattended.

A thin entry point. It owns the module-level ``parse_args`` the ``--help`` scan
reads and the ``main(argv)`` the dispatcher calls, one module per mode because
``modes.SCRIPT_TO_MODE`` keys each mode by its script. Everything it does lives
in ``utils/improve_workflow.py``, shared with ``--improve-plan`` and with the
native leg's planner, so the two composites and the two legs cannot drift.

Usage::

    uv run --project <skill-dir> -- python <skill-dir>/multi_llm.py \\
        improve-code <plan> [--models …|--quick] [--files …|--files-from …] \\
        [--base-ref <ref>] [--resume] [--force]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

# Absolute, symlinks preserved — see utils/cli_common.py.
sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

from utils import improve_workflow  # noqa: E402
from utils.stream_bootstrap import bootstrap_streams  # noqa: E402

#: This module's mode word in ``modes.py``.
MODE = "improve-code"


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    return improve_workflow.parse_args(MODE, argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    bootstrap_streams()
    return improve_workflow.entry_point(MODE, argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
