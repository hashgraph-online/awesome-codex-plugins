#!/usr/bin/env bash
# validate.sh — minimal self-validation
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
exec bash "$REPO_ROOT/skills/heal-skill/scripts/audit.sh" "$SKILL_DIR"
