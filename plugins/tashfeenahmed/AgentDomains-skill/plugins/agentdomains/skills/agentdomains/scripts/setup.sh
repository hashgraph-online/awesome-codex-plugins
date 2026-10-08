#!/usr/bin/env bash
# Ensure the agentdomains CLI is installed and an account exists.
set -e

if ! command -v agentdomains >/dev/null 2>&1; then
  echo "Installing agentdomains CLI..."
  if command -v go >/dev/null 2>&1; then
    go install github.com/tashfeenahmed/AgentDomains/cmd/agentdomains@latest
    # make sure GOBIN is on PATH for this session
    export PATH="$PATH:$(go env GOPATH)/bin"
  else
    echo "Go toolchain not found. Install Go, or download a prebuilt binary from:"
    echo "  https://github.com/tashfeenahmed/AgentDomains/releases"
    exit 1
  fi
fi

if [ ! -f "$HOME/.agentdomains/config.json" ] && [ -z "${AGENTDOMAINS_API_KEY:-}" ]; then
  echo "Creating an AgentDomains account..."
  agentdomains signup
else
  echo "AgentDomains already configured."
  agentdomains whoami || true
fi

echo
echo "Ready. Claim a domain with:"
echo "  agentdomains claim <name> --email you@example.com --type A --content <ip> --json"
echo "(--email is required only on this account's first claim.)"
echo "Docs: https://docs.agentdomains.co"
