#!/usr/bin/env node

/**
 * Docker Build & Push (GHCR + Docker Hub)
 *
 * Builds a Docker image for linux/amd64 and pushes to a container registry.
 * Automatically selects the best registry: GHCR (via gh CLI) > Docker Hub.
 *
 * Usage:
 *   node build-push.mjs <work-dir> <repo-name>              # auto-detect registry
 *   node build-push.mjs <work-dir> <repo-name> --registry ghcr
 *   node build-push.mjs <work-dir> <repo-name> --registry dockerhub --user <docker-hub-user>
 *
 * Output (JSON):
 *   { "success": true, "image": "ghcr.io/owner/repo:20260304-143022", "registry": "ghcr" }
 *   { "success": false, "error": "build failed: ..." }
 */

import { execFileSync, execSync } from 'child_process'
import fs from 'fs'
import path from 'path'
import { validateArtifactData } from './artifact-validator.mjs'
import { ensureGhScopesWithPrompt, hasGhCli, run } from './gh-auth-utils.mjs'

// ── Helpers ───────────────────────────────────────────────

function getDateTag () {
  const d = new Date()
  const date = `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`
  const time = `${String(d.getHours()).padStart(2, '0')}${String(d.getMinutes()).padStart(2, '0')}${String(d.getSeconds()).padStart(2, '0')}`
  return `${date}-${time}`
}

function runFile (command, args, opts = {}) {
  return execFileSync(command, args, { encoding: 'utf-8', stdio: ['ignore', 'pipe', 'pipe'], ...opts }).trim()
}

function sleep (ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

function ensureBuildDir (workDir) {
  const buildDir = path.join(workDir, '.sealos', 'build')
  fs.mkdirSync(buildDir, { recursive: true })
  return buildDir
}

function writeBuildResult (workDir, payload) {
  const validation = validateArtifactData('build-result', payload)
  if (!validation.valid) {
    throw new Error(`Invalid build-result artifact: ${validation.errors.map(err => `${err.path} ${err.message}`).join('; ')}`)
  }

  const buildDir = ensureBuildDir(workDir)
  fs.writeFileSync(
    path.join(buildDir, 'build-result.json'),
    JSON.stringify(payload, null, 2),
  )
}

// ── Registry Detection ───────────────────────────────────

function detectGhcr () {
  try {
    run('gh auth status')
    const user = run('gh api user -q .login')
    if (!user) return null
    return { registry: 'ghcr', user }
  } catch {
    return null
  }
}

function promptGhLogin () {
  if (!process.stdin.isTTY || !process.stdout.isTTY) {
    return {
      ok: false,
      error: 'gh CLI is installed but not authenticated, and interactive login is not available in this terminal. Run: gh auth login',
    }
  }

  console.error('gh CLI is installed but not authenticated. Opening `gh auth login` for GHCR access...')

  try {
    execSync('gh auth login', { stdio: 'inherit' })
  } catch {
    return {
      ok: false,
      error: 'gh auth login was not completed. GHCR push requires a successful GitHub CLI login.',
    }
  }

  const ghcr = detectGhcr()
  if (!ghcr) {
    return {
      ok: false,
      error: 'gh auth login completed, but GitHub CLI is still not authenticated for GHCR use.',
    }
  }

  return { ok: true, registryInfo: ghcr }
}

function loginGhcr (user) {
  try {
    const token = run('gh auth token')
    execSync(`echo "${token}" | docker login ghcr.io -u ${user} --password-stdin`, { stdio: 'pipe' })
    return true
  } catch (e) {
    return false
  }
}

async function ensureGhcrRegistry ({ triggerLogin = false } = {}) {
  const requiredScopes = ['write:packages']

  if (!hasGhCli()) {
    return {
      ok: false,
      error: 'gh CLI is not installed. Install it with: brew install gh && gh auth login',
    }
  }

  let ghcr = detectGhcr()
  if (!ghcr && triggerLogin) {
    const loginResult = promptGhLogin()
    if (!loginResult.ok) return loginResult
    ghcr = loginResult.registryInfo
  }

  if (!ghcr) {
    return {
      ok: false,
      error: 'gh CLI not authenticated. Run: gh auth login',
    }
  }

  const scopeCheck = await ensureGhScopesWithPrompt(
    requiredScopes,
    'GHCR push and later private-image deploy',
  )
  if (!scopeCheck.ok) {
    return scopeCheck
  }

  if (!loginGhcr(ghcr.user)) {
    return {
      ok: false,
      error: 'Failed to login to ghcr.io via gh CLI',
    }
  }

  return { ok: true, registryInfo: ghcr }
}

function getGhcrPackageVisibility (packageName) {
  try {
    return runFile('gh', ['api', `/user/packages/container/${packageName}`, '-q', '.visibility'])
  } catch {
    return null
  }
}

async function verifyGhcrPublicPull (user, packageName, tag) {
  const visibility = getGhcrPackageVisibility(packageName)
  const manifestUrl = `https://ghcr.io/v2/${user}/${packageName}/manifests/${tag}`
  const acceptHeader = 'application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.v2+json, application/vnd.docker.distribution.manifest.list.v2+json'

  let lastStatus = null
  let lastError = null

  for (let attempt = 0; attempt < 5; attempt++) {
    try {
      const tokenResponse = await fetch(`https://ghcr.io/token?scope=repository:${user}/${packageName}:pull`)
      lastStatus = tokenResponse.status

      if (tokenResponse.ok) {
        const tokenPayload = await tokenResponse.json()
        if (tokenPayload.token) {
          const manifestResponse = await fetch(manifestUrl, {
            headers: {
              Authorization: `Bearer ${tokenPayload.token}`,
              Accept: acceptHeader,
            },
          })

          lastStatus = manifestResponse.status
          if (manifestResponse.ok) {
            return { ok: true, visibility }
          }

          if (manifestResponse.status === 401 || manifestResponse.status === 403) {
            break
          }
        }
      }
    } catch (error) {
      lastError = error.message
    }

    if (attempt < 4) {
      await sleep(2000)
    }
  }

  return { ok: false, visibility, status: lastStatus, error: lastError }
}

function formatGhcrPullabilityWarning (user, packageName, tag, verification) {
  const settingsUrl = `https://github.com/users/${user}/packages/container/package/${packageName}/settings`
  const visibility = verification.visibility || 'unknown'
  const status = verification.status ? ` GHCR manifest check status: ${verification.status}.` : ''
  const detail = verification.error ? ` Last check error: ${verification.error}.` : ''
  return [
    `Built and pushed ${`ghcr.io/${user}/${packageName}:${tag}`}, but the image is not anonymously pullable from GHCR.`,
    `Current package visibility: ${visibility}.${status}${detail}`,
    `This is acceptable when the deploy step creates an image pull secret from local gh CLI credentials.`,
    `If you want a public image instead, change the package visibility in GitHub Packages: ${settingsUrl}`,
  ].join(' ')
}

function detectDockerHub () {
  try {
    const info = run('docker info 2>/dev/null')
    const match = info.match(/Username:\s*(\S+)/)
    if (match) return { registry: 'dockerhub', user: match[1] }
    return null
  } catch {
    return null
  }
}

/**
 * Auto-detect the best available registry.
 * Priority: GHCR (via gh CLI) > Docker Hub (already logged in)
 */
async function autoDetectRegistry () {
  // 1. Try GHCR via gh CLI
  if (hasGhCli()) {
    const ghcrResult = await ensureGhcrRegistry({ triggerLogin: true })
    if (ghcrResult.ok) return ghcrResult.registryInfo
    throw ghcrResult
  }

  // 2. Try Docker Hub (already logged in)
  const dockerhub = detectDockerHub()
  if (dockerhub) return dockerhub

  // 3. Nothing available
  return null
}

// ── Build & Push ─────────────────────────────────────────

async function buildAndPush (workDir, repoName, registryInfo) {
  const tag = getDateTag()
  const sanitized = repoName.toLowerCase().replace(/[^a-z0-9_.-]/g, '-')
  const startedAt = new Date().toISOString()

  let remoteImage
  if (registryInfo.registry === 'ghcr') {
    remoteImage = `ghcr.io/${registryInfo.user}/${sanitized}:${tag}`
  } else {
    remoteImage = `${registryInfo.user}/${sanitized}:${tag}`
  }

  const dockerfilePath = path.join(workDir, 'Dockerfile')
  if (!fs.existsSync(dockerfilePath)) {
    writeBuildResult(workDir, {
      outcome: 'failed',
      registry: registryInfo.registry,
      build: { image_name: sanitized, started_at: startedAt },
      push: { remote_image: remoteImage },
      error: 'No Dockerfile found in work directory',
      finished_at: new Date().toISOString(),
    })
    return { success: false, error: 'No Dockerfile found in work directory' }
  }

  try {
    execSync(
      `docker buildx build --platform linux/amd64 -t ${remoteImage} --push .`,
      { cwd: workDir, stdio: 'pipe', timeout: 600000 },
    )

    let warning = null
    let requiresImagePullSecret = false
    if (registryInfo.registry === 'ghcr') {
      const pullVerification = await verifyGhcrPublicPull(registryInfo.user, sanitized, tag)
      if (!pullVerification.ok) {
        warning = formatGhcrPullabilityWarning(registryInfo.user, sanitized, tag, pullVerification)
        requiresImagePullSecret = true
      }
    }

    writeBuildResult(workDir, {
      outcome: 'success',
      registry: registryInfo.registry,
      build: { image_name: sanitized, started_at: startedAt },
      push: { remote_image: remoteImage, pushed_at: new Date().toISOString() },
      finished_at: new Date().toISOString(),
    })

    const result = { success: true, image: remoteImage, registry: registryInfo.registry }
    if (warning) {
      result.warning = warning
      result.requires_image_pull_secret = requiresImagePullSecret
    }
    return result
  } catch (e) {
    const error = e.stderr?.toString() || e.message
    writeBuildResult(workDir, {
      outcome: 'failed',
      registry: registryInfo.registry,
      build: { image_name: sanitized, started_at: startedAt },
      push: { remote_image: remoteImage },
      error,
      finished_at: new Date().toISOString(),
    })
    return { success: false, error }
  }
}

// ── CLI ────────────────────────────────────────────────────

function parseArgs (argv) {
  const args = argv.slice(2)
  const parsed = { workDir: null, repoName: null, registry: null, user: null }

  const positional = []
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--registry' && args[i + 1]) {
      parsed.registry = args[++i]
    } else if (args[i] === '--user' && args[i + 1]) {
      parsed.user = args[++i]
    } else {
      positional.push(args[i])
    }
  }

  parsed.workDir = positional[0] || null
  parsed.repoName = positional[1] || null
  return parsed
}

const args = parseArgs(process.argv)

if (!args.workDir || !args.repoName) {
  console.error('Usage: node build-push.mjs <work-dir> <repo-name> [--registry ghcr|dockerhub] [--user <user>]')
  process.exit(1)
}

// Determine registry
let registryInfo

if (args.registry === 'ghcr') {
  // Explicit GHCR
  const ghcrResult = await ensureGhcrRegistry({ triggerLogin: true })
  if (!ghcrResult.ok) {
    console.log(JSON.stringify({ success: false, ...(ghcrResult.error ? ghcrResult : { error: 'Failed to prepare GHCR registry access' }) }))
    process.exit(1)
  }
  registryInfo = ghcrResult.registryInfo
} else if (args.registry === 'dockerhub') {
  // Explicit Docker Hub
  if (!args.user) {
    const dh = detectDockerHub()
    if (!dh) {
      console.log(JSON.stringify({ success: false, error: 'Not logged in to Docker Hub. Run: docker login' }))
      process.exit(1)
    }
    registryInfo = dh
  } else {
    registryInfo = { registry: 'dockerhub', user: args.user }
  }
} else {
  // Auto-detect
  try {
    registryInfo = await autoDetectRegistry()
  } catch (error) {
    const structured = error && typeof error === 'object' && 'error' in error
    console.log(JSON.stringify({
      success: false,
      ...(structured ? error : { error: error.message }),
    }))
    process.exit(1)
  }
  if (!registryInfo) {
    console.log(JSON.stringify({
      success: false,
      error: 'No container registry available. Install gh CLI (brew install gh && gh auth login) or run docker login.',
    }))
    process.exit(1)
  }
}

const result = await buildAndPush(path.resolve(args.workDir), args.repoName, registryInfo)
console.log(JSON.stringify(result, null, 2))

if (!result.success) process.exit(1)
