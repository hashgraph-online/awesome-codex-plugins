import { createHash, randomUUID } from 'node:crypto'
import { mkdir, readFile, rename, rm, writeFile } from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { setTimeout as delay } from 'node:timers/promises'
import {
  admittedCall,
  claimApproval,
  credentialID,
  decisionStatus,
  loadConfig as loadConnection,
  loadReviewer,
  localStatus,
  queueOutcomeReport,
  rememberAdmittedCall,
} from '../../core/bridge.mjs'
import { ExecutionOutcome } from '../../core/generated/outcomes.mjs'
import { captureInput } from '../../core/input-capture.mjs'
import { runtimeSettings } from './settings.mjs'

// Codex hook adapter: maps Codex's hook events onto Actera decisions, call
// identities and execution reports, and Decisions back onto Codex's
// PreToolUse output. A call that needs approval is held here while a
// reviewer decides in Actera, Slack or email, or in Codex (see review.mjs).
// Codex (0.165, Windows) does not finish a call until every process its hook
// started has exited, so this adapter starts no background helpers: reports
// are sent from the hook itself and the scanner runs once per call.

const MAX_HOOK_BYTES = 16 * 1024 * 1024
const MAX_TRANSCRIPT_BYTES = 256 * 1024 * 1024
const DETAIL_FIELDS = ['tool_name', 'tool_use_id', 'turn_id', 'source', 'model']

export function bridgeHome() {
  return process.env.ACTERA_CODEX_BRIDGE_HOME || path.join(os.homedir(), '.actera', 'codex')
}

export async function loadConfig(home = bridgeHome(), env = process.env) {
  const config = await loadConnection(home)
  return config ? { ...config, ...(await runtimeSettings(home, env)) } : undefined
}

function scalar(value) {
  return typeof value === 'string'
    ? value.slice(0, 1024)
    : typeof value === 'number' || typeof value === 'boolean'
      ? value
      : undefined
}

// Codex names MCP tools mcp__<server>__<tool>, like Claude Code. The server
// segment is a local registration key, so it is evidence, not the action type.
export function mcpToolForHook(hook) {
  const name = hook.tool_name
  if (typeof name !== 'string' || !name.startsWith('mcp__')) return undefined
  const remainder = name.slice('mcp__'.length)
  const separator = remainder.indexOf('__')
  if (separator < 1 || separator + 2 >= remainder.length) throw new Error('Codex supplied an invalid MCP tool name')
  return { server_key: remainder.slice(0, separator), tool_name: remainder.slice(separator + 2) }
}

export async function activityForHook(hook, config, home = bridgeHome(), eventId = randomUUID(), occurredAt = new Date().toISOString()) {
  if (!hook || typeof hook !== 'object' || Array.isArray(hook) || !/^[A-Za-z]+$/.test(hook.hook_event_name || ''))
    throw new Error('Invalid Codex hook event')
  const eventName = hook.hook_event_name
  const toolName = typeof hook.tool_name === 'string' ? hook.tool_name : undefined
  if (toolName?.length > 256) throw new Error('Codex tool name exceeds 256 characters')
  const mcp = mcpToolForHook(hook)
  const details = { schema_version: 1, source: 'codex_hook', event_id: eventId, capture: config.capture }
  for (const field of DETAIL_FIELDS) {
    const value = scalar(hook[field])
    if (value !== undefined) details[field] = value
  }
  if (hook.tool_input && typeof hook.tool_input === 'object' && !Array.isArray(hook.tool_input)) {
    details.tool_input_fields = Object.keys(hook.tool_input)
    // Codex waits on every process a hook leaves running, so the scanner
    // helper must exit before the hook does.
    const captured = await captureInput(hook.tool_input, config.capture, { scannerRoot: path.join(home, 'scanner'), persistentScanner: false })
    details.input_capture = captured.metadata
    if (captured.parameters !== undefined) details.tool_input = captured.parameters
    if (captured.metadata.status === 'omitted') details.tool_input_omitted = captured.metadata.reason
  }
  const codex = {}
  for (const field of ['session_id', 'turn_id', 'cwd', 'permission_mode', 'model']) {
    const value = scalar(hook[field])
    if (value !== undefined) codex[field] = value
  }
  return {
    idempotency_key: `codex-hook:${credentialID(config)}:${eventId}`,
    event_type: `codex.hook.${eventName}`,
    agent: { id: config.agentId },
    action: {
      type: mcp ? `codex.mcp.${mcp.tool_name}` : toolName ? `codex.tool.${toolName}` : `codex.hook.${eventName}`,
      attributes: { hook_event: eventName, ...(toolName ? { tool_name: toolName } : {}), ...(mcp ? { mcp } : {}) },
    },
    context: { codex },
    occurred_at: occurredAt,
    details,
  }
}

export function evaluationForHook(hook, config, activity) {
  if (hook.hook_event_name !== 'PreToolUse' || !activity.details.tool_name)
    throw new Error('Only PreToolUse tool calls can be evaluated')
  if (activity.details.tool_input_omitted && activity.details.tool_input_omitted !== 'metadata_only' && config.mode === 'ENFORCING')
    throw new Error(`Actera tool inputs unavailable: ${activity.details.tool_input_omitted}`)
  const callIdentity = [credentialID(config), hook.session_id || '', hook.tool_use_id || activity.details.event_id]
  const callHash = createHash('sha256').update(JSON.stringify(callIdentity)).digest('hex')
  return {
    idempotency_key: `codex-tool:${callHash}`,
    mode: config.mode || 'MONITORING',
    agent: { id: config.agentId },
    action: {
      type: activity.action.type,
      attributes: {
        tool_name: activity.details.tool_name,
        ...(activity.action.attributes.mcp ? { mcp: activity.action.attributes.mcp } : {}),
        ...(activity.details.tool_input ? { parameters: activity.details.tool_input } : {}),
        ...(activity.details.tool_input_fields ? { input_fields: activity.details.tool_input_fields } : {}),
      },
    },
    context: {
      codex: { ...activity.context.codex, ...(hook.tool_use_id ? { tool_use_id: hook.tool_use_id } : {}) },
      source: 'codex_hook',
      capture: config.capture || 'tool-inputs',
      ...(activity.details.input_capture ? { input_capture: activity.details.input_capture } : {}),
    },
  }
}

function toolCallKey(hook, config) {
  if (!hook.session_id || !hook.tool_use_id || typeof hook.tool_name !== 'string') return undefined
  return createHash('sha256')
    .update(JSON.stringify([config.baseUrl, credentialID(config), config.agentId, hook.session_id, hook.tool_use_id]))
    .digest('hex')
}

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`
  if (value && typeof value === 'object')
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
      .join(',')}}`
  return JSON.stringify(value)
}

// A retry is the same proposed effect only within one Codex session, for the
// same tool and exact arguments. Never persist plaintext tool arguments.
export function approvalFingerprint(hook, config) {
  if (!hook.session_id || typeof hook.tool_name !== 'string' || !hook.tool_input || typeof hook.tool_input !== 'object' || Array.isArray(hook.tool_input))
    return undefined
  return createHash('sha256')
    .update(canonicalJson([credentialID(config), config.agentId, hook.session_id, hook.tool_name, hook.tool_input]))
    .digest('hex')
}

export async function rememberToolDecision(hook, config, request, decision, home = bridgeHome()) {
  const key = toolCallKey(hook, config)
  if (!key) throw new Error('A session and tool invocation ID are required for reporting')
  await rememberAdmittedCall(home, key, { decisionId: decision?.id, request, fingerprint: approvalFingerprint(hook, config) })
}

// Codex reports no success flag to PostToolUse, but its session transcript
// records each call's final status under the same ID before the hook runs.
// The transcript format is not a documented contract, so anything
// unexpected leaves the outcome UNKNOWN rather than guessing.
export async function transcriptOutcome(hook) {
  if (typeof hook.transcript_path !== 'string' || typeof hook.tool_use_id !== 'string') return undefined
  let text
  try {
    text = await readFile(hook.transcript_path, 'utf8')
  } catch {
    return undefined
  }
  if (text.length > MAX_TRANSCRIPT_BYTES || !text.includes(hook.tool_use_id)) return undefined
  let status
  for (const line of text.split('\n')) {
    if (!line.includes(hook.tool_use_id)) continue
    try {
      const item = JSON.parse(line).payload?.item
      if (item?.id === hook.tool_use_id && typeof item.status === 'string') status = item.status
    } catch { /* A partially written last line is not evidence. */ }
  }
  return { completed: ExecutionOutcome.SUCCESS, failed: ExecutionOutcome.FAILURE, declined: ExecutionOutcome.CANCELLED }[status]
}

export async function enqueueToolOutcome(hook, config, home = bridgeHome()) {
  if (hook.hook_event_name !== 'PostToolUse') return undefined
  const key = toolCallKey(hook, config)
  if (!key) return undefined
  const admitted = await admittedCall(home, key)
  if (!admitted) return undefined
  const fingerprint = approvalFingerprint(hook, config)
  if (!fingerprint || fingerprint !== admitted.fingerprint)
    throw new Error('Post-tool call does not match the admitted Actera action')
  const request = admitted.request
  const reported = await transcriptOutcome(hook)
  const outcome = reported ?? ExecutionOutcome.UNKNOWN
  const details = {
    schema_version: 1,
    source: 'codex_hook',
    hook_event: hook.hook_event_name,
    tool_name: hook.tool_name,
    tool_use_id: hook.tool_use_id,
    outcome_scope: 'tool_call',
    outcome_source: reported ? 'codex_transcript' : 'unavailable',
    summary: {
      [ExecutionOutcome.SUCCESS]: 'Codex reported that the tool call completed successfully.',
      [ExecutionOutcome.FAILURE]: 'Codex reported that the tool call failed.',
      [ExecutionOutcome.CANCELLED]: 'Codex reported that the tool call was declined.',
      [ExecutionOutcome.UNKNOWN]: 'Codex ran the tool call but did not record whether it succeeded.',
    }[outcome],
  }
  return queueOutcomeReport(home, key, outcome, {
    idempotency_key: `codex-tool-outcome:${credentialID(config)}:${key}:${outcome}`,
    decision_id: admitted.decisionId,
    _decision_request: request,
    outcome,
    occurred_at: new Date().toISOString(),
    agent: request.agent,
    action: request.action,
    context: request.context,
    details,
  })
}

// Wait for a reviewer while Codex waits for this hook. An approval releases
// exactly this call; anything else ends the hold with the current status.
// Aborting stops the wait without claiming an approval.
export async function holdForApproval(config, decision, home = bridgeHome(), { holdMs, pollMs, signal } = {}) {
  const deadline = Date.now() + holdMs
  let current = decision
  while (Date.now() < deadline && !signal?.aborted) {
    try {
      await delay(Math.min(pollMs, Math.max(0, deadline - Date.now())), undefined, { signal })
      current = await decisionStatus(config, decision.id)
    } catch {
      continue // A transient lookup failure keeps the call held, never released.
    }
    if (signal?.aborted) break
    if (current.status === 'APPROVED')
      return (await claimApproval(home, decision.id)) ? current : { ...current, status: 'ALREADY_RELEASED' }
    if (current.status !== 'PENDING_APPROVAL') return current
  }
  return current
}

// Codex shows these reasons to the model, which relays them to the person.
export function codexToolDecision(decision) {
  // Codex (0.165) rejects permissionDecision "allow" as a hook failure, so an
  // allowed or approved call returns nothing and Codex's own approval flow
  // still applies.
  if (decision.status === 'ALLOWED' || decision.status === 'APPROVED') return null
  // Codex appends ". Command: ..." to the reason, so it carries no final period.
  const deny = (reason) => ({ hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny', permissionDecisionReason: reason.replace(/\.$/, '') } })
  const review = decision.review_url ? ` Review it at ${decision.review_url}.` : ''
  if (decision.status === 'PENDING_APPROVAL' && decision.unansweredInCodex)
    return deny(`Actera is holding this tool call for a reviewer (decision ${decision.id}), and it was not approved in Codex. Ask the person to approve it in Actera${decision.review_url ? ` at ${decision.review_url}` : ''}. Once it is approved, retry this exact tool call; the approval releases one matching retry. Codex cannot show Actera's prompt when approvals are off (Full access) or in codex exec.`)
  if (decision.status === 'PENDING_APPROVAL')
    return deny(`Actera decision ${decision.id} is still waiting for a reviewer.${review} Once it is approved, retry this exact tool call; the approval releases one matching retry.`)
  if (decision.status === 'ALREADY_RELEASED')
    return deny(`Actera decision ${decision.id} was approved, but that approval already released another call.`)
  if (decision.status === 'REVIEW_FAILED')
    return deny(`Actera did not record your review of decision ${decision.id}: ${decision.explanation} The call is still held; retry it to review again or approve it in Actera.`)
  if (decision.status === 'REJECTED' && decision.reviewedIn === 'codex')
    return deny(`The person denied this tool call in Codex (Actera decision ${decision.id}). Do not retry it unless they ask.`)
  if (decision.status === 'REJECTED')
    return deny(`A reviewer rejected this tool call in Actera (decision ${decision.id})${decision.reason ? `: ${decision.reason}` : '.'}`)
  return deny(`Actera decision ${decision.id} ${decision.status.toLowerCase().replaceAll('_', ' ')}: ${decision.explanation || 'Tool call not allowed.'}`)
}

// Untrusted or disabled Codex hooks never run and say nothing, so the plugin
// records each run; status reports a connection whose hooks have never run.
export async function recordHookRun(home, event) {
  const file = path.join(home, 'last-hook.json')
  await mkdir(home, { recursive: true, mode: 0o700 })
  const temporary = `${file}.${randomUUID()}.tmp`
  try {
    await writeFile(temporary, JSON.stringify({ at: new Date().toISOString(), event }) + '\n', { mode: 0o600 })
    await rename(temporary, file)
  } finally {
    await rm(temporary, { force: true })
  }
}

async function lastHookRun(home) {
  try { return JSON.parse(await readFile(path.join(home, 'last-hook.json'), 'utf8')) } catch { return null }
}

export function codexEvaluationFailure(error) {
  return { hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny', permissionDecisionReason: `Actera could not evaluate this tool call: ${error.message}` } }
}

export async function status(home = bridgeHome(), env = process.env) {
  const config = await loadConfig(home, env)
  const { delivery, ...local } = await localStatus(home)
  const lastHook = await lastHookRun(home)
  return {
    configured: !!config,
    settings: await runtimeSettings(home, env),
    settingsManagedBy: '$actera-mode',
    ...(config ? { baseUrl: config.baseUrl, agentId: config.agentId, capture: config.capture, mode: config.mode, onEvaluationError: config.onEvaluationError } : {}),
    lastHook,
    // Whether this machine holds a reviewer link; Actera confirms it per review.
    ...(config ? { reviewerLinked: await loadReviewer(config, home).then(() => true, () => false) } : {}),
    ...(config && !lastHook ? { hooksNeedAttention: 'No Actera hook has run in Codex yet. Open /hooks in Codex, trust the Actera hooks, then start a new session.' } : {}),
    // Reports are sent by the hooks themselves; there is no background worker.
    ...local,
  }
}

export async function readHookInput(stream) {
  const chunks = []
  let size = 0
  for await (const chunk of stream) {
    size += chunk.length
    if (size > MAX_HOOK_BYTES) throw new Error('Codex hook input exceeds 16 MiB')
    chunks.push(chunk)
  }
  return JSON.parse(Buffer.concat(chunks).toString('utf8'))
}
