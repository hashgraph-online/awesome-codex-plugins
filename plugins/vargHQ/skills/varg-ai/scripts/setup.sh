#!/usr/bin/env bash
#
# varg-ai skill setup
#
# Detects environment capabilities and determines the available rendering mode.
# No dependencies required -- runs on any system with bash and curl.
#
# Usage:
#   bash scripts/setup.sh
#

set -euo pipefail

# ── Colors ─────────────────────────────────────────────────────

green()  { printf '\033[32m%s\033[0m' "$1"; }
red()    { printf '\033[31m%s\033[0m' "$1"; }
yellow() { printf '\033[33m%s\033[0m' "$1"; }
dim()    { printf '\033[2m%s\033[0m' "$1"; }
bold()   { printf '\033[1m%s\033[0m' "$1"; }
cyan()   { printf '\033[36m%s\033[0m' "$1"; }

# ── Helpers ────────────────────────────────────────────────────

CREDENTIALS_FILE="$HOME/.varg/credentials"

# Check for saved credentials at ~/.varg/credentials
check_saved_credentials() {
  if [ -f "$CREDENTIALS_FILE" ]; then
    # Extract api_key using grep/sed (works without jq)
    SAVED_KEY=$(grep -o '"api_key"[[:space:]]*:[[:space:]]*"[^"]*"' "$CREDENTIALS_FILE" 2>/dev/null | sed 's/.*"api_key"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || echo "")
    SAVED_EMAIL=$(grep -o '"email"[[:space:]]*:[[:space:]]*"[^"]*"' "$CREDENTIALS_FILE" 2>/dev/null | sed 's/.*"email"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || echo "")
    if [ -n "$SAVED_KEY" ]; then
      return 0
    fi
  fi
  return 1
}

# ── Main ───────────────────────────────────────────────────────

echo ""
bold "varg-ai Skill Setup"
echo ""

HAS_BUN=0
HAS_FFMPEG=0
HAS_FFPROBE=0
HAS_KEY=0

# 1. Check VARG_API_KEY (env var, then saved credentials)
echo "API Key:"

if [ -n "${VARG_API_KEY:-}" ]; then
  echo "  $(green '[OK]') VARG_API_KEY is set (env)"
  HAS_KEY=1

  # Test gateway connectivity
  if command -v curl &>/dev/null; then
    RESPONSE=$(curl -s -w "\n%{http_code}" \
      -H "Authorization: Bearer $VARG_API_KEY" \
      "https://api.varg.ai/v2/billing/balance" 2>/dev/null || echo "error")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" = "200" ]; then
      BALANCE=$(echo "$BODY" | grep -o '"available":[0-9]*' | grep -o '[0-9]*' || echo "")
      if [ -n "$BALANCE" ]; then
        DOLLARS=$(echo "scale=2; $BALANCE / 100" | bc 2>/dev/null || echo "?")
        echo "  $(green '[OK]') Gateway connected. Balance: $BALANCE credits (\$$DOLLARS)"
      else
        echo "  $(green '[OK]') Gateway connected."
      fi
    elif [ "$HTTP_CODE" = "401" ]; then
      echo "  $(red '[ERR]') Invalid API key (401 Unauthorized)"
    else
      echo "  $(yellow '[WARN]') Could not verify API key (HTTP $HTTP_CODE)"
    fi
  fi
elif check_saved_credentials; then
  echo "  $(green '[OK]') VARG_API_KEY found ($CREDENTIALS_FILE)"
  if [ -n "$SAVED_EMAIL" ]; then
    echo "  $(dim "    Account: $SAVED_EMAIL")"
  fi
  export VARG_API_KEY=$SAVED_KEY
  HAS_KEY=1

  # Test gateway connectivity
  if command -v curl &>/dev/null; then
    RESPONSE=$(curl -s -w "\n%{http_code}" \
      -H "Authorization: Bearer $VARG_API_KEY" \
      "https://api.varg.ai/v2/billing/balance" 2>/dev/null || echo "error")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" = "200" ]; then
      BALANCE=$(echo "$BODY" | grep -o '"available":[0-9]*' | grep -o '[0-9]*' || echo "")
      if [ -n "$BALANCE" ]; then
        DOLLARS=$(echo "scale=2; $BALANCE / 100" | bc 2>/dev/null || echo "?")
        echo "  $(green '[OK]') Gateway connected. Balance: $BALANCE credits (\$$DOLLARS)"
      else
        echo "  $(green '[OK]') Gateway connected."
      fi
    elif [ "$HTTP_CODE" = "401" ]; then
      echo "  $(red '[ERR]') Invalid API key (401 Unauthorized)"
    else
      echo "  $(yellow '[WARN]') Could not verify API key (HTTP $HTTP_CODE)"
    fi
  fi
else
  echo "  $(red '[MISSING]') VARG_API_KEY not set"
  echo ""
  echo "  Get your API key at: $(cyan 'https://varg.ai/dashboard/api')"
  echo ""
  echo "  Then set it:"
  echo "    $(cyan 'export VARG_API_KEY=varg_xxx')"
  echo "    $(dim 'echo VARG_API_KEY=varg_xxx >> .env')"
  echo ""
  echo "  Or save globally:"
  echo "    $(dim "mkdir -p ~/.varg && echo '{\"api_key\":\"varg_xxx\"}' > ~/.varg/credentials && chmod 600 ~/.varg/credentials")"
fi

# 2. Check bun
echo ""
echo "Local Tools:"

if command -v bun &>/dev/null; then
  BUN_VERSION=$(bun --version 2>/dev/null || echo "unknown")
  echo "  $(green '[OK]') bun $BUN_VERSION"
  HAS_BUN=1
else
  echo "  $(dim '[--]') bun not found $(dim '(needed for local render mode only)')"
fi

# 3. Check ffmpeg
if command -v ffmpeg &>/dev/null; then
  echo "  $(green '[OK]') ffmpeg found"
  HAS_FFMPEG=1
else
  echo "  $(dim '[--]') ffmpeg not found $(dim '(needed for local render mode only)')"
fi

# 4. Check ffprobe
if command -v ffprobe &>/dev/null; then
  echo "  $(green '[OK]') ffprobe found"
  HAS_FFPROBE=1
else
  echo "  $(dim '[--]') ffprobe not found $(dim '(needed for local render mode only)')"
fi

# 5. Determine mode
echo ""
bold "── Available Mode ──────────────────────────"
echo ""

if [ "$HAS_BUN" -eq 1 ] && [ "$HAS_FFMPEG" -eq 1 ] && [ "$HAS_FFPROBE" -eq 1 ]; then
  echo "  $(green 'LOCAL RENDER') $(dim '(full power)')"
  echo ""
  echo "  You have all local tools. You can use either:"
  echo ""
  echo "  Local render (faster, more flexible):"
  dim "    bunx vargai@0.4.0-alpha124 render video.tsx --preview   (free preview)"
  echo ""
  dim "    bunx vargai@0.4.0-alpha124 render video.tsx --verbose   (full render)"
  echo ""
  echo "  Cloud render (via API):"
  echo "  $(dim '  curl -X POST https://api.varg.ai/v2/render \')"
  echo "  $(dim '    -H "Authorization: Bearer $VARG_API_KEY" \')"
  echo "  $(dim '    -H "Content-Type: application/json" \')"
  echo "  $(dim '    -d '\''{"code": "..."}'\''')"
  echo ""
else
  echo "  $(yellow 'CLOUD RENDER') $(dim '(zero-install)')"
  echo ""
  echo "  Send TSX code to the render service via curl:"
  echo ""
  echo "  $(dim 'curl -X POST https://api.varg.ai/v2/render \')"
  echo "  $(dim '  -H "Authorization: Bearer $VARG_API_KEY" \')"
  echo "  $(dim '  -H "Content-Type: application/json" \')"
  echo "  $(dim '  -d '\''{"code": "export default (<Render>...</Render>)"}'\''')"
  echo ""

  if [ "$HAS_BUN" -eq 0 ]; then
    echo "  To unlock local render mode, install bun:"
    dim "    curl -fsSL https://bun.sh/install | bash"
    echo ""
  fi
  if [ "$HAS_FFMPEG" -eq 0 ] || [ "$HAS_FFPROBE" -eq 0 ]; then
    echo "  To unlock local render mode, install ffmpeg (includes ffprobe):"
    dim "    brew install ffmpeg        # macOS"
    dim "    apt install ffmpeg         # Ubuntu/Debian"
    dim "    winget install ffmpeg      # Windows"
    echo ""
  fi
fi

if [ "$HAS_KEY" -eq 0 ]; then
  echo "  $(red 'Note: VARG_API_KEY is required for both modes.')"
  echo "  $(dim "Get your key at $(cyan 'https://varg.ai/dashboard/api')")"
  echo ""
fi
