#!/usr/bin/env node

import { execSync } from 'child_process'
import { ensureGhScopes, getMissingScopes, parseGhScopes, getGhAuthStatusOutput, hasGhCli } from './gh-auth-utils.mjs'

function fail(message, extra = {}, code = 1) {
  console.error(JSON.stringify({ success: false, error: message, ...extra }, null, 2))
  process.exit(code)
}

function parseArgs(argv) {
  const args = argv.slice(2)
    .flatMap(arg => arg.split(','))
    .map(arg => arg.trim())
    .filter(Boolean)

  if (args.length === 0) {
    fail('Usage: node gh-refresh-scopes.mjs <scope[,scope2,...]>')
  }

  return Array.from(new Set(args))
}

const requiredScopes = parseArgs(process.argv)

if (!hasGhCli()) {
  fail('gh CLI is not installed. Install it with: brew install gh && gh auth login')
}

const status = getGhAuthStatusOutput()
if (!status.authenticated) {
  fail('gh CLI not authenticated. Run: gh auth login')
}

const initialCheck = ensureGhScopes(requiredScopes, 'GHCR flow')
if (initialCheck.ok) {
  console.log(JSON.stringify({
    success: true,
    skipped: true,
    reason: 'required scopes already satisfied',
    scopes: initialCheck.scopes,
    required_scopes: requiredScopes,
  }, null, 2))
  process.exit(0)
}

if (!process.stdin.isTTY || !process.stdout.isTTY) {
  const currentScopes = parseGhScopes(status.output)
  fail('TTY is required to refresh GitHub scopes in-place', {
    action: 'gh_scope_refresh_required',
    retryable: true,
    tty_required: true,
    required_scopes: requiredScopes,
    missing_scopes: getMissingScopes(currentScopes, requiredScopes),
  })
}

const scopeList = requiredScopes.join(',')
console.error(`Refreshing GitHub scopes: ${scopeList}`)

try {
  execSync(`gh auth refresh -h github.com -s ${scopeList}`, { stdio: 'inherit' })
} catch {
  fail('gh auth refresh was not completed', {
    action: 'gh_scope_refresh_required',
    retryable: true,
    tty_required: true,
    required_scopes: requiredScopes,
  })
}

const scopeCheck = ensureGhScopes(requiredScopes, 'GHCR flow')
if (scopeCheck.ok) {
  console.log(JSON.stringify({
    success: true,
    refreshed: true,
    scopes: scopeCheck.scopes,
    required_scopes: requiredScopes,
  }, null, 2))
  process.exit(0)
}

console.error('gh auth refresh completed but scopes are still missing. Trying a full GitHub CLI re-auth in this same session...')

try {
  execSync(`gh auth login --hostname github.com --git-protocol https --web --scopes ${scopeList}`, { stdio: 'inherit' })
} catch {
  fail('gh auth refresh completed, but follow-up gh auth login was not completed', scopeCheck)
}

const relogged = ensureGhScopes(requiredScopes, 'GHCR flow')
if (!relogged.ok) {
  fail('GitHub CLI re-auth completed, but required scopes are still missing', relogged)
}

console.log(JSON.stringify({
  success: true,
  refreshed: true,
  relogged: true,
  scopes: relogged.scopes,
  required_scopes: requiredScopes,
}, null, 2))
