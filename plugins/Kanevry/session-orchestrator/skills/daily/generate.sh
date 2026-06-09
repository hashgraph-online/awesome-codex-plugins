#!/usr/bin/env bash
# generate.sh — Create today's daily note in the Meta-Vault.
#
# Usage:
#   bash generate.sh
#   VAULT_DIR=/path/to/vault bash generate.sh
#
# Behavior:
#   - Resolves VAULT_DIR from env, else $PWD. Must contain 03-daily/.
#   - Computes today's date via `date +%Y-%m-%d` (Europe/Vienna via system TZ).
#   - Target path: $VAULT_DIR/03-daily/YYYY-MM-DD.md
#   - If target exists → idempotent no-op (exit 0).
#   - Otherwise substitutes placeholders into templates/daily.md.tpl and writes.
#
# Exit codes:
#   0 — created OR already-exists (idempotent)
#   1 — unexpected runtime failure (set -e)
#   2 — infra error: template file missing
#   3 — config error: VAULT_DIR does not exist
#   4 — vault structure error: 03-daily/ missing

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="${SCRIPT_DIR}/templates/daily.md.tpl"

# ── Resolve VAULT_DIR ──────────────────────────────────────────────────────
: "${VAULT_DIR:=$PWD}"

if [[ ! -f "$TEMPLATE" ]]; then
  echo "error: template not found: $TEMPLATE" >&2
  exit 2
fi

if [[ ! -d "$VAULT_DIR" ]]; then
  echo "error: VAULT_DIR does not exist: $VAULT_DIR" >&2
  exit 3
fi

DAILY_DIR="$VAULT_DIR/03-daily"
if [[ ! -d "$DAILY_DIR" ]]; then
  echo "error: 03-daily/ not found in vault: $DAILY_DIR" >&2
  echo "hint: run this skill from inside the Meta-Vault, or set VAULT_DIR." >&2
  exit 4
fi

# ── Compute date / weekday ─────────────────────────────────────────────────
DATE="$(date +%Y-%m-%d)"
DOW="$(date +%u)"  # 1=Mon .. 7=Sun

# Hardcoded German weekday lookup (locale-independent for reliability).
case "$DOW" in
  1) WEEKDAY="Montag" ;;
  2) WEEKDAY="Dienstag" ;;
  3) WEEKDAY="Mittwoch" ;;
  4) WEEKDAY="Donnerstag" ;;
  5) WEEKDAY="Freitag" ;;
  6) WEEKDAY="Samstag" ;;
  7) WEEKDAY="Sonntag" ;;
  *) WEEKDAY="Unknown" ;;
esac

TARGET="$DAILY_DIR/${DATE}.md"

# ── Idempotency check ──────────────────────────────────────────────────────
if [[ -f "$TARGET" ]]; then
  # corrupt file guard: 0-byte or missing YAML frontmatter opener → re-create
  if [[ ! -s "$TARGET" ]] || [[ "$(head -c 3 "$TARGET")" != "---" ]]; then
    rm -f "$TARGET"
  else
    echo "Daily note already exists: $TARGET"
    exit 0
  fi
fi

# ── Render template ────────────────────────────────────────────────────────
TITLE="Daily ${DATE}"

# sed substitution — placeholders are {{name}}, no shell interpolation in the
# template, so this is safe with simple replacement.
sed \
  -e "s|{{date}}|${DATE}|g" \
  -e "s|{{created}}|${DATE}|g" \
  -e "s|{{updated}}|${DATE}|g" \
  -e "s|{{title}}|${TITLE}|g" \
  -e "s|{{weekday}}|${WEEKDAY}|g" \
  "$TEMPLATE" > "$TARGET.tmp"

mv "$TARGET.tmp" "$TARGET"

echo "Created daily note: $TARGET"
exit 0
