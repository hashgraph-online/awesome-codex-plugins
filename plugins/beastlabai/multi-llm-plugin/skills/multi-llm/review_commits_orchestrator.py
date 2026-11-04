#!/usr/bin/env python3
"""``--review-commits``: review a commit range with every model, then group and
validate the findings.

A thin entry point, as ``improve_code_orchestrator.py`` is. It owns the
module-level ``parse_args`` the ``--help`` scan reads and the ``main(argv)`` the
dispatcher calls, one module per mode because ``modes.SCRIPT_TO_MODE`` keys each
mode by its script. Everything it does lives in ``utils/commit_review.py``, the
front-door core the three commit modes and ``util commit-brief`` share
(plans/review-commits.md §2.1), so the doors cannot drift apart. It resolves the range, prints the commit block, writes or reuses the
commit brief and records ``commit_range``, then runs review-code on the
brief in-process, re-recorded as ``review-code``.

``utils.commit_review`` is imported inside each function rather than at module
scope: importing this module stays side-effect free and cheap, as every
dispatch target's must (``tests/test_instruction_portability.py``).

Usage::

    uv run --project <skill-dir> -- python <skill-dir>/multi_llm.py \\
        review-commits [<range>] [--focus "<text>"] [--context-plan <path>] \\
        [--models …|--quick] [--files …|--files-from …] [--resume] [--force]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

# Absolute, symlinks preserved — see utils/cli_common.py.
sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

from utils.stream_bootstrap import bootstrap_streams  # noqa: E402

#: This module's mode word in ``modes.py``.
MODE = "review-commits"


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    from utils import commit_review

    return commit_review.parse_args(MODE, argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    bootstrap_streams()
    from utils import commit_review

    return commit_review.front_door(
        MODE, list(sys.argv[1:] if argv is None else argv)
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
