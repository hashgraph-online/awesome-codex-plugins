import { createHash, randomBytes } from 'node:crypto'
import { spawn } from 'node:child_process'
import { createServer, request } from 'node:http'
import { mkdir, readFile, writeFile, rename } from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { setTimeout as delay } from 'node:timers/promises'
import { deliverBatch, loadConfig, pendingCount, pruneLocalState } from './bridge.mjs'

const protocol = 1
const revision = 4
// Without reports or control requests, the sender exits; the next hook starts one.
const idleMs = () => Number(process.env.ACTERA_CLAUDE_DELIVERY_IDLE_MS) || 5 * 60 * 1000
const identity = home => createHash('sha256').update((process.platform === 'win32' ? path.resolve(home).toLowerCase() : path.resolve(home))).digest('hex')
const stateFile = home => path.join(home, 'delivery-worker.json')
async function state(home) {
  try { return JSON.parse(await readFile(stateFile(home), 'utf8')) } catch { return undefined }
}

function rpc(port, route, token, timeout = 2000) {
  return new Promise((resolve, reject) => {
    const req = request({ hostname: '127.0.0.1', port, path: route, method: 'POST', agent: false,
      headers: token ? { authorization: `Bearer ${token}` } : {} }, res => {
      let text = ''
      res.on('data', data => { text += data; if (text.length > 32768) req.destroy(new Error('Invalid delivery worker response')) })
      res.on('end', () => {
        try { if (res.statusCode !== 200) throw new Error('Delivery worker rejected request'); resolve(JSON.parse(text)) } catch (e) { reject(e) }
      })
      res.on('error', reject)
    })
    const timer = setTimeout(() => req.destroy(new Error('Delivery worker timeout')), timeout)
    req.on('close', () => clearTimeout(timer))
    req.on('error', reject)
    req.end()
  })
}

export async function deliveryStatus(home) {
  const saved = await state(home)
  // A worker that stopped cleanly says so; probing its old port only adds latency.
  if (saved && saved.running !== false) {
    try {
      const current = await rpc(saved.port, '/status', saved.token, 500)
      if (current.identity === identity(home) && current.protocol === protocol) return current
    } catch { /* Status must distinguish a stopped worker from an empty queue. */ }
  }
  const { token, ...safe } = saved || {}
  return { ...safe, running: false, state: 'stopped' }
}

async function spawnWorker(home, stdio) {
  await mkdir(home, { recursive: true, mode: 0o700 })
  // Windows locks a process's working directory; never hold the user's project.
  return spawn(process.execPath, [fileURLToPath(new URL('../../bin/delivery-worker.mjs', import.meta.url)), home],
    { detached: true, windowsHide: true, stdio, cwd: os.homedir() })
}

// Hooks hand delivery to the worker without waiting for it to start. Reports
// are already on disk, so a slow or contested startup cannot cost a report.
export async function startDelivery(home) {
  const current = await deliveryStatus(home)
  if (current.running && current.revision === revision) return
  const child = await spawnWorker(home, 'ignore')
  child.on('error', () => {}) // The next hook or status command retries the start.
  child.unref()
}

// Explicit commands wait until a current sender is serving this directory.
export async function ensureDelivery(home) {
  const current = await deliveryStatus(home)
  if (current.running && current.revision === revision) return
  const child = await spawnWorker(home, ['ignore', 'pipe', 'pipe'])
  await new Promise((resolve, reject) => {
    let output = '', errors = ''
    // Replacing an older sender waits for its in-flight batch.
    const timer = setTimeout(() => { child.kill(); reject(new Error('Delivery worker did not start')) }, 70000)
    child.stderr.on('data', data => { errors = (errors + data).slice(-1000) })
    child.once('error', e => { clearTimeout(timer); reject(e) })
    child.once('exit', code => { clearTimeout(timer); if (!output.includes('READY')) reject(new Error(errors || `Delivery worker exited (${code})`)) })
    child.stdout.on('data', data => {
      output += data
      if (output.includes('READY')) { clearTimeout(timer); resolve() }
    })
  })
  child.stdout.destroy(); child.stderr.destroy(); child.unref()
}

export async function flushDelivery(home) {
  await ensureDelivery(home)
  const saved = await state(home)
  return rpc(saved.port, '/flush', saved.token, 65000)
}

export async function stopDelivery(home) {
  const saved = await state(home)
  if (!saved) return
  if (!(await deliveryStatus(home)).running) return
  await rpc(saved.port, '/stop', saved.token, 65000)
  for (let i = 0; i < 100 && (await deliveryStatus(home)).running; i++) await delay(20)
}

export async function runDelivery(home) {
  home = path.resolve(home)
  const id = identity(home)
  const running = await deliveryStatus(home)
  if (running.running) {
    if (running.revision >= revision) { console.log('READY'); return }
    // Replace an older sender before electing, so queue records are only
    // drained by the current implementation from here on.
    const old = await state(home)
    await rpc(old.port, '/stop', old.token, 65000).catch(() => {})
    for (let i = 0; i < 250 && (await deliveryStatus(home)).running; i++) await delay(20)
  }
  const token = randomBytes(32).toString('hex')
  // released: the bridge directory was disconnected or another sender took
  // over, so this one must not write discovery again on its way out.
  let stopping = false, released = false, idle = false, busy = Promise.resolve(), failures = 0, lastActive = Date.now()
  const previous = await state(home)
  const health = { protocol, revision, identity: id, pid: process.pid, running: true, state: 'idle', lastError: previous?.lastError || null, nextRetryAt: null }
  const serialized = fn => {
    const operation = busy.then(fn)
    busy = operation.catch(() => {})
    return operation
  }
  async function drain() {
    if (stopping) return { sent: 0, pending: await pendingCount(home) }
    const config = await loadConfig(home)
    if (!config) { stopping = released = true; return { sent: 0, pending: 0 } }
    health.state = 'sending'; health.nextRetryAt = null
    const result = await deliverBatch(config, { home, limit: 16, timeoutMs: 3000, force: true })
    if (result.error) {
      failures++
      health.state = 'retrying'
      delete health.recoveredAt
      health.lastError = { at: new Date().toISOString(), message: result.error }
      const backoff = Math.min(30000, 1000 * 2 ** Math.min(failures - 1, 5))
      health.nextRetryAt = new Date(Date.now() + Math.max(backoff, result.retryAfterMs || 0)).toISOString()
    } else {
      failures = 0; health.state = result.pending ? 'sending' : 'idle'; health.nextRetryAt = null
      // Keep the last failure visible, with a separate recovery time.
      if (health.lastError) health.recoveredAt = new Date().toISOString()
    }
    await saveState()
    return result
  }
  const server = createServer(async (req, res) => {
    req.resume()
    res.setHeader('content-type', 'application/json')
    if (req.url === '/identity') { res.end(JSON.stringify({ identity: id, protocol })); return }
    if (req.headers.authorization !== `Bearer ${token}`) { res.writeHead(403); res.end('{}'); return }
    lastActive = Date.now()
    try {
      if (req.url === '/status') res.end(JSON.stringify(health))
      else if (req.url === '/stop') { stopping = true; await busy; res.end('{}') }
      else if (req.url === '/flush') res.end(JSON.stringify(await serialized(async () => {
        let sent = 0, result
        const deadline = Date.now() + 50000
        do { result = await drain(); sent += result.sent } while (result.pending && !result.error && Date.now() < deadline)
        return { ...result, sent }
      })))
      else { res.writeHead(404); res.end('{}') }
    } catch (error) { res.writeHead(500); res.end(JSON.stringify({ error: error.message })) }
  })
  // The OS-held listening socket is the election lock. It disappears on process
  // death, avoiding stale-file locks and concurrent recovery/rename races.
  const firstPort = 20000 + parseInt(id.slice(0, 8), 16) % 30000
  const listen = candidate => new Promise((resolve, reject) => {
    server.once('error', reject)
    server.listen(candidate, '127.0.0.1', () => { server.removeListener('error', reject); resolve(candidate) })
  })
  let port
  for (let offset = 0; offset < 100 && !port; offset++) {
    const candidate = firstPort + offset
    try {
      port = await listen(candidate)
    } catch (error) {
      if (error.code !== 'EADDRINUSE') throw error
      const owner = await rpc(candidate, '/identity', undefined, 500).catch(() => undefined)
      if (owner?.identity === id && owner.protocol === protocol) {
        // The elected worker may still be writing its discovery file, or a
        // stopping worker may still hold the port it is about to release.
        for (let i = 0; i < 100 && !port; i++) {
          if ((await deliveryStatus(home)).running) { console.log('READY'); return }
          await delay(20)
          port = await listen(candidate).catch(() => undefined)
        }
        if (!port) throw new Error('Delivery worker discovery timed out')
      }
    }
  }
  if (!port) throw new Error('No local delivery worker port available')
  async function saveState() {
    const temporary = `${stateFile(home)}.${process.pid}.tmp`
    await writeFile(temporary, JSON.stringify({ port, token, ...health }), { mode: 0o600 })
    for (let attempt = 0; ; attempt++) {
      try { await rename(temporary, stateFile(home)); break }
      catch (error) {
        if (!['EPERM', 'EACCES', 'EBUSY'].includes(error.code) || attempt >= 20) throw error
        await delay(20)
      }
    }
  }
  await pruneLocalState(home)
  await saveState()
  console.log('READY')
  try {
    while (!stopping) {
      // Removing the bridge directory or its connection retires the sender.
      if (!(await loadConfig(home))) { released = true; break }
      // Keep discovery published so hooks can reach this sender. A file naming
      // another process means that sender owns the directory now.
      const published = await state(home)
      if (!published) await saveState()
      else if (published.pid !== process.pid) { released = true; break }
      if (await pendingCount(home)) {
        lastActive = Date.now()
        if (!health.nextRetryAt || Date.parse(health.nextRetryAt) <= Date.now()) await serialized(drain)
      } else if (Date.now() - lastActive >= idleMs()) { idle = true; break }
      await delay(200)
    }
  } finally {
    await busy
    // Persist failure history before releasing ownership. A replacement cannot
    // write discovery until this socket closes.
    if (!released) {
      health.running = false; health.state = 'stopped'
      await saveState()
    }
    await new Promise(resolve => server.close(resolve))
  }
  // A hook may have saved a report and seen this sender running just before
  // it stopped answering. Hand that report to a successor.
  if (idle && await pendingCount(home)) await startDelivery(home)
}
