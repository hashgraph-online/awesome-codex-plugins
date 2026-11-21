#!/usr/bin/env node
import { readFileSync } from 'node:fs'
import { createInterface } from 'node:readline'
import { recordEvaluationError } from '../../core/bridge.mjs'
import { openBrowser } from '../../core/pairing.mjs'
import { bridgeHome, codexEvaluationFailure, loadConfig, recordHookRun } from './bridge.mjs'
import { holdMs, pollMs, preToolUse } from './pre-tool-use.mjs'
import { holdWithReview } from './review.mjs'
import { SettingsError } from './settings.mjs'

// Codex starts this MCP server from the plugin, and the plugin's PreToolUse
// hook is an mcp_tool hook that calls pre_tool_use here. Unlike a command
// hook, a call on this server can ask the person in Codex (MCP elicitation)
// while it waits, which is how a held call is reviewed in Codex.

const { version } = JSON.parse(readFileSync(new URL('../../../package.json', import.meta.url), 'utf8'))
const HOOK_FIELDS = ['session_id', 'turn_id', 'transcript_path', 'cwd', 'model', 'permission_mode', 'tool_name', 'tool_use_id', 'tool_input']
const pending = new Map()
let canAsk = false
let nextId = 1

const send = (message) => process.stdout.write(JSON.stringify({ jsonrpc: '2.0', ...message }) + '\n')

// One elicitation; aborting withdraws it from Codex.
function ask(params, signal) {
  if (!canAsk || signal.aborted) return Promise.resolve({ action: 'cancel' })
  const id = `actera-review-${nextId++}`
  return new Promise((resolve) => {
    const settle = (answer) => {
      if (!pending.delete(id)) return
      signal.removeEventListener('abort', withdraw)
      resolve(answer)
    }
    const withdraw = () => {
      send({ method: 'notifications/cancelled', params: { requestId: id, reason: 'Decided in Actera' } })
      settle({ action: 'cancel' })
    }
    pending.set(id, settle)
    signal.addEventListener('abort', withdraw, { once: true })
    send({ id, method: 'elicitation/create', params })
  })
}

const tool = {
  name: 'pre_tool_use',
  title: 'Actera tool check',
  description: 'Called by the Actera PreToolUse hook to check a Codex tool call. Not for direct use.',
  inputSchema: {
    type: 'object',
    properties: Object.fromEntries(HOOK_FIELDS.map((field) => [field, field === 'tool_input' ? {} : { type: ['string', 'null'] }])),
    required: ['session_id', 'tool_name', 'tool_use_id', 'tool_input'],
  },
}

async function checkToolCall(args, meta) {
  // Codex marks the model's own MCP calls with turn metadata; hook calls carry none.
  if (meta?.['x-codex-turn-metadata'] || meta?.callId) throw new Error('pre_tool_use is only for the Actera hook')
  const hook = { hook_event_name: 'PreToolUse' }
  for (const field of HOOK_FIELDS) if (args?.[field] !== undefined && args[field] !== null) hook[field] = args[field]
  const home = bridgeHome()
  let config
  try {
    config = await loadConfig(home)
  } catch (error) {
    if (!(error instanceof SettingsError)) throw error
    await recordEvaluationError(error, home).catch(() => {})
    return codexEvaluationFailure(error)
  }
  if (!config) return null
  await recordHookRun(home, 'PreToolUse').catch(() => {})
  const hold = (decision) => holdWithReview(config, decision, home, hook, { holdMs: holdMs(), pollMs: pollMs(), ask, openBrowser })
  return preToolUse(hook, config, home, { hold })
}

async function handle(message) {
  if (message.method === 'initialize') {
    canAsk = !!message.params?.capabilities?.elicitation
    return send({
      id: message.id,
      result: {
        protocolVersion: message.params?.protocolVersion ?? '2025-06-18',
        capabilities: { tools: {} },
        serverInfo: { name: 'actera', title: 'Actera', version },
      },
    })
  }
  if (message.method === 'tools/list') return send({ id: message.id, result: { tools: [tool] } })
  if (message.method === 'tools/call') {
    try {
      if (message.params?.name !== tool.name) throw new Error(`Unknown tool ${message.params?.name}`)
      const output = await checkToolCall(message.params.arguments, message.params._meta)
      return send({ id: message.id, result: { content: [{ type: 'text', text: JSON.stringify(output ?? {}) }] } })
    } catch (error) {
      return send({ id: message.id, result: { isError: true, content: [{ type: 'text', text: `Actera: ${error.message}` }] } })
    }
  }
  if (message.id !== undefined && message.method) send({ id: message.id, result: {} })
}

createInterface({ input: process.stdin }).on('line', (line) => {
  if (!line.trim()) return
  let message
  try { message = JSON.parse(line) } catch { return }
  if (message.id !== undefined && !message.method) {
    // An elicitation answer; a JSON-RPC error counts as no answer.
    return pending.get(message.id)?.(message.result ?? { action: 'cancel' })
  }
  handle(message).catch((error) => process.stderr.write(`Actera MCP server: ${error.message}\n`))
})
