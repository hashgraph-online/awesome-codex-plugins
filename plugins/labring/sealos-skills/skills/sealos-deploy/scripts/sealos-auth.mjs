#!/usr/bin/env node

/**
 * Sealos Cloud Authentication — OAuth2 Device Grant Flow (RFC 8628)
 *
 * Usage:
 *   node sealos-auth.mjs check              # Check authentication status + current workspace
 *   node sealos-auth.mjs login [region]     # Start OAuth2 device login flow
 *   node sealos-auth.mjs list               # List all workspaces
 *   node sealos-auth.mjs switch <ns>        # Switch workspace (by id, uid, or teamName)
 *   node sealos-auth.mjs info               # Show current auth details
 *
 * Environment variables:
 *   SEALOS_REGION   — Sealos Cloud region URL (default from config.json)
 *
 * Flow:
 *   1. POST /api/auth/oauth2/device  → { device_code, user_code, verification_uri_complete }
 *   2. User opens verification_uri_complete in browser to authorize
 *   3. Script polls /api/auth/oauth2/token until approved
 *   4. Receives access_token → exchanges for regional token + kubeconfig
 *   5. Saves tokens to ~/.sealos/auth.json, kubeconfig to ~/.sealos/kubeconfig
 */

import { writeFileSync, readFileSync, existsSync, mkdirSync } from 'fs'
import { execSync } from 'child_process'
import { homedir, platform } from 'os'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

// ── Paths ────────────────────────────────────────────────
const __dirname = dirname(fileURLToPath(import.meta.url))
const SEALOS_DIR = join(homedir(), '.sealos')
const KC_PATH = join(SEALOS_DIR, 'kubeconfig')
const AUTH_PATH = join(SEALOS_DIR, 'auth.json')

// ── Skill constants (from config.json) ───────────────────
const CONFIG_PATH = join(__dirname, '..', 'config.json')
const config = JSON.parse(readFileSync(CONFIG_PATH, 'utf-8'))
const CLIENT_ID = config.client_id
const DEFAULT_REGION = config.default_region

// ── Check ──────────────────────────────────────────────

function check () {
  if (!existsSync(KC_PATH)) {
    return { authenticated: false }
  }

  try {
    const kc = readFileSync(KC_PATH, 'utf-8')
    if (kc.includes('server:') && (kc.includes('token:') || kc.includes('client-certificate'))) {
      const auth = existsSync(AUTH_PATH) ? JSON.parse(readFileSync(AUTH_PATH, 'utf-8')) : {}
      return {
        authenticated: true,
        kubeconfig_path: KC_PATH,
        region: auth.region || 'unknown',
        workspace: auth.current_workspace?.id || 'unknown'
      }
    }
  } catch { }

  return { authenticated: false }
}

// ── Device Grant Flow ──────────────────────────────────

/**
 * Step 1: Request device authorization
 * POST /api/auth/oauth2/device
 * Body: { client_id }
 * Response: { device_code, user_code, verification_uri, verification_uri_complete, expires_in, interval }
 */
async function requestDeviceAuthorization (region) {
  const res = await fetch(`${region}/api/auth/oauth2/device`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: CLIENT_ID,
      grant_type: 'urn:ietf:params:oauth:grant-type:device_code'
    })
  })

  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`Device authorization request failed (${res.status}): ${body || res.statusText}`)
  }

  return res.json()
}

/**
 * Step 2: Poll for token
 * POST /api/auth/oauth2/token
 * Body: { client_id, grant_type, device_code }
 *
 * Possible responses:
 * - 200: { access_token, token_type, ... }  → success
 * - 400: { error: "authorization_pending" } → keep polling
 * - 400: { error: "slow_down" }             → increase interval by 5s
 * - 400: { error: "access_denied" }         → user denied
 * - 400: { error: "expired_token" }         → device code expired
 */
async function pollForToken (region, deviceCode, interval, expiresIn) {
  // Hard cap at 10 minutes regardless of server's expires_in
  const maxWait = Math.min(expiresIn, 600) * 1000
  const deadline = Date.now() + maxWait
  let pollInterval = interval * 1000
  let lastLoggedMinute = -1

  while (Date.now() < deadline) {
    await sleep(pollInterval)

    // Log remaining time every minute
    const remaining = Math.ceil((deadline - Date.now()) / 60000)
    if (remaining !== lastLoggedMinute && remaining > 0) {
      lastLoggedMinute = remaining
      process.stderr.write(`  Waiting for authorization... (${remaining} min remaining)\n`)
    }

    const res = await fetch(`${region}/api/auth/oauth2/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        client_id: CLIENT_ID,
        grant_type: 'urn:ietf:params:oauth:grant-type:device_code',
        device_code: deviceCode
      })
    })

    if (res.ok) {
      // Success — got the token
      return res.json()
    }

    const body = await res.json().catch(() => ({}))

    switch (body.error) {
      case 'authorization_pending':
        // User hasn't authorized yet, keep polling
        break

      case 'slow_down':
        // Increase polling interval by 5 seconds (RFC 8628 §3.5)
        pollInterval += 5000
        break

      case 'access_denied':
        throw new Error('Authorization denied by user')

      case 'expired_token':
        throw new Error('Device code expired. Please run login again.')

      default:
        throw new Error(`Token request failed: ${body.error || res.statusText}`)
    }
  }

  throw new Error('Authorization timed out (10 minutes). Please run login again.')
}

/**
 * Step 3: Exchange global access_token for regional token + kubeconfig
 */
async function getRegionToken (region, globalToken) {
  const res = await fetch(`${region}/api/auth/regionToken`, {
    method: 'POST',
    headers: {
      Authorization: globalToken,
      'Content-Type': 'application/json'
    }
  })

  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`Region token exchange failed (${res.status}): ${body || res.statusText}`)
  }

  return res.json()
}

/**
 * List all workspaces (namespaces) for the authenticated user
 */
async function listWorkspaces (region, regionalToken) {
  const res = await fetch(`${region}/api/auth/namespace/list`, {
    headers: { Authorization: regionalToken }
  })

  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`List workspaces failed (${res.status}): ${body || res.statusText}`)
  }

  return res.json()
}

/**
 * Switch to a different workspace (namespace)
 */
async function switchWorkspace (region, regionalToken, nsUid) {
  const res = await fetch(`${region}/api/auth/namespace/switch`, {
    method: 'POST',
    headers: {
      Authorization: regionalToken,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ ns_uid: nsUid })
  })

  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`Switch workspace failed (${res.status}): ${body || res.statusText}`)
  }

  return res.json()
}

/**
 * Get kubeconfig for the current workspace
 */
async function getKubeconfig (region, regionalToken) {
  const res = await fetch(`${region}/api/auth/getKubeconfig`, {
    headers: { Authorization: regionalToken }
  })

  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`Get kubeconfig failed (${res.status}): ${body || res.statusText}`)
  }

  return res.json()
}

function sleep (ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// ── Login (Device Grant Flow) ──────────────────────────

async function login (region = DEFAULT_REGION) {
  region = region.replace(/\/+$/, '')

  // Step 1: Request device authorization
  const deviceAuth = await requestDeviceAuthorization(region)

  const {
    device_code: deviceCode,
    user_code: userCode,
    verification_uri: verificationUri,
    verification_uri_complete: verificationUriComplete,
    expires_in: expiresIn,
    interval = 5
  } = deviceAuth

  // Output device authorization info for the AI tool / user to display
  const authPrompt = {
    action: 'user_authorization_required',
    user_code: userCode,
    verification_uri: verificationUri,
    verification_uri_complete: verificationUriComplete,
    expires_in: expiresIn,
    message: `Please open the following URL in your browser to authorize:\n\n  ${verificationUriComplete || verificationUri}\n\nAuthorization code: ${userCode}\nExpires in: ${Math.floor(expiresIn / 60)} minutes`
  }

  // Print the authorization prompt to stderr so it's visible to the user
  // while stdout is reserved for JSON output
  process.stderr.write('\n' + authPrompt.message + '\n\nWaiting for authorization...\n')

  // Auto-open browser
  const url = verificationUriComplete || verificationUri
  try {
    const cmd = platform() === 'darwin' ? 'open' : platform() === 'win32' ? 'start' : 'xdg-open'
    execSync(`${cmd} "${url}"`, { stdio: 'ignore' })
    process.stderr.write('Browser opened automatically.\n')
  } catch {
    process.stderr.write('Could not open browser automatically. Please open the URL manually.\n')
  }

  // Step 2: Poll for token
  const tokenResponse = await pollForToken(region, deviceCode, interval, expiresIn)
  const accessToken = tokenResponse.access_token

  if (!accessToken) {
    throw new Error('Token response missing access_token')
  }

  process.stderr.write('Authorization received. Exchanging for regional token...\n')

  // Step 3: Exchange global token for regional token + kubeconfig
  const regionData = await getRegionToken(region, accessToken)
  const regionalToken = regionData.data?.token
  const kubeconfig = regionData.data?.kubeconfig

  if (!regionalToken) {
    throw new Error('Region token response missing data.token field')
  }
  if (!kubeconfig) {
    throw new Error('Region token response missing data.kubeconfig field')
  }

  // Determine current workspace from namespace list
  let currentWorkspace = null
  try {
    const nsData = await listWorkspaces(region, regionalToken)
    const namespaces = nsData.data?.namespaces || nsData.data || []
    if (Array.isArray(namespaces) && namespaces.length > 0) {
      // The first namespace or the one matching the default is the current workspace
      currentWorkspace = namespaces.find(ns => ns.nstype === 'private') || namespaces[0]
    }
  } catch {
    // Non-fatal: workspace info is optional during login
  }

  // Save kubeconfig to ~/.sealos/kubeconfig
  mkdirSync(SEALOS_DIR, { recursive: true })
  writeFileSync(KC_PATH, kubeconfig, { mode: 0o600 })

  // Save auth info with tokens
  const authData = {
    region,
    access_token: accessToken,
    regional_token: regionalToken,
    authenticated_at: new Date().toISOString(),
    auth_method: 'oauth2_device_grant'
  }
  if (currentWorkspace) {
    authData.current_workspace = {
      uid: currentWorkspace.uid,
      id: currentWorkspace.id,
      teamName: currentWorkspace.teamName
    }
  }
  writeFileSync(AUTH_PATH, JSON.stringify(authData, null, 2), { mode: 0o600 })

  process.stderr.write('Authentication successful!\n')

  return { kubeconfig_path: KC_PATH, region, workspace: currentWorkspace?.id || 'default' }
}

// ── Info ───────────────────────────────────────────────

function info () {
  const status = check()
  if (!status.authenticated) {
    return { authenticated: false, message: 'Not authenticated. Run: node sealos-auth.mjs login' }
  }

  const auth = existsSync(AUTH_PATH) ? JSON.parse(readFileSync(AUTH_PATH, 'utf-8')) : {}
  return {
    authenticated: true,
    kubeconfig_path: KC_PATH,
    region: auth.region || 'unknown',
    auth_method: auth.auth_method || 'unknown',
    authenticated_at: auth.authenticated_at || 'unknown',
    current_workspace: auth.current_workspace || null
  }
}

// ── List Workspaces ─────────────────────────────────────

async function list () {
  const auth = loadAuth()
  if (!auth.regional_token) {
    throw new Error('No regional_token found. Please run: node sealos-auth.mjs login')
  }

  const nsData = await listWorkspaces(auth.region, auth.regional_token)
  const namespaces = nsData.data?.namespaces || nsData.data || []

  return {
    current: auth.current_workspace?.id || null,
    workspaces: Array.isArray(namespaces)
      ? namespaces.map(ns => ({
        uid: ns.uid,
        id: ns.id,
        teamName: ns.teamName,
        role: ns.role,
        nstype: ns.nstype
      }))
      : []
  }
}

// ── Switch Workspace ────────────────────────────────────

async function switchWs (target) {
  if (!target) {
    throw new Error('Usage: node sealos-auth.mjs switch <namespace-id-or-uid>')
  }

  const auth = loadAuth()
  if (!auth.regional_token) {
    throw new Error('No regional_token found. Please run: node sealos-auth.mjs login')
  }

  // Find matching workspace
  const nsData = await listWorkspaces(auth.region, auth.regional_token)
  const namespaces = nsData.data?.namespaces || nsData.data || []

  if (!Array.isArray(namespaces) || namespaces.length === 0) {
    throw new Error('No workspaces found')
  }

  const targetLower = target.toLowerCase()
  const match = namespaces.find(ns =>
    ns.id === target ||
    ns.uid === target ||
    ns.id?.toLowerCase().includes(targetLower) ||
    ns.teamName?.toLowerCase().includes(targetLower)
  )

  if (!match) {
    const available = namespaces.map(ns => `  ${ns.id} (${ns.teamName})`).join('\n')
    throw new Error(`No workspace matching "${target}". Available:\n${available}`)
  }

  process.stderr.write(`Switching to workspace: ${match.id} (${match.teamName})...\n`)

  // Switch namespace to get new regional token
  const switchData = await switchWorkspace(auth.region, auth.regional_token, match.uid)
  const newToken = switchData.data?.token
  if (!newToken) {
    throw new Error('Switch response missing data.token')
  }

  // Get kubeconfig for the new workspace
  const kcData = await getKubeconfig(auth.region, newToken)
  const kubeconfig = kcData.data?.kubeconfig
  if (!kubeconfig) {
    throw new Error('Kubeconfig response missing data.kubeconfig')
  }

  // Update auth.json
  auth.regional_token = newToken
  auth.current_workspace = {
    uid: match.uid,
    id: match.id,
    teamName: match.teamName
  }
  writeFileSync(AUTH_PATH, JSON.stringify(auth, null, 2), { mode: 0o600 })

  // Update kubeconfig
  writeFileSync(KC_PATH, kubeconfig, { mode: 0o600 })

  process.stderr.write(`Switched to workspace: ${match.id}\n`)

  return {
    workspace: { uid: match.uid, id: match.id, teamName: match.teamName },
    kubeconfig_path: KC_PATH
  }
}

// ── Helpers ─────────────────────────────────────────────

function loadAuth () {
  if (!existsSync(AUTH_PATH)) {
    throw new Error('Not authenticated. Please run: node sealos-auth.mjs login')
  }
  return JSON.parse(readFileSync(AUTH_PATH, 'utf-8'))
}

// ── CLI ────────────────────────────────────────────────

const [, , cmd, ...rawArgs] = process.argv

// --insecure flag: skip TLS certificate verification (for self-signed certs)
const insecure = rawArgs.includes('--insecure')
const args = rawArgs.filter(a => a !== '--insecure')

if (insecure) {
  process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'
}

try {
  switch (cmd) {
    case 'check': {
      console.log(JSON.stringify(check()))
      break
    }

    case 'login': {
      const region = args[0] || process.env.SEALOS_REGION || DEFAULT_REGION
      const result = await login(region)
      console.log(JSON.stringify(result))
      break
    }

    case 'info': {
      console.log(JSON.stringify(info(), null, 2))
      break
    }

    case 'list': {
      const result = await list()
      console.log(JSON.stringify(result, null, 2))
      break
    }

    case 'switch': {
      const target = args[0]
      const result = await switchWs(target)
      console.log(JSON.stringify(result, null, 2))
      break
    }

    default: {
      console.log(`Sealos Cloud Auth — OAuth2 Device Grant Flow

Usage:
  node sealos-auth.mjs check              Check authentication status + current workspace
  node sealos-auth.mjs login [region]     Start OAuth2 device login flow
  node sealos-auth.mjs login --insecure   Skip TLS verification (self-signed cert)
  node sealos-auth.mjs list               List all workspaces
  node sealos-auth.mjs switch <ns>        Switch workspace (by id, uid, or teamName)
  node sealos-auth.mjs info               Show current auth details

Environment:
  SEALOS_REGION   Region URL (default: ${DEFAULT_REGION})

Flow:
  1. Run "login" → opens browser for authorization
  2. Approve in browser → script receives token automatically
  3. Token exchanged for regional token + kubeconfig → saved to ~/.sealos/`)
    }
  }
} catch (err) {
  // If TLS error and not using --insecure, hint the user
  if (!insecure && (err.message.includes('fetch failed') || err.message.includes('self-signed') || err.message.includes('CERT'))) {
    console.error(JSON.stringify({ error: err.message, hint: 'Try adding --insecure for self-signed certificates' }))
  } else {
    console.error(JSON.stringify({ error: err.message }))
  }
  process.exit(1)
}
