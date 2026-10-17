#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${SKILL_ROUTING_KIT_REPO:-https://github.com/juew/Skill-Routing-Kit.git}"
SCRIPT_SOURCE="${BASH_SOURCE[0]:-}"
if [[ -z "$SCRIPT_SOURCE" || "$SCRIPT_SOURCE" == -* ]]; then
  SCRIPT_SOURCE="${0:-}"
fi

SCRIPT_DIR=""
if [[ -n "$SCRIPT_SOURCE" && "$SCRIPT_SOURCE" != -* ]]; then
  SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_SOURCE")" >/dev/null 2>&1 && pwd || true)"
fi

cleanup_dir=""
if [[ -n "$SCRIPT_DIR" && -f "$SCRIPT_DIR/../.codex-plugin/plugin.json" ]]; then
  ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
else
  if ! command -v git >/dev/null 2>&1; then
    echo "git is required for remote installation. Install git or clone the repository manually." >&2
    exit 1
  fi
  cleanup_dir="$(mktemp -d)"
  git clone --depth 1 "$REPO_URL" "$cleanup_dir/Skill-Routing-Kit" >/dev/null
  ROOT_DIR="$cleanup_dir/Skill-Routing-Kit"
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to run the installer." >&2
  exit 1
fi

python3 "$ROOT_DIR/scripts/install.py" "$@"

if [[ -n "$cleanup_dir" ]]; then
  rm -rf "$cleanup_dir"
fi
