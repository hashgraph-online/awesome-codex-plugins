#!/usr/bin/env bash
# Check reference coverage, including file modes, types, and unusual paths.
# Usage: split-coverage.sh [-r remote] [-n] [-v] [-i] <base> <reference> <slice1> [slice2 ...]
# Run with -h for details. Requires Python 3. No working-tree or remote writes.
set -euo pipefail
exec python3 "$(dirname "$0")/split_coverage.py" "$@"
