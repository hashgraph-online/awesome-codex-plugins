#!/usr/bin/env node
import {
  agentReadiness,
  deliverBatch,
  disconnect,
  provisionBridge,
  recordEvaluationError,
  reviewerLinkStatus,
  startReviewerLink,
} from '../../core/bridge.mjs'
import { stopDelivery } from '../../core/delivery.mjs'
import { connectWithSetupCode, openBrowser, pair } from '../../core/pairing.mjs'
import { stopScanner } from '../../core/scanner-client.mjs'
import {
  bridgeHome,
  codexEvaluationFailure,
  enqueueToolOutcome,
  holdForApproval,
  loadConfig,
  readHookInput,
  recordHookRun,
  status,
} from './bridge.mjs'
import { deliverQueued, holdMs, pollMs, preToolUse } from './pre-tool-use.mjs'
import { SettingsError, saveSetting } from './settings.mjs'
import path from 'node:path'

function option(name) {
  const index = process.argv.indexOf(`--${name}`)
  return index >= 0 ? process.argv[index + 1] : undefined
}

async function readText(stream) {
  let value = ''
  for await (const chunk of stream) {
    value += chunk.toString('utf8')
    if (value.length > 4096) throw new Error('API key input is too long')
  }
  return value
}

async function connect(home) {
  const setupCode = option('setup-code')
  const result = setupCode !== undefined
    ? await connectWithSetupCode({ client: 'codex', home, code: setupCode })
    : await pair({
      client: 'codex',
      home,
      reconnect: process.argv.includes('--reconnect'),
      onWaiting: ({ codeHint, browserUrl }) => process.stdout.write(`Confirm code ${codeHint} in the Actera page that just opened.\nIf it did not open, visit: ${browserUrl}\nWaiting for an administrator to approve the connection...\n`),
    })
  const { modeName, evaluationFailureName } = (await status(home)).settings
  process.stdout.write(`${result.alreadyConnected ? 'Actera was already connected' : 'Actera is connected'} to agent ${result.agentId}.\n`)
  if (process.env.ACTERA_API_ORIGIN) process.stdout.write(`Using the ACTERA_API_ORIGIN override: ${result.baseUrl}\n`)
  if (result.archivedEvents) process.stdout.write(`Preserved ${result.archivedEvents} undelivered reports from the previous connection in ${result.archivePath}.\n`)
  process.stdout.write(`Mode: ${modeName}. When Actera cannot evaluate: ${evaluationFailureName}.\n`)
}

async function main() {
  const command = process.argv[2]
  const home = bridgeHome()
  if (command === 'delivery-stop') { await stopDelivery(home); return }
  if (command === 'scanner-stop') { await stopScanner(path.join(home, 'scanner')); return }
  if (command === 'connect') { await connect(home); return }
  if (command === 'disconnect') {
    // Deliver here rather than through the core's background worker: Codex
    // waits for processes its commands leave running.
    const config = await loadConfig(home, {})
    if (config && !process.argv.includes('--discard')) {
      const result = await deliverBatch(config, { home, force: true, timeoutMs: 5000 })
      if (result.pending)
        throw new Error(`${result.pending} report(s) could not be delivered${result.error ? ` (${result.error})` : ''}. Run disconnect --discard to delete them.`)
    }
    process.stdout.write(JSON.stringify(await disconnect(home, { discard: true })) + '\n')
    return
  }
  if (command === 'setup') {
    if (!process.argv.includes('--api-key-stdin')) throw new Error('Pipe the agent key with --api-key-stdin')
    const result = await provisionBridge({
      baseUrl: option('base-url') ?? process.env.ACTERA_API_ORIGIN,
      agentId: option('agent-id'),
      capture: option('capture'),
      apiKey: (await readText(process.stdin)).trim(),
    }, home)
    process.stdout.write(`Configured ${result.agentId} for ${result.baseUrl} (${result.capture}).\n`)
    return
  }
  if (command === 'mode' || command === 'evaluation-failure') {
    await saveSetting(home, command === 'mode' ? 'mode' : 'evaluationFailure', process.argv[3])
    process.stdout.write(JSON.stringify((await status(home)).settings) + '\n')
    return
  }
  if (command === 'status') {
    process.stdout.write(JSON.stringify(await status(home), null, 2) + '\n')
    return
  }
  let config
  try { config = await loadConfig(home) } catch (error) {
    if (command !== 'hook' || !(error instanceof SettingsError)) throw error
    const hook = await readHookInput(process.stdin)
    await recordEvaluationError(error, home).catch(() => {})
    if (hook.hook_event_name === 'PreToolUse') process.stdout.write(JSON.stringify(codexEvaluationFailure(error)) + '\n')
    return
  }
  if (command === 'ready') {
    if (!config) throw new Error('Run setup first')
    process.stdout.write(JSON.stringify(await agentReadiness(config, undefined, home)) + '\n')
    return
  }
  if (command === 'link') {
    if (!config) throw new Error('Connect first with $actera-connect')
    const link = await startReviewerLink(config, home)
    openBrowser(link.browserUrl)
    process.stdout.write(`Link your signed-in Actera account in the page that just opened.\nIf it did not open, visit: ${link.browserUrl}\n`)
    return
  }
  if (command === 'link-status') {
    if (!config) throw new Error('Connect first with $actera-connect')
    process.stdout.write(JSON.stringify(await reviewerLinkStatus(config, home)) + '\n')
    return
  }
  if (command === 'flush') {
    if (!config) throw new Error('Run setup first')
    const result = await deliverBatch(config, { home, force: true, timeoutMs: 5000 })
    process.stdout.write(JSON.stringify(result) + '\n')
    if (result.error) process.exitCode = 1
    return
  }
  if (command === 'hook') {
    const hook = await readHookInput(process.stdin)
    if (!config) return
    await recordHookRun(home, hook.hook_event_name).catch(() => {})
    if (hook.hook_event_name === 'PreToolUse') {
      // Without Codex's MCP review prompt, a held call waits for a reviewer elsewhere.
      const hold = (decision) => holdForApproval(config, decision, home, { holdMs: holdMs(), pollMs: pollMs() })
      const output = await preToolUse(hook, config, home, { hold })
      if (output) process.stdout.write(JSON.stringify(output) + '\n')
      return
    }
    try {
      await enqueueToolOutcome(hook, config, home)
      await deliverQueued(config, home)
    } catch (error) {
      await recordEvaluationError(error, home).catch(() => {})
    }
    return // Other lifecycle hooks add nothing to Codex's context.
  }
  throw new Error('Usage: actera-hook.mjs connect [--setup-code CODE | --reconnect] | mode monitoring|enforcing | evaluation-failure block|allow | status | link | link-status | ready | flush | disconnect [--discard] | setup --api-key-stdin | hook')
}

main().catch((error) => {
  process.stderr.write(`Actera Codex bridge: ${error.message}\n`)
  process.exitCode = 1
})
