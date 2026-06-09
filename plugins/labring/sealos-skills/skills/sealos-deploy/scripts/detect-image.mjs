#!/usr/bin/env node

/**
 * Container Image Detection
 *
 * Detects existing container images for a GitHub project.
 * Checks Docker Hub, GHCR, docker-compose, CI workflows, and README references.
 *
 * Usage:
 *   node detect-image.mjs <github-url> [work-dir]     # Remote repo
 *   node detect-image.mjs <work-dir>                   # Local project (auto-detect GitHub URL from git remote)
 *
 * Output (JSON):
 *   { "found": true, "image": "ghcr.io/zxh326/kite", "tag": "v0.4.0", "source": "ghcr-readme", "platforms": ["linux/amd64"] }
 *   { "found": false }
 */

import fs from 'fs'
import path from 'path'
import { execSync } from 'child_process'

// ── Infrastructure images to exclude ─────────────────────

const INFRA_IMAGES = new Set([
  'postgres', 'postgresql', 'mysql', 'mariadb', 'redis', 'mongo', 'mongodb',
  'memcached', 'elasticsearch', 'rabbitmq', 'minio', 'nats', 'zookeeper',
  'kafka', 'consul', 'vault', 'nginx', 'traefik', 'envoy', 'haproxy',
])

function isInfraImage (name) {
  const lower = name.toLowerCase()
  return INFRA_IMAGES.has(lower) || [...INFRA_IMAGES].some(inf => lower.startsWith(inf + ':') || lower === inf)
}

// ── GitHub URL Parser ──────────────────────────────────────

function parseGithubUrl (url) {
  const sshMatch = url.match(/git@github\.com:([^/]+)\/(.+?)(?:\.git)?$/)
  if (sshMatch) return { owner: sshMatch[1], repo: sshMatch[2] }

  const httpsMatch = url.match(/github\.com\/([^/]+)\/([^/]+?)(?:\.git)?(?:\/.*)?$/)
  if (httpsMatch) return { owner: httpsMatch[1], repo: httpsMatch[2] }

  return null
}

// ── Image Reference Parser ────────────────────────────────

function parseImageRef (raw) {
  const s = raw.trim().replace(/^['"]|['"]$/g, '')
  if (!s || s.startsWith('$') || s.startsWith('{')) return null

  // ghcr.io/owner/repo:tag
  const ghcrMatch = s.match(/^ghcr\.io\/([a-zA-Z0-9_.-]+)\/([a-zA-Z0-9_.-]+)(?::([a-zA-Z0-9_.-]+))?$/)
  if (ghcrMatch) return { registry: 'ghcr', owner: ghcrMatch[1], repo: ghcrMatch[2], tag: ghcrMatch[3] || null }

  // docker.io/owner/repo:tag or owner/repo:tag
  const dockerMatch = s.match(/^(?:docker\.io\/)?([a-zA-Z0-9_.-]+)\/([a-zA-Z0-9_.-]+)(?::([a-zA-Z0-9_.-]+))?$/)
  if (dockerMatch) {
    const owner = dockerMatch[1]
    const repo = dockerMatch[2]
    if (owner === 'library') return null
    return { registry: 'dockerhub', owner, repo, tag: dockerMatch[3] || null }
  }

  return null
}

// ── Docker Hub ─────────────────────────────────────────────

async function checkDockerHub (namespace, repoName) {
  const url = `https://hub.docker.com/v2/namespaces/${namespace}/repositories/${repoName}/tags?page_size=10`
  try {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 10000)
    const resp = await fetch(url, { signal: controller.signal })
    clearTimeout(timer)

    if (!resp.ok) return null

    const data = await resp.json()
    if (!data.results || data.results.length === 0) return null

    const versionTagRe = /^v?\d+\.\d+/
    let bestTag = null

    for (const entry of data.results) {
      const hasAmd64 = entry.images?.some(img => img.architecture === 'amd64')
      if (!hasAmd64) continue

      const platforms = entry.images
        .map(img => `${img.os}/${img.architecture}`)
        .filter((v, i, a) => a.indexOf(v) === i)

      if (!bestTag || (versionTagRe.test(entry.name) && !versionTagRe.test(bestTag.tag))) {
        bestTag = { tag: entry.name, platforms }
      }
    }

    if (!bestTag) return null

    return { source: 'dockerhub', image: `${namespace}/${repoName}`, tag: bestTag.tag, platforms: bestTag.platforms }
  } catch {
    return null
  }
}

// ── GHCR ───────────────────────────────────────────────────

async function checkGhcr (owner, repo) {
  try {
    // Get anonymous token
    const tokenController = new AbortController()
    const tokenTimer = setTimeout(() => tokenController.abort(), 10000)
    const tokenResp = await fetch(
      `https://ghcr.io/token?scope=repository:${owner}/${repo}:pull`,
      { signal: tokenController.signal },
    )
    clearTimeout(tokenTimer)

    if (!tokenResp.ok) return null
    const { token } = await tokenResp.json()

    // List tags
    const tagsController = new AbortController()
    const tagsTimer = setTimeout(() => tagsController.abort(), 10000)
    const tagsResp = await fetch(
      `https://ghcr.io/v2/${owner}/${repo}/tags/list`,
      { headers: { Authorization: `Bearer ${token}` }, signal: tagsController.signal },
    )
    clearTimeout(tagsTimer)

    if (!tagsResp.ok) return null
    const { tags } = await tagsResp.json()
    if (!tags || tags.length === 0) return null

    // Prefer version tags
    const versionTagRe = /^v?\d+\.\d+/
    const sorted = [...tags].sort((a, b) => {
      const aVer = versionTagRe.test(a) ? 1 : 0
      const bVer = versionTagRe.test(b) ? 1 : 0
      return bVer - aVer
    })

    // Check manifest for amd64
    for (const tag of sorted.slice(0, 5)) {
      try {
        const mfController = new AbortController()
        const mfTimer = setTimeout(() => mfController.abort(), 10000)
        const mfResp = await fetch(
          `https://ghcr.io/v2/${owner}/${repo}/manifests/${tag}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              Accept: 'application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.docker.distribution.manifest.v2+json',
            },
            signal: mfController.signal,
          },
        )
        clearTimeout(mfTimer)

        if (!mfResp.ok) continue

        const manifest = await mfResp.json()
        let platforms = []

        if (manifest.manifests) {
          platforms = manifest.manifests
            .filter(m => m.platform)
            .map(m => `${m.platform.os}/${m.platform.architecture}`)
          if (!platforms.some(p => p.includes('amd64'))) continue
        } else {
          platforms = ['linux/amd64']
        }

        return { source: 'ghcr', image: `ghcr.io/${owner}/${repo}`, tag, platforms }
      } catch {
        continue
      }
    }

    return null
  } catch {
    return null
  }
}

// ── Docker Compose Image Extraction ────────────────────────

function extractImagesFromCompose (workDir) {
  const images = []
  const composeNames = ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml']

  for (const name of composeNames) {
    const p = path.join(workDir, name)
    if (!fs.existsSync(p)) continue

    const content = fs.readFileSync(p, 'utf-8')

    // Match "image:" lines in docker-compose
    for (const m of content.matchAll(/^\s*image:\s*['"]?([^\s'"#]+)['"]?/gm)) {
      const ref = parseImageRef(m[1])
      if (!ref) continue
      if (isInfraImage(ref.repo) || isInfraImage(ref.owner)) continue
      images.push(ref)
    }

    break // only read first compose file found
  }

  // Deduplicate
  const seen = new Set()
  return images.filter(img => {
    const key = `${img.registry}:${img.owner}/${img.repo}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

// ── CI Workflow Image Extraction ───────────────────────────

function extractImagesFromWorkflows (workDir) {
  const images = []
  const workflowDir = path.join(workDir, '.github', 'workflows')

  if (!fs.existsSync(workflowDir)) return images

  let files
  try {
    files = fs.readdirSync(workflowDir).filter(f => f.endsWith('.yml') || f.endsWith('.yaml'))
  } catch {
    return images
  }

  for (const file of files) {
    const content = fs.readFileSync(path.join(workflowDir, file), 'utf-8')

    // Match: docker push <image>
    for (const m of content.matchAll(/docker\s+push\s+['"]?([^\s'"$]+)['"]?/g)) {
      const ref = parseImageRef(m[1])
      if (ref) images.push(ref)
    }

    // Match: docker buildx ... --push ... -t <image>
    for (const m of content.matchAll(/docker\s+buildx\s+[^]*?-t\s+['"]?([^\s'"$]+)['"]?/g)) {
      const ref = parseImageRef(m[1])
      if (ref) images.push(ref)
    }

    // Match: images: field (GitHub Actions docker/build-push-action)
    for (const m of content.matchAll(/images:\s*['"]?([^\s'"#]+)['"]?/g)) {
      const ref = parseImageRef(m[1])
      if (ref) images.push(ref)
    }

    // Match: tags: field with full image references
    for (const m of content.matchAll(/tags:\s*[|>]?\s*\n((?:\s+.+\n?)*)/g)) {
      const block = m[1]
      for (const line of block.split('\n')) {
        const tagMatch = line.match(/^\s*-?\s*['"]?([^\s'"#$]+)['"]?\s*$/)
        if (tagMatch) {
          const ref = parseImageRef(tagMatch[1])
          if (ref) images.push(ref)
        }
      }
    }
  }

  // Deduplicate
  const seen = new Set()
  return images.filter(img => {
    const key = `${img.registry}:${img.owner}/${img.repo}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

// ── README Image Extraction ────────────────────────────────

function extractImagesFromReadme (workDir) {
  const images = []
  for (const name of ['README.md', 'readme.md', 'README.MD', 'Readme.md']) {
    const p = path.join(workDir, name)
    if (fs.existsSync(p)) {
      const content = fs.readFileSync(p, 'utf-8')

      // Match ghcr.io/owner/repo:tag
      for (const m of content.matchAll(/ghcr\.io\/([a-zA-Z0-9_.-]+)\/([a-zA-Z0-9_.-]+)(?::([a-zA-Z0-9_.-]+))?/g)) {
        images.push({ registry: 'ghcr', owner: m[1], repo: m[2], tag: m[3] || null })
      }

      // Match docker run/pull commands
      for (const m of content.matchAll(/docker\s+(?:run|pull)\s+[^\n]*?(?:docker\.io\/)?([a-zA-Z0-9_.-]+)\/([a-zA-Z0-9_.-]+)(?::([a-zA-Z0-9_.-]+))?/g)) {
        if (m[1] === 'io') continue
        images.push({ registry: 'dockerhub', owner: m[1], repo: m[2], tag: m[3] || null })
      }

      // Match hub.docker.com/r/<namespace>/<repo> URLs
      for (const m of content.matchAll(/hub\.docker\.com\/r\/([a-zA-Z0-9_.-]+)\/([a-zA-Z0-9_.-]+)/g)) {
        images.push({ registry: 'dockerhub', owner: m[1], repo: m[2], tag: null })
      }

      break
    }
  }

  // Deduplicate
  const seen = new Set()
  return images.filter(img => {
    const key = `${img.registry}:${img.owner}/${img.repo}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

// ── Docker Hub Search + Verify ─────────────────────────────

async function searchAndVerifyDockerHub (query, githubOwner, githubRepo) {
  try {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 10000)
    const resp = await fetch(
      `https://hub.docker.com/v2/search/repositories/?query=${encodeURIComponent(query)}&page_size=5`,
      { signal: controller.signal },
    )
    clearTimeout(timer)

    if (!resp.ok) return null
    const data = await resp.json()
    if (!data.results || data.results.length === 0) return null

    const githubUrlPattern = new RegExp(`github\\.com[/:]${githubOwner}/${githubRepo}`, 'i')

    for (const result of data.results) {
      const ns = result.repo_owner || result.repo_name?.split('/')[0]
      const repo = result.repo_name?.includes('/') ? result.repo_name.split('/')[1] : result.repo_name
      if (!ns || !repo) continue

      // Fetch detail to check full_description for GitHub URL
      try {
        const detailController = new AbortController()
        const detailTimer = setTimeout(() => detailController.abort(), 10000)
        const detailResp = await fetch(
          `https://hub.docker.com/v2/repositories/${ns}/${repo}/`,
          { signal: detailController.signal },
        )
        clearTimeout(detailTimer)

        if (!detailResp.ok) continue
        const detail = await detailResp.json()

        const desc = (detail.full_description || '') + ' ' + (detail.description || '')
        if (!githubUrlPattern.test(desc)) continue

        // Verified match — check tags for amd64
        const tagResult = await checkDockerHub(ns, repo)
        if (tagResult) {
          return { ...tagResult, source: 'dockerhub-search' }
        }
      } catch {
        continue
      }
    }

    return null
  } catch {
    return null
  }
}

// ── Orchestrator ───────────────────────────────────────────

async function detectExistingImage (githubUrl, workDir) {
  const parsed = parseGithubUrl(githubUrl)
  if (!parsed) {
    return { found: false, error: 'Cannot parse GitHub URL' }
  }
  const { owner, repo } = parsed

  // ── Phase 1: Direct name checks ──

  // 1. Docker Hub <owner>/<repo>
  const dockerhub = await checkDockerHub(owner, repo)
  if (dockerhub) return { found: true, ...dockerhub }

  // 2. Docker Hub <repo>/<repo> (common pattern: GitHub org ≠ Docker Hub namespace)
  if (repo !== owner) {
    const dockerhubFallback = await checkDockerHub(repo, repo)
    if (dockerhubFallback) return { found: true, ...dockerhubFallback }
  }

  // 3. GHCR <owner>/<repo>
  const ghcr = await checkGhcr(owner, repo)
  if (ghcr) return { found: true, ...ghcr }

  // ── Phase 2: Project file evidence ──

  if (workDir) {
    // 4. docker-compose.yml image: scan
    const composeImages = extractImagesFromCompose(workDir)
    for (const img of composeImages) {
      if (img.registry === 'ghcr') {
        const result = await checkGhcr(img.owner, img.repo)
        if (result) return { found: true, ...result, source: 'compose' }
      } else {
        const result = await checkDockerHub(img.owner, img.repo)
        if (result) return { found: true, ...result, source: 'compose' }
      }
    }

    // 5. CI workflow docker push scan
    const workflowImages = extractImagesFromWorkflows(workDir)
    for (const img of workflowImages) {
      if (img.registry === 'ghcr') {
        const result = await checkGhcr(img.owner, img.repo)
        if (result) return { found: true, ...result, source: 'ci-workflow' }
      } else {
        const result = await checkDockerHub(img.owner, img.repo)
        if (result) return { found: true, ...result, source: 'ci-workflow' }
      }
    }
  }

  // ── Phase 3: README scan ──

  if (workDir) {
    const readmeImages = extractImagesFromReadme(workDir)

    for (const img of readmeImages) {
      if (img.owner === owner && img.repo === repo) continue

      if (img.registry === 'ghcr') {
        const result = await checkGhcr(img.owner, img.repo)
        if (result) return { found: true, ...result, source: `${result.source}-readme` }
      } else {
        const result = await checkDockerHub(img.owner, img.repo)
        if (result) return { found: true, ...result, source: `${result.source}-readme` }
      }
    }
  }

  // ── Phase 4: Docker Hub search + verify ──

  const searchResult = await searchAndVerifyDockerHub(repo, owner, repo)
  if (searchResult) return { found: true, ...searchResult }

  return { found: false }
}

// ── Git Remote Helper ─────────────────────────────────────

function getGithubUrlFromGitRemote (dir) {
  try {
    const remote = execSync('git remote get-url origin', { cwd: dir, encoding: 'utf-8' }).trim()
    if (remote.includes('github.com')) return remote
  } catch {}
  return null
}

// ── CLI ────────────────────────────────────────────────────

const [, , arg1, arg2] = process.argv

if (!arg1) {
  console.error('Usage: node detect-image.mjs <github-url> [work-dir]')
  console.error('       node detect-image.mjs <work-dir>')
  process.exit(1)
}

// Determine if arg1 is a URL or a local path
let githubUrl, workDir
if (/^https?:\/\//.test(arg1) || arg1.startsWith('git@')) {
  githubUrl = arg1
  workDir = arg2 || '.'
} else {
  // arg1 is a local path, try to get GitHub URL from git remote
  workDir = arg1
  githubUrl = getGithubUrlFromGitRemote(workDir)
}

if (githubUrl) {
  const result = await detectExistingImage(githubUrl, workDir)
  console.log(JSON.stringify(result, null, 2))
} else {
  // No GitHub URL available — scan project files and README for image references
  const allImages = [
    ...extractImagesFromCompose(workDir),
    ...extractImagesFromWorkflows(workDir),
    ...extractImagesFromReadme(workDir),
  ]

  // Deduplicate across all sources
  const seen = new Set()
  const unique = allImages.filter(img => {
    const key = `${img.registry}:${img.owner}/${img.repo}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })

  for (const img of unique) {
    let result
    if (img.registry === 'ghcr') {
      result = await checkGhcr(img.owner, img.repo)
    } else {
      result = await checkDockerHub(img.owner, img.repo)
    }
    if (result) {
      console.log(JSON.stringify({ found: true, ...result, source: `${result.source}-local` }, null, 2))
      process.exit(0)
    }
  }
  console.log(JSON.stringify({ found: false }))
}
