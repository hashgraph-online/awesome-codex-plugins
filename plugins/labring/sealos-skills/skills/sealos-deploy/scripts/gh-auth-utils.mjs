#!/usr/bin/env node

import { execSync } from 'child_process'
import { dirname, join } from 'path'
import { createInterface } from 'readline/promises'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const GH_REFRESH_SCRIPT = join(__dirname, 'gh-refresh-scopes.mjs')
const IMPLIED_SCOPES = {
  'write:packages': ['read:packages'],
}

export function run (cmd, opts = {}) {
  return execSync(cmd, { encoding: 'utf-8', stdio: 'pipe', ...opts }).trim()
}

export function hasGhCli () {
  try {
    run('gh --version')
    return true
  } catch {
    return false
  }
}

export function getGhAuthStatusOutput () {
  try {
    return {
      authenticated: true,
      output: run('gh auth status 2>&1'),
    }
  } catch (error) {
    const output = `${error.stdout || ''}${error.stderr || ''}`.trim()
    return {
      authenticated: false,
      output,
    }
  }
}

export function parseGhScopes (statusOutput) {
  const text = String(statusOutput || '')
  const scopes = Array.from(text.matchAll(/'([^']+)'/g), (match) => match[1])
  return Array.from(new Set(scopes))
}

function expandImpliedScopes (scopes) {
  const expanded = new Set(scopes)
  for (const scope of Array.from(expanded)) {
    const implied = IMPLIED_SCOPES[scope] || []
    for (const item of implied) expanded.add(item)
  }
  return Array.from(expanded)
}

export function getMissingScopes (presentScopes, requiredScopes) {
  const have = new Set(expandImpliedScopes(presentScopes))
  return Array.from(new Set(requiredScopes)).filter(scope => !have.has(scope))
}

export function buildScopeRefreshCommand (requiredScopes) {
  const scopeList = Array.from(new Set(requiredScopes)).join(',')
  return `node ${JSON.stringify(GH_REFRESH_SCRIPT)} ${scopeList}`
}

function buildScopeLoginCommand (requiredScopes) {
  const scopeList = Array.from(new Set(requiredScopes)).join(',')
  return `gh auth login --hostname github.com --git-protocol https --web --scopes ${scopeList}`
}

function buildScopeRefreshAction (requiredScopes, purpose, presentScopes) {
  const normalizedScopes = Array.from(new Set(requiredScopes))
  const missingScopes = getMissingScopes(presentScopes, normalizedScopes)
  return {
    ok: false,
    action: 'gh_scope_refresh_required',
    retryable: true,
    tty_required: true,
    purpose,
    required_scopes: normalizedScopes,
    missing_scopes: missingScopes,
    suggested_command: buildScopeRefreshCommand(normalizedScopes),
    error: `gh CLI is authenticated but missing required GitHub scopes for ${purpose}: ${missingScopes.join(', ')}`,
  }
}

export function ensureGhScopes (requiredScopes, purpose) {
  if (!hasGhCli()) {
    return {
      ok: false,
      error: 'gh CLI is not installed. Install it with: brew install gh && gh auth login',
    }
  }

  const status = getGhAuthStatusOutput()
  if (!status.authenticated) {
    return {
      ok: false,
      error: 'gh CLI not authenticated. Run: gh auth login',
    }
  }

  const currentScopes = parseGhScopes(status.output)
  const missingScopes = getMissingScopes(currentScopes, requiredScopes)
  if (missingScopes.length === 0) {
    return { ok: true, scopes: currentScopes }
  }

  return buildScopeRefreshAction(requiredScopes, purpose, currentScopes)
}

export async function ensureGhScopesWithPrompt (requiredScopes, purpose, promptText = 'Missing GitHub Packages permission for GHCR. Refresh now? (y/n) ') {
  const scopeCheck = ensureGhScopes(requiredScopes, purpose)
  if (scopeCheck.ok || scopeCheck.action !== 'gh_scope_refresh_required') {
    return scopeCheck
  }

  if (!process.stdin.isTTY || !process.stdout.isTTY) {
    return scopeCheck
  }

  const rl = createInterface({
    input: process.stdin,
    output: process.stdout,
  })

  let answer = ''
  try {
    answer = await rl.question(promptText)
  } finally {
    rl.close()
  }

  if (!/^(y|yes)$/i.test(String(answer).trim())) {
    return {
      ...scopeCheck,
      user_declined: true,
      retryable: false,
      error: `${scopeCheck.error}. User declined GitHub scope refresh.`,
    }
  }

  const scopeList = Array.from(new Set(requiredScopes)).join(',')
  try {
    execSync(`gh auth refresh -h github.com -s ${scopeList}`, { stdio: 'inherit' })
  } catch {
    return {
      ...scopeCheck,
      error: `gh auth refresh was not completed. ${scopeCheck.error}`,
    }
  }

  const refreshed = ensureGhScopes(requiredScopes, purpose)
  if (refreshed.ok) {
    return {
      ...refreshed,
      refreshed: true,
    }
  }
  console.error(`gh auth refresh completed but scopes are still missing. Trying a full GitHub CLI re-auth for ${purpose} in this same session...`)

  try {
    execSync(buildScopeLoginCommand(requiredScopes), { stdio: 'inherit' })
  } catch {
    return {
      ...refreshed,
      error: `gh auth refresh completed, but required scopes are still missing for ${purpose}. Follow-up gh auth login was not completed.`,
    }
  }

  const relogged = ensureGhScopes(requiredScopes, purpose)
  if (relogged.ok) {
    return {
      ...relogged,
      refreshed: true,
      relogged: true,
    }
  }

  return {
    ...relogged,
    error: `GitHub CLI re-auth completed, but required scopes are still missing for ${purpose}: ${relogged.missing_scopes?.join(', ') || 'unknown'}`,
  }
}
