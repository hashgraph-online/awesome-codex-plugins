#!/usr/bin/env bash
set -euo pipefail

TUNNEL_MODE="${1:-none}"
case "$TUNNEL_MODE" in
  none|quick|named) ;;
  *) printf '%s\n' 'Tunnel mode must be none, quick, or named.' >&2; exit 2 ;;
esac
NEEDS_CLOUDFLARED=0
if [[ "$TUNNEL_MODE" == 'quick' || "$TUNNEL_MODE" == 'named' ]]; then NEEDS_CLOUDFLARED=1; fi

log() { printf '%s\n' "$*" >&2; }

version_at_least_311() {
  "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)' >/dev/null 2>&1
}

find_python() {
  for candidate in python3.13 python3.12 python3.11 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && version_at_least_311 "$(command -v "$candidate")"; then
      command -v "$candidate"
      return 0
    fi
  done
  return 1
}

root_run() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    log 'Installing MCP prerequisites needs root access or sudo.'
    exit 2
  fi
}

install_python_311_or_newer() {
  local package
  if command -v apt-get >/dev/null 2>&1; then
    for package in python3.13 python3.12 python3.11; do
      if apt-cache show "$package" >/dev/null 2>&1; then
        root_run apt-get install -y "$package" >&2
        return
      fi
    done
  elif command -v dnf >/dev/null 2>&1; then
    for package in python3.13 python3.12 python3.11; do
      if dnf repoquery --available "$package" 2>/dev/null | grep -q .; then
        root_run dnf install -y "$package" >&2
        return
      fi
    done
  elif command -v yum >/dev/null 2>&1; then
    for package in python3.13 python3.12 python3.11; do
      if yum list available "$package" 2>/dev/null | grep -q "$package"; then
        root_run yum install -y "$package" >&2
        return
      fi
    done
  fi
  log 'The configured Linux package repositories do not provide Python 3.11 or newer.'
  exit 2
}

install_curl() {
  command -v curl >/dev/null 2>&1 && return
  if command -v apt-get >/dev/null 2>&1; then
    root_run apt-get install -y curl >&2
  elif command -v dnf >/dev/null 2>&1; then
    root_run dnf install -y curl >&2
  elif command -v yum >/dev/null 2>&1; then
    root_run yum install -y curl >&2
  elif command -v pacman >/dev/null 2>&1; then
    root_run pacman -Sy --noconfirm curl >&2
  else
    log 'No supported Linux package manager was found to install curl for Cloudflare Tunnel setup.'
    exit 2
  fi
  command -v curl >/dev/null 2>&1 || { log 'curl is not available after dependency installation.'; exit 2; }
}

install_homebrew() {
  if ! command -v brew >/dev/null 2>&1; then
    log 'Installing Homebrew so MCP prerequisites can be installed.'
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" >&2
    if [[ -x /opt/homebrew/bin/brew ]]; then eval "$(/opt/homebrew/bin/brew shellenv)"; fi
    if [[ -x /usr/local/bin/brew ]]; then eval "$(/usr/local/bin/brew shellenv)"; fi
  fi
  command -v brew >/dev/null 2>&1 || { log 'Homebrew installation did not provide brew.'; exit 2; }
}

PYTHON="$(find_python || true)"

OS="$(uname -s)"
if [[ "$OS" == 'Darwin' ]]; then
  missing=()
  [[ -n "$PYTHON" ]] || missing+=(python@3.13)
  command -v git >/dev/null 2>&1 || missing+=(git)
  if ((NEEDS_CLOUDFLARED)) && ! command -v cloudflared >/dev/null 2>&1; then missing+=(cloudflared); fi
  if ((${#missing[@]})); then
    install_homebrew
    brew install "${missing[@]}" >&2
  fi
  PYTHON="$(find_python || true)"
elif [[ "$OS" == 'Linux' ]]; then
  if [[ -z "$PYTHON" ]] || ! command -v git >/dev/null 2>&1; then
    if command -v apt-get >/dev/null 2>&1; then
      root_run apt-get update >&2
      root_run apt-get install -y git python3 >&2
    elif command -v dnf >/dev/null 2>&1; then
      root_run dnf install -y git python3 >&2
    elif command -v yum >/dev/null 2>&1; then
      root_run yum install -y git python3 >&2
    elif command -v pacman >/dev/null 2>&1; then
      root_run pacman -Sy --noconfirm git python >&2
    else
      log 'No supported Linux package manager was found for Git and Python 3.11+.'
      exit 2
    fi
    PYTHON="$(find_python || true)"
    if [[ -z "$PYTHON" ]]; then
      install_python_311_or_newer
      PYTHON="$(find_python || true)"
    fi
  fi
  if ((NEEDS_CLOUDFLARED)) && ! command -v cloudflared >/dev/null 2>&1; then
    install_curl
    if command -v apt-get >/dev/null 2>&1; then
      root_run mkdir -p --mode=0755 /usr/share/keyrings >&2
      curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | root_run tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
      printf '%s\n' 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main' | root_run tee /etc/apt/sources.list.d/cloudflared.list >/dev/null
      root_run apt-get update >&2
      root_run apt-get install -y cloudflared >&2
    elif command -v dnf >/dev/null 2>&1; then
      curl -fsSL https://pkg.cloudflare.com/cloudflared.repo | root_run tee /etc/yum.repos.d/cloudflared.repo >/dev/null
      root_run dnf install -y cloudflared >&2
    elif command -v yum >/dev/null 2>&1; then
      curl -fsSL https://pkg.cloudflare.com/cloudflared.repo | root_run tee /etc/yum.repos.d/cloudflared.repo >/dev/null
      root_run yum install -y cloudflared >&2
    elif command -v pacman >/dev/null 2>&1; then
      root_run pacman -Sy --noconfirm cloudflared >&2
    else
      log 'No supported Linux package manager was found for cloudflared.'
      exit 2
    fi
  fi
else
  log "Unsupported operating system: $OS"
  exit 2
fi

[[ -n "$PYTHON" ]] && version_at_least_311 "$PYTHON" || { log 'Python 3.11 or newer is not available after dependency installation.'; exit 2; }
command -v git >/dev/null 2>&1 || { log 'Git is not available after dependency installation.'; exit 2; }
if ((NEEDS_CLOUDFLARED)); then
  command -v cloudflared >/dev/null 2>&1 || { log 'cloudflared is not available after dependency installation.'; exit 2; }
fi

if [[ "$OS" == 'Darwin' ]]; then
  STATE_HOME="$HOME/Library/Application Support/chatgpt-agent"
else
  STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}/chatgpt-agent"
fi
REPO="${CHATGPT_AGENT_SOURCE:-}"
if [[ -z "$REPO" && -f "$PWD/agentctl.py" && -f "$PWD/mcp_server.py" ]]; then REPO="$PWD"; fi
if [[ -z "$REPO" ]]; then
  CANDIDATE="$(cd "$(dirname "$0")/../../.." && pwd)"
  if [[ -f "$CANDIDATE/agentctl.py" && -f "$CANDIDATE/mcp_server.py" ]]; then REPO="$CANDIDATE"; fi
fi
if [[ -z "$REPO" ]]; then
  REPO="$STATE_HOME/package"
  mkdir -p "$STATE_HOME"
  if [[ -d "$REPO/.git" ]]; then
    [[ -z "$(git -C "$REPO" status --porcelain)" ]] || { log "Bridge package has local changes at $REPO; review them before updating."; exit 2; }
    git -C "$REPO" pull --ff-only >&2
  elif [[ -e "$REPO" ]]; then
    log "Bridge install path exists but is not a Git checkout: $REPO"
    exit 2
  elif [[ -n "${CHATGPT_AGENT_REF:-}" ]]; then
    git clone --depth 1 --branch "$CHATGPT_AGENT_REF" https://github.com/TohmaN233/chatgpt-review-agent-skill.git "$REPO" >&2
  else
    git clone --depth 1 https://github.com/TohmaN233/chatgpt-review-agent-skill.git "$REPO" >&2
  fi
fi

for required in agentctl.py mcp_server.py cloudflare_tunnel.py; do
  [[ -f "$REPO/$required" ]] || { log "Bridge package is incomplete: $required is missing from $REPO"; exit 2; }
done

cloudflared_path=""
if ((NEEDS_CLOUDFLARED)); then cloudflared_path="$(command -v cloudflared)"; fi
"$PYTHON" -c 'import json,sys; print(json.dumps({"repository":sys.argv[1],"python":sys.argv[2],"tunnel_mode":sys.argv[3],"cloudflared":sys.argv[4] or None}))' \
  "$REPO" "$PYTHON" "$TUNNEL_MODE" "$cloudflared_path"
