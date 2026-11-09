import { ensureDelivery, flushDelivery, deliveryStatus, startDelivery, stopDelivery } from './delivery.mjs'
import { ExecutionOutcome } from './generated/outcomes.mjs'
import { DEFAULT_API_ORIGIN } from './defaults.mjs'
import { createHash, randomUUID } from 'node:crypto'
import { readFile, writeFile, mkdir, readdir, rename, rm, stat, link } from 'node:fs/promises'
import os from 'node:os'
import { stopScanner } from './scanner-client.mjs'
import path from 'node:path'

// Host-neutral bridge state: connection, durable report queue, admitted-call
// correlation, approval reuse and reviewer delegation. Host adapters derive
// call identities and payloads from their own hook events and pass them in.

// Each event can contain up to 512 KiB of tool input. Reserve outcome capacity
// for tool calls already admitted when the offline spool approaches its limit.
const MAX_QUEUED_EVENTS = 128
const MAX_QUEUED_WITH_OUTCOMES = 256
const RETRY_WINDOW_MS = 60 * 60 * 1000
const OUTCOME_WINDOW_MS = 7 * 24 * 60 * 60 * 1000
const MAINTENANCE_INTERVAL_MS = 60 * 60 * 1000

export function bridgeHome() {
  return process.env.ACTERA_CLAUDE_BRIDGE_HOME || path.join(os.homedir(), '.actera', 'claude-code')
}

function configPath(home) {
  return path.join(home, 'config.json')
}
function queuePath(home) {
  return path.join(home, 'queue')
}
function markerPath(home) {
  return path.join(home, 'registered.json')
}
function offlinePath(home) {
  return path.join(home, 'offline-until.json')
}

function limitNoticePath(home) {
  return path.join(home, 'limit-notice.json')
}
function errorPath(home) {
  return path.join(home, 'last-error.json')
}
function deliveredPath(home) {
  return path.join(home, 'last-delivery.json')
}

function maintenancePath(home) {
  return path.join(home, 'last-maintenance.json')
}

function approvalPath(home, fingerprint) {
  return path.join(home, 'approvals', `${fingerprint}.json`)
}

function approvalClaimPath(home, decisionId) {
  const decisionHash = createHash('sha256').update(decisionId).digest('hex')
  return path.join(home, 'approvals', `${decisionHash}.claimed`)
}

async function legacyApprovalClaimed(home, decisionId) {
  const decisionHash = createHash('sha256').update(decisionId).digest('hex')
  try {
    return (await readdir(path.join(home, 'approvals'))).some((name) => name.endsWith(`-${decisionHash}.claimed`))
  } catch (error) {
    if (error?.code === 'ENOENT') return false
    throw error
  }
}

function reviewerPath(home) {
  return path.join(home, 'reviewer.json')
}

export function credentialID(config) {
  return createHash('sha256').update(config.apiKey).digest('hex').slice(0, 16)
}

function toolCallPath(home, key) {
  return path.join(home, 'tool-calls', `${key}.json`)
}

async function writeJsonAtomic(file, value) {
  await mkdir(path.dirname(file), { recursive: true, mode: 0o700 })
  const temporary = `${file}.${randomUUID()}.tmp`
  try {
    await writeFile(temporary, JSON.stringify(value) + '\n', { flag: 'wx', mode: 0o600 })
    await rename(temporary, file)
  } catch (error) {
    await rm(temporary, { force: true })
    throw error
  }
}

async function readJson(file) {
  try {
    return JSON.parse(await readFile(file, 'utf8'))
  } catch (error) {
    if (error?.code === 'ENOENT') return undefined
    throw error
  }
}

export function validateConfig(input) {
  const url = new URL(input.baseUrl ?? DEFAULT_API_ORIGIN)
  if (url.username || url.password || url.search || url.hash || url.pathname !== '/')
    throw new Error('Actera base URL must be an origin without a path or credentials')
  if (
    url.protocol !== 'https:' &&
    !(url.protocol === 'http:' && ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname))
  )
    throw new Error('Use HTTPS for remote Actera; HTTP is permitted only on loopback')
  if (!/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/.test(input.agentId))
    throw new Error('Agent ID must be 1–128 letters, digits, dots, underscores, colons, or hyphens')
  if (!/^actera_\S{25,}$/.test(input.apiKey)) throw new Error('A valid actera_ API key is required')
  if (input.capture !== undefined && !['metadata', 'tool-inputs'].includes(input.capture)) throw new Error('Capture must be metadata or tool-inputs')
  return {
    version: 3,
    baseUrl: url.origin,
    agentId: input.agentId,
    apiKey: input.apiKey,
    capture: input.capture || 'tool-inputs',
  }
}

export async function configure(input, home = bridgeHome()) {
  await stopDelivery(home)
  await rm(path.join(home, 'delivery-worker.json'), { force: true })
  const previous = await readJson(configPath(home))
  const config = validateConfig(input)
  const sameIdentity =
    previous?.baseUrl === config.baseUrl &&
    previous?.agentId === config.agentId &&
    previous?.apiKey === config.apiKey
  const queued = await queueFiles(home)
  if (queued.length && sameIdentity && previous.version === 3)
    throw new Error(`Flush the ${queued.length} queued event(s) before changing configuration`)
  const archive = previous && (!sameIdentity || previous.version !== 3) && queued.length
    ? await archivePreviousConnection(home, previous, queued.length)
    : undefined
  try {
    await writeJsonAtomic(configPath(home), config)
  } catch (error) {
    if (archive) await archive.restore()
    throw error
  }
  await rm(markerPath(home), { force: true })
  await rm(offlinePath(home), { force: true })
  await rm(errorPath(home), { force: true })
  await rm(deliveredPath(home), { force: true })
  if (!sameIdentity) await rm(reviewerPath(home), { force: true })
  return {
    baseUrl: config.baseUrl,
    agentId: config.agentId,
    capture: config.capture,
    home,
    ...(archive ? { archivedEvents: archive.count, archivePath: archive.path } : {}),
  }
}

async function archivePreviousConnection(home, previous, count) {
  const archive = path.join(home, 'archived', `${new Date().toISOString().replaceAll(':', '-')}-${randomUUID()}`)
  await mkdir(archive, { recursive: true, mode: 0o700 })
  await writeJsonAtomic(path.join(archive, 'config.json'), previous)
  const moved = []
  const names = [
    'queue', 'approvals', 'tool-calls', 'tool-outcomes', 'reviewer.json', 'registered.json',
    'offline-until.json', 'limit-notice.json', 'last-error.json', 'last-delivery.json', 'last-maintenance.json',
  ]
  const restore = async () => {
    for (const name of moved.reverse()) await rename(path.join(archive, name), path.join(home, name))
    await rm(archive, { recursive: true, force: true })
  }
  try {
    for (const name of names) {
      try {
        await rename(path.join(home, name), path.join(archive, name))
        moved.push(name)
      } catch (error) {
        if (error?.code !== 'ENOENT') throw error
      }
    }
  } catch (error) {
    await restore()
    throw error
  }
  return { path: archive, count, restore }
}

// The stored connection only. Host adapters add their own mode settings.
export async function loadConfig(home = bridgeHome()) {
  return readJson(configPath(home))
}

export async function provisionBridge(input, home = bridgeHome(), timeoutMs = 8000) {
  const pending = validateConfig(input)
  const readiness = await agentReadiness(pending, timeoutMs, home)
  const result = await configure(pending, home)
  return result
}

// Persist the admitted (already redacted) action, rather than reconstructing
// authority from incidental metadata on a later lifecycle hook.
export async function rememberAdmittedCall(home, key, record) {
  await writeJsonAtomic(toolCallPath(home, key), { ...record, savedAt: Date.now() })
}

export async function admittedCall(home, key) {
  return readJson(toolCallPath(home, key))
}

// Persist the first body for each outcome so retries retain occurred_at too.
// Atomic link publication elects one body across concurrent hook processes.
export async function queueOutcomeReport(home, key, outcome, report) {
  const outcomeFile = path.join(home, 'tool-outcomes', `${key}-${outcome}.json`)
  await mkdir(path.dirname(outcomeFile), { recursive: true })
  const candidate = `${outcomeFile}.${randomUUID()}.tmp`
  await writeJsonAtomic(candidate, { _tool_call_key: key, ...report })
  try {
    await link(candidate, outcomeFile)
  } catch (error) {
    if (error.code !== 'EEXIST') throw error
  } finally { await rm(candidate, { force: true }) }
  const stableReport = await readJson(outcomeFile)
  if (await readJson(`${outcomeFile}.sent`)) return stableReport
  await queueReport(home, stableReport, undefined, MAX_QUEUED_WITH_OUTCOMES)
  return stableReport
}

export async function rememberPendingApproval(home, fingerprint, decision, request) {
  if (!fingerprint || decision.status !== 'PENDING_APPROVAL') return
  await writeJsonAtomic(approvalPath(home, fingerprint), {
    decisionId: decision?.id,
    idempotencyKey: request.idempotency_key,
    actionType: request.action.type,
    savedAt: Date.now(),
  })
}

export async function previousApproval(home, fingerprint, config, request, timeoutMs = 5000) {
  if (!fingerprint) return undefined
  const saved = await readJson(approvalPath(home, fingerprint))
  if (!saved || Date.now() - saved.savedAt > RETRY_WINDOW_MS || saved.actionType !== request.action.type)
    return undefined
  const claimPath = approvalClaimPath(home, saved.decisionId)
  if (await legacyApprovalClaimed(home, saved.decisionId)) return undefined
  try {
    await readFile(claimPath)
    return undefined // That approval already released one tool call.
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error
  }
  const response = await fetch(`${config.baseUrl}/v1/decisions/${encodeURIComponent(saved.decisionId)}/status`, {
    headers: { authorization: `Bearer ${config.apiKey}` },
    redirect: 'error',
    signal: AbortSignal.timeout(timeoutMs),
  })
  if (!response.ok) throw new Error(`Actera decision lookup returned HTTP ${response.status}`)
  const decision = await response.json()
  if (
    decision.id !== saved.decisionId ||
    decision.agent_id !== config.agentId ||
    decision.action_type !== saved.actionType ||
    decision.idempotency_key !== saved.idempotencyKey
  )
    throw new Error('Saved approval does not match the Actera Decision')
  if (decision.status === 'APPROVED' && !(await claimApproval(home, saved.decisionId))) return undefined
  if (decision.status !== 'APPROVED' && decision.status !== 'PENDING_APPROVAL')
    await rm(approvalPath(home, fingerprint), { force: true })
  return decision
}

export async function startReviewerLink(config, home = bridgeHome(), timeoutMs = 8000) {
  const response = await fetch(`${config.baseUrl}/v1/reviewer-links`, {
    method: 'POST',
    headers: { authorization: `Bearer ${config.apiKey}`, 'content-type': 'application/json' },
    body: '{}',
    redirect: 'error',
    signal: AbortSignal.timeout(timeoutMs),
  })
  if (!response.ok) throw new Error(`Actera account link returned HTTP ${response.status}`)
  const link = await response.json()
  let browserUrl
  try {
    browserUrl = new URL(link.browser_url)
  } catch {
    throw new Error('Actera returned an invalid account link')
  }
  const apiUrl = new URL(config.baseUrl)
  const loopbackAlias =
    apiUrl.protocol === 'http:' &&
    browserUrl.protocol === 'http:' &&
    ['localhost', '127.0.0.1'].includes(apiUrl.hostname) &&
    ['localhost', '127.0.0.1'].includes(browserUrl.hostname) &&
    apiUrl.port === browserUrl.port
  if (
    !/^actera_reviewer_\S{40,}$/.test(link.approval_token) ||
    !/^[0-9a-f-]{36}$/i.test(link.workspace_id) ||
    !(browserUrl.origin === apiUrl.origin || loopbackAlias) ||
    browserUrl.pathname !== '/auth/reviewer-link' ||
    !browserUrl.searchParams.get('code')
  )
    throw new Error('Actera returned an invalid account link')
  await writeJsonAtomic(reviewerPath(home), {
    token: link.approval_token,
    workspaceId: link.workspace_id,
    baseUrl: config.baseUrl,
    agentId: config.agentId,
    credentialId: credentialID(config),
  })
  return { browserUrl: link.browser_url, workspaceId: link.workspace_id }
}

export async function loadReviewer(config, home = bridgeHome()) {
  const reviewer = await readJson(reviewerPath(home))
  if (
    !reviewer ||
    reviewer.baseUrl !== config.baseUrl ||
    reviewer.agentId !== config.agentId ||
    reviewer.credentialId !== credentialID(config) ||
    !/^actera_reviewer_\S{40,}$/.test(reviewer.token)
  )
    throw new Error('Link your Actera account first with actera-hook.mjs link')
  return reviewer
}

export async function reviewerLinkStatus(config, home = bridgeHome(), timeoutMs = 5000) {
  const reviewer = await loadReviewer(config, home)
  const response = await fetch(`${config.baseUrl}/v1/reviewer-links/status`, {
    headers: { authorization: `Bearer ${reviewer.token}` },
    redirect: 'error',
    signal: AbortSignal.timeout(timeoutMs),
  })
  if (!response.ok) throw new Error(`Actera account link status returned HTTP ${response.status}`)
  const status = await response.json()
  return { linked: status.linked === true, workspaceId: reviewer.workspaceId }
}

// An approved Decision releases exactly one held tool call. Returns false
// when another call already used it.
export async function claimApproval(home, decisionId) {
  if (await legacyApprovalClaimed(home, decisionId)) return false
  try {
    await mkdir(path.dirname(approvalClaimPath(home, decisionId)), { recursive: true, mode: 0o700 })
    await writeFile(approvalClaimPath(home, decisionId), JSON.stringify({ at: new Date().toISOString() }) + '\n', {
      flag: 'wx',
      mode: 0o600,
    })
    return true
  } catch (error) {
    if (error?.code === 'EEXIST') return false
    throw error
  }
}

// The narrow status of one Decision, as the bound agent may read it.
export async function decisionStatus(config, decisionId, timeoutMs = 5000) {
  const response = await fetch(`${config.baseUrl}/v1/decisions/${encodeURIComponent(decisionId)}/status`, {
    headers: { authorization: `Bearer ${config.apiKey}` },
    redirect: 'error',
    signal: AbortSignal.timeout(timeoutMs),
  })
  if (!response.ok) throw new Error(`Actera decision lookup returned HTTP ${response.status}`)
  const decision = await response.json()
  if (decision.id !== decisionId || decision.agent_id !== config.agentId)
    throw new Error('Decision does not belong to this agent')
  return decision
}

const alreadyReleased = () => new Error('This approved Decision already released another tool call')

// The linked person approves or rejects a held Decision from the agent host.
// Actera checks that they may review it; an approval is claimed for this call.
export async function reviewDecision(config, decisionId, choice, { home = bridgeHome(), idempotencyPrefix, rejectReason, timeoutMs = 8000 }) {
  if (!/^[0-9a-f-]{36}$/i.test(decisionId) || !['approve', 'reject'].includes(choice))
    throw new Error('Invalid Decision or review choice')
  let decision = await decisionStatus(config, decisionId, timeoutMs)
  if (decision.status === 'PENDING_APPROVAL') {
    const reviewer = await loadReviewer(config, home)
    const response = await fetch(`${config.baseUrl}/v1/decisions/${decisionId}/${choice}`, {
      method: 'POST',
      headers: {
        authorization: `Bearer ${reviewer.token}`,
        'Actera-Workspace-Id': reviewer.workspaceId,
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        idempotency_key: `${idempotencyPrefix}-${choice}:${decisionId}`,
        ...(choice === 'reject' ? { reason: rejectReason } : {}),
      }),
      redirect: 'error',
      signal: AbortSignal.timeout(timeoutMs),
    })
    if (!response.ok) throw new Error(`Actera ${choice} returned HTTP ${response.status}`)
    decision = await response.json()
  }
  if (
    decision.id !== decisionId ||
    decision.agent_id !== config.agentId ||
    decision.status !== (choice === 'approve' ? 'APPROVED' : 'REJECTED')
  )
    throw new Error('Actera returned an unexpected review result')
  if (choice === 'approve' && !(await claimApproval(home, decisionId))) throw alreadyReleased()
  return { id: decision.id, status: decision.status }
}

// A reviewer can resolve a held call in Actera while the host's prompt is
// open. An approval found here is claimed for this call.
export async function reviewedElsewhere(config, decisionId, home = bridgeHome(), timeoutMs = 5000) {
  if (!/^[0-9a-f-]{36}$/i.test(decisionId)) throw new Error('Invalid Decision')
  const decision = await decisionStatus(config, decisionId, timeoutMs)
  if (decision.status === 'APPROVED' && !(await claimApproval(home, decisionId))) throw alreadyReleased()
  return { id: decision.id, status: decision.status, ...(decision.reason ? { reason: decision.reason } : {}) }
}

export async function requestDecision(config, request, timeoutMs = 8000) {
  const decision = await postActera(config, 'decisions', request, timeoutMs)
  if (!decision?.id || typeof decision.status !== 'string') throw new Error('Actera returned an invalid Decision')
  return decision
}

export async function agentReadiness(config, timeoutMs = 5000, home = bridgeHome()) {
  const response = await fetch(`${config.baseUrl}/v1/agents/${encodeURIComponent(config.agentId)}/readiness`, {
    headers: { authorization: `Bearer ${config.apiKey}` },
    redirect: 'error',
    signal: AbortSignal.timeout(timeoutMs),
  })
  if (!response.ok) throw new Error(`Actera agent readiness returned HTTP ${response.status}`)
  const readiness = await response.json()
  if (readiness.agent_id !== config.agentId || readiness.ready !== true || !['DISCOVERED', 'ACTIVE'].includes(readiness.status))
    throw new Error(`Actera agent ${config.agentId} is unavailable or returned inconsistent readiness`)
  return readiness
}

async function queueReport(home, activity, filename = `${Date.now()}-${randomUUID()}.json`, limit = MAX_QUEUED_EVENTS) {
  if ((await queueFiles(home)).length >= limit)
    throw new Error('Actera report queue is full; flush queued events before continuing')
  await writeJsonAtomic(path.join(queuePath(home), filename), activity)
}

export async function pruneLocalState(home) {
  const now = Date.now()
  const marker = await readJson(maintenancePath(home))
  if (marker && now - marker.at < MAINTENANCE_INTERVAL_MS) return
  for (const [directory, maxAge] of [
    ['approvals', OUTCOME_WINDOW_MS],
    ['tool-calls', OUTCOME_WINDOW_MS],
  ]) {
    let names
    try {
      names = await readdir(path.join(home, directory))
    } catch (error) {
      if (error?.code === 'ENOENT') continue
      throw error
    }
    for (const name of names) {
      if (!name.endsWith('.json') && !name.endsWith('.claimed')) continue
      const file = path.join(home, directory, name)
      try {
        // Unresolved calls can still hold backend capacity. Keep correlation
        // until a definitive result has actually been acknowledged.
        if (directory === 'tool-calls') {
          const call = await readJson(file)
          if (!call?.resolvedAt || now - call.resolvedAt <= maxAge) continue
        }
        if (now - (await stat(file)).mtimeMs > maxAge) {
          await rm(file, { force: true })
          if (directory === 'tool-calls') {
            const key = name.replace(/\.json$/, '')
            for (const outcome of Object.values(ExecutionOutcome)) {
              await rm(path.join(home, 'tool-outcomes', `${key}-${outcome}.json`), { force: true })
              await rm(path.join(home, 'tool-outcomes', `${key}-${outcome}.json.sent`), { force: true })
            }
          }
        }
      } catch (error) {
        if (error?.code !== 'ENOENT') throw error
      }
    }
  }
  await writeJsonAtomic(maintenancePath(home), { at: now })
}

async function queueFiles(home) {
  try {
    return (await readdir(queuePath(home))).filter((name) => name.endsWith('.json')).sort()
  } catch (error) {
    if (error?.code === 'ENOENT') return []
    throw error
  }
}

async function postActera(config, endpoint, body, timeoutMs) {
  const response = await fetch(`${config.baseUrl}/v1/${endpoint}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${config.apiKey}` },
    body: JSON.stringify(body),
    redirect: 'error',
    signal: AbortSignal.timeout(timeoutMs),
  })
  if (response.status === 429) throw await limitError(endpoint, response)
  if (!response.ok) throw new Error(`Actera ${endpoint} returned HTTP ${response.status}`)
  return response.json()
}

// Actera reports a monthly limit with the time left in the month. Retrying
// sooner is refused, and the wait is capped so a plan change is noticed.
const MAX_RETRY_WAIT_MS = 60 * 60 * 1000

async function limitError(endpoint, response) {
  const body = await response.json().catch(() => undefined)
  const monthly = body?.message === 'evaluation_monthly_limit_exceeded'
  const error = new Error(monthly
    ? 'This Actera workspace has used its monthly decisions. New activity is not recorded until the limit resets or the plan changes; see Plan & usage in Actera.'
    : `Actera ${endpoint} returned HTTP 429`)
  error.monthlyLimit = monthly
  const seconds = Number(response.headers.get('retry-after'))
  if (seconds > 0) error.retryAfterMs = Math.min(seconds * 1000, MAX_RETRY_WAIT_MS)
  return error
}

// Tells the person about a monthly limit once a day rather than on every tool call.
export async function limitNotice(error, home = bridgeHome()) {
  if (!error?.monthlyLimit) return undefined
  const last = await readJson(limitNoticePath(home))
  if (last?.at > Date.now() - 24 * 60 * 60 * 1000) return undefined
  await writeJsonAtomic(limitNoticePath(home), { at: Date.now() })
  return error.message
}

export async function deliverBatch(config, { home = bridgeHome(), limit = Infinity, timeoutMs = 1500, force = false } = {}) {
  await pruneLocalState(home)
  const files = await queueFiles(home)
  if (!files.length) return { sent: 0, pending: 0 }
  const offline = await readJson(offlinePath(home))
  if (!force && offline?.until > Date.now()) return { sent: 0, pending: files.length, offline: true }
  let sent = 0
  try {
    for (const file of files.slice(0, limit)) {
      const fullPath = path.join(queuePath(home), file)
      let activity
      try {
        activity = await readJson(fullPath)
      } catch (error) {
        throw new Error(`Cannot read queued event ${file}: ${error.message}`)
      }
      if (!activity) continue // Another hook invocation delivered the same file.
      // Old plugin versions queued derived enforcement reports. They contain no
      // execution evidence and must not prevent delivery of actual outcomes.
      if (activity.enforcement && !activity.outcome) {
        if (activity._decision_request && !activity.decision_id) {
          activity = { _decision_request: activity._decision_request }
        } else {
          await rm(fullPath, { force: true })
          continue
        }
      }
      const { _decision_request: request, _tool_call_key: callKey, ...report } = activity
      const acknowledgement = callKey && path.join(home, 'tool-outcomes', `${callKey}-${report.outcome}.json.sent`)
      if (acknowledgement && await readJson(acknowledgement)) {
        await rm(fullPath, { force: true })
        continue
      }
      const decisionOnly = request && Object.keys(report).length === 0
      if (report.event_type) throw new Error("Legacy queued reports must be archived by reconnecting; they are not replayed into usage")
      if (!report.decision_id && request) {
        const decision = await postActera(config, 'decisions', request, timeoutMs)
        if (!decision?.id) throw new Error('Actera returned an invalid Decision')
        report.decision_id = decision.id
      }
      if (decisionOnly) {
        await rm(fullPath, { force: true })
        sent++
        continue
      }
      if (!report.decision_id) throw new Error('Legacy hook queue requires migration; reconnect using the new plugin')
      await postActera(config, `decisions/${encodeURIComponent(report.decision_id)}/reports`, report, timeoutMs)
      if (callKey && [ExecutionOutcome.SUCCESS, ExecutionOutcome.FAILURE].includes(report.outcome)) {
        const callFile = toolCallPath(home, callKey)
        const call = await readJson(callFile)
        if (call) await writeJsonAtomic(callFile, { ...call, resolvedAt: Date.now() })
      }
      if (acknowledgement) await writeJsonAtomic(acknowledgement, { at: Date.now() })
      await writeJsonAtomic(deliveredPath(home), {
        at: new Date().toISOString(),
        outcome: activity.outcome,
        agentId: activity.agent.id,
        sessionId: activity.context?.claude?.session_id || activity.context?.codex?.session_id || null,
        toolName: activity.details?.tool_name || null,
      })
      await rm(fullPath, { force: true })
      sent++
    }
    await rm(offlinePath(home), { force: true })
  } catch (error) {
    if (!force) await writeJsonAtomic(offlinePath(home), { until: Date.now() + 10_000 })
    return { sent, pending: (await queueFiles(home)).length, error: error.message, retryAfterMs: error.retryAfterMs }
  }
  return { sent, pending: (await queueFiles(home)).length }
}

// Explicit flushes use the same elected sender as background delivery.
export async function flush(config, { home = bridgeHome(), force = false } = {}) {
  if (!(await queueFiles(home)).length) return { sent: 0, pending: 0 }
  const worker = await deliveryStatus(home)
  if (!force && worker.nextRetryAt && Date.parse(worker.nextRetryAt) > Date.now())
    return { sent: 0, pending: (await queueFiles(home)).length, offline: true }
  return flushDelivery(home)
}

// Removes this machine's connection after delivering what it can. The agent
// key stays valid in Actera until an administrator disables it.
export async function disconnect(home = bridgeHome(), { discard = false } = {}) {
  const config = await loadConfig(home)
  if (config && !discard) {
    const result = await flush(config, { home, force: true })
    if (result.pending)
      throw new Error(`${result.pending} report(s) could not be delivered${result.error ? ` (${result.error})` : ''}. Run disconnect --discard to delete them.`)
  }
  const revoke = config ? await revokeConnection(config) : undefined
  await stopDelivery(home)
  // Only a scanner that was extracted here can be running.
  const scanner = path.join(home, 'scanner')
  if (await stat(scanner).catch(() => undefined)) await stopScanner(scanner)
  await rm(home, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 })
  return { disconnected: !!config, home, ...revoke }
}

// Ends this connection in Actera too, so it stops showing as connected. A 401
// means the key no longer works, which is already the result we want. Local
// state is removed either way; the person can still disconnect in Actera.
export async function revokeConnection(config, timeoutMs = 5000) {
  try {
    const response = await fetch(`${config.baseUrl}/v1/connection/disconnect`, {
      method: 'POST',
      headers: { 'content-type': 'application/json', authorization: `Bearer ${config.apiKey}` },
      body: '{}',
      redirect: 'error',
      signal: AbortSignal.timeout(timeoutMs),
    })
    if (response.ok || response.status === 401) return { revoked: true }
    return { revoked: false, revokeError: `Actera returned HTTP ${response.status}. Disconnect the agent in Actera.` }
  } catch (error) {
    return { revoked: false, revokeError: `Could not reach Actera (${error.message}). Disconnect the agent in Actera.` }
  }
}

// Hooks only hand off to the worker; commands that report on delivery wait for it.
export async function wakeDelivery(home = bridgeHome(), { wait = false } = {}) {
  if (!(await loadConfig(home))) return
  await (wait ? ensureDelivery(home) : startDelivery(home))
}

export async function pendingCount(home) {
  return (await queueFiles(home)).length
}

export async function queueSummary(home) {
  const files = await queueFiles(home)
  let executionReports = 0, decisionRetries = 0, oldest = Infinity
  for (const file of files) {
    try {
      const item = await readJson(path.join(queuePath(home), file))
      if (!item) continue
      if (item.outcome) executionReports++
      else decisionRetries++
      oldest = Math.min(oldest, (await stat(path.join(queuePath(home), file))).mtimeMs)
    } catch (error) { if (error.code !== 'ENOENT') throw error }
  }
  return { total: executionReports + decisionRetries, executionReports, decisionRetries,
    oldestPendingAt: Number.isFinite(oldest) ? new Date(oldest).toISOString() : null,
    oldestPendingAgeSeconds: Number.isFinite(oldest) ? Math.max(0, Math.floor((Date.now() - oldest) / 1000)) : 0 }
}

// Delivery and error state for a host's status command.
export async function localStatus(home = bridgeHome()) {
  const files = await queueFiles(home)
  return {
    pending: files.length,
    queue: await queueSummary(home),
    delivery: await deliveryStatus(home),
    lastDelivered: await readJson(deliveredPath(home)),
    lastError: await readJson(errorPath(home)),
  }
}

export async function recordEvaluationError(error, home = bridgeHome()) {
  await writeJsonAtomic(errorPath(home), { at: new Date().toISOString(), message: error.message })
}

// Retry a policy evaluation that could not be delivered by the pre-tool hook.
export async function enqueueDecision(request, home = bridgeHome()) {
  await queueReport(home, { _decision_request: request })
}
