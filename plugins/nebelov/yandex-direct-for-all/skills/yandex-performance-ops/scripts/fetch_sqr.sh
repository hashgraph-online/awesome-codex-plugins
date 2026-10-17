#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
for argument in "$@"; do
  if [[ "$argument" == "--token" || "$argument" == "--direct-token" ]]; then
    echo "Сырой токен в командной строке запрещён; используйте --access-file" >&2
    exit 2
  fi
done
exec python3 "$SCRIPT_DIR/fetch_sqr_parallel.py" "$@"
