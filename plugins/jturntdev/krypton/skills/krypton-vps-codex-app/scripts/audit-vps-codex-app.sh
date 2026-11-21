#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  audit-vps-codex-app.sh --host SSH_ALIAS [--repo-url GIT_URL] [--repo-path REMOTE_PATH]

Read-only checks for a Linux VPS intended to be used as a Codex App SSH host.

Options:
  --host        SSH alias or host configured on the machine running Codex App.
  --repo-url    Optional Git URL to test from the VPS with git ls-remote.
  --repo-path   Optional remote repo path to inspect, for example ~/src/repo.
  -h, --help    Show this help.
EOF
}

HOST=""
REPO_URL=""
REPO_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      HOST="${2:-}"
      shift 2
      ;;
    --repo-path)
      REPO_PATH="${2:-}"
      shift 2
      ;;
    --repo-url)
      REPO_URL="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$HOST" ]]; then
  echo "Missing --host" >&2
  usage >&2
  exit 2
fi

shell_quote() {
  local value="$1"
  printf "%s" "$value" | sed "s/'/'\\\\''/g; 1s/^/'/; \$s/\$/'/"
}

echo "== Local SSH config =="
ssh_config_tmp="$(mktemp "${TMPDIR:-/tmp}/krypton-vps-codex-app-ssh-config.XXXXXX")"
ssh_config_err_tmp="$(mktemp "${TMPDIR:-/tmp}/krypton-vps-codex-app-ssh-config-err.XXXXXX")"
if ssh -G "$HOST" >"$ssh_config_tmp" 2>"$ssh_config_err_tmp"; then
  awk '
    $1 == "hostname" { print "hostname: " $2 }
    $1 == "user" { print "user: " $2 }
    $1 == "identityfile" && seen_identity != 1 { print "identityfile: " $2; seen_identity = 1 }
  ' "$ssh_config_tmp"
else
  echo "[WARN] ssh -G could not resolve host alias. Raw error:"
  sed -n '1,6p' "$ssh_config_err_tmp" || true
fi
rm -f "$ssh_config_tmp" "$ssh_config_err_tmp"

echo
echo "== Remote audit =="
repo_assignment="REPO_PATH=$(shell_quote "$REPO_PATH")"
repo_url_assignment="REPO_URL=$(shell_quote "$REPO_URL")"

ssh \
  -o BatchMode=yes \
  -o ConnectTimeout=10 \
  "$HOST" \
  "$repo_assignment $repo_url_assignment bash -s" <<'REMOTE'
set -u

failures=0
warnings=0

pass() {
  printf '[PASS] %s\n' "$1"
}

warn() {
  warnings=$((warnings + 1))
  printf '[WARN] %s\n' "$1"
}

fail() {
  failures=$((failures + 1))
  printf '[FAIL] %s\n' "$1"
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

echo "host: $(hostname 2>/dev/null || echo unknown)"
remote_user="$(whoami 2>/dev/null || echo unknown)"
echo "user: $remote_user"
echo "shell: ${SHELL:-unknown}"
echo "pwd: $(pwd 2>/dev/null || echo unknown)"

if [ "$remote_user" = "root" ]; then
  warn "remote SSH user is root; use root only for bootstrap and configure a non-root daily Codex user"
fi

if [ "$(uname -s 2>/dev/null)" = "Linux" ]; then
  pass "remote host is Linux"
else
  fail "remote host is not Linux"
fi

if [ -r /etc/os-release ]; then
  . /etc/os-release
  echo "os: ${PRETTY_NAME:-unknown}"
  if [ "${ID:-}" = "ubuntu" ] && [ "${VERSION_ID:-}" = "24.04" ]; then
    pass "Ubuntu 24.04 detected"
  elif [ "${ID:-}" = "ubuntu" ]; then
    warn "Ubuntu detected, but not 24.04 (${VERSION_ID:-unknown})"
  else
    warn "not Ubuntu; verify this is intentional"
  fi
else
  warn "/etc/os-release is not readable"
fi

for cmd in git ssh tmux codex; do
  if have_cmd "$cmd"; then
    pass "$cmd is on PATH ($(command -v "$cmd"))"
  else
    fail "$cmd is missing from PATH"
  fi
done

for cmd in node npm pnpm corepack python3 rg curl unzip docker gh jq cmux claude; do
  if have_cmd "$cmd"; then
    pass "$cmd is on PATH ($(command -v "$cmd"))"
  else
    warn "$cmd is not on PATH"
  fi
done

if have_cmd codex; then
  codex --version 2>/dev/null | sed 's/^/codex version: /' || warn "codex exists but --version failed"
fi

if [ -n "${SHELL:-}" ] && [ -x "${SHELL:-}" ]; then
  if "$SHELL" -lc 'command -v codex >/dev/null 2>&1'; then
    pass "codex is visible from the login shell"
  else
    fail "codex is not visible from the login shell"
  fi
else
  warn "cannot test login-shell PATH because SHELL is missing or not executable"
fi

if [ -d "$HOME/.codex" ]; then
  pass "~/.codex exists"
  if [ -f "$HOME/.codex/auth.json" ]; then
    mode="$(stat -c '%a' "$HOME/.codex/auth.json" 2>/dev/null || echo unknown)"
    size="$(wc -c < "$HOME/.codex/auth.json" 2>/dev/null || echo unknown)"
    case "$mode" in
      400|600)
        pass "~/.codex/auth.json exists (mode $mode, ${size} bytes; contents not shown)"
        ;;
      *)
        warn "~/.codex/auth.json exists but mode is $mode; restrict it to 600 or 400"
        ;;
    esac
  else
    warn "~/.codex/auth.json not found; auth may be in a keyring or not configured"
  fi
else
  warn "~/.codex does not exist"
fi

if [ -n "${REPO_URL:-}" ]; then
  redacted_repo_url="$(printf "%s" "$REPO_URL" | sed -E 's#(https?://)[^/@]+@#\1[redacted]@#')"
  echo "repo_url: $redacted_repo_url"
  if printf "%s" "$REPO_URL" | grep -Eq '^https?://[^/]+@'; then
    warn "repo URL appears to contain credentials; avoid tokens in Git remote URLs"
  fi
  if have_cmd git; then
    if git ls-remote --exit-code "$REPO_URL" HEAD >/dev/null 2>&1; then
      pass "GitHub repo is reachable from the VPS"
    else
      warn "GitHub repo is not reachable from the VPS; authenticate GitHub or choose another repo access method"
    fi
  fi
fi

if [ -n "${REPO_PATH:-}" ]; then
  case "$REPO_PATH" in
    "~")
      expanded_repo="$HOME"
      ;;
    "~/"*)
      expanded_repo="$HOME/${REPO_PATH#~/}"
      ;;
    *)
      expanded_repo="$REPO_PATH"
      ;;
  esac
  echo "repo_path: $expanded_repo"
  if [ -d "$expanded_repo/.git" ]; then
    pass "repo path contains a Git checkout"
    git -C "$expanded_repo" rev-parse --show-toplevel 2>/dev/null | sed 's/^/git root: /' || warn "could not resolve git root"
    status_tmp="$(mktemp "${TMPDIR:-/tmp}/krypton-vps-codex-app-git-status.XXXXXX")"
    if git -C "$expanded_repo" status --short >"$status_tmp" 2>/dev/null; then
      status_count="$(wc -l < "$status_tmp" | tr -d ' ')"
      if [ "$status_count" -eq 0 ]; then
        pass "Git status is clean"
      else
        warn "Git status is dirty ($status_count entries); showing first 80"
        sed -n '1,80p' "$status_tmp" | sed 's/^/git status: /'
        if [ "$status_count" -gt 80 ]; then
          warn "Git status output truncated after 80 entries"
        fi
      fi
    else
      warn "could not read git status"
    fi
    rm -f "$status_tmp"
    if [ -f "$expanded_repo/AGENTS.md" ]; then
      pass "repo has AGENTS.md"
    else
      warn "repo has no root AGENTS.md"
    fi
  elif [ -d "$expanded_repo" ]; then
    fail "repo path exists but is not a Git checkout"
  else
    fail "repo path does not exist"
  fi
else
  warn "no --repo-path supplied; skipped repo checks"
fi

echo
echo "summary: failures=$failures warnings=$warnings"
if [ "$failures" -gt 0 ]; then
  exit 1
fi
REMOTE
