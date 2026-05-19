#!/usr/bin/env bash
set -euo pipefail
python -m thoth.observe.dashboard "${1:-start}"
