import { createHash, createHmac, randomBytes, randomUUID } from 'node:crypto'
import { spawn } from 'node:child_process'
import { chmodSync, mkdirSync, readFileSync, statSync, renameSync, rmSync, writeFileSync } from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { gunzipSync } from 'node:zlib'

const vendor = fileURLToPath(new URL('../../vendor/gitleaks/', import.meta.url))
import http from 'node:http'
import { setTimeout as delay } from 'node:timers/promises'
const hash = value => createHash('sha256').update(value).digest('hex')
export function scannerBinary({ platform = process.platform, arch = process.arch, cacheRoot } = {}) {
  const manifest = JSON.parse(readFileSync(path.join(vendor, 'manifest.json'), 'utf8'))
  const entry = manifest.binaries[`${platform}-${arch}`]
  if (!entry) throw new Error('unsupported_platform')
  const root = cacheRoot || path.join(process.env.ACTERA_CLAUDE_BRIDGE_HOME || path.join(os.homedir(), '.actera', 'claude-code'), 'scanner')
  const executable = path.join(root, `${entry.sha256}${platform === 'win32' ? '.exe' : ''}`)
  try {
    if (hash(readFileSync(executable)) !== entry.sha256) throw new Error('scanner_integrity_failure')
  } catch (error) {
    if (error.code !== 'ENOENT') throw error
    const compressed = readFileSync(path.join(vendor, entry.file))
    if (hash(compressed) !== entry.compressedSha256) throw new Error('scanner_integrity_failure')
    const bytes = gunzipSync(compressed, { maxOutputLength: 128 * 1024 * 1024 })
    if (hash(bytes) !== entry.sha256) throw new Error('scanner_integrity_failure')
    mkdirSync(root, { recursive: true, mode: 0o700 })
    const temporary = `${executable}.${randomUUID()}.tmp`
    try {
      writeFileSync(temporary, bytes, { flag: 'wx', mode: 0o700 })
      try { renameSync(temporary, executable) } catch (error) {
        // Concurrent hooks can prepare the same immutable binary.
        if (hash(readFileSync(executable)) !== entry.sha256) throw error
      }
    } finally { rmSync(temporary, { force: true }) }
  }
  if (process.platform !== 'win32') chmodSync(executable, 0o700)
  return { executable, version: manifest.version, protocol: manifest.protocol, sha256: entry.sha256, root }
}

function statePath(binary) { return path.join(binary.root, `helper-${binary.sha256}.json`) }
function readState(binary) {
  try {
    const state = JSON.parse(readFileSync(statePath(binary), 'utf8'))
    if (state.sha256 !== binary.sha256 || !Number.isInteger(state.port) || state.port < 1 || state.port > 65535 || !/^[a-f0-9]{64}$/.test(state.token)) return undefined
    return state
  } catch { return undefined }
}

// HTTP is deliberately restricted to IPv4 loopback, with no redirects, proxy,
// cookies, or browser CORS. A proof of possession is checked before sending input.
function request(state, route, body, timeout = 4000) {
  return new Promise((resolve, reject) => {
    const content = body === undefined ? undefined : JSON.stringify(body)
    const req = http.request({ hostname: '127.0.0.1', port: state.port, path: route,
      method: content === undefined ? 'GET' : 'POST', agent: false,
      headers: { ...(route.startsWith('/health?') ? {} : { authorization: `Bearer ${state.token}` }), 'content-type': 'application/json', ...(content === undefined ? {} : { 'content-length': Buffer.byteLength(content) }) },
    }, res => {
      const chunks = []; let size = 0
      res.on('data', chunk => { size += chunk.length; if (size > 4 * 1024 * 1024) req.destroy(new Error('scanner_failure')); else chunks.push(chunk) })
      res.on('error', () => reject(new Error('scanner_failure')))
      res.on('end', () => {
        if (res.statusCode !== 200) return reject(new Error('scanner_failure'))
        try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))) } catch { reject(new Error('scanner_invalid_output')) }
      })
    })
    const timer = setTimeout(() => req.destroy(new Error('scanner_failure')), timeout)
    req.on('close', () => clearTimeout(timer))
    req.on('error', () => reject(new Error('scanner_failure')))
    req.end(content)
  })
}

async function healthy(binary, state) {
  if (!state) return false
  try {
    const challenge = randomBytes(32).toString('hex')
    const result = await request(state, `/health?challenge=${challenge}`, undefined, 500)
    const proof = createHmac('sha256', Buffer.from(state.token, 'hex')).update(challenge).digest('hex')
    return result.protocol === binary.protocol && result.version === binary.version && result.proof === proof
  } catch { return false }
}

// publish: false keeps the helper private to the caller, which must shut it down.
async function launch(binary, { publish = true } = {}) {
  const token = randomBytes(32).toString('hex')
  // Windows locks a process's working directory, so running from the plugin
  // folder would block uninstalling it. The helper reads no files from it.
  const child = spawn(binary.executable, [], { detached: true, windowsHide: true, stdio: ['pipe', 'pipe', 'ignore'], cwd: os.homedir() })
  let text = ''
  try {
    const ready = await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('scanner_failure')), 8000)
      child.once('error', () => { clearTimeout(timer); reject(new Error('scanner_failure')) })
      child.once('exit', () => { clearTimeout(timer); reject(new Error('scanner_failure')) })
      child.stdin.on('error', () => {})
      child.stdout.on('data', chunk => {
        text += chunk
        if (text.length > 4096) { clearTimeout(timer); reject(new Error('scanner_invalid_output')); return }
        if (!text.includes('\n')) return
        clearTimeout(timer)
        try { resolve(JSON.parse(text.split('\n')[0])) } catch { reject(new Error('scanner_invalid_output')) }
      })
      child.stdin.end(JSON.stringify({ token, idle_seconds: 300 }))
    })
    if (!Number.isInteger(ready.port) || ready.port < 1 || ready.port > 65535 || ready.pid !== child.pid || ready.protocol !== binary.protocol || ready.version !== binary.version) throw new Error('scanner_invalid_output')
    const state = { port: ready.port, pid: ready.pid, token, sha256: binary.sha256 }
    if (!await healthy(binary, state)) throw new Error('scanner_failure')
    if (publish) {
      const temporary = `${statePath(binary)}.${randomUUID()}.tmp`
      try {
        writeFileSync(temporary, JSON.stringify(state), { flag: 'wx', mode: 0o600 })
        renameSync(temporary, statePath(binary))
      } finally { rmSync(temporary, { force: true }) }
    }
    child.stdout.destroy()
    child.unref()
    return state
  } catch {
    child.kill()
    throw new Error('scanner_failure')
  }
}

async function ensureHelper(binary) {
  const deadline = Date.now() + 10000
  const lock = `${statePath(binary)}.lock`
  while (Date.now() < deadline) {
    const state = readState(binary)
    if (await healthy(binary, state)) return state
    try {
      writeFileSync(lock, JSON.stringify({ pid: process.pid }), { flag: 'wx', mode: 0o600 })
    } catch (error) {
      if (error.code !== 'EEXIST') throw new Error('scanner_failure')
      // Recover abandoned startup locks. Never terminate a PID read from disk.
      try {
        const owner = JSON.parse(readFileSync(lock, 'utf8'))
        let alive = true
        try { process.kill(owner.pid, 0) } catch (error) { alive = error.code !== 'ESRCH' }
        if (!alive || Date.now() - statSync(lock).mtimeMs > 10000) rmSync(lock, { force: true })
      } catch {
        try { if (Date.now() - statSync(lock).mtimeMs > 10000) rmSync(lock, { force: true }) } catch { /* Another hook completed startup. */ }
      }
      await delay(30)
      continue
    }
    try {
      const current = readState(binary)
      return await healthy(binary, current) ? current : await launch(binary)
    } finally { rmSync(lock, { force: true }) }
  }
  throw new Error('scanner_failure')
}

function checkedFindings(findings) {
  if (!Array.isArray(findings) || findings.some(f => typeof f.Secret !== 'string' || !f.Secret || typeof f.RuleID !== 'string')) throw new Error('scanner_invalid_output')
  return findings
}

async function shutdown(state) {
  await request(state, '/shutdown', {}).catch(() => {})
  // Let Windows release the executable before test/installation cleanup.
  for (let i = 0; i < 100; i++) {
    try { process.kill(state.pid, 0) } catch { break }
    await delay(10)
  }
}

export async function scan(text, cacheRoot) {
  const binary = scannerBinary({ cacheRoot })
  const state = await ensureHelper(binary)
  return checkedFindings(await request(state, '/scan', { text }))
}

// One scan with a private helper that exits before this returns, for hosts
// that wait on every process a hook leaves running (Codex on Windows).
export async function scanOnce(text, cacheRoot) {
  const binary = scannerBinary({ cacheRoot })
  const state = await launch(binary, { publish: false })
  try {
    return checkedFindings(await request(state, '/scan', { text }))
  } finally {
    await shutdown(state)
  }
}

export async function stopScanner(cacheRoot) {
  const binary = scannerBinary({ cacheRoot })
  const state = readState(binary)
  if (await healthy(binary, state)) await shutdown(state)
  rmSync(statePath(binary), { force: true })
}
