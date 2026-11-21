#!/usr/bin/env python3
"""Executable compatibility wrapper for the local ActivityWatch reports."""

import os as _os
import pathlib
import sys

SCRIPT_DIR = str(pathlib.Path(__file__).resolve().parent)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from summary_core import *

# Keep the historical module attribute available for callers that patch the
# system timezone lookup through this compatibility wrapper.
os = _os
from summary_core.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
