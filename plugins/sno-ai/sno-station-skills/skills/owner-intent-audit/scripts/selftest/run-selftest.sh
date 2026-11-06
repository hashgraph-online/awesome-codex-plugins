#!/usr/bin/env bash
set -Eeuo pipefail

selftest_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
bash "$selftest_dir/verify-review-boundary.sh"
